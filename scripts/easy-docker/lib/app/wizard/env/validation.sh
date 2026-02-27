#!/usr/bin/env bash

is_valid_email_address() {
  local value="${1}"

  case "${value}" in
  *@*.*)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

is_valid_port_number() {
  local value="${1}"

  if ! [[ "${value}" =~ ^[0-9]+$ ]]; then
    return 1
  fi

  if [ "${value}" -lt 1 ] || [ "${value}" -gt 65535 ]; then
    return 1
  fi

  return 0
}

EASY_DOCKER_LAST_INVALID_DOMAIN=""

reset_domain_validation_feedback() {
  EASY_DOCKER_LAST_INVALID_DOMAIN=""
}

trim_domain_token() {
  local result_var="${1}"
  local value="${2}"

  while true; do
    case "${value}" in
    ' '*)
      value="${value# }"
      ;;
    *' ')
      value="${value% }"
      ;;
    $'\t'*)
      value="${value#$'\t'}"
      ;;
    *$'\t')
      value="${value%$'\t'}"
      ;;
    *)
      break
      ;;
    esac
  done

  printf -v "${result_var}" "%s" "${value}"
  return 0
}

normalize_domain_token() {
  local result_var="${1}"
  local raw_token="${2}"
  local token="${raw_token}"

  trim_domain_token token "${token}"
  if [ -z "${token}" ]; then
    return 1
  fi

  while true; do
    case "${token}" in
    \"*\")
      token="${token#\"}"
      token="${token%\"}"
      ;;
    \'*\')
      token="${token#\'}"
      token="${token%\'}"
      ;;
    \`*\`)
      token="${token#\`}"
      token="${token%\`}"
      ;;
    \[*\])
      token="${token#\[}"
      token="${token%\]}"
      ;;
    \(*\))
      token="${token#(}"
      token="${token%)}"
      ;;
    \"*)
      token="${token#\"}"
      ;;
    \'*)
      token="${token#\'}"
      ;;
    \`*)
      token="${token#\`}"
      ;;
    \[*)
      token="${token#\[}"
      ;;
    \(*)
      token="${token#(}"
      ;;
    *)
      break
      ;;
    esac
  done

  while true; do
    case "${token}" in
    *\")
      token="${token%\"}"
      ;;
    *\')
      token="${token%\'}"
      ;;
    *\`)
      token="${token%\`}"
      ;;
    *\])
      token="${token%\]}"
      ;;
    *\))
      token="${token%)}"
      ;;
    *)
      break
      ;;
    esac
  done

  trim_domain_token token "${token}"
  if [ -z "${token}" ]; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${token}"
  return 0
}

is_valid_domain_name() {
  local domain="${1}"
  local normalized_domain=""
  local label=""
  local tld=""
  local last_index=0
  local -a labels=()

  if ! normalize_domain_token normalized_domain "${domain}"; then
    return 1
  fi

  case "${normalized_domain}" in
  *[[:space:],:/?#!@]* | *";"* | .* | *. | *..* | *\**)
    return 1
    ;;
  esac

  if [ "${#normalized_domain}" -lt 5 ] || [ "${#normalized_domain}" -gt 253 ]; then
    return 1
  fi

  local IFS='.'
  read -r -a labels <<<"${normalized_domain}"
  if [ "${#labels[@]}" -ne 3 ] && [ "${#labels[@]}" -ne 4 ]; then
    return 1
  fi

  for label in "${labels[@]}"; do
    if [ -z "${label}" ]; then
      return 1
    fi

    if [ "${#label}" -gt 63 ]; then
      return 1
    fi

    case "${label}" in
    [A-Za-z0-9]*) ;;
    *)
      return 1
      ;;
    esac

    case "${label}" in
    *[A-Za-z0-9]) ;;
    *)
      return 1
      ;;
    esac

    case "${label}" in
    *[!A-Za-z0-9-]*)
      return 1
      ;;
    esac
  done

  last_index=$((${#labels[@]} - 1))
  tld="${labels[last_index]}"
  if ! [[ "${tld}" =~ ^[A-Za-z]{2,63}$ ]]; then
    return 1
  fi

  return 0
}

parse_domains_input_to_lines() {
  local result_var="${1}"
  local raw_value="${2}"
  local sanitized_value=""
  local token=""
  local normalized_token=""
  local parsed_domain_lines=""
  local -a tokens=()
  local IFS=$' \t\n'

  reset_domain_validation_feedback

  sanitized_value="${raw_value//$'\r'/ }"
  sanitized_value="${sanitized_value//$'\n'/ }"
  sanitized_value="${sanitized_value//$'\t'/ }"
  sanitized_value="${sanitized_value//,/ }"
  sanitized_value="${sanitized_value//;/ }"

  read -r -a tokens <<<"${sanitized_value}"
  if [ "${#tokens[@]}" -eq 0 ]; then
    EASY_DOCKER_LAST_INVALID_DOMAIN="${raw_value}"
    return 1
  fi

  for token in "${tokens[@]}"; do
    if ! normalize_domain_token normalized_token "${token}"; then
      EASY_DOCKER_LAST_INVALID_DOMAIN="${token}"
      return 1
    fi

    if ! is_valid_domain_name "${normalized_token}"; then
      EASY_DOCKER_LAST_INVALID_DOMAIN="${normalized_token}"
      return 1
    fi

    if [ -z "${parsed_domain_lines}" ]; then
      parsed_domain_lines="${normalized_token}"
    else
      parsed_domain_lines="${parsed_domain_lines}"$'\n'"${normalized_token}"
    fi
  done

  if [ -z "${parsed_domain_lines}" ]; then
    return 1
  fi

  printf -v "${result_var}" "%s" "${parsed_domain_lines}"
  return 0
}

domain_lines_to_csv() {
  local domain_lines="${1}"
  local domain=""
  local csv_value=""

  while IFS= read -r domain; do
    if [ -z "${domain}" ]; then
      continue
    fi

    if [ -z "${csv_value}" ]; then
      csv_value="${domain}"
    else
      csv_value="${csv_value},${domain}"
    fi
  done <<EOF
${domain_lines}
EOF

  printf '%s' "${csv_value}"
}

domain_lines_to_sites_rule() {
  local domain_lines="${1}"
  local domain=""
  local sites_rule=""
  local rule_part=""

  while IFS= read -r domain; do
    if [ -z "${domain}" ]; then
      continue
    fi

    rule_part="$(printf "Host(\`%s\`)" "${domain}")"
    if [ -z "${sites_rule}" ]; then
      sites_rule="${rule_part}"
    else
      sites_rule="${sites_rule} || ${rule_part}"
    fi
  done <<EOF
${domain_lines}
EOF

  printf '%s' "${sites_rule}"
}

is_valid_domain_list_value() {
  local value="${1}"
  local domain_lines=""

  if ! parse_domains_input_to_lines domain_lines "${value}"; then
    return 1
  fi

  if [ -z "${domain_lines}" ]; then
    return 1
  fi

  return 0
}

is_valid_domains_value() {
  local value="${1}"

  if ! is_valid_domain_list_value "${value}"; then
    return 1
  fi

  return 0
}

prompt_env_value_with_validation() {
  local result_var="${1}"
  local stack_dir="${2}"
  local variable_name="${3}"
  local guidance_text="${4}"
  local placeholder="${5}"
  local required_mode="${6}"
  local validation_kind="${7}"
  local input_value=""
  local normalized_value=""
  local invalid_domain_input=""
  local validation_feedback=""
  local prompt_status=0
  local is_first_prompt=1

  while true; do
    input_value="$(prompt_single_host_env_value "${stack_dir}" "${variable_name}" "${guidance_text}" "${placeholder}" "${is_first_prompt}" "${validation_feedback}")"
    prompt_status=$?
    is_first_prompt=0
    validation_feedback=""
    if [ "${prompt_status}" -ne 0 ]; then
      return 2
    fi

    normalized_value="$(printf '%s' "${input_value}" | tr -d '\r\n')"

    case "${normalized_value}" in
    /back | /BACK | /Back | /cancel | /CANCEL | /Cancel)
      return 2
      ;;
    esac

    if [ -z "${normalized_value}" ]; then
      if [ "${required_mode}" = "required" ]; then
        validation_feedback="Value required for ${variable_name}."
        continue
      fi

      printf -v "${result_var}" "%s" ""
      return 0
    fi

    case "${validation_kind}" in
    email)
      if ! is_valid_email_address "${normalized_value}"; then
        validation_feedback="Invalid email format for ${variable_name}."
        continue
      fi
      ;;
    port)
      if ! is_valid_port_number "${normalized_value}"; then
        validation_feedback="Invalid port for ${variable_name}. Use 1-65535."
        continue
      fi
      ;;
    domains)
      if ! is_valid_domains_value "${normalized_value}"; then
        invalid_domain_input="${EASY_DOCKER_LAST_INVALID_DOMAIN}"
        if [ -z "${invalid_domain_input}" ]; then
          invalid_domain_input="${normalized_value}"
        fi
        validation_feedback="Domain '${invalid_domain_input}' cannot be used for ${variable_name}. Use sub.domain.tld or sub.sub.domain.tld."
        continue
      fi
      ;;
    nginx_hosts)
      if ! is_valid_domains_value "${normalized_value}"; then
        validation_feedback="Invalid ${variable_name}. Use domains separated by comma or space."
        continue
      fi
      ;;
    none | "") ;;
    *)
      show_warning_message "Unknown validation rule: ${validation_kind}"
      return 1
      ;;
    esac

    printf -v "${result_var}" "%s" "${normalized_value}"
    return 0
  done
}
