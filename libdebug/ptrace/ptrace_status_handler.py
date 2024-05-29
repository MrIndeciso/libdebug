#
# This file is part of libdebug Python library (https://github.com/libdebug/libdebug).
# Copyright (c) 2023-2024 Roberto Alessandro Bertolini, Gabriele Digregorio. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for details.
#

import os
import signal
from typing import TYPE_CHECKING

from libdebug.architectures.ptrace_software_breakpoint_patcher import (
    software_breakpoint_byte_size,
)
from libdebug.data.syscall_hook import SyscallHook
from libdebug.data.signal_hook import SignalHook
from libdebug.liblog import liblog
from libdebug.ptrace.ptrace_constants import SYSCALL_SIGTRAP, StopEvents
from libdebug.state.debugging_context import provide_context
from libdebug.state.thread_context import ThreadContext
from libdebug.utils.signal_utils import resolve_signal_name
from libdebug.state.resume_context import ResumeStatus

if TYPE_CHECKING:
    from libdebug.data.breakpoint import Breakpoint
    from libdebug.interfaces.debugging_interface import DebuggingInterface
    from libdebug.state.debugging_context import DebuggingContext


class PtraceStatusHandler:
    def __init__(self):
        self.context: "DebuggingContext" = provide_context(self)
        self.ptrace_interface: "DebuggingInterface" = self.context.debugging_interface
        self._threads_with_signals_to_deliver: list[int] = []
        self._assume_race_sigstop: bool = True  # Assume the stop is due to a race condition with SIGSTOP sent by the debugger

    def _handle_clone(self, thread_id: int, results: list):
        # https://go.googlesource.com/debug/+/a09ead70f05c87ad67bd9a131ff8352cf39a6082/doc/ptrace-nptl.txt
        # "At this time, the new thread will exist, but will initially
        # be stopped with a SIGSTOP.  The new thread will automatically be
        # traced and will inherit the PTRACE_O_TRACECLONE option from its
        # parent.  The attached process should wait on the new thread to receive
        # the SIGSTOP notification."

        # Check if we received the SIGSTOP notification for the new thread
        # If not, we need to wait for it
        # 4991 == (WIFSTOPPED && WSTOPSIG(status) == SIGSTOP)
        if (thread_id, 4991) not in results:
            os.waitpid(thread_id, 0)
        self.ptrace_interface.register_new_thread(thread_id)

    def _handle_exit(self, thread_id: int):
        if self.context.get_thread_by_id(thread_id):
            self.ptrace_interface.unregister_thread(thread_id)

    def _handle_breakpoints(self, thread_id: int) -> bool:
        thread = self.context.get_thread_by_id(thread_id)

        if not hasattr(thread, "instruction_pointer"):
            # This is a signal trap hit on process startup
            # Do not resume the process until the user decides to do so
            self.context._resume_context.resume = ResumeStatus.NOT_RESUME
            return

        ip = thread.instruction_pointer

        bp: None | "Breakpoint"

        enabled_breakpoints = {}
        for bp in self.context.breakpoints.values():
            if bp.enabled and not bp._disabled_for_step:
                enabled_breakpoints[bp.address] = bp

        bp = None

        if ip in enabled_breakpoints:
            # Hardware breakpoint hit
            liblog.debugger("Hardware breakpoint hit at 0x%x" % ip)
            bp = self.context.breakpoints[ip]
        else:
            # If the trap was caused by a software breakpoint, we need to restore the original instruction
            # and set the instruction pointer to the previous instruction.
            ip -= software_breakpoint_byte_size()

            if ip in enabled_breakpoints:
                # Software breakpoint hit
                liblog.debugger("Software breakpoint hit at 0x%x", ip)
                bp = self.context.breakpoints[ip]

                # Set the instruction pointer to the previous instruction
                thread.instruction_pointer = ip

                # Link the breakpoint to the thread, so that we can step over it
                bp._linked_thread_ids.append(thread_id)

        # Manage watchpoints
        if bp is None:
            bp = self.ptrace_interface.hardware_bp_helpers[
                thread_id
            ].is_watchpoint_hit()
            if bp is not None:
                liblog.debugger("Watchpoint hit at 0x%x", bp.address)

        if bp:
            bp.hit_count += 1

            if bp.callback:
                bp.callback(thread, bp)
                self.context._resume_context.resume = ResumeStatus.RESUME
            else:
                # If the breakpoint has no callback, we need to stop the process despite the other signals
                self.context._resume_context.resume = ResumeStatus.NOT_RESUME

    def _manage_syscall_on_enter(
        self,
        hook: SyscallHook,
        thread: ThreadContext,
        syscall_number: int,
        hijacked_set: set[int],
    ):
        """Manage the on_enter hook of a syscall."""
        # Call the user-defined hook if it exists
        if hook.on_enter_user and hook.enabled:
            old_args = [
                thread.syscall_arg0,
                thread.syscall_arg1,
                thread.syscall_arg2,
                thread.syscall_arg3,
                thread.syscall_arg4,
                thread.syscall_arg5,
            ]
            hook.on_enter_user(thread, syscall_number)

            # Check if the syscall number has changed
            syscall_number_after_hook = thread.syscall_number

            if syscall_number_after_hook != syscall_number:
                # Pretty print the syscall number before the hook
                if hook.on_enter_pprint:
                    hook.on_enter_pprint(
                        thread, syscall_number, hijacked=True, old_args=old_args
                    )

                # The syscall number has changed
                if syscall_number_after_hook in self.context.syscall_hooks:
                    hook_hijack = self.context.syscall_hooks[syscall_number_after_hook]

                    # Check if the new syscall has to be hooked
                    if hook.hook_hijack:
                        if syscall_number_after_hook not in hijacked_set:
                            hijacked_set.add(syscall_number_after_hook)
                        else:
                            # The syscall has already been hijacked in the current chain
                            raise RuntimeError(
                                "Syscall hijacking loop detected. Check your hooks to avoid infinite loops."
                            )

                        # Call recursively the function to manage the new syscall
                        self._manage_syscall_on_enter(
                            hook_hijack,
                            thread,
                            syscall_number_after_hook,
                            hijacked_set,
                        )
                    elif hook_hijack.on_enter_pprint:
                        # Pretty print the syscall number
                        hook_hijack.on_enter_pprint(thread, syscall_number_after_hook)
                        hook_hijack._has_entered = True
                        hook_hijack._skip_exit = True
                    else:
                        # Skip the exit hook of the syscall that has been hijacked
                        hook_hijack._has_entered = True
                        hook_hijack._skip_exit = True
            elif hook.on_enter_pprint:
                # Pretty print the syscall number
                hook.on_enter_pprint(thread, syscall_number, user_hooked=True)
                hook._has_entered = True
            else:
                hook._has_entered = True
        elif hook.on_enter_pprint:
            # Pretty print the syscall number
            hook.on_enter_pprint(thread, syscall_number)
            hook._has_entered = True
        elif hook.on_exit_pprint or hook.on_exit_user:
            # The syscall has been entered but the user did not define an on_enter hook
            hook._has_entered = True

    def _handle_syscall(self, thread_id: int) -> bool:
        """Handle a syscall trap."""

        thread = self.context.get_thread_by_id(thread_id)

        if not hasattr(thread, "syscall_number"):
            # This is another spurious trap, we don't know what to do with it
            return

        syscall_number = thread.syscall_number

        if syscall_number not in self.context.syscall_hooks:
            # This is a syscall we don't care about
            # Resume the execution
            self.context._resume_context.resume = ResumeStatus.RESUME
            return

        hook = self.context.syscall_hooks[syscall_number]

        if not hook._has_entered:
            # The syscall is being entered
            liblog.debugger(
                "Syscall %d entered on thread %d", syscall_number, thread_id
            )

            self._manage_syscall_on_enter(
                hook, thread, syscall_number, {syscall_number}
            )

        else:
            # The syscall is being exited
            liblog.debugger("Syscall %d exited on thread %d", syscall_number, thread_id)

            if hook.enabled and not hook._skip_exit:
                # Increment the hit count only if the syscall hook is enabled
                hook.hit_count += 1

            # Call the user-defined hook if it exists
            if hook.on_exit_user and hook.enabled and not hook._skip_exit:
                # Pretty print the return value before the hook
                if hook.on_exit_pprint:
                    return_value_before_hook = thread.syscall_return
                hook.on_exit_user(thread, syscall_number)
                if hook.on_exit_pprint:
                    return_value_after_hook = thread.syscall_return
                    if return_value_after_hook != return_value_before_hook:
                        hook.on_exit_pprint(
                            (return_value_before_hook, return_value_after_hook)
                        )
                    else:
                        hook.on_exit_pprint(return_value_after_hook)
            elif hook.on_exit_pprint:
                # Pretty print the return value
                hook.on_exit_pprint(thread.syscall_return)

            hook._has_entered = False
            hook._skip_exit = False

        self.context._resume_context.resume = ResumeStatus.RESUME

    def _manage_signal_callback(
        self,
        hook: SignalHook,
        thread: ThreadContext,
        signal_number: int,
        hijacked_set: set[int],
    ) -> None:
        if hook.enabled:
            hook.hit_count += 1
            if hook.callback:
                # Execute the user-defined callback
                hook.callback(thread, signal_number)

                new_signal_number = thread.signal_number

                if new_signal_number != signal_number:
                    # The signal number has changed
                    liblog.debugger(
                        "Signal %s (%d) has been hijacked to %s (%d)",
                        resolve_signal_name(signal_number),
                        signal_number,
                        resolve_signal_name(new_signal_number),
                        new_signal_number,
                    )

                    if hook.hook_hijack:
                        if new_signal_number in self.context.signal_hooks:
                            hijack_hook = self.context.signal_hooks[new_signal_number]
                            if new_signal_number not in hijacked_set:
                                hijacked_set.add(new_signal_number)
                            else:
                                # The signal has already been hijacked in the current chain
                                raise RuntimeError(
                                    "Signal hijacking loop detected. Check your hooks to avoid infinite loops."
                                )
                            # Call recursively the function to manage the new signal
                            self._manage_signal_callback(
                                hijack_hook, thread, new_signal_number, hijacked_set
                            )

    def _handle_signal(self, thread: ThreadContext) -> bool:
        """Handle the signal trap."""

        signal_number = thread.signal_number

        if signal_number in self.context.signal_hooks:
            hook = self.context.signal_hooks[signal_number]

            self._manage_signal_callback(hook, thread, signal_number, {signal_number})

            self.context._resume_context.resume = ResumeStatus.RESUME

    def _internal_signal_handler(
        self, pid: int, signum: int, results: list, status: int
    ):
        """Internal handler for signals used by the debugger."""
        if signum == SYSCALL_SIGTRAP:
            # We hit a syscall
            liblog.debugger("Child thread %d stopped on syscall hook", pid)
            self._handle_syscall(pid)
        elif signum == signal.SIGSTOP and self.context._resume_context.force_interrupt:
            # The user has requested an interrupt, we need to stop the process despite the ohter signals
            liblog.debugger(
                "Child thread %d stopped with signal %s",
                pid,
                resolve_signal_name(signum),
            )
            self.context._resume_context.resume = ResumeStatus.NOT_RESUME
            self.context._resume_context.force_interrupt = False
        elif signum == signal.SIGTRAP:
            # The trap decides if we hit a breakpoint. If so, it decides whether we should stop or
            # continue the execution and wait for the next trap
            self._handle_breakpoints(pid)

            if self.context._resume_context.is_a_step:
                self.context._resume_context.resume = ResumeStatus.NOT_RESUME
                self.context._resume_context.is_a_step = False

            event = status >> 8
            match event:
                case StopEvents.CLONE_EVENT:
                    # The process has been cloned
                    message = self.ptrace_interface._get_event_msg(pid)
                    liblog.debugger(
                        "Process {} cloned, new thread_id: {}".format(pid, message)
                    )
                    self._handle_clone(message, results)
                    self.context._resume_context.resume = ResumeStatus.RESUME
                case StopEvents.SECCOMP_EVENT:
                    # The process has installed a seccomp
                    liblog.debugger("Process {} installed a seccomp".format(pid))
                    self.context._resume_context.resume = ResumeStatus.RESUME
                case StopEvents.EXIT_EVENT:
                    # The tracee is still alive; it needs
                    # to be PTRACE_CONTed or PTRACE_DETACHed to finish exiting.
                    # so we don't call self._handle_exit(pid) here
                    # it will be called at the next wait (hopefully)
                    message = self.ptrace_interface._get_event_msg(pid)
                    liblog.debugger(
                        "Thread {} exited with status: {}".format(pid, message)
                    )
                    self.context._resume_context.resume = ResumeStatus.RESUME

    def _handle_change(self, pid: int, status: int, results: list):
        """Handle a change in the status of a traced process."""

        if os.WIFSTOPPED(status):
            signum = os.WSTOPSIG(status)

            if signum != signal.SIGSTOP:
                self._assume_race_sigstop = False

            # Check if the debugger needs to handle the signal
            self._internal_signal_handler(pid, signum, results, status)

            thread = self.context.get_thread_by_id(pid)

            if thread is not None:
                thread.signal_number = signum

                # Handle the signal
                self._handle_signal(thread)

                # We might have to deliver the signal to the thread
                self._threads_with_signals_to_deliver.append(pid)

        if os.WIFEXITED(status):
            # The thread has exited normally
            exitstatus = os.WEXITSTATUS(status)
            liblog.debugger("Child process %d exited with status %d", pid, exitstatus)
            self._handle_exit(pid)
            self.context._resume_context.resume = ResumeStatus.RESUME

        if os.WIFSIGNALED(status):
            # The thread has exited with a signal
            termsig = os.WTERMSIG(status)
            liblog.debugger("Child process %d exited with signal %d", pid, termsig)
            self._handle_exit(pid)
            self.context._resume_context.resume = ResumeStatus.RESUME

    def manage_change(self, result):
        """Manage the result of the waitpid and handle the changes."""

        # Assume that the stop depends on SIGSTOP sent by the debugger
        # This is a workaround for some race conditions that may happen
        self._assume_race_sigstop = True

        for pid, status in result:
            if pid == -1:
                # This is a spurious trap, we can ignore it
                self.context._resume_context.resume = ResumeStatus.RESUME
            else:
                self._handle_change(pid, status, result)

        if self._assume_race_sigstop:
            self.context._resume_context.resume = ResumeStatus.RESUME
            return

        # Deliver the signals to the threads
        self.ptrace_interface.deliver_signal(self._threads_with_signals_to_deliver)

        # Clear the list of threads with signals to deliver
        self._threads_with_signals_to_deliver.clear()

    def check_for_new_threads(self, pid: int):
        """Check for new threads in the process and register them."""
        if not os.path.exists(f"/proc/{pid}/task"):
            return

        tids = [int(x) for x in os.listdir(f"/proc/{pid}/task")]
        for tid in tids:
            if not self.context.get_thread_by_id(tid):
                self.ptrace_interface.register_new_thread(tid)
                liblog.debugger("Manually registered new thread %d" % tid)
