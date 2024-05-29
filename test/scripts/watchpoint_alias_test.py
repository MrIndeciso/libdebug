#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2023-2024 Francesco Panebianco, Gabriele Digregorio, Roberto Alessandro Bertolini. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import unittest

from libdebug import debugger


class WatchpointAliasTest(unittest.TestCase):
    def test_watchpoint_alias(self):
        d = debugger("binaries/watchpoint_test", auto_interrupt_on_command=False)

        d.run()

        d.watchpoint("global_char", condition="rw", length=1)
        d.watchpoint("global_int", condition="w", length=4)
        d.watchpoint("global_long", condition="rw", length=8)

        d.cont()

        self.assertEqual(d.rip, 0x401111)  # mov byte ptr [global_char], 0x1

        d.cont()

        self.assertEqual(d.rip, 0x401124)  # mov dword ptr [global_int], 0x4050607

        d.cont()

        self.assertEqual(
            d.rip, 0x401135
        )  # mov qword ptr [global_long], 0x8090a0b0c0d0e0f

        d.cont()

        self.assertEqual(d.rip, 0x401155)  # movzx eax, byte ptr [global_char]

        d.cont()

        self.assertEqual(d.rip, 0x401173)  # mov rax, qword ptr [global_long]

        d.cont()

        d.kill()

    def test_watchpoint_callback(self):
        global_char_ip = []
        global_int_ip = []
        global_long_ip = []

        def watchpoint_global_char(t, b):
            nonlocal global_char_ip

            global_char_ip.append(t.rip)

        def watchpoint_global_int(t, b):
            nonlocal global_int_ip

            global_int_ip.append(t.rip)

        def watchpoint_global_long(t, b):
            nonlocal global_long_ip

            global_long_ip.append(t.rip)

        d = debugger("binaries/watchpoint_test", auto_interrupt_on_command=False)

        d.run()

        wp1 = d.watchpoint(
            "global_char", condition="rw", length=1, callback=watchpoint_global_char
        )
        wp2 = d.watchpoint(
            "global_int", condition="w", length=4, callback=watchpoint_global_int
        )
        wp3 = d.watchpoint(
            "global_long", condition="rw", length=8, callback=watchpoint_global_long
        )

        d.cont()

        d.kill()

        self.assertEqual(global_char_ip[0], 0x401111)  # mov byte ptr [global_char], 0x1
        self.assertEqual(
            global_int_ip[0], 0x401124
        )  # mov dword ptr [global_int], 0x4050607
        self.assertEqual(
            global_long_ip[0], 0x401135
        )  # mov qword ptr [global_long], 0x8090a0b0c0d0e0f
        self.assertEqual(
            global_char_ip[1], 0x401155
        )  # movzx eax, byte ptr [global_char]
        self.assertEqual(
            global_long_ip[1], 0x401173
        )  # mov rax, qword ptr [global_long]

        self.assertEqual(len(global_char_ip), 2)
        self.assertEqual(len(global_int_ip), 1)

        # There is one extra hit performed by the exit routine of libc
        self.assertEqual(len(global_long_ip), 3)

        self.assertEqual(wp1.hit_count, 2)
        self.assertEqual(wp2.hit_count, 1)

        # There is one extra hit performed by the exit routine of libc
        self.assertEqual(wp3.hit_count, 3)
