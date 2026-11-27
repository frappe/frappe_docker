#!/usr/bin/env bash

restart_stack_with_compose_from_metadata() {
  local stack_dir="${1}"
  local stop_status=0
  local start_status=0

  # shellcheck disable=SC2034 # Read by manage flow after restart_stack_with_compose_from_metadata fails.
  EASY_DOCKER_COMPOSE_ERROR_DETAIL=""

  if stop_stack_with_compose_from_metadata "${stack_dir}"; then
    :
  else
    stop_status=$?
    case "${stop_status}" in
    41)
      return 57
      ;;
    42)
      return 58
      ;;
    43)
      return 59
      ;;
    44)
      return 60
      ;;
    45)
      return 61
      ;;
    46)
      return 62
      ;;
    *)
      return 63
      ;;
    esac
  fi

  if start_stack_with_compose_from_metadata "${stack_dir}"; then
    return 0
  fi

  start_status=$?
  case "${start_status}" in
  31)
    return 57
    ;;
  32)
    return 58
    ;;
  33)
    return 59
    ;;
  34)
    return 60
    ;;
  35)
    return 61
    ;;
  36)
    return 62
    ;;
  38)
    return 64
    ;;
  39)
    return 65
    ;;
  *)
    return 63
    ;;
  esac
}
