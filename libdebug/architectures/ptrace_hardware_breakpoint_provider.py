#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2023-2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from typing import Callable

from libdebug.architectures.aarch64.aarch64_ptrace_hw_bp_helper import (
    Aarch64HardwareBreakpointManager,
)
from libdebug.architectures.amd64.amd64_ptrace_hw_bp_helper import (
    Amd64PtraceHardwareBreakpointManager,
)
from libdebug.architectures.i386.i386_ptrace_hw_bp_helper import (
    I386PtraceHardwareBreakpointManager,
)
from libdebug.architectures.ptrace_hardware_breakpoint_manager import (
    PtraceHardwareBreakpointManager,
)
from libdebug.state.thread_context import ThreadContext
from libdebug.utils.libcontext import libcontext


def ptrace_hardware_breakpoint_manager_provider(
    thread: ThreadContext,
    peek_user: Callable[[int, int], int],
    poke_user: Callable[[int, int, int], None],
) -> PtraceHardwareBreakpointManager:
    """Returns an instance of the hardware breakpoint manager to be used by the `_InternalDebugger` class."""
    platform = libcontext.platform

    match platform:
        case "x86_64":
            return Amd64PtraceHardwareBreakpointManager(thread, peek_user, poke_user)
        case "i686":
            return I386PtraceHardwareBreakpointManager(thread, peek_user, poke_user)
        case "aarch64":
            return Aarch64HardwareBreakpointManager(thread, peek_user, poke_user)
        case _:
            raise NotImplementedError(f"Platform {platform} not available.")
