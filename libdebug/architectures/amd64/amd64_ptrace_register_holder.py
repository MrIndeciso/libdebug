#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2023-2024 Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

from dataclasses import dataclass

from libdebug.ptrace.ptrace_register_holder import PtraceRegisterHolder
from libdebug.utils.register_utils import (
    get_reg_8h,
    get_reg_8l,
    get_reg_16,
    get_reg_32,
    get_reg_64,
    set_reg_8h,
    set_reg_8l,
    set_reg_16,
    set_reg_32,
    set_reg_64,
)

AMD64_GP_REGS = ["a", "b", "c", "d"]

AMD64_BASE_REGS = ["bp", "sp", "si", "di"]

AMD64_EXT_REGS = ["r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]

AMD64_REGS = [
    "r15",
    "r14",
    "r13",
    "r12",
    "rbp",
    "rbx",
    "r11",
    "r10",
    "r9",
    "r8",
    "rax",
    "rcx",
    "rdx",
    "rsi",
    "rdi",
    "orig_rax",
    "rip",
    "cs",
    "eflags",
    "rsp",
    "ss",
    "fs_base",
    "gs_base",
    "ds",
    "es",
    "fs",
    "gs",
]


@dataclass
class Amd64PtraceRegisterHolder(PtraceRegisterHolder):
    """A class that provides views and setters for the registers of an x86_64 process, specifically for the `ptrace` debugging backend."""

    def apply_on(self, target, target_class):
        target.regs = self.register_file

        # If the accessors are already defined, we don't need to redefine them
        if hasattr(target_class, "instruction_pointer"):
            return

        def get_property_64(name):
            def getter(self):
                return get_reg_64(self.regs, name)

            def setter(self, value):
                set_reg_64(self.regs, name, value)

            return property(getter, setter, None, name)

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
        for name in AMD64_GP_REGS:
            name_64 = "r" + name + "x"
            name_32 = "e" + name + "x"
            name_16 = name + "x"
            name_8l = name + "l"
            name_8h = name + "h"

            setattr(target_class, name_64, get_property_64(name_64))
            setattr(target_class, name_32, get_property_32(name_64))
            setattr(target_class, name_16, get_property_16(name_64))
            setattr(target_class, name_8l, get_property_8l(name_64))
            setattr(target_class, name_8h, get_property_8h(name_64))

        for name in AMD64_BASE_REGS:
            name_64 = "r" + name
            name_32 = "e" + name
            name_16 = name
            name_8l = name + "l"

            setattr(target_class, name_64, get_property_64(name_64))
            setattr(target_class, name_32, get_property_32(name_64))
            setattr(target_class, name_16, get_property_16(name_64))
            setattr(target_class, name_8l, get_property_8l(name_64))

        for name in AMD64_EXT_REGS:
            name_64 = name
            name_32 = name + "d"
            name_16 = name + "w"
            name_8l = name + "b"

            setattr(target_class, name_64, get_property_64(name_64))
            setattr(target_class, name_32, get_property_32(name_64))
            setattr(target_class, name_16, get_property_16(name_64))
            setattr(target_class, name_8l, get_property_8l(name_64))

        # setup special registers
        setattr(target_class, "rip", get_property_64("rip"))

        # setup generic "instruction_pointer" property
        setattr(target_class, "instruction_pointer", get_property_64("rip"))

        # setup generic syscall properties
        setattr(target_class, "syscall_number", get_property_64("orig_rax"))
        setattr(target_class, "syscall_return", get_property_64("rax"))
        setattr(target_class, "syscall_arg0", get_property_64("rdi"))
        setattr(target_class, "syscall_arg1", get_property_64("rsi"))
        setattr(target_class, "syscall_arg2", get_property_64("rdx"))
        setattr(target_class, "syscall_arg3", get_property_64("r10"))
        setattr(target_class, "syscall_arg4", get_property_64("r8"))
        setattr(target_class, "syscall_arg5", get_property_64("r9"))

        # now for the floating point registers
        fpregs_size = self.fp_register_file.fpregs_component_size

        match fpregs_size:
            case 896:
                self._handle_fpregs_896(target, target_class)
            case 2560:
                self._handle_fpregs_2560(target, target_class)
            case _:
                raise ValueError(
                    f"Unsupported floating point register size: {fpregs_size}"
                )

    def _handle_fpregs_896(self, target, target_class):
        # standard avx register configuration
        from cffi import FFI

        ffi = FFI()

        target.fpregs = ffi.buffer(self.fp_register_file, 4096)

        ymm_offset = 8 + self.fp_register_file.fpregs_avx_offset
        xmm_offset = 8 + 160

        def get_ymm_property(name, offset, ptrace_getter, ptrace_setter):
            def getter(self):
                ptrace_getter(self)

                xmm_val = int.from_bytes(
                    self.fpregs[xmm_offset + offset : xmm_offset + offset + 16],
                    "little",
                )
                ymm_val = int.from_bytes(
                    self.fpregs[ymm_offset + offset : ymm_offset + offset + 16],
                    "little",
                )
                return ymm_val << 128 | xmm_val

            def setter(self, value):
                xmm_val = value & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                ymm_val = value >> 128
                self.fpregs[xmm_offset + offset : xmm_offset + offset + 16] = (
                    xmm_val.to_bytes(16, "little")
                )
                self.fpregs[ymm_offset + offset : ymm_offset + offset + 16] = (
                    ymm_val.to_bytes(16, "little")
                )

                ptrace_setter(self)

            return property(getter, setter, None, name)

        for i in range(16):
            name = f"ymm{i}"
            offset = i * 16
            setattr(
                target_class,
                name,
                get_ymm_property(
                    name,
                    offset,
                    self.fp_get_callback,
                    self.fp_set_callback,
                ),
            )

    def _handle_fpregs_2560(self, target, target_class):
        self._handle_fpregs_896(target, target_class)

        # avx512 register configuration
        xmm_offset = 160
        ymm_offset = 576
        avx_zmm_0_offset = 1024
        avx_zmm_1_offset = 1536

        def get_zmm_property_0(name, offset, ptrace_getter, ptrace_setter):
            def getter(self):
                ptrace_getter(self)

                xmm_val = int.from_bytes(
                    self.fpregs[xmm_offset + offset : xmm_offset + offset + 16],
                    "little",
                )
                ymm_val = int.from_bytes(
                    self.fpregs[ymm_offset + offset : ymm_offset + offset + 16],
                    "little",
                )
                zmm_val = int.from_bytes(
                    self.fpregs[
                        avx_zmm_0_offset + (offset * 2) : avx_zmm_0_offset
                        + (offset * 2)
                        + 32
                    ],
                    "little",
                )
                return zmm_val << 256 | ymm_val << 128 | xmm_val

            def setter(self, value):
                xmm_val = value & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                ymm_val = (value >> 128) & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                zmm_val = value >> 256

                self.fpregs[xmm_offset + offset : xmm_offset + offset + 16] = (
                    xmm_val.to_bytes(16, "little")
                )
                self.fpregs[ymm_offset + offset : ymm_offset + offset + 16] = (
                    ymm_val.to_bytes(16, "little")
                )
                self.fpregs[
                    avx_zmm_0_offset + (offset * 2) : avx_zmm_0_offset
                    + (offset * 2)
                    + 32
                ] = zmm_val.to_bytes(32, "little")

                ptrace_setter(self)

            return property(getter, setter, None, name)

        def get_zmm_property_1(name, offset, ptrace_getter, ptrace_setter):
            def getter(self):
                ptrace_getter(self)

                zmm_val = int.from_bytes(
                    self.fpregs[
                        avx_zmm_1_offset + offset : avx_zmm_1_offset + offset + 64
                    ],
                    "little",
                )

                return zmm_val

            def setter(self, value):
                zmm_val = value

                self.fpregs[
                    avx_zmm_1_offset + offset : avx_zmm_1_offset + offset + 64
                ] = zmm_val.to_bytes(64, "little")

                ptrace_setter(self)

            return property(getter, setter, None, name)

        for i in range(16):
            name = f"zmm{i}"
            offset = i * 16
            setattr(
                target_class,
                name,
                get_zmm_property_0(
                    name,
                    offset,
                    self.fp_get_callback,
                    self.fp_set_callback,
                ),
            )

        for i in range(16, 32):
            name = f"zmm{i}"
            offset = i * 64
            setattr(
                target_class,
                name,
                get_zmm_property_1(
                    name,
                    offset,
                    self.fp_get_callback,
                    self.fp_set_callback,
                ),
            )
