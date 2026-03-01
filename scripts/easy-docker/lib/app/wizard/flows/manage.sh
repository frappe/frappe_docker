#!/usr/bin/env bash

handle_manage_selected_stack_flow() {
  local stack_name="${1}"
  local stack_dir=""
  local stack_action=""
  local apps_action=""
  local docker_action=""
  local stack_metadata_path=""
  local stack_apps_path=""
  local custom_apps_update_status=0
  local persist_apps_status=0
  local render_compose_status=0
  local generated_compose_path=""

  stack_dir="$(get_stack_dir_by_name "${stack_name}" || true)"
  if [ -z "${stack_dir}" ]; then
    show_warning_and_wait "Could not resolve stack directory for '${stack_name}'." 2
    return "${FLOW_CONTINUE}"
  fi

  while true; do
    stack_action="$(show_manage_stack_actions_menu "${stack_name}" "${stack_dir}" || true)"
    case "${stack_action}" in
    "Apps")
      while true; do
        apps_action="$(show_manage_stack_apps_menu "${stack_name}" "${stack_dir}" || true)"
        case "${apps_action}" in
        "Generate apps.json")
          stack_metadata_path="${stack_dir}/metadata.json"
          stack_apps_path="${stack_dir}/apps.json"
          if [ ! -f "${stack_metadata_path}" ]; then
            show_warning_and_wait "Cannot generate apps.json because metadata is missing: ${stack_metadata_path}" 3
            continue
          fi

          if persist_stack_apps_json_from_metadata_apps "${stack_dir}"; then
            :
          else
            persist_apps_status=$?
            show_warning_and_wait "Could not generate ${stack_apps_path} (${persist_apps_status})." 3
            continue
          fi

          show_warning_and_wait "apps.json generated successfully: ${stack_apps_path}" 3
          ;;
        "Select apps and branches")
          if update_stack_custom_modular_apps "${stack_dir}"; then
            :
          else
            custom_apps_update_status=$?
            case "${custom_apps_update_status}" in
            2 | 130)
              continue
              ;;
            3)
              stack_metadata_path="${stack_dir}/metadata.json"
              show_warning_and_wait "Cannot update app selection because metadata is missing: ${stack_metadata_path}" 3
              continue
              ;;
            *)
              show_warning_and_wait "Could not update app selection (${custom_apps_update_status}) for stack: ${stack_name}" 3
              continue
              ;;
            esac
          fi

          stack_apps_path="${stack_dir}/apps.json"
          show_warning_and_wait "App selection updated in ${stack_dir}/metadata.json and ${stack_apps_path}." 3
          ;;
        "Back" | "")
          break
          ;;
        "Exit and close easy-docker")
          return "${FLOW_EXIT_APP}"
          ;;
        *)
          show_warning_and_wait "Unknown apps action: ${apps_action}"
          ;;
        esac
      done
      ;;
    "Docker")
      while true; do
        docker_action="$(show_manage_stack_docker_menu "${stack_name}" "${stack_dir}" || true)"
        case "${docker_action}" in
        "Generate docker compose from env")
          generated_compose_path="$(get_stack_generated_compose_path "${stack_dir}")"
          if render_stack_compose_from_metadata "${stack_dir}"; then
            :
          else
            render_compose_status=$?
            show_warning_and_wait "Could not generate docker compose (${render_compose_status}) for ${generated_compose_path}." 3
            continue
          fi

          show_warning_and_wait "Docker compose generated successfully: ${generated_compose_path}" 3
          ;;
        "Back" | "")
          break
          ;;
        "Exit and close easy-docker")
          return "${FLOW_EXIT_APP}"
          ;;
        *)
          show_warning_and_wait "Unknown docker action: ${docker_action}"
          ;;
        esac
      done
      ;;
    "Back" | "")
      return "${FLOW_CONTINUE}"
      ;;
    "Exit and close easy-docker")
      return "${FLOW_EXIT_APP}"
      ;;
    *)
      show_warning_and_wait "Unknown stack action: ${stack_action}"
      ;;
    esac
  done
}
