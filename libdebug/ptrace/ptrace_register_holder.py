#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from dataclasses import dataclass
from typing import Callable

from libdebug.data.register_holder import RegisterHolder


@dataclass
class PtraceRegisterHolder(RegisterHolder):
    """An abstract class that holds the state of the registers of a process, specifically for the `ptrace` debugging backend.

    This class should not be instantiated directly, but rather through the `register_holder_provider` function.

    Attributes:
        register_file (object): The content of the register file of the process, as returned by `ptrace`.
        fp_register_file (object): The content of the floating-point register file of the process, as returned by `ptrace`.
        fp_get_callback (callable[[], None]): A callback function that updates the floating-point register file of the process.
        fp_set_callback (callable[[], None]): A callback function that updates the floating-point register file of the process.
    """

    register_file: object
    fp_register_file: object
    fp_get_callback: Callable[[], None]
    fp_set_callback: Callable[[], None]
