#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  local repo_root=""

  easy_docker_test_begin
  easy_docker_test_source_apps_modules
  easy_docker_test_install_jq_stub

  repo_root="$(easy_docker_test_repo_root)"
  # shellcheck source=scripts/easy-docker/lib/app/wizard/common/site/metadata.sh
  source "${repo_root}/scripts/easy-docker/lib/app/wizard/common/site/metadata.sh"
}

teardown() {
  easy_docker_test_end
}

@test "site metadata readers keep existing values independent of JSON layout" {
  local sandbox_root=""
  local stack_dir=""
  local expected_apps=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "site-metadata-read")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "site-metadata-read")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "site": {
    "name": "site-a.local",
    "last_error": "",
    "created_at": "2026-04-20T10:00:00Z",
    "last_backup_at": "2026-04-20T12:00:00Z",
    "apps_installed": [
      "erpnext",
      "crm",
      "my_custom_app"
    ]
  }
}
EOF
  expected_apps=$'erpnext\ncrm\nmy_custom_app'

  run get_stack_site_name "${stack_dir}"
  [ "${status}" -eq 0 ]
  [ "${output}" = "site-a.local" ]

  run get_stack_site_created_at "${stack_dir}"
  [ "${status}" -eq 0 ]
  [ "${output}" = "2026-04-20T10:00:00Z" ]

  run get_stack_site_last_backup_at "${stack_dir}"
  [ "${status}" -eq 0 ]
  [ "${output}" = "2026-04-20T12:00:00Z" ]

  run get_stack_site_apps_installed_lines "${stack_dir}"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected_apps}" ]
}

@test "persist_stack_site_metadata keeps the canonical site layout and preserves top-level metadata order" {
  local sandbox_root=""
  local stack_dir=""
  local expected_metadata=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "site-metadata-write")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "site-metadata-write")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "schema_version": 1,
  "stack_name": "site-metadata-write",
  "setup_type": "production",
  "frappe_branch": "version-16",
  "created_at": "2026-04-20T10:00:00Z",
  "wizard": {
    "topology": "single-host"
  }
}
EOF

  if ! persist_stack_site_metadata "${stack_dir}" "single-site" "site-a.local" $'erpnext\ncrm' "create-site" "" "" "2026-04-20T10:00:00Z" "2026-04-20T12:00:00Z" ""; then
    false
  fi

  expected_metadata="$(
    cat <<'EOF'
{
  "schema_version": 1,
  "stack_name": "site-metadata-write",
  "setup_type": "production",
  "frappe_branch": "version-16",
  "created_at": "2026-04-20T10:00:00Z",
  "wizard": {
    "topology": "single-host"
  },
  "site": {
      "mode": "single-site",
      "name": "site-a.local",
      "apps_installed": [
        "erpnext",
        "crm"
      ],
      "last_action": "create-site",
      "last_error": "",
      "error_log_path": "",
      "created_at": "2026-04-20T10:00:00Z",
      "updated_at": "2026-04-20T12:00:00Z",
      "last_backup_at": ""
    }
}
EOF
  )"

  run cat "${stack_dir}/metadata.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected_metadata}" ]
}
