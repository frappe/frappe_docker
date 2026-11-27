#!/usr/bin/env bash

collect_split_services_env_lines() {
  local result_env_var="${1}"
  local result_apps_metadata_var="${2}"
  local stack_dir="${3}"
  local proxy_mode_id="${4}"
  local data_mode_id="${5}"
  local database_id="${6}"
  local redis_id="${7}"
  local collected_split_services_env_lines=""
  local collected_split_services_apps_metadata_json_object=""
  local value=""
  local domains_value=""
  local domain_lines=""
  local site_domains_value=""
  local sites_rule_value=""
  local nginx_proxy_hosts_value=""
  local db_port=""
  local prompt_status=0

  if collect_stack_image_and_apps_env_lines collected_split_services_env_lines collected_split_services_apps_metadata_json_object "${stack_dir}"; then
    :
  else
    prompt_status=$?
    return "${prompt_status}"
  fi

  case "${proxy_mode_id}" in
  traefik-https)
    if prompt_env_value_with_validation domains_value "${stack_dir}" "SITE_DOMAINS" "Required for Traefik HTTPS routing.\nUse hostnames like example.com, app.example.com, localhost, or dev.localhost.\nEnter multiple domains separated by comma or space.\nLet's Encrypt still requires a public DNS name.\nType /back to return." "erp.example.com dev.localhost" "required" "domains"; then
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
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "SITE_DOMAINS" "${site_domains_value}")"

    sites_rule_value="$(domain_lines_to_sites_rule "${domain_lines}")"
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "SITES_RULE" "${sites_rule_value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "LETSENCRYPT_EMAIL" "Required for Let's Encrypt certificate registration.\nType /back to return." "admin@example.com" "required" "email"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "LETSENCRYPT_EMAIL" "${value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi

    if prompt_env_value_with_validation value "${stack_dir}" "HTTPS_PUBLISH_PORT" "Optional. Press Enter to keep default 443.\nType /back to return." "443" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTPS_PUBLISH_PORT" "${value}")"
    fi
    ;;
  nginxproxy-https)
    if prompt_env_value_with_validation domains_value "${stack_dir}" "SITE_DOMAINS" "Required for nginx-proxy routing.\nUse hostnames like example.com, app.example.com, localhost, or dev.localhost.\nEnter multiple domains separated by comma or space.\nLet's Encrypt still requires a public DNS name.\nType /back to return." "erp.example.com dev.localhost" "required" "domains"; then
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
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "SITE_DOMAINS" "${site_domains_value}")"

    nginx_proxy_hosts_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "NGINX_PROXY_HOSTS" "${nginx_proxy_hosts_value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "LETSENCRYPT_EMAIL" "Required for Let's Encrypt certificate registration.\nType /back to return." "admin@example.com" "required" "email"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "LETSENCRYPT_EMAIL" "${value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi

    if prompt_env_value_with_validation value "${stack_dir}" "HTTPS_PUBLISH_PORT" "Optional. Press Enter to keep default 443.\nType /back to return." "443" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTPS_PUBLISH_PORT" "${value}")"
    fi
    ;;
  nginxproxy-http)
    if prompt_env_value_with_validation domains_value "${stack_dir}" "SITE_DOMAINS" "Required for nginx-proxy routing.\nUse hostnames like example.com, app.example.com, localhost, or dev.localhost.\nEnter multiple domains separated by comma or space.\nType /back to return." "erp.example.com dev.localhost" "required" "domains"; then
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
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "SITE_DOMAINS" "${site_domains_value}")"

    nginx_proxy_hosts_value="$(domain_lines_to_csv "${domain_lines}")"
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "NGINX_PROXY_HOSTS" "${nginx_proxy_hosts_value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "HTTP_PUBLISH_PORT" "Optional. Press Enter to keep default 80.\nType /back to return." "80" "optional" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    if [ -n "${value}" ]; then
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
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
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
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
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "HTTP_PUBLISH_PORT" "${value}")"
    fi
    ;;
  *)
    show_warning_and_wait "Unknown proxy mode id: ${proxy_mode_id}" 2
    return 1
    ;;
  esac

  case "${data_mode_id}" in
  managed)
    case "${database_id}" in
    postgres)
      if prompt_env_value_with_validation value "${stack_dir}" "DB_PASSWORD" "Required for PostgreSQL database service.\nType /back to return." "changeit" "required" "none"; then
        :
      else
        prompt_status=$?
        return "${prompt_status}"
      fi
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "DB_PASSWORD" "${value}")"
      ;;
    mariadb)
      if prompt_env_value_with_validation value "${stack_dir}" "DB_PASSWORD" "Optional but recommended for MariaDB.\nPress Enter to use default from override.\nType /back to return." "changeit" "optional" "none"; then
        :
      else
        prompt_status=$?
        return "${prompt_status}"
      fi
      if [ -n "${value}" ]; then
        collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "DB_PASSWORD" "${value}")"
      fi
      ;;
    *)
      show_warning_and_wait "Unknown database id: ${database_id}" 2
      return 1
      ;;
    esac

    case "${redis_id}" in
    managed)
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_CACHE" "redis-cache:6379")"
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_QUEUE" "redis-queue:6379")"
      ;;
    external)
      if prompt_env_value_with_validation value "${stack_dir}" "REDIS_CACHE" "Required for external Redis cache.\nUse host:port such as redis.example.internal:6379.\nType /back to return." "redis.example.internal:6379" "required" "hostport"; then
        :
      else
        prompt_status=$?
        return "${prompt_status}"
      fi
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_CACHE" "${value}")"

      if prompt_env_value_with_validation value "${stack_dir}" "REDIS_QUEUE" "Required for external Redis queue.\nUse host:port such as redis.example.internal:6379.\nType /back to return." "redis.example.internal:6379" "required" "hostport"; then
        :
      else
        prompt_status=$?
        return "${prompt_status}"
      fi
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_QUEUE" "${value}")"
      ;;
    disabled | "")
      :
      ;;
    *)
      show_warning_and_wait "Unknown Redis id: ${redis_id}" 2
      return 1
      ;;
    esac
    ;;
  external)
    case "${database_id}" in
    postgres)
      db_port="5432"
      ;;
    mariadb)
      db_port="3306"
      ;;
    *)
      show_warning_and_wait "Unknown database id: ${database_id}" 2
      return 1
      ;;
    esac

    if prompt_env_value_with_validation value "${stack_dir}" "DB_HOST" "Required for external database.\nUse a hostname or IP address.\nType /back to return." "db.example.internal" "required" "host"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "DB_HOST" "${value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "DB_PORT" "Required for external database.\nPress Enter to keep the default port.\nType /back to return." "${db_port}" "required" "port"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "DB_PORT" "${value}")"

    if prompt_env_value_with_validation value "${stack_dir}" "DB_PASSWORD" "Required for external database access.\nType /back to return." "changeit" "required" "none"; then
      :
    else
      prompt_status=$?
      return "${prompt_status}"
    fi
    collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "DB_PASSWORD" "${value}")"

    case "${redis_id}" in
    managed)
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_CACHE" "redis-cache:6379")"
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_QUEUE" "redis-queue:6379")"
      ;;
    external)
      if prompt_env_value_with_validation value "${stack_dir}" "REDIS_CACHE" "Required for external Redis cache.\nUse host:port such as redis.example.internal:6379.\nType /back to return." "redis.example.internal:6379" "required" "hostport"; then
        :
      else
        prompt_status=$?
        return "${prompt_status}"
      fi
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_CACHE" "${value}")"

      if prompt_env_value_with_validation value "${stack_dir}" "REDIS_QUEUE" "Required for external Redis queue.\nUse host:port such as redis.example.internal:6379.\nType /back to return." "redis.example.internal:6379" "required" "hostport"; then
        :
      else
        prompt_status=$?
        return "${prompt_status}"
      fi
      collected_split_services_env_lines="$(append_env_line "${collected_split_services_env_lines}" "REDIS_QUEUE" "${value}")"
      ;;
    disabled | "")
      :
      ;;
    *)
      show_warning_and_wait "Unknown Redis id: ${redis_id}" 2
      return 1
      ;;
    esac
    ;;
  *)
    show_warning_and_wait "Unknown data mode id: ${data_mode_id}" 2
    return 1
    ;;
  esac

  printf -v "${result_env_var}" "%s" "${collected_split_services_env_lines}"
  printf -v "${result_apps_metadata_var}" "%s" "${collected_split_services_apps_metadata_json_object}"
  return 0
}
