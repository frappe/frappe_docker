#!/usr/bin/env bash

append_stack_installable_app_line() {
  local result_var="${1}"
  local existing_lines="${2:-}"
  local app_name="${3:-}"

  if [ -z "${app_name}" ]; then
    printf -v "${result_var}" "%s" "${existing_lines}"
    return 0
  fi

  while IFS= read -r existing_app; do
    if [ "${existing_app}" = "${app_name}" ]; then
      printf -v "${result_var}" "%s" "${existing_lines}"
      return 0
    fi
  done <<EOF
${existing_lines}
EOF

  if [ -z "${existing_lines}" ]; then
    printf -v "${result_var}" "%s" "${app_name}"
  else
    printf -v "${result_var}" "%s\n%s" "${existing_lines}" "${app_name}"
  fi
}

get_stack_selected_installable_apps() {
  local result_var="${1}"
  local stack_dir="${2}"
  local metadata_path=""
  local predefined_apps_csv=""
  local app_name=""
  local installable_app_lines=""
  local deferred_erpnext=""
  local ordered_app_lines=""
  local -a predefined_apps=()

  metadata_path="${stack_dir}/metadata.json"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  predefined_apps_csv="$(get_metadata_apps_predefined_csv "${metadata_path}" || true)"
  if [ -z "${predefined_apps_csv}" ]; then
    printf -v "${result_var}" "%s" ""
    return 0
  fi

  IFS=',' read -r -a predefined_apps <<<"${predefined_apps_csv}"
  for app_name in "${predefined_apps[@]}"; do
    if [ -z "${app_name}" ] || [ "${app_name}" = "frappe" ]; then
      continue
    fi

    if [ "${app_name}" = "erpnext" ]; then
      deferred_erpnext="${app_name}"
      continue
    fi

    append_stack_installable_app_line installable_app_lines "${installable_app_lines}" "${app_name}"
  done

  if [ -n "${deferred_erpnext}" ]; then
    ordered_app_lines="${deferred_erpnext}"
    if [ -n "${installable_app_lines}" ]; then
      ordered_app_lines="${ordered_app_lines}"$'\n'"${installable_app_lines}"
    fi
  else
    ordered_app_lines="${installable_app_lines}"
  fi

  printf -v "${result_var}" "%s" "${ordered_app_lines}"
  return 0
}
