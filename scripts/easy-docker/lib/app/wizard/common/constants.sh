#!/usr/bin/env bash

# Shared flow/status constants used across sourced wizard modules.
# shellcheck disable=SC2034
readonly FLOW_CONTINUE=0
readonly FLOW_BACK_TO_MAIN=10
readonly FLOW_EXIT_APP=11
readonly FLOW_ABORT_INPUT=12
readonly FLOW_OPEN_MANAGE_STACK=13
