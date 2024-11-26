# testing how things work

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
    callback: tpa
    short_description: TPA's own Ansible screen output
    version_added: "2.2"
    description:
        - this callback shows all tasks as one line of output
    extends_documentation_fragment:
        - default_callback
        - result_format_callback
    type: stdout
    requirements:
        - set as stdout in config
    options:
        standard_plugin:
            description: show output equivalent to the default plugin
            type: bool
            ini:
                - section: default
                - key: standard_plugin
            env:
                - name: TPA_USE_DEFAULT_OUTPUT
            default: false



"""

import inspect

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible.utils.color import stringc


class CallbackModule(CallbackModule_default):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "stdout"
    CALLBACK_NAME = "tpa"

    def zero_everything(self):
        self._ok = 0
        self._skipped = 0
        self._failed = 0
        self._next_task_uuid = None
        self._uuid_stack = []
        self._task_name = ""
        self._use_standard_plugin = False
        self._errors = []
        self._output_lines = []
        self._pending_output_line = False

    def __init__(self, display=None):
        self._super = super(CallbackModule, self)
        self._super.__init__()
        self.zero_everything()

    def v2_playbook_on_include(self, included_file):
        # this is only called for non-role includes
        if self._use_standard_plugin:
            self._super.v2_playbook_on_include(included_file)
        else:
            self._task_name += " " + included_file._filename.partition("roles/")[2]

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_task_start(task, is_conditional)
        else:
            # show counters for already-finished task
            self._show_task_counters()

            self._task_name = task.get_name().strip()
            self._task_uuid = task._uuid
            self._output_lines = []
            self._errors = []

            # if this isn't the task we were expecting, that's because the last task
            # was an include that got expanded
            if self._task_uuid != self._next_task_uuid:
                self._uuid_stack.append(self._next_task_uuid)

            if self._task_uuid in self._uuid_stack:
                while self._task_uuid != self._uuid_stack[-1]:
                    self._uuid_stack.pop()
                self._uuid_stack.pop()

            # to establish the expected next task, we look at our caller's iterator
            stack = inspect.stack()  # list of FrameInfo
            try:
                strategy_frame = stack[3].frame
                iterator = strategy_frame.f_locals["iterator"]

                next_task = iterator.all_tasks[iterator.cur_task]  #
                if next_task is not None:
                    self._next_task_uuid = next_task._uuid
            finally:
                del strategy_frame
                del iterator

            self._ok = 0
            self._skipped = 0
            self._failed = 0

            self._show_task_lead_line()

    def v2_playbook_on_play_start(self, play):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_play_start(play)
        else:
            self.zero_everything()
            name = play.get_name().strip()
            if not name:
                msg = "PLAY"
            else:
                msg = "PLAY [%s]" % (name)
            self._current_play = play

            self._display.banner(msg)

    def v2_playbook_on_stats(self, stats):
        if not self._use_standard_plugin:
            self._show_task_counters()

        self._super.v2_playbook_on_stats(stats)

    def v2_runner_on_start(self, host, task):
        if self._use_standard_plugin:
            self._super.v2_runner_on_start(host, task)

    def v2_runner_on_ok(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_on_ok(result)
        else:
            if result._task.action in C._ACTION_DEBUG:
                self._clean_results(result._result, result._task.action)
                self._output_lines.append(
                    f"{result._host.get_name()} => { self._dump_results(result._result) }"
                )
            self._ok += 1

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if self._use_standard_plugin:
            self._super.v2_runner_on_failed(result, ignore_errors)
        else:
            if not ignore_errors:
                host_label = self.host_label(result)
                self._errors.append(
                    "fatal: [%s]: FAILED! => %s"
                    % (
                        host_label,
                        self._dump_results(result._result),
                    )
                )

            self._failed += 1

    def v2_runner_on_skipped(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_on_skipped(result)
        else:
            self._skipped += 1

    def v2_runner_on_unreachable(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_on_unreachable(result)
        else:
            host_label = self.host_label(result)
            self._errors.append(
                "fatal: [%s]: UNREACHABLE! => %s"
                % (
                    host_label,
                    self._dump_results(result._result),
                )
            )

            self._failed += 1

    def v2_playbook_on_no_hosts_matched(self):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_no_hosts_matched()

    def v2_playbook_on_no_hosts_remaining(self):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_no_hosts_remaining()

    def v2_playbook_on_cleanup_task_start(self, task):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_cleanup_task_start(task)

    def v2_playbook_on_handler_task_start(self, task):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_handler_task_start(task)

    def v2_on_file_diff(self, result):
        if self._use_standard_plugin:
            self._super.v2_on_file_diff(result)

    def v2_runner_item_on_ok(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_item_on_ok(result)

    def v2_runner_item_on_failed(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_item_on_failed(result)

    def v2_runner_item_on_skipped(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_item_on_skipped(result)

    def v2_playbook_on_start(self, playbook):
        if self.get_option("standard_plugin") or self._display.verbosity > 0:
            self._display.display("Switching to standard plugin")
            self._use_standard_plugin = True
        if self._use_standard_plugin:
            self._super.v2_playbook_on_start(playbook)

    def v2_runner_retry(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_retry(result)

    def v2_runner_on_async_poll(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_on_async_poll(result)

    def v2_runner_on_async_ok(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_on_async_ok(result)

    def v2_runner_on_async_failed(self, result):
        if self._use_standard_plugin:
            self._super.v2_runner_on_async_failed(result)

    def v2_playbook_on_notify(self, handler, host):
        if self._use_standard_plugin:
            self._super.v2_playbook_on_notify(handler, host)

    def _show_task_lead_line(self):
        def _suppress_task(name):
            return name.endswith(("set_fact", "assert", "meta"))

        if not _suppress_task(self._task_name):
            self._pending_output_line = True
            indents = len(self._uuid_stack) * "  "
            self._display.display("%s%s" % (indents, self._task_name), newline=False)

    def _show_task_counters(self):
        error_color = C.COLOR_WARN
        if self._errors:
            error_color = C.COLOR_ERROR
        indents = len(self._uuid_stack) * "  "

        if self._pending_output_line:
            self._pending_output_line = False
            self._display.display(
                " (%s/%s/%s)"
                % (
                    stringc(str(self._ok), C.COLOR_OK),
                    stringc(str(self._skipped), C.COLOR_SKIP),
                    stringc(str(self._failed), error_color),
                ),
                screen_only=True,
            )
            self._display.display(
                "%s %s ok, %s skipped, %s failed"
                % (indents, self._ok, self._skipped, self._failed),
                log_only=True,
            )

        for error in self._errors:
            self._display.display("%s%s" % (indents, error), C.COLOR_ERROR)
        for line in self._output_lines:
            self._display.display("%s%s" % (indents, line), C.COLOR_OK)
