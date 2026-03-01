#!/usr/bin/env bash

collect_single_host_env_lines() {
  local result_env_var="${1}"
  local result_apps_metadata_var="${2}"
  local stack_dir="${3}"
  local proxy_mode_id="${4}"
  local database_id="${5}"
  local collected_env_lines=""
  local value=""
  local domains_value=""
  local domain_lines=""
  local site_domains_value=""
  local custom_image_value=""
  local custom_tag_value=""
  local selected_apps_metadata_json_object=""
  local sites_rule_value=""
  local nginx_proxy_hosts_value=""
  local prompt_status=0

  if prompt_env_value_with_validation custom_image_value "${stack_dir}" "CUSTOM_IMAGE" "Required for custom modular image mode.\nExample: ghcr.io/acme/frappe-custom\nType /back to return." "ghcr.io/acme/frappe-custom" "required" "none"; then
    :
  else
    prompt_status=$?
    return "${prompt_status}"
  fi
  collected_env_lines="$(append_env_line "${collected_env_lines}" "CUSTOM_IMAGE" "${custom_image_value}")"

  if prompt_env_value_with_validation custom_tag_value "${stack_dir}" "CUSTOM_TAG" "Required for custom modular image mode.\nExample: v1.0.0\nType /back to return." "v1.0.0" "required" "none"; then
    :
  else
    prompt_status=$?
    return "${prompt_status}"
  fi
  collected_env_lines="$(append_env_line "${collected_env_lines}" "CUSTOM_TAG" "${custom_tag_value}")"

  if prompt_custom_modular_apps_data selected_apps_metadata_json_object "${stack_dir}"; then
    :
  else
    prompt_status=$?
    return "${prompt_status}"
  fi

  if [ -z "${selected_apps_metadata_json_object}" ]; then
    return 1
  fi

  case "${proxy_mode_id}" in
  traefik-https)
    if prompt_env_value_with_validation domains_value "${stack_dir}" "SITE_DOMAINS" "Required for Traefik HTTPS routing.\nUse only domains in format sub.domain.tld or sub.sub.domain.tld.\nEnter multiple domains separated by comma or space.\nType /back to return." "erp.example.com crm.eu.example.com" "required" "domains"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi

    if ! parse_domains_input_to_lines domain_lines "${domains_value}"; then
      show_warning_message "Could not parse SITE_DOMAINS."
      return 1
    fi

    site_domains_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_env_lines="$(append_env_line "${collected_env_lines}" "SITE_DOMAINS" "${site_domains_value}")"

    sites_rule_value="$(domain_lines_to_sites_rule "${domain_lines}")"
    collected_env_lines="$(append_env_line "${collected_env_lines}" "SITES_RULE" "${sites_rule_value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "LETSENCRYPT_EMAIL" "Required for Let's Encrypt certificate registration.\nType /back to return." "admin@example.com" "required" "email"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_env_lines="$(append_env_line "${collected_env_lines}" "LETSENCRYPT_EMAIL" "${value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi

    if prompt_env_value_with_validation value "${stack_dir}" "HTTPS_PUBLISH_PORT" "Optional. Press Enter to keep default 443.\nType /back to return." "443" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTPS_PUBLISH_PORT" "${value}")"
    fi
    ;;
  nginxproxy-https)
    if prompt_env_value_with_validation domains_value "${stack_dir}" "SITE_DOMAINS" "Required for nginx-proxy routing.\nUse only domains in format sub.domain.tld or sub.sub.domain.tld.\nEnter multiple domains separated by comma or space.\nType /back to return." "erp.example.com crm.eu.example.com" "required" "domains"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi

    if ! parse_domains_input_to_lines domain_lines "${domains_value}"; then
      show_warning_message "Could not parse SITE_DOMAINS."
      return 1
    fi

    site_domains_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_env_lines="$(append_env_line "${collected_env_lines}" "SITE_DOMAINS" "${site_domains_value}")"

    nginx_proxy_hosts_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_env_lines="$(append_env_line "${collected_env_lines}" "NGINX_PROXY_HOSTS" "${nginx_proxy_hosts_value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "LETSENCRYPT_EMAIL" "Required for Let's Encrypt certificate registration.\nType /back to return." "admin@example.com" "required" "email"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_env_lines="$(append_env_line "${collected_env_lines}" "LETSENCRYPT_EMAIL" "${value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi

    if prompt_env_value_with_validation value "${stack_dir}" "HTTPS_PUBLISH_PORT" "Optional. Press Enter to keep default 443.\nType /back to return." "443" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTPS_PUBLISH_PORT" "${value}")"
    fi
    ;;
  nginxproxy-http)
    if prompt_env_value_with_validation domains_value "${stack_dir}" "SITE_DOMAINS" "Required for nginx-proxy routing.\nUse only domains in format sub.domain.tld or sub.sub.domain.tld.\nEnter multiple domains separated by comma or space.\nType /back to return." "erp.example.com crm.eu.example.com" "required" "domains"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi

    if ! parse_domains_input_to_lines domain_lines "${domains_value}"; then
      show_warning_message "Could not parse SITE_DOMAINS."
      return 1
    fi

    site_domains_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_env_lines="$(append_env_line "${collected_env_lines}" "SITE_DOMAINS" "${site_domains_value}")"

    nginx_proxy_hosts_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_env_lines="$(append_env_line "${collected_env_lines}" "NGINX_PROXY_HOSTS" "${nginx_proxy_hosts_value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi
    ;;
  traefik-http)
    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi
    ;;
  caddy-external | no-proxy)
    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 8080 for no-proxy frontend publishing.\nType /back to return." "8080" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi
    ;;
  *)
    show_warning_and_wait "Unknown proxy mode id: ${proxy_mode_id}" 2
    return 1
    ;;
  esac

  case "${database_id}" in
  postgres)
    if prompt_env_value_with_validation value "${stack_dir}" "DB_PASSWORD" "Required for PostgreSQL database service.\nType /back to return." "changeit" "required" "none"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_env_lines="$(append_env_line "${collected_env_lines}" "DB_PASSWORD" "${value}")"
    ;;
  mariadb)
    if prompt_env_value_with_validation value "${stack_dir}" "DB_PASSWORD" "Optional but recommended for MariaDB.\nPress Enter to use default from override.\nType /back to return." "changeit" "optional" "none"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_env_lines="$(append_env_line "${collected_env_lines}" "DB_PASSWORD" "${value}")"
    fi
    ;;
  *)
    show_warning_and_wait "Unknown database id: ${database_id}" 2
    return 1
    ;;
  esac

  printf -v "${result_env_var}" "%s" "${collected_env_lines}"
  printf -v "${result_apps_metadata_var}" "%s" "${selected_apps_metadata_json_object}"
  return 0
}
