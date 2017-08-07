# This callback plugin displays results in a format that's convenient
# for TPA. For example, it always displays task banners, and it does
# not show failures that have been ignored.
#
# It's loosely based on the "actionable" plugin included with Ansible.

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default

class CallbackModule(CallbackModule_default):

    CALLBACK_VERSION = 0.9
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'tpa'

    def __init__(self):
        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()
        self.last_task = None
        self.shown_title = False

    def v2_playbook_on_handler_task_start(self, task):
        self.super_ref.v2_playbook_on_handler_task_start(task)
        self.shown_title = True

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.last_task = task
        self.shown_title = False

    def display_task_banner(self):
        if not self.shown_title:
            self.super_ref.v2_playbook_on_task_start(self.last_task, None)
            self.shown_title = True

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.display_task_banner()
        if not ignore_errors:
            self.super_ref.v2_runner_on_failed(result, ignore_errors)

    def v2_runner_on_ok(self, result):
        self.display_task_banner()
        if result._result.get('changed', False):
            self.super_ref.v2_runner_on_ok(result)

    def v2_runner_on_unreachable(self, result):
        self.display_task_banner()
        self.super_ref.v2_runner_on_unreachable(result)

    def v2_runner_on_skipped(self, result):
        self.display_task_banner()
        pass

    def v2_playbook_on_include(self, included_file):
        self.display_task_banner()
        pass

    def v2_runner_item_on_ok(self, result):
        self.display_task_banner()
        if result._result.get('changed', False):
            self.super_ref.v2_runner_item_on_ok(result)

    def v2_runner_item_on_skipped(self, result):
        pass

    def v2_runner_item_on_failed(self, result):
        self.display_task_banner()
        self.super_ref.v2_runner_item_on_failed(result)
