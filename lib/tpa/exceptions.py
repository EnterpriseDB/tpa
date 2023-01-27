#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.


class ConfigureError(Exception):
    MSG = "Error"

class ClusterError(Exception):
    MSG = "Error"

class InstanceError(Exception):
    MSG = "Error"

class TransmogrifierError(Exception):
    MSG = "Error"