#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2025 - All rights reserved.

class ArchitectureError(Exception):
    MSG = "Error"

class AWSPlatformError(Exception):
    MSG = "Error"

class ConfigureError(Exception):
    MSG = "Error"

class ClusterError(Exception):
    MSG = "Error"

class DockerPlatformError(Exception):
    MSG = "Error"

class ExternalCommandError(Exception):
    MSG = "Error"

class InstanceError(Exception):
    MSG = "Error"

class NetError(Exception):
    MSG = "Error"

class PGDArchitectureError(Exception):
    MSG = "Error"

class PlatformError(Exception):
    MSG = "Error"

class TransmogrifierError(Exception):
    MSG = "Error"

class UnsupportedArchitectureError(Exception):
    MSG = "Error"
