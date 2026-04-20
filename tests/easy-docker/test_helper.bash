#!/usr/bin/env bash

easy_docker_test_repo_root() {
  local helper_dir=""

  helper_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  (cd "${helper_dir}/../.." && pwd)
}

easy_docker_test_begin() {
  EASY_DOCKER_TEST_TMPDIR="$(mktemp -d)"
  export EASY_DOCKER_TEST_TMPDIR
  unset EASY_DOCKER_REPO_ROOT_OVERRIDE
}

easy_docker_test_end() {
  if [ -n "${EASY_DOCKER_TEST_TMPDIR:-}" ] && [ -d "${EASY_DOCKER_TEST_TMPDIR}" ]; then
    rm -rf "${EASY_DOCKER_TEST_TMPDIR}"
  fi
}

easy_docker_test_bin_dir() {
  printf '%s/bin\n' "${EASY_DOCKER_TEST_TMPDIR}"
}

easy_docker_test_write_executable() {
  local target_path="${1}"
  local system_bash=""
  shift

  system_bash="$(command -v bash)"
  mkdir -p "$(dirname "${target_path}")"

  {
    printf '#!%s\n' "${system_bash}"
    printf '%s\n' "$@"
  } >"${target_path}"
  chmod +x "${target_path}"
}

easy_docker_test_write_bin_command() {
  local command_name="${1}"
  local target_path=""
  shift

  target_path="$(easy_docker_test_bin_dir)/${command_name}"
  easy_docker_test_write_executable "${target_path}" "$@"
}

easy_docker_test_prepend_bin_dir() {
  PATH="$(easy_docker_test_bin_dir):${PATH}"
  export PATH
}

easy_docker_test_source_common_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  # shellcheck source=scripts/easy-docker/lib/core/commands.sh
  source "${repo_root}/scripts/easy-docker/lib/core/commands.sh"
  # shellcheck source=scripts/easy-docker/lib/core/messages.sh
  source "${repo_root}/scripts/easy-docker/lib/core/messages.sh"
  # shellcheck source=scripts/easy-docker/lib/core/json.sh
  source "${repo_root}/scripts/easy-docker/lib/core/json.sh"
}

easy_docker_test_source_core_render_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/core.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/core.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/render.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/compose/render.sh"
}

easy_docker_test_source_apps_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/core.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/core.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/helpers.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/helpers.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps/metadata.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/apps/metadata.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps/persistence.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/apps/persistence.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/apps/catalog.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/apps/catalog.sh"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/compose/build.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/compose/build.sh"
}

easy_docker_test_source_docker_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/checks/docker.sh
  source "${repo_root}/scripts/easy-docker/lib/checks/docker.sh"
}

easy_docker_test_source_jq_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/checks/jq.sh
  source "${repo_root}/scripts/easy-docker/lib/checks/jq.sh"
}

easy_docker_test_source_gum_modules() {
  local repo_root=""

  repo_root="$(easy_docker_test_repo_root)"

  easy_docker_test_source_common_modules

  # shellcheck source=scripts/easy-docker/lib/install/gum/package_manager.sh
  source "${repo_root}/scripts/easy-docker/lib/install/gum/package_manager.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/github_release.sh
  source "${repo_root}/scripts/easy-docker/lib/install/gum/github_release.sh"
  # shellcheck source=scripts/easy-docker/lib/install/gum/ensure.sh
  source "${repo_root}/scripts/easy-docker/lib/install/gum/ensure.sh"
}

easy_docker_test_create_repo_sandbox() {
  local sandbox_name="${1}"
  local sandbox_root=""

  sandbox_root="${EASY_DOCKER_TEST_TMPDIR}/repo-${sandbox_name}"
  mkdir -p "${sandbox_root}/.easy-docker/stacks" "${sandbox_root}/overrides"
  printf '%s\n' "${sandbox_root}"
}

easy_docker_test_override_repo_root() {
  EASY_DOCKER_REPO_ROOT_OVERRIDE="${1}"
  export EASY_DOCKER_REPO_ROOT_OVERRIDE
}

