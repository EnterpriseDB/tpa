# Make coding more python3-ish

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: json
    short_description: Ansible screen output as JSON
    version_added: "2.2"
    description:
        - This callback converts all events into JSON output to stdout
    type: stdout
    requirements:
      - Set as stdout in config
    options:
      show_custom_stats:
        version_added: "2.6"
        name: Show custom stats
        description: 'This adds the custom stats set via the set_stats plugin to the play recap'
        default: False
        env:
          - name: ANSIBLE_SHOW_CUSTOM_STATS
        ini:
          - key: show_custom_stats
            section: defaults
        type: bool
    notes:
      - When using a strategy such as free, host_pinned, or a custom strategy, host results will
        be added to new task results in ``.plays[].tasks[]``. As such, there will exist duplicate
        task objects indicated by duplicate task IDs at ``.plays[].tasks[].task.id``, each with an
        individual host result for the task.
'''

import datetime

from ansible.plugins.callback.json import CallbackModule as JsonCallbackModule

def current_time():
    return '%sZ' % datetime.datetime.utcnow().isoformat()


class CallbackModule(JsonCallbackModule):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'json'

    def _record_task_result(self, on_info, result, **kwargs):
        """This function is used as a partial to add failed/skipped info in a single method"""
        host = result._host
        task = result._task

        result_copy = result._result.copy()
        result_copy.update(on_info)
        result_copy['action'] = task.action
        if result_copy.get('failed', False) and kwargs.get('ignore_errors', False):
            result_copy['failed'] = 'ignored'

        task_result = self._find_result_task(host, task)

        task_result['hosts'][host.name] = result_copy
        end_time = current_time()
        task_result['task']['duration']['end'] = end_time
        self.results[-1]['play']['duration']['end'] = end_time

        if not self._is_lockstep:
            key = (host.get_name(), task._uuid)
            del self._task_map[key]
