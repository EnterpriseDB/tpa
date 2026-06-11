#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.
"""Raise operator-facing warnings that TPA deliberately wants the user to notice.

A plain Ansible ``display.warning()`` is printed inline at the moment it is
raised and then scrolls out of sight during a long run, interleaved with the
benign warnings Ansible itself emits. Warnings raised through ``tpa_warning()``
are emitted normally *and* tagged with ``WARNING_MARKER`` so that TPA's ``tpa``
stdout callback can recognise them, reproduce them in a consolidated block at
the end of the run, and leave the unrelated Ansible-core warnings out of it.

The marker is carried in the *text* of the warning on purpose. Most TPA
warnings are raised while a task runs -- i.e. in a forked worker process, whose
Python state does not cross back to the controller. The message text does cross
back (Ansible forwards it to the controller's Display), so tagging the text is
what lets the controller-side callback identify the warning regardless of which
process raised it. The callback strips the marker before displaying, so the
operator never sees it.
"""

from ansible.utils.display import Display

# Prepended to the text of warnings raised via tpa_warning(). Delimited with
# NULs so it can never collide with real warning text and renders as nothing if
# it ever leaks to a terminal. lib/callback_plugins/tpa.py strips this exact
# string; keep the two in step.
WARNING_MARKER = "\x00TPA-DELIBERATE-WARNING\x00"


def tpa_warning(msg):
    """Emit an operator-facing warning and tag it for the end-of-run recap.

    Use this in preference to ``display.warning()`` for warnings TPA chooses to
    raise on purpose and wants the operator to see even after a long run.
    """
    Display().warning(WARNING_MARKER + str(msg))
