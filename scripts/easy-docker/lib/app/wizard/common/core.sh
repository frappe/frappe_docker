#!/usr/bin/env bash

get_easy_docker_repo_root() {
  local app_lib_dir=""

  if [ -n "${EASY_DOCKER_REPO_ROOT_OVERRIDE:-}" ]; then
    printf '%s\n' "${EASY_DOCKER_REPO_ROOT_OVERRIDE}"
    return 0
  fi

  app_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # core.sh lives in scripts/easy-docker/lib/app/wizard/common
  # so we need 6 levels up to reach repository root.
  (cd "${app_lib_dir}/../../../../../.." && pwd)
}

get_easy_docker_stacks_dir() {
  printf '%s/.easy-docker/stacks\n' "$(get_easy_docker_repo_root)"
}

get_current_utc_timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ"
}

is_valid_stack_name() {
  local stack_name="${1}"

  if [ -z "${stack_name}" ]; then
    return 1
  fi

  case "${stack_name}" in
  *[!A-Za-z0-9._-]*)
    return 1
    ;;
  *)
    return 0
    ;;
  esac
}

create_stack_directory_with_metadata() {
  local stack_dir_var="${1}"
  local stack_name="${2}"
  local setup_type="${3:-production}"
  local frappe_branch="${4:-}"
  local stacks_dir=""
  local created_stack_dir=""
  local metadata_path=""
  local created_at=""

  stacks_dir="$(get_easy_docker_stacks_dir)"
  created_stack_dir="${stacks_dir}/${stack_name}"
  metadata_path="${created_stack_dir}/metadata.json"

  if ! mkdir -p "${stacks_dir}"; then
    return 1
  fi

  if [ -e "${created_stack_dir}" ]; then
    return 2
  fi

  if [ -z "${frappe_branch}" ]; then
    return 1
  fi

  if ! mkdir -p "${created_stack_dir}"; then
    return 1
  fi

  created_at="$(get_current_utc_timestamp)"

  if ! cat >"${metadata_path}" <<EOF; then
{
  "schema_version": 1,
  "stack_name": "${stack_name}",
  "setup_type": "${setup_type}",
  "frappe_branch": "${frappe_branch}",
  "created_at": "${created_at}"
}
EOF
    rollback_stack_directory "${created_stack_dir}" >/dev/null 2>&1 || true
    return 1
  fi

  printf -v "${stack_dir_var}" "%s" "${created_stack_dir}"
  return 0
}

rollback_stack_directory() {
  local stack_dir="${1}"
  local stacks_dir=""

  if [ -z "${stack_dir}" ]; then
    return 1
  fi

  stacks_dir="$(get_easy_docker_stacks_dir)"
  case "${stack_dir}" in
  "${stacks_dir}"/*) ;;
  *)
    return 2
    ;;
  esac

  if [ ! -d "${stack_dir}" ]; then
    return 0
  fi

  rm -rf -- "${stack_dir}"
}

get_metadata_string_field() {
  local metadata_path="${1}"
  local field_name="${2}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if ! easy_docker_require_jq; then
    return 1
  fi

  # shellcheck disable=SC2016
  easy_docker_run_jq -r --arg field_name "${field_name}" '[.. | objects | .[$field_name]? | select(type == "string")][0] // empty' "${metadata_path}"
}

get_env_file_key_value() {
  local env_file="${1}"
  local key="${2}"
  local value=""

  if [ ! -f "${env_file}" ]; then
    return 1
  fi

  value="$(
    awk -v key="${key}" '
      /^[[:space:]]*#/ { next }
      $0 !~ /=/ { next }
      {
        line = $0
        sub(/\r$/, "", line)
        pos = index(line, "=")
        if (pos == 0) {
          next
        }
        k = substr(line, 1, pos - 1)
        sub(/^[[:space:]]*export[[:space:]]+/, "", k)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", k)
        if (k != key) {
          next
        }
        v = substr(line, pos + 1)
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", v)
        print v
        exit
      }
    ' "${env_file}"
  )"

  if [ -z "${value}" ]; then
    return 1
  fi

  case "${value}" in
  \"*\")
    value="${value#\"}"
    value="${value%\"}"
    ;;
  \'*\')
    value="${value#\'}"
    value="${value%\'}"
    ;;
  esac

  printf '%s\n' "${value}"
}

get_default_erpnext_version() {
  local repo_root=""
  local source_env_file=""
  local value=""

  if [ -n "${ERPNEXT_VERSION:-}" ]; then
    printf '%s\n' "${ERPNEXT_VERSION}"
    return 0
  fi

  repo_root="$(get_easy_docker_repo_root)"
  for source_env_file in "${repo_root}/.env" "${repo_root}/example.env"; do
    value="$(get_env_file_key_value "${source_env_file}" "ERPNEXT_VERSION" || true)"
    if [ -n "${value}" ]; then
      printf '%s\n' "${value}"
      return 0
    fi
  done

  return 1
}

get_default_frappe_branch() {
  local repo_root=""
  local source_env_file=""
  local value=""

  if [ -n "${FRAPPE_BRANCH:-}" ]; then
    printf '%s\n' "${FRAPPE_BRANCH}"
    return 0
  fi

  repo_root="$(get_easy_docker_repo_root)"
  for source_env_file in "${repo_root}/.env" "${repo_root}/example.env"; do
    value="$(get_env_file_key_value "${source_env_file}" "FRAPPE_BRANCH" || true)"
    if [ -n "${value}" ]; then
      printf '%s\n' "${value}"
      return 0
    fi
  done

  printf 'version-15\n'
  return 0
}

get_stack_frappe_branch() {
  local stack_dir="${1}"
  local metadata_path=""
  local value=""

  metadata_path="${stack_dir}/metadata.json"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  value="$(get_metadata_string_field "${metadata_path}" "frappe_branch" || true)"
  if [ -z "${value}" ]; then
    return 1
  fi

  printf '%s\n' "${value}"
  return 0
}

get_stack_env_path() {
  local stack_dir="${1}"
  local metadata_path=""
  local stack_name=""

  metadata_path="${stack_dir}/metadata.json"
  stack_name="$(get_metadata_string_field "${metadata_path}" "stack_name" || true)"
  if [ -z "${stack_name}" ]; then
    stack_name="${stack_dir##*/}"
  fi

  printf '%s/%s.env\n' "${stack_dir}" "${stack_name}"
}

