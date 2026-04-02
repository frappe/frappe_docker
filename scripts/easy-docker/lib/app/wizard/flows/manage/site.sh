#!/usr/bin/env bash

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
  local existing_site_last_backup_at=""
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
        show_warning_and_wait "Site created successfully, selected stack apps were installed, and bench migrate completed: ${site_name}" 3
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
        show_warning_and_wait "The site metadata could not be written to metadata.json." 4
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
      64)
        show_warning_and_wait "The site was created and apps were installed, but bench migrate failed. ${EASY_DOCKER_SITE_ERROR_DETAIL:-Check the output above.} ${EASY_DOCKER_SITE_ERROR_LOG_PATH:+See ${stack_dir}/${EASY_DOCKER_SITE_ERROR_LOG_PATH}}" 7
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
        existing_site_last_backup_at="$(get_stack_site_last_backup_at "${stack_dir}" || true)"
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
            "${existing_site_apps_csv}" \
            "${existing_site_last_backup_at}" || true
        )"
        case "${existing_site_details_action}" in
        "Backup site now")
          show_warning_message "Creating backup for site: ${existing_site_name}"
          if backup_configured_stack_site "${stack_dir}"; then
            existing_site_last_backup_at="$(get_stack_site_last_backup_at "${stack_dir}" || true)"
            show_warning_and_wait "Site backup completed successfully: ${existing_site_name}${existing_site_last_backup_at:+ (last backup at ${existing_site_last_backup_at})}" 4
            continue
          fi

          site_flow_status=$?
          case "${site_flow_status}" in
          71)
            show_warning_and_wait "Cannot back up site: backend service is not running yet. Start the stack first." 4
            ;;
          72)
            show_warning_and_wait "Cannot back up site for this topology yet. Only single-host stacks are supported." 4
            ;;
          73)
            show_warning_and_wait "Cannot back up site because no configured site was found in metadata.json." 4
            ;;
          74)
            show_warning_and_wait "Cannot back up site because stack metadata, env, or compose inputs are incomplete." 4
            ;;
          75)
            show_warning_and_wait "Site backup failed. ${EASY_DOCKER_SITE_ERROR_DETAIL:-Check the output above.} ${EASY_DOCKER_SITE_ERROR_LOG_PATH:+See ${stack_dir}/${EASY_DOCKER_SITE_ERROR_LOG_PATH}}" 6
            ;;
          76)
            show_warning_and_wait "The backup command finished, but the backup metadata could not be written to metadata.json." 5
            ;;
          *)
            show_warning_and_wait "Site backup failed (${site_flow_status})." 4
            ;;
          esac
          continue
          ;;
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
            else
              site_flow_status=$?
            fi
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
              show_warning_and_wait "The cleared site metadata could not be written to metadata.json." 4
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
