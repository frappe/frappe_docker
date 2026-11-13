#!/usr/bin/env bash

json_escape_string() {
  local raw_value="${1}"

  raw_value="${raw_value//\\/\\\\}"
  raw_value="${raw_value//\"/\\\"}"
  raw_value="${raw_value//$'\n'/\\n}"
  raw_value="${raw_value//$'\r'/\\r}"
  raw_value="${raw_value//$'\t'/\\t}"

  printf '%s' "${raw_value}"
}

build_compose_files_json_array() {
  local compose_files_lines="${1}"
  local line=""
  local first=1

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi

    if [ "${first}" -eq 1 ]; then
      printf '      "%s"' "${line}"
      first=0
    else
      printf ',\n      "%s"' "${line}"
    fi
  done <<EOF
${compose_files_lines}
EOF
}

build_env_json_object() {
  local env_lines="${1}"
  local line=""
  local key=""
  local value=""
  local escaped_key=""
  local escaped_value=""
  local first=1

  printf '{'

  while IFS= read -r line; do
    if [ -z "${line}" ]; then
      continue
    fi

    case "${line}" in
    *=*) ;;
    *)
      continue
      ;;
    esac

    key="${line%%=*}"
    value="${line#*=}"
    escaped_key="$(json_escape_string "${key}")"
    escaped_value="$(json_escape_string "${value}")"

    if [ "${first}" -eq 1 ]; then
      printf '\n      "%s": "%s"' "${escaped_key}" "${escaped_value}"
      first=0
    else
      printf ',\n      "%s": "%s"' "${escaped_key}" "${escaped_value}"
    fi
  done <<EOF
${env_lines}
EOF

  if [ "${first}" -eq 1 ]; then
    printf '}'
  else
    printf '\n    }'
  fi
}

append_env_line() {
  local existing_lines="${1}"
  local key="${2}"
  local value="${3}"

  if [ -z "${existing_lines}" ]; then
    printf '%s=%s' "${key}" "${value}"
    return
  fi

  printf '%s\n%s=%s' "${existing_lines}" "${key}" "${value}"
}
