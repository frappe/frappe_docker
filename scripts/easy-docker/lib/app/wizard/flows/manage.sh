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
  local build_image_status=0
  local compose_start_status=0
  local generated_compose_path=""
  local stack_runtime_status=""

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
      show_warning_message "Starting stack with docker compose: ${stack_name}"
      if start_stack_with_compose_from_metadata "${stack_dir}"; then
        :
      else
        compose_start_status=$?
        case "${compose_start_status}" in
        31)
          show_warning_and_wait "Cannot start stack: metadata.json is missing in ${stack_dir}." 4
          ;;
        32)
          show_warning_and_wait "Cannot start stack: stack env file not found in ${stack_dir}." 4
          ;;
        33)
          show_warning_and_wait "Cannot start stack: topology is missing in metadata.json. Re-run the topology wizard for this stack." 4
          ;;
        34)
          show_warning_and_wait "Cannot start stack via docker compose for topology '${EASY_DOCKER_COMPOSE_ERROR_DETAIL}'. Use the topology-specific runbook path." 5
          ;;
        35)
          show_warning_and_wait "Cannot start stack: no compose files configured in metadata.json." 4
          ;;
        36)
          show_warning_and_wait "Cannot start stack: compose file is missing -> ${EASY_DOCKER_COMPOSE_ERROR_DETAIL}" 4
          ;;
        37)
          show_warning_and_wait "docker compose up failed. Check the output above for details." 4
          ;;
        *)
          show_warning_and_wait "Cannot start stack with docker compose (${compose_start_status})." 4
          ;;
        esac
        continue
      fi

      show_warning_and_wait "Stack started successfully with docker compose: ${stack_name}" 3
      ;;
    "Docker")
      while true; do
        docker_action="$(show_manage_stack_docker_menu "${stack_name}" "${stack_dir}" || true)"
        case "${docker_action}" in
        "Build custom image")
          show_warning_message "Starting docker build for stack: ${stack_name}"
          if build_stack_custom_image "${stack_dir}"; then
            :
          else
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
            continue
          fi

          show_warning_and_wait "Custom image build finished successfully for stack: ${stack_name}" 3
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
