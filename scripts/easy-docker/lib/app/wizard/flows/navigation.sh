#!/usr/bin/env bash

handle_abort_wizard_flow() {
  local stack_dir="${1}"
  local abort_action=""
  local rollback_status=0

  abort_action="$(show_abort_wizard_prompt "${stack_dir}" || true)"
  case "${abort_action}" in
  "Rollback files and return to main menu")
    if rollback_stack_directory "${stack_dir}"; then
      return "${FLOW_BACK_TO_MAIN}"
    fi

    rollback_status=$?
    if [ "${rollback_status}" -eq 2 ]; then
      show_warning_and_wait "Refused rollback for unsafe path: ${stack_dir}" 2
    else
      show_warning_and_wait "Could not rollback stack files: ${stack_dir}" 2
    fi
    return "${FLOW_CONTINUE}"
    ;;
  "Keep files and return to main menu")
    return "${FLOW_BACK_TO_MAIN}"
    ;;
  "Back to topology selection" | "")
    return "${FLOW_CONTINUE}"
    ;;
  *)
    show_warning_and_wait "Unknown abort action: ${abort_action}"
    return "${FLOW_CONTINUE}"
    ;;
  esac
}

handle_stack_topology_flow() {
  local stack_dir="${1}"
  local topology_action=""
  local abort_status=0

  while true; do
    topology_action="$(show_stack_topology_menu "${stack_dir}" || true)"
    case "${topology_action}" in
    "Single-host" | "Single-host (recommended)")
      handle_single_host_stack_flow "${stack_dir}"
      ;;
    "Split services")
      handle_topology_examples_flow "${topology_action}"
      ;;
    "Abort wizard to main menu")
      handle_abort_wizard_flow "${stack_dir}"
      abort_status=$?
      case "${abort_status}" in
      "${FLOW_BACK_TO_MAIN}")
        return "${FLOW_BACK_TO_MAIN}"
        ;;
      *) ;;
      esac
      ;;
    "")
      return "${FLOW_CONTINUE}"
      ;;
    *)
      show_warning_and_wait "Unknown topology selection: ${topology_action}"
      ;;
    esac
  done
}
