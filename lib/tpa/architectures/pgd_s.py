#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2026 - All rights reserved.

from ..exceptions import PGDArchitectureError, PGDSDeprecatedError
from .pgd import PGD
from typing import List, Tuple


class PGDS(PGD):

    def __init__(self, *args, **kwargs):
        raise PGDSDeprecatedError()
