#!/usr/bin/env bash

run_build_stack_custom_image_with_feedback() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local build_image_status=0

  show_warning_message "Starting docker build for stack: ${stack_name}"
  if build_stack_custom_image "${stack_dir}"; then
    show_warning_and_wait "Custom image build finished successfully for stack: ${stack_name}" 3
    return 0
  fi

  build_image_status=$?
  case "${build_image_status}" in
  11)
    show_warning_and_wait "Custom image build failed: missing metadata.json in ${stack_dir}." 4
    ;;
  12)
    show_warning_and_wait "Custom image build failed: stack env file not found in ${stack_dir}." 4
    ;;
  13)
    show_warning_and_wait "Custom image build failed: CUSTOM_IMAGE is missing in stack env file." 4
    ;;
  14)
    show_warning_and_wait "Custom image build failed: CUSTOM_TAG is missing in stack env file." 4
    ;;
  15)
    show_warning_and_wait "Custom image build failed: frappe_branch missing in metadata.json." 4
    ;;
  16)
    show_warning_and_wait "Custom image build failed: could not generate apps.json from metadata app selection." 4
    ;;
  17)
    show_warning_and_wait "Custom image build failed: apps.json not found after generation." 4
    ;;
  18)
    show_warning_and_wait "Custom image build failed: base64 command is not available in this environment." 4
    ;;
  19)
    show_warning_and_wait "Custom image build failed: apps.json could not be base64-encoded." 4
    ;;
  20)
    show_warning_and_wait "Custom image build failed: images/layered/Containerfile not found." 4
    ;;
  21)
    show_warning_and_wait "Custom image build failed: docker build returned an error. Check the output above." 4
    ;;
  22)
    show_warning_and_wait "Custom image build failed: git is required for app branch precheck (git ls-remote)." 4
    ;;
  23)
    show_warning_and_wait "Custom image build failed: could not parse app entries from apps.json." 4
    ;;
  24)
    show_warning_and_wait "Custom image build failed: app branch precheck failed -> ${EASY_DOCKER_BUILD_ERROR_DETAIL}" 6
    ;;
  *)
    show_warning_and_wait "Custom image build failed (${build_image_status})." 4
    ;;
  esac

  return "${build_image_status}"
}

prompt_manage_stack_site_name_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local stack_dir="${3}"
  local input_site_name=""
  local suggestion=""
  local prompt_status=0

  suggestion="$(get_stack_primary_site_name_suggestion "${stack_dir}" || true)"
  while true; do
    input_site_name="$(prompt_stack_site_name "${stack_name}" "${suggestion}")"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return "${FLOW_ABORT_INPUT}"
    fi

    input_site_name="$(printf '%s' "${input_site_name}" | tr -d '\r\n')"
    case "${input_site_name}" in
    "")
      show_warning_and_wait "Site name is required." 2
      ;;
    /back | /Back | /BACK)
      return "${FLOW_ABORT_INPUT}"
      ;;
    *)
      if ! is_valid_stack_site_name "${input_site_name}"; then
        show_warning_and_wait "Site name may only contain letters, numbers, dots, dashes, and underscores." 3
        continue
      fi
      printf -v "${result_var}" "%s" "${input_site_name}"
      return "${FLOW_CONTINUE}"
      ;;
    esac
  done
}

prompt_manage_stack_site_admin_password_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local input_admin_password=""
  local prompt_status=0

  while true; do
    input_admin_password="$(prompt_stack_site_admin_password "${stack_name}")"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return "${FLOW_ABORT_INPUT}"
    fi

    input_admin_password="$(printf '%s' "${input_admin_password}" | tr -d '\r\n')"
    case "${input_admin_password}" in
    "")
      show_warning_and_wait "Administrator password is required." 2
      ;;
    /back | /Back | /BACK)
      return "${FLOW_ABORT_INPUT}"
      ;;
    *)
      printf -v "${result_var}" "%s" "${input_admin_password}"
      return "${FLOW_CONTINUE}"
      ;;
    esac
  done
}

