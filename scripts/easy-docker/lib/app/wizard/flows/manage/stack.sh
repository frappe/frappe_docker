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
  local compose_start_status=0
  local generated_compose_path=""
  local stack_runtime_status=""
  local missing_custom_image_action=""
  local delete_stack_confirmation_action=""
  local delete_stack_keyword=""

  stack_dir="$(get_stack_dir_by_name "${stack_name}" || true)"
  if [ -z "${stack_dir}" ]; then
    show_warning_and_wait "Could not resolve stack directory for '${stack_name}'." 2
    return "${FLOW_CONTINUE}"
  fi

  while true; do
    get_stack_compose_runtime_status_label stack_runtime_status "${stack_dir}"
    stack_action="$(show_manage_stack_actions_menu "${stack_name}" "${stack_dir}" "${stack_runtime_status}" || true)"
    case "${stack_action}" in
    "Apps")
      while true; do
        apps_action="$(show_manage_stack_apps_menu "${stack_name}" "${stack_dir}" || true)"
        case "${apps_action}" in
        "Regenerate apps.json from metadata")
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
    "Start stack in Docker Compose")
      while true; do
        show_warning_message "Starting stack with docker compose: ${stack_name}"
        if start_stack_with_compose_from_metadata "${stack_dir}"; then
          show_warning_and_wait "Stack started successfully with docker compose: ${stack_name}" 3
          break
        else
          compose_start_status=$?
        fi
        case "${compose_start_status}" in
        31)
          show_warning_and_wait "Cannot start stack: metadata.json is missing in ${stack_dir}." 4
          break
          ;;
        32)
          show_warning_and_wait "Cannot start stack: stack env file not found in ${stack_dir}." 4
          break
          ;;
        33)
          show_warning_and_wait "Cannot start stack: topology is missing in metadata.json. Re-run the topology wizard for this stack." 4
          break
          ;;
        34)
          show_warning_and_wait "Cannot start stack via docker compose for topology '${EASY_DOCKER_COMPOSE_ERROR_DETAIL}'. Use the topology-specific runbook path." 5
          break
          ;;
        35)
          show_warning_and_wait "Cannot start stack: no compose files configured in metadata.json." 4
          break
          ;;
        36)
          show_warning_and_wait "Cannot start stack: compose file is missing -> ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 4
          break
          ;;
        37)
          show_warning_and_wait "docker compose up failed. Check the output above for details." 4
          break
          ;;
        38)
          missing_custom_image_action="$(
            show_missing_custom_image_start_menu "${stack_name}" "${stack_dir}" "${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" || true
          )"
          case "${missing_custom_image_action}" in
          "Build custom image now")
            if run_build_stack_custom_image_with_feedback "${stack_name}" "${stack_dir}"; then
              continue
            fi
            break
            ;;
          "Back" | "")
            break
            ;;
          "Exit and close easy-docker")
            return "${FLOW_EXIT_APP}"
            ;;
          *)
            show_warning_and_wait "Unknown missing-image action: ${missing_custom_image_action}" 2
            break
            ;;
          esac
          ;;
        39)
          show_warning_and_wait "Cannot inspect custom image before start. Check Docker and try again. Details: ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 5
          break
          ;;
        *)
          show_warning_and_wait "Cannot start stack with docker compose (${compose_start_status})." 4
          break
          ;;
        esac
      done
      ;;
    "Stop stack in Docker Compose")
      show_warning_message "Stopping stack with docker compose: ${stack_name}"
      if stop_stack_with_compose_from_metadata "${stack_dir}"; then
        show_warning_and_wait "Stack stopped successfully with docker compose: ${stack_name}" 3
        continue
      fi

      compose_start_status=$?
      case "${compose_start_status}" in
      41)
        show_warning_and_wait "Cannot stop stack: metadata.json is missing in ${stack_dir}." 4
        ;;
      42)
        show_warning_and_wait "Cannot stop stack: stack env file not found in ${stack_dir}." 4
        ;;
      43)
        show_warning_and_wait "Cannot stop stack: topology is missing in metadata.json. Re-run the topology wizard for this stack." 4
        ;;
      44)
        show_warning_and_wait "Cannot stop stack via docker compose for topology '${EASY_DOCKER_COMPOSE_ERROR_DETAIL}'. Use the topology-specific runbook path." 5
        ;;
      45)
        show_warning_and_wait "Cannot stop stack: no compose files configured in metadata.json." 4
        ;;
      46)
        show_warning_and_wait "Cannot stop stack: compose file is missing -> ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 4
        ;;
      47)
        show_warning_and_wait "docker compose stop failed. Check the output above for details." 4
        ;;
      *)
        show_warning_and_wait "Cannot stop stack with docker compose (${compose_start_status})." 4
        ;;
      esac
      ;;
    "Delete stack")
      delete_stack_confirmation_action="$(
        show_manage_stack_delete_confirmation "${stack_name}" "${stack_dir}" || true
      )"
      case "${delete_stack_confirmation_action}" in
      "Yes")
        if ! prompt_manage_stack_delete_keyword_with_cancel delete_stack_keyword "${stack_name}"; then
          continue
        fi
        if [ "${delete_stack_keyword}" != "delete" ]; then
          continue
        fi

        show_warning_message "Deleting stack with docker compose resources: ${stack_name}"
        if delete_stack_with_compose_from_metadata "${stack_dir}"; then
          show_warning_and_wait "Stack deleted successfully with containers, networks, volumes, image, and stack directory: ${stack_name}" 5
          return "${FLOW_CONTINUE}"
        fi

        compose_start_status=$?
        case "${compose_start_status}" in
        48)
          show_warning_and_wait "Cannot delete stack: metadata.json is missing in ${stack_dir}." 4
          ;;
        49)
          show_warning_and_wait "Cannot delete stack: stack env file not found in ${stack_dir}." 4
          ;;
        50)
          show_warning_and_wait "Cannot delete stack: topology is missing in metadata.json. Re-run the topology wizard for this stack." 4
          ;;
        51)
          show_warning_and_wait "Cannot delete stack via docker compose for topology '${EASY_DOCKER_COMPOSE_ERROR_DETAIL}'. Use the topology-specific runbook path." 5
          ;;
        52)
          show_warning_and_wait "Cannot delete stack: no compose files configured in metadata.json." 4
          ;;
        53)
          show_warning_and_wait "Cannot delete stack: compose file is missing -> ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 4
          ;;
        54)
          show_warning_and_wait "docker compose down failed. Check the output above for details." 4
          ;;
        55)
          show_warning_and_wait "Stack resources were removed, but the configured custom image could not be deleted -> ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 5
          ;;
        56)
          show_warning_and_wait "Docker resources were removed, but the stack directory could not be deleted -> ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 5
          ;;
        *)
          show_warning_and_wait "Cannot delete stack with docker compose (${compose_start_status})." 4
          ;;
        esac
        ;;
      "No" | "")
        continue
        ;;
      "Exit and close easy-docker")
        return "${FLOW_EXIT_APP}"
        ;;
      *)
        show_warning_and_wait "Unknown delete-stack action: ${delete_stack_confirmation_action}" 2
        ;;
      esac
      ;;
    "Docker")
      while true; do
        docker_action="$(show_manage_stack_docker_menu "${stack_name}" "${stack_dir}" || true)"
        case "${docker_action}" in
        "Build custom image")
          if run_build_stack_custom_image_with_feedback "${stack_name}" "${stack_dir}"; then
            :
          else
            continue
          fi
          ;;
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
    "Site")
      if handle_manage_stack_site_flow "${stack_name}" "${stack_dir}"; then
        :
      else
        compose_start_status=$?
        case "${compose_start_status}" in
        "${FLOW_EXIT_APP}")
          return "${FLOW_EXIT_APP}"
          ;;
        *)
          continue
          ;;
        esac
      fi
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
