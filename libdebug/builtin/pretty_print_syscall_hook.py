#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2024 Roberto Alessandro Bertolini, Gabriele Digregorio. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from typing import TYPE_CHECKING, Tuple, Any
from libdebug.utils.print_style import PrintStyle
from libdebug.utils.syscall_utils import (
    resolve_syscall_name,
    resolve_syscall_arguments,
)

if TYPE_CHECKING:
    from libdebug.state.thread_context import ThreadContext

def pprint_on_enter(d: "ThreadContext", syscall_number: int, **kwargs: Any):
    """Function that will be called when a syscall is entered in pretty print mode.

    Args:
        d (ThreadContext): the thread context.
        syscall_number (int): the syscall number.
        **kwargs (bool): the keyword arguments.
    """
    syscall_name = resolve_syscall_name(syscall_number)
    syscall_args = resolve_syscall_arguments(syscall_number)

    values = [
        d.syscall_arg0,
        d.syscall_arg1,
        d.syscall_arg2,
        d.syscall_arg3,
        d.syscall_arg4,
        d.syscall_arg5,
    ]

    if "old_args" in kwargs:
        old_args = kwargs["old_args"]
        entries = [
            f"{arg} = {PrintStyle.BRIGHT_YELLOW}0x{value:x}{PrintStyle.DEFAULT_COLOR}"
            if old_value == value
            else f"{arg} = {PrintStyle.BRIGHT_YELLOW}0x{old_value:x} -> {PrintStyle.BRIGHT_YELLOW}0x{value:x}{PrintStyle.DEFAULT_COLOR}"
            for arg, value, old_value in zip(syscall_args, values, old_args)
            if arg is not None
        ]
    else:
        entries = [
            f"{arg} = {PrintStyle.BRIGHT_YELLOW}0x{value:x}{PrintStyle.DEFAULT_COLOR}"
            for arg, value in zip(syscall_args, values)
            if arg is not None
        ]

    hijacked = kwargs.get("hijacked", False)
    user_hooked = kwargs.get("user_hooked", False)
    if hijacked:
        print(
            f"{PrintStyle.RED}(user hijacked) {PrintStyle.STRIKE}{PrintStyle.BLUE}{syscall_name}{PrintStyle.DEFAULT_COLOR}({', '.join(entries)}){PrintStyle.RESET}"
        )
    elif user_hooked:
        print(
            f"{PrintStyle.RED}(user hooked) {PrintStyle.BLUE}{syscall_name}{PrintStyle.DEFAULT_COLOR}({', '.join(entries)}) = ",
            end="",
        )
    else:
        print(
            f"{PrintStyle.BLUE}{syscall_name}{PrintStyle.DEFAULT_COLOR}({', '.join(entries)}) = ",
            end="",
        )


def pprint_on_exit(syscall_return: int | Tuple[int, int]):
    """Function that will be called when a syscall is exited in pretty print mode.

    Args:
        syscall_return (int | list[int]): the syscall return value.
    """

    if isinstance(syscall_return, Tuple):
        print(
            f"{PrintStyle.YELLOW}{PrintStyle.STRIKE}0x{syscall_return[0]:x}{PrintStyle.RESET} {PrintStyle.YELLOW}0x{syscall_return[1]:x}{PrintStyle.RESET}"
        )
    else:
        print(f"{PrintStyle.YELLOW}0x{syscall_return:x}{PrintStyle.RESET}")
