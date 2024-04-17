#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from libdebug.ptrace.ptrace_register_holder import PtraceRegisterHolder
from libdebug.utils.register_utils import (
    get_reg_8h,
    get_reg_8l,
    get_reg_16,
    get_reg_32,
    set_reg_8h,
    set_reg_8l,
    set_reg_16,
    set_reg_32,
)

I386_GP_REGS = ["a", "b", "c", "d"]

I386_BASE_REGS = ["bp", "sp", "si", "di"]


class I386PtraceRegisterHolder(PtraceRegisterHolder):
    """A class that provides views and setters for the registers of an i386 process, specifically for the `ptrace` debugging backend."""

    def apply_on(self, target, target_class):
        target.regs = self.register_file

        # If the accessors are already defined, we don't need to redefine them
        if hasattr(target_class, "instruction_pointer"):
            return

        def get_property_32(name):
            def getter(self):
                return get_reg_32(self.regs, name)

            def setter(self, value):
                set_reg_32(self.regs, name, value)

            return property(getter, setter, None, name)

        def get_property_16(name):
            def getter(self):
                return get_reg_16(self.regs, name)

            def setter(self, value):
                set_reg_16(self.regs, name, value)

            return property(getter, setter, None, name)

        def get_property_8l(name):
            def getter(self):
                return get_reg_8l(self.regs, name)

            def setter(self, value):
                set_reg_8l(self.regs, name, value)

            return property(getter, setter, None, name)

        def get_property_8h(name):
            def getter(self):
                return get_reg_8h(self.regs, name)

            def setter(self, value):
                set_reg_8h(self.regs, name, value)

            return property(getter, setter, None, name)

        # setup accessors
        for name in I386_GP_REGS:
            name_32 = "e" + name + "x"
            name_16 = name + "x"
            name_8l = name + "l"
            name_8h = name + "h"

            setattr(target_class, name_32, get_property_32(name_32))
            setattr(target_class, name_16, get_property_16(name_32))
            setattr(target_class, name_8l, get_property_8l(name_32))
            setattr(target_class, name_8h, get_property_8h(name_32))

        for name in I386_BASE_REGS:
            name_32 = "e" + name
            name_16 = name

            setattr(target_class, name_32, get_property_32(name_32))
            setattr(target_class, name_16, get_property_16(name_32))

        # setup special registers
        setattr(target_class, "eip", get_property_32("eip"))

        # setup generic "instruction_pointer" property
        setattr(target_class, "instruction_pointer", get_property_32("eip"))

        # setup generic syscall properties
        setattr(target_class, "syscall_number", get_property_32("orig_eax"))
        setattr(target_class, "syscall_return", get_property_32("eax"))
        setattr(target_class, "syscall_arg0", get_property_32("ebx"))
        setattr(target_class, "syscall_arg1", get_property_32("ecx"))
        setattr(target_class, "syscall_arg2", get_property_32("edx"))
        setattr(target_class, "syscall_arg3", get_property_32("esi"))
        setattr(target_class, "syscall_arg4", get_property_32("edi"))
        setattr(target_class, "syscall_arg5", get_property_32("ebp"))
