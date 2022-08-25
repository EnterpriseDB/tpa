# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

# We can't be sure that Python is installed when we use this action to verify
# a remote host's availability. the upstream action plugin wait_for_connection
# uses ping module to ensure end to end connectivity to a remote host, we change
# this to use a raw `echo` command that includes a timestamp as return output.

from __future__ import absolute_import, division, print_function

__metaclass__ = type
import time
from datetime import datetime, timedelta
from ansible.plugins.action import ActionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    DEFAULT_CONNECT_TIMEOUT = 5
    DEFAULT_DELAY = 0
    DEFAULT_SLEEP = 1
    DEFAULT_TIMEOUT = 600

    def do_until_success_or_timeout(
        self, what, timeout, connect_timeout, what_desc, sleep=1
    ):
        max_end_time = datetime.utcnow() + timedelta(seconds=timeout)
        e = None
        while datetime.utcnow() < max_end_time:
            try:
                what(connect_timeout)
                if what_desc:
                    display.debug("wait_for_ssh: %s success" % what_desc)
                return
            except Exception as e:
                error = e  # PY3 compatibility to store exception for use outside of this block
                if what_desc:
                    display.debug(
                        "wait_for_ssh: %s fail (expected), retrying in %d seconds..."
                        % (what_desc, sleep)
                    )
                time.sleep(sleep)
        raise TimedOutException("timed out waiting for %s: %s" % (what_desc, error))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        connect_timeout = int(
            self._task.args.get("connect_timeout", self.DEFAULT_CONNECT_TIMEOUT)
        )
        delay = int(self._task.args.get("delay", self.DEFAULT_DELAY))
        sleep = int(self._task.args.get("sleep", self.DEFAULT_SLEEP))
        timeout = int(self._task.args.get("timeout", self.DEFAULT_TIMEOUT))
        if self._play_context.check_mode:
            display.vvv("wait_for_ssh: skipping for check_mode")
            return dict(skipped=True)
        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        def raw_test(connect_timeout):
            display.vvv("wait_for_ssh: attempting raw test")

            pong = "pong %s" % (int(time.time()))
            raw_result = self._low_level_execute_command("echo %s" % pong)
            if pong not in raw_result["stdout_lines"]:
                raise Exception("raw test failed")

        start = datetime.now()
        if delay:
            time.sleep(delay)
        try:
            self.do_until_success_or_timeout(
                raw_test, timeout, connect_timeout, what_desc="raw test", sleep=sleep
            )
        except TimedOutException as e:
            result["failed"] = True
            result["msg"] = str(e)
        elapsed = datetime.now() - start
        result["elapsed"] = elapsed.seconds

        return result