prompt_manage_stack_delete_keyword_with_cancel() {
  local result_var="${1}"
  local stack_name="${2}"
  local delete_confirmation=""
  local prompt_status=0

  while true; do
    delete_confirmation="$(prompt_manage_stack_delete_keyword "${stack_name}")"
    prompt_status=$?
    if [ "${prompt_status}" -ne 0 ]; then
      return "${FLOW_ABORT_INPUT}"
    fi

    delete_confirmation="$(printf '%s' "${delete_confirmation}" | tr -d '\r\n')"
    case "${delete_confirmation}" in
    /back | /Back | /BACK | "")
      return "${FLOW_ABORT_INPUT}"
      ;;
    delete)
      printf -v "${result_var}" "%s" "${delete_confirmation}"
      return "${FLOW_CONTINUE}"
      ;;
    *)
      show_warning_and_wait "Type exactly delete to confirm stack removal." 3
      ;;
    esac
  done
}

handle_manage_stack_site_flow() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local site_action=""
  local site_name=""
  local admin_password=""
  local site_flow_status=0
  local existing_site_entry=""
  local existing_site_name=""
  local existing_site_created_at=""
  local existing_site_apps_lines=""
  local existing_site_apps_csv=""
  local existing_site_details_action=""
  local site_delete_confirmation=""

  while true; do
    existing_site_entry=""
    get_stack_site_menu_entry existing_site_entry "${stack_dir}" || true

    site_action="$(show_manage_stack_site_menu "${stack_name}" "${stack_dir}" "${existing_site_entry}" || true)"
    case "${site_action}" in
    "Create new site")
      if ! prompt_manage_stack_site_name_with_cancel site_name "${stack_name}" "${stack_dir}"; then
        continue
      fi

      if ! prompt_manage_stack_site_admin_password_with_cancel admin_password "${stack_name}"; then
        continue
      fi

      show_warning_message "Creating the first site for stack: ${stack_name}"
      if bootstrap_first_stack_site "${stack_dir}" "${site_name}" "${admin_password}"; then
        show_warning_and_wait "Site created successfully and selected stack apps were installed: ${site_name}" 3
        continue
      else
        site_flow_status=$?
      fi

      case "${site_flow_status}" in
      51)
        show_warning_and_wait "Cannot manage site: backend service is not running yet. Start the stack first." 4
        ;;
      52)
        show_warning_and_wait "Cannot manage site for this topology yet. Only single-host stacks are supported." 4
        ;;
      53)
        show_warning_and_wait "A site is already configured for this stack. Phase 1 supports one site per stack." 4
        ;;
      54)
        show_warning_and_wait "Cannot manage site because stack metadata, env, or compose inputs are incomplete." 4
        ;;
      55)
        show_warning_and_wait "Could not create the site. ${EASY_DOCKER_SITE_ERROR_DETAIL:-Check the output above for bench new-site details.} ${EASY_DOCKER_SITE_ERROR_LOG_PATH:+See ${stack_dir}/${EASY_DOCKER_SITE_ERROR_LOG_PATH}}" 6
        ;;
      56)
        show_warning_and_wait "The site was created, but app installation failed. ${EASY_DOCKER_SITE_ERROR_DETAIL:-Check the output above.} ${EASY_DOCKER_SITE_ERROR_LOG_PATH:+See ${stack_dir}/${EASY_DOCKER_SITE_ERROR_LOG_PATH}}" 6
        ;;
      57)
        show_warning_and_wait "Site bootstrap currently supports only MariaDB-backed single-host stacks." 4
        ;;
      58)
        show_warning_and_wait "The site state could not be written to metadata.json." 4
        ;;
      59)
        show_warning_and_wait "Cannot create site: stack services are not ready yet. Wait and try again." 4
        ;;
      60)
        show_warning_and_wait "Site creation failed and automatic cleanup could not remove all partial data. Manual cleanup is required." 5
        ;;
      61)
        show_warning_and_wait "Cannot create site because the site name was empty or unsafe for cleanup operations." 4
        ;;
      62)
        show_warning_and_wait "Cannot prepare the stack for site creation because the bench runtime files could not be repaired." 4
        ;;
      63)
        show_warning_and_wait "Cannot install the selected stack apps because at least one app is missing from the backend image. ${EASY_DOCKER_SITE_ERROR_DETAIL} ${EASY_DOCKER_SITE_ERROR_LOG_PATH:+See ${stack_dir}/${EASY_DOCKER_SITE_ERROR_LOG_PATH}}" 7
        ;;
      *)
        show_warning_and_wait "Site bootstrap failed (${site_flow_status})." 4
        ;;
      esac
      ;;
    "Back" | "")
      return "${FLOW_CONTINUE}"
      ;;
    "Exit and close easy-docker")
      return "${FLOW_EXIT_APP}"
      ;;
    *)
      if [ -n "${existing_site_entry}" ] && [ "${site_action}" = "${existing_site_entry}" ]; then
        existing_site_name="$(get_stack_site_name "${stack_dir}" || true)"
        existing_site_created_at="$(get_stack_site_created_at "${stack_dir}" || true)"
        existing_site_apps_lines="$(get_stack_site_apps_installed_lines "${stack_dir}" || true)"
        if stack_backend_service_is_running "${stack_dir}" >/dev/null 2>&1; then
          get_stack_site_runtime_selected_apps_lines existing_site_apps_lines "${stack_dir}" "${existing_site_name}" || true
        fi
        if [ -n "${existing_site_apps_lines}" ]; then
          existing_site_apps_csv="$(printf '%s' "${existing_site_apps_lines}" | tr '\n' ',' | sed 's/,$//')"
        else
          existing_site_apps_csv="None"
        fi

        existing_site_details_action="$(
          show_manage_stack_site_details \
            "${stack_name}" \
            "${stack_dir}" \
            "${existing_site_name}" \
            "${existing_site_created_at}" \
            "${existing_site_apps_csv}" || true
        )"
        case "${existing_site_details_action}" in
        "Delete site")
          site_delete_confirmation="$(
            show_manage_stack_site_delete_confirmation \
              "${stack_name}" \
              "${stack_dir}" \
              "${existing_site_name}" || true
          )"
          case "${site_delete_confirmation}" in
          "Yes")
            show_warning_message "Deleting site for stack: ${stack_name}"
            if delete_configured_stack_site "${stack_dir}"; then
              show_warning_and_wait "Site deleted successfully with its database: ${existing_site_name}" 3
              continue
            fi

            site_flow_status=$?
            case "${site_flow_status}" in
            51)
              show_warning_and_wait "Cannot delete site: backend service is not running yet. Start the stack first." 4
              ;;
            52)
              show_warning_and_wait "Cannot delete site for this topology yet. Only single-host stacks are supported." 4
              ;;
            54)
              show_warning_and_wait "Cannot delete site because stack metadata, env, or compose inputs are incomplete." 4
              ;;
            58)
              show_warning_and_wait "The cleared site state could not be written to metadata.json." 4
              ;;
            60)
              show_warning_and_wait "Site deletion could not remove all site or database data automatically. Manual cleanup is required." 5
              ;;
            61)
              show_warning_and_wait "Cannot delete site because the configured site name was empty or unsafe for cleanup operations." 4
              ;;
            *)
              show_warning_and_wait "Site deletion failed (${site_flow_status})." 4
              ;;
            esac
            continue
            ;;
          "No" | "")
            continue
            ;;
          "Exit and close easy-docker")
            return "${FLOW_EXIT_APP}"
            ;;
          *)
            show_warning_and_wait "Unknown site delete confirmation action: ${site_delete_confirmation}" 2
            continue
            ;;
          esac
          ;;
        "Back" | "")
          continue
          ;;
        "Exit and close easy-docker")
          return "${FLOW_EXIT_APP}"
          ;;
        *)
          show_warning_and_wait "Unknown site details action: ${existing_site_details_action}" 2
          ;;
        esac
        continue
      fi

      show_warning_and_wait "Unknown site action: ${site_action}" 2
      ;;
    esac
  done
}

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
