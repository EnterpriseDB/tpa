---
title: Testing BDR3
author:
- Gianni Ciolli
- Amruta Deolasee
date: 27 March 2019
version: 0.1 (DRAFT 2)
---

# Overview

This document describes all the tests currently carried out on BDR3.

# Test Groups

1. Regression tests
2. TAP tests
3. Isolation tests
4. TPA tests
5. HA tests
6. Package tests

Note that:

- Testing of new features is generally covered in variable detail in
  some or all of Regression, TAP and Isolation tests

- The Functionality testing part is covered in all groups except
  Package tests

## Regression Tests

- Run nightly on sources retrieved from artifacts of the latest
  packages in CI

- Functionalities are tested on a two-database BDR3 cluster running on
  the same instance

- Basic SQL queries can be tested here

- Quite extensive coverage

## TAP Tests

- Run nightly on sources retrieved from artifacts of the latest
  packages in CI

- Multi-instance BDR3 cluster

- These tests covers most of the tests where we need server
  start/stop/restart/crash

## Isolation Tests

- Run nightly on sources retrieved from artifacts of the latest
  packages in CI

- 2-3 database BDR3 cluster

- Cover conflict testing scenarios

## TPA Tests

- Run nightly on packages from CI

- Using both BDR-Simple and CAMO2X2 architectures

## HA Tests

- Being reviewed and fine tuned

- Will be running using `tpaexec`

- Will include crash tests

## Package Tests

- Run in our CI Acceptance Test stage