easy_docker_test_stack_dir() {
  local stack_name="${1}"

  printf '%s/.easy-docker/stacks/%s\n' "${EASY_DOCKER_REPO_ROOT_OVERRIDE}" "${stack_name}"
}

easy_docker_test_install_docker_stub() {
  local log_file=""

  log_file="${EASY_DOCKER_TEST_TMPDIR}/docker.invocations"

  # shellcheck disable=SC2016
  easy_docker_test_write_bin_command docker \
    'set -euo pipefail' \
    "log_file=\"${log_file}\"" \
    'printf '"'"'%s\n'"'"' "docker $*" >>"${log_file}"' \
    'if [ "${1:-}" != "compose" ]; then' \
    '  echo "unexpected docker subcommand: ${1:-}" >&2' \
    '  exit 64' \
    'fi' \
    'if [ "${!#}" != "config" ]; then' \
    '  echo "expected docker compose config invocation" >&2' \
    '  exit 65' \
    'fi' \
    'printf '"'"'invocation=%s\n'"'"' "docker $*"' \
    'printf '"'"'erpnext=%s\n'"'"' "${ERPNEXT_VERSION:-}"'

  easy_docker_test_prepend_bin_dir
}

easy_docker_test_install_jq_stub() {
  # shellcheck disable=SC2016
  easy_docker_test_write_bin_command jq \
    'set -euo pipefail' \
    'raw_output=0' \
    'exit_status=0' \
    'filter_expr=""' \
    'file_path=""' \
    'arg_field_name=""' \
    'arg_key=""' \
    'arg_app_id=""' \
    'while [ "$#" -gt 0 ]; do' \
    '  case "${1}" in' \
    '    -r)' \
    '      raw_output=1' \
    '      shift' \
    '      ;;' \
    '    -e)' \
    '      exit_status=1' \
    '      shift' \
    '      ;;' \
    '    --arg)' \
    '      case "${2}" in' \
    '        field_name) arg_field_name="${3}" ;;' \
    '        key) arg_key="${3}" ;;' \
    '        app_id) arg_app_id="${3}" ;;' \
    '      esac' \
    '      shift 3' \
    '      ;;' \
    '    --indent)' \
    '      shift 2' \
    '      ;;' \
    '    -*)' \
    '      shift' \
    '      ;;' \
    '    *)' \
    '      if [ -z "${filter_expr}" ]; then' \
    '        filter_expr="${1}"' \
    '      elif [ -z "${file_path}" ]; then' \
    '        file_path="${1}"' \
    '      else' \
    '        echo "unsupported jq stub arguments" >&2' \
    '        exit 2' \
    '      fi' \
    '      shift' \
    '      ;;' \
    '  esac' \
    'done' \
    'if [ -z "${filter_expr}" ]; then' \
    '  echo "missing jq filter" >&2' \
    '  exit 2' \
    'fi' \
    'cleanup_file=""' \
    'if [ -n "${file_path}" ] && [ "${file_path}" != "-" ]; then' \
    '  payload_path="${file_path}"' \
    'else' \
    '  payload_path="$(mktemp)"' \
    '  cleanup_file="${payload_path}"' \
    '  cat >"${payload_path}"' \
    'fi' \
    'jq_stub_cleanup() {' \
    '  if [ -n "${cleanup_file}" ] && [ -f "${cleanup_file}" ]; then' \
    '    rm -f "${cleanup_file}"' \
    '  fi' \
    '}' \
    'trap jq_stub_cleanup EXIT' \
    'jq_stub_is_object() {' \
    '  awk '"'"'BEGIN { found=0 } /^[[:space:]]*$/ { next } { if ($0 ~ /^[[:space:]]*{/) found=1; exit } END { exit(found ? 0 : 1) }'"'"' "${payload_path}"' \
    '}' \
    'jq_stub_first_string_field() {' \
    '  local field_name="${1}"' \
    '  awk -v field_name="${field_name}" '"'"'match($0, "\"" field_name "\"[[:space:]]*:[[:space:]]*\"([^\"]*)\"", parts) { print parts[1]; exit }'"'"' "${payload_path}"' \
    '}' \
    'jq_stub_array_strings() {' \
    '  local key="${1}"' \
    '  awk -v key="${key}" '"'"'' \
    '    function emit_matches(segment, parts) {' \
    '      while (match(segment, /"([^"]+)"/, parts)) {' \
    '        print parts[1]' \
    '        segment = substr(segment, RSTART + RLENGTH)' \
    '      }' \
    '    }' \
    '    $0 ~ "\"" key "\"[[:space:]]*:[[:space:]]*\\[" {' \
    '      segment = $0' \
    '      sub(/^.*\[[[:space:]]*/, "", segment)' \
    '      emit_matches(segment)' \
    '      if (segment ~ /\]/) {' \
    '        exit' \
    '      }' \
    '      in_array = 1' \
    '      next' \
    '    }' \
    '    in_array {' \
    '      emit_matches($0)' \
    '      if ($0 ~ /\]/) {' \
    '        exit' \
    '      }' \
    '    }' \
    '  '"'"' "${payload_path}"' \
    '}' \
    'jq_stub_object_entries() {' \
    '  local key="${1}"' \
    '  awk -v key="${key}" '"'"'' \
    '    $0 ~ "\"" key "\"[[:space:]]*:[[:space:]]*\\{" { in_object = 1; next }' \
    '    in_object && /^[[:space:]]*}/ { exit }' \
    '    in_object && match($0, /"([^"]+)"[[:space:]]*:[[:space:]]*"([^"]+)"/, parts) { print parts[1] "|" parts[2] }' \
    '  '"'"' "${payload_path}"' \
    '}' \
    'jq_stub_lookup_object_value() {' \
    '  local object_key="${1}"' \
    '  local lookup_key="${2}"' \
    '  awk -v object_key="${object_key}" -v lookup_key="${lookup_key}" '"'"'' \
    '    $0 ~ "\"" object_key "\"[[:space:]]*:[[:space:]]*\\{" { in_object = 1; next }' \
    '    in_object && /^[[:space:]]*}/ { exit }' \
    '    in_object && match($0, /"([^"]+)"[[:space:]]*:[[:space:]]*"([^"]+)"/, parts) {' \
    '      if (parts[1] == lookup_key) {' \
    '        print parts[2]' \
    '        exit' \
    '      }' \
    '    }' \
    '  '"'"' "${payload_path}"' \
    '}' \
    'jq_stub_top_level_keys() {' \
    '  awk '"'"'match($0, /^  "([^"]+)":/, parts) { print parts[1] }'"'"' "${payload_path}"' \
    '}' \
    'jq_stub_count_delta() {' \
    '  local line="${1}"' \
    '  local opens=0' \
    '  local closes=0' \
    '  local tmp=""' \
    '  tmp="${line//[^\{]/}"' \
    '  opens=$((opens + ${#tmp}))' \
    '  tmp="${line//[^\[]/}"' \
    '  opens=$((opens + ${#tmp}))' \
    '  tmp="${line//[^\}]/}"' \
    '  closes=$((closes + ${#tmp}))' \
    '  tmp="${line//[^\]]/}"' \
    '  closes=$((closes + ${#tmp}))' \
    '  printf "%s\n" "$((opens - closes))"' \
    '}' \
    'jq_stub_top_level_value() {' \
    '  local key="${1}"' \
    '  local line=""' \
    '  local value=""' \
    '  local in_block=0' \
    '  local depth=0' \
    '  local delta=0' \
    '  while IFS= read -r line || [ -n "${line}" ]; do' \
    '    if [ "${in_block}" -eq 0 ]; then' \
    '      case "${line}" in' \
    '        "  \"${key}\":"*)' \
    '          value="${line#*: }"' \
    '          if [[ "${value}" == \{* || "${value}" == \[* ]]; then' \
    '            printf "%s\n" "${value}"' \
    '            depth="$(jq_stub_count_delta "${value}")"' \
    '            if [ "${depth}" -le 0 ]; then' \
    '              return 0' \
    '            fi' \
    '            in_block=1' \
    '          else' \
    '            value="${value%,}"' \
    '            printf "%s\n" "${value}"' \
    '            return 0' \
    '          fi' \
    '          ;;' \
    '      esac' \
    '    else' \
    '      delta="$(jq_stub_count_delta "${line}")"' \
    '      if [ $((depth + delta)) -le 0 ]; then' \
    '        printf "%s\n" "${line%,}"' \
    '        return 0' \
    '      fi' \
    '      printf "%s\n" "${line}"' \
    '      depth=$((depth + delta))' \
    '    fi' \
    '  done <"${payload_path}"' \
    '}' \
    'jq_stub_apps_custom_lines() {' \
    '  local repo=""' \
    '  local branch=""' \
    '  awk '"'"'' \
    '    /"custom"[[:space:]]*:[[:space:]]*\[/ { in_custom = 1; next }' \
    '    in_custom && /\]/ { exit }' \
    '    in_custom && match($0, /"repo"[[:space:]]*:[[:space:]]*"([^"]+)"/, parts) { repo = parts[1] }' \
    '    in_custom && match($0, /"branch"[[:space:]]*:[[:space:]]*"([^"]+)"/, parts) { branch = parts[1] }' \
    '    in_custom && repo != "" && branch != "" { print repo "|" branch; repo = ""; branch = "" }' \
    '  '"'"' "${payload_path}"' \
    '}' \
    'jq_stub_apps_json_refs() {' \
    '  awk '"'"'match($0, /"url"[[:space:]]*:[[:space:]]*"([^"]+)".*"branch"[[:space:]]*:[[:space:]]*"([^"]+)"/, parts) { print parts[1] "|" parts[2] }'"'"' "${payload_path}"' \
    '}' \
    'case "${filter_expr}" in' \
    '  "(.apps.predefined // []) | join(\",\")")' \
    '    output="$(jq_stub_array_strings "predefined" | paste -sd, -)"' \
    '    [ -n "${output}" ] && printf "%s\n" "${output}"' \
    '    ;;' \
    '  "(.apps.custom // [])[]? | select(has(\"repo\") and has(\"branch\")) | \"\\(.repo)|\\(.branch)\"")' \
    '    jq_stub_apps_custom_lines' \
    '    ;;' \
    '  "(.apps.predefined_branches // {}) | to_entries[]? | \"\\(.key)|\\(.value)\"")' \
    '    jq_stub_object_entries "predefined_branches"' \
    '    ;;' \
    '  ".apps.predefined_branches[\$app_id] // empty")' \
    '    jq_stub_lookup_object_value "predefined_branches" "${arg_app_id}"' \
    '    ;;' \
    '  "[.. | objects | .[\$field_name]? | select(type == \"string\")][0] // empty")' \
    '    jq_stub_first_string_field "${arg_field_name}"' \
    '    ;;' \
    '  "([.. | objects | .compose_files? | select(type == \"array\")] | .[0] // [])[]?")' \
    '    jq_stub_array_strings "compose_files"' \
    '    ;;' \
    '  ".site[\$field_name] // empty")' \
    '    jq_stub_first_string_field "${arg_field_name}"' \
    '    ;;' \
    '  "(.site.apps_installed // [])[]? | select(type == \"string\")")' \
    '    jq_stub_array_strings "apps_installed"' \
    '    ;;' \
    '  "type == \"object\"")' \
    '    if jq_stub_is_object; then' \
    '      [ "${exit_status}" -eq 0 ] && printf "true\n"' \
    '      exit 0' \
    '    fi' \
    '    [ "${exit_status}" -eq 1 ] && exit 1' \
    '    printf "false\n"' \
    '    exit 0' \
    '    ;;' \
    '  "keys_unsorted[]")' \
    '    jq_stub_top_level_keys' \
    '    ;;' \
    '  ".[\$key]")' \
    '    jq_stub_top_level_value "${arg_key}"' \
    '    ;;' \
    '  ".[]? | select((.url // \"\") != \"\" and (.branch // \"\") != \"\") | \"\\(.url)|\\(.branch)\"")' \
    '    jq_stub_apps_json_refs' \
    '    ;;' \
    '  *)' \
    '    echo "unsupported jq filter in stub: ${filter_expr}" >&2' \
    '    exit 2' \
    '    ;;' \
    'esac'

  easy_docker_test_prepend_bin_dir
}
