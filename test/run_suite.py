#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2023-2024 Gabriele Digregorio, Roberto Alessandro Bertolini, Francesco Panebianco. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import sys
import unittest

from scripts.attach_test import AttachTest
from scripts.auto_waiting_test import AutoWaitingNcuts, AutoWaitingTest
from scripts.backtrace_test import BacktraceTest
from scripts.basic_test import BasicPieTest, BasicTest, ControlFlowTest, HwBasicTest
from scripts.breakpoint_test import BreakpointTest
from scripts.brute_test import BruteTest
from scripts.builtin_hooks_test import AntidebugEscapingTest
from scripts.callback_test import CallbackTest
from scripts.finish_test import FinishTest
from scripts.deep_dive_division import DeepDiveDivision
from scripts.hijack_syscall_test import SyscallHijackTest
from scripts.jumpout import Jumpout
from scripts.large_binary_sym_test import LargeBinarySymTest
from scripts.memory_test import MemoryTest
from scripts.multiple_debuggers_test import MultipleDebuggersTest
from scripts.ncuts import Ncuts
from scripts.pprint_syscalls_test import PPrintSyscallsTest
from scripts.speed_test import SpeedTest
from scripts.syscall_hook_test import SyscallHookTest
from scripts.thread_test import ComplexThreadTest, ThreadTest
from scripts.vmwhere1 import Vmwhere1
from scripts.waiting_test import WaitingNcuts, WaitingTest
from scripts.watchpoint_alias_test import WatchpointAliasTest
from scripts.watchpoint_test import WatchpointTest