get_stack_compose_project_name() {
  local stack_dir="${1}"
  local metadata_path=""
  local stack_name=""
  local project_name=""

  metadata_path="${stack_dir}/metadata.json"
  stack_name="$(get_metadata_string_field "${metadata_path}" "stack_name" || true)"
  if [ -z "${stack_name}" ]; then
    stack_name="${stack_dir##*/}"
  fi

  project_name="$(
    printf '%s' "${stack_name}" |
      tr '[:upper:]' '[:lower:]' |
      sed 's/[^a-z0-9_-]/-/g; s/--*/-/g; s/^-*//; s/-*$//'
  )"
  if [ -z "${project_name}" ]; then
    project_name="stack"
  fi

  printf 'easydocker-%s\n' "${project_name}"
}

get_stack_generated_compose_path() {
  local stack_dir="${1}"

  printf '%s/compose.generated.yaml\n' "${stack_dir}"
}

get_stack_dir_by_name() {
  local stack_name="${1}"
  local stacks_dir=""
  local stack_dir=""
  local metadata_path=""
  local candidate_name=""

  stacks_dir="$(get_easy_docker_stacks_dir)"
  if [ ! -d "${stacks_dir}" ]; then
    return 1
  fi

  for stack_dir in "${stacks_dir}"/*; do
    if [ ! -d "${stack_dir}" ]; then
      continue
    fi

    metadata_path="${stack_dir}/metadata.json"
    if [ ! -f "${metadata_path}" ]; then
      continue
    fi

    candidate_name="$(get_metadata_string_field "${metadata_path}" "stack_name" || true)"
    if [ "${candidate_name}" = "${stack_name}" ]; then
      printf '%s\n' "${stack_dir}"
      return 0
    fi
  done

  return 1
}

get_stack_topology() {
  local stack_dir="${1}"
  local metadata_path=""
  local topology=""

  metadata_path="${stack_dir}/metadata.json"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  topology="$(get_metadata_string_field "${metadata_path}" "topology" || true)"
  if [ -z "${topology}" ]; then
    return 1
  fi

  printf '%s\n' "${topology}"
  return 0
}

get_stack_setup_type() {
  local stack_dir="${1}"
  local metadata_path=""
  local setup_type=""

  metadata_path="${stack_dir}/metadata.json"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  setup_type="$(get_metadata_string_field "${metadata_path}" "setup_type" || true)"
  if [ -z "${setup_type}" ]; then
    return 1
  fi

  printf '%s\n' "${setup_type}"
  return 0
}

get_metadata_compose_files_lines() {
  local metadata_path="${1}"

  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if ! easy_docker_require_jq; then
    return 1
  fi

  easy_docker_run_jq -r '([.. | objects | .compose_files? | select(type == "array")] | .[0] // [])[]?' "${metadata_path}"
}