def fast_suite():
    suite = unittest.TestSuite()
    suite.addTest(BasicTest("test_basic"))
    suite.addTest(BasicTest("test_registers"))
    suite.addTest(BasicTest("test_step"))
    suite.addTest(BasicTest("test_step_hardware"))
    suite.addTest(BasicPieTest("test_basic"))
    suite.addTest(BreakpointTest("test_bps"))
    suite.addTest(BreakpointTest("test_bp_disable"))
    suite.addTest(BreakpointTest("test_bp_disable_hw"))
    suite.addTest(BreakpointTest("test_bp_disable_reenable"))
    suite.addTest(BreakpointTest("test_bp_disable_reenable_hw"))
    suite.addTest(MemoryTest("test_memory"))
    suite.addTest(MemoryTest("test_mem_access_libs"))
    suite.addTest(MemoryTest("test_memory_exceptions"))
    suite.addTest(HwBasicTest("test_basic"))
    suite.addTest(HwBasicTest("test_registers"))
    suite.addTest(BacktraceTest("test_backtrace"))
    suite.addTest(AttachTest("test_attach"))
    suite.addTest(ThreadTest("test_thread"))
    suite.addTest(ThreadTest("test_thread_hardware"))
    suite.addTest(ComplexThreadTest("test_thread"))
    suite.addTest(CallbackTest("test_callback_simple"))
    suite.addTest(CallbackTest("test_callback_simple_hardware"))
    suite.addTest(CallbackTest("test_callback_memory"))
    suite.addTest(CallbackTest("test_callback_jumpout"))
    suite.addTest(CallbackTest("test_callback_intermixing"))
    suite.addTest(FinishTest("test_finish_exact_no_auto_interrupt_no_breakpoint"))
    suite.addTest(FinishTest("test_finish_heuristic_no_auto_interrupt_no_breakpoint"))
    suite.addTest(FinishTest("test_finish_exact_auto_interrupt_no_breakpoint"))
    suite.addTest(FinishTest("test_finish_heuristic_auto_interrupt_no_breakpoint"))
    suite.addTest(FinishTest("test_finish_exact_no_auto_interrupt_breakpoint"))
    suite.addTest(FinishTest("test_finish_heuristic_no_auto_interrupt_breakpoint"))
    suite.addTest(FinishTest("test_heuristic_return_address"))
    suite.addTest(FinishTest("test_exact_breakpoint_return"))
    suite.addTest(FinishTest("test_heuristic_breakpoint_return"))
    suite.addTest(FinishTest("test_breakpoint_collision"))
    suite.addTest(Jumpout("test_jumpout"))
    suite.addTest(Ncuts("test_ncuts"))
    suite.addTest(ControlFlowTest("test_step_until_1"))
    suite.addTest(ControlFlowTest("test_step_until_2"))
    suite.addTest(ControlFlowTest("test_step_until_3"))
    suite.addTest(ControlFlowTest("test_step_and_cont"))
    suite.addTest(ControlFlowTest("test_step_and_cont_hardware"))
    suite.addTest(ControlFlowTest("test_step_until_and_cont"))
    suite.addTest(ControlFlowTest("test_step_until_and_cont_hardware"))
    suite.addTest(MultipleDebuggersTest("test_multiple_debuggers"))
    suite.addTest(LargeBinarySymTest("test_large_binary_symbol_load_times"))
    suite.addTest(LargeBinarySymTest("test_large_binary_demangle"))
    suite.addTest(WaitingTest("test_bps_waiting"))
    suite.addTest(WaitingTest("test_jumpout_waiting"))
    suite.addTest(WaitingNcuts("test_ncuts"))
    suite.addTest(AutoWaitingTest("test_bps_auto_waiting"))
    suite.addTest(AutoWaitingTest("test_jumpout_auto_waiting"))
    suite.addTest(AutoWaitingNcuts("test_ncuts"))
    suite.addTest(WatchpointTest("test_watchpoint"))
    suite.addTest(WatchpointAliasTest("test_watchpoint_alias"))
    suite.addTest(SyscallHookTest("test_hooks"))
    suite.addTest(SyscallHookTest("test_hooks_with_pprint"))
    suite.addTest(SyscallHookTest("test_hook_disabling"))
    suite.addTest(SyscallHookTest("test_hook_disabling_with_pprint"))
    suite.addTest(SyscallHookTest("test_hook_overwrite"))
    suite.addTest(SyscallHookTest("test_hook_overwrite_with_pprint"))
    suite.addTest(AntidebugEscapingTest("test_antidebug_escaping"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall_with_pprint"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall_hook"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall_hook_with_pprint"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall_args"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall_args_with_pprint"))
    suite.addTest(SyscallHijackTest("test_hijack_syscall_wrong_args"))
    suite.addTest(SyscallHijackTest("loop_detection_test"))
    suite.addTest(PPrintSyscallsTest("test_pprint_syscalls_generic"))
    suite.addTest(PPrintSyscallsTest("test_pprint_syscalls_with_statement"))
    suite.addTest(PPrintSyscallsTest("test_pprint_syscalls_hooking"))
    suite.addTest(PPrintSyscallsTest("test_pprint_hijack_syscall"))
    suite.addTest(PPrintSyscallsTest("test_pprint_which_syscalls_pprint_after"))
    suite.addTest(PPrintSyscallsTest("test_pprint_which_syscalls_pprint_before"))
    suite.addTest(
        PPrintSyscallsTest("test_pprint_which_syscalls_pprint_after_and_before")
    )
    suite.addTest(PPrintSyscallsTest("test_pprint_which_syscalls_not_pprint_after"))
    suite.addTest(PPrintSyscallsTest("test_pprint_which_syscalls_not_pprint_before"))
    suite.addTest(
        PPrintSyscallsTest("test_pprint_which_syscalls_not_pprint_after_and_before")
    )
    return suite


def complete_suite():
    suite = fast_suite()
    suite.addTest(Vmwhere1("test_vmwhere1"))
    suite.addTest(Vmwhere1("test_vmwhere1_callback"))
    suite.addTest(BruteTest("test_bruteforce"))
    suite.addTest(CallbackTest("test_callback_bruteforce"))
    suite.addTest(SpeedTest("test_speed"))
    suite.addTest(SpeedTest("test_speed_hardware"))
    suite.addTest(DeepDiveDivision("test_deep_dive_division"))
    return suite


def thread_stress_suite():
    suite = unittest.TestSuite()
    for _ in range(1024):
        suite.addTest(ThreadTest("test_thread"))
        suite.addTest(ThreadTest("test_thread_hardware"))
        suite.addTest(ComplexThreadTest("test_thread"))
    return suite


if __name__ == "__main__":
    if sys.version_info >= (3, 12):
        runner = unittest.TextTestRunner(verbosity=2, durations=3)
    else:
        runner = unittest.TextTestRunner(verbosity=2)

    if len(sys.argv) > 1 and sys.argv[1].lower() == "slow":
        suite = complete_suite()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "thread_stress":
        suite = thread_stress_suite()
        runner.verbosity = 1
    else:
        suite = fast_suite()

    result = runner.run(suite)

    if result.wasSuccessful():
        print("All tests passed")
    else:
        print("Some tests failed")
        print("\nFailed Tests:")
        for test, err in result.failures:
            print(f"{test}: {err}")
        print("\nErrors:")
        for test, err in result.errors:
            print(f"{test}: {err}")
