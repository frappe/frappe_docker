#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_apps_modules
  easy_docker_test_install_jq_stub
}

teardown() {
  easy_docker_test_end
}

write_predefined_apps_catalog() {
  local sandbox_root="${1}"

  mkdir -p "${sandbox_root}/scripts/easy-docker/config"
  cat >"${sandbox_root}/scripts/easy-docker/config/apps.tsv" <<'EOF'
erpnext	ERPNext	https://github.com/frappe/erpnext	version-16	version-16,version-15
crm	CRM	https://github.com/frappe/crm	main	main,develop
EOF
}

write_containerfile_fixture() {
  local sandbox_root="${1}"

  mkdir -p "${sandbox_root}/images/layered"
  cat >"${sandbox_root}/images/layered/Containerfile" <<'EOF'
FROM scratch
EOF
}

write_stack_metadata_fixture() {
  local stack_dir="${1}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "schema_version": 1,
  "stack_name": "my-production-stack",
  "setup_type": "production",
  "frappe_branch": "version-16",
  "created_at": "2026-04-08T16:12:09Z",
  "apps": {
      "predefined": [
        "erpnext",
        "crm"
      ],
      "predefined_branches": {
        "erpnext": "version-16",
        "crm": "main"
      },
      "custom": [
        {
          "repo": "https://github.com/example/custom-app",
          "branch": "stable"
        }
      ]
    },
  "wizard": {
    "topology": "single-host",
    "selection": {
      "proxy_mode_id": "traefik-http"
    },
    "env": {
      "CUSTOM_IMAGE": "production_image",
      "CUSTOM_TAG": "v1.0.0"
    },
    "compose_files": [
      "compose.yaml",
      "overrides/compose.proxy.yaml"
    ],
    "updated_at": "2026-04-08T16:19:02Z"
  }
}
EOF
}

@test "metadata app readers use jq and keep expected line formats" {
  local sandbox_root=""
  local stack_dir=""
  local expected_custom=""
  local expected_branches=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "apps-reader")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "apps-reader")"
  mkdir -p "${stack_dir}"
  write_stack_metadata_fixture "${stack_dir}"

  expected_custom='https://github.com/example/custom-app|stable'
  expected_branches=$'erpnext|version-16\ncrm|main'

  run get_metadata_apps_predefined_csv "${stack_dir}/metadata.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "erpnext,crm" ]

  run get_metadata_apps_custom_lines "${stack_dir}/metadata.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected_custom}" ]

  run get_metadata_apps_predefined_branch_lines "${stack_dir}/metadata.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected_branches}" ]
}

@test "persist_stack_metadata_apps_object keeps apps before wizard with legacy formatting" {
  local sandbox_root=""
  local stack_dir=""
  local metadata_path=""
  local apps_json_object=""
  local expected=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "apps-persist")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "apps-persist")"
  mkdir -p "${stack_dir}"
  metadata_path="${stack_dir}/metadata.json"

  cat >"${metadata_path}" <<'EOF'
{
  "schema_version": 1,
  "stack_name": "my-production-stack",
  "wizard": {
    "topology": "single-host"
  }
}
EOF

  build_metadata_apps_json_object apps_json_object "erpnext,crm" $'erpnext|version-16\ncrm|main' ""

  run persist_stack_metadata_apps_object "${stack_dir}" "${apps_json_object}"
  [ "${status}" -eq 0 ]

  expected=$'{\n  "schema_version": 1,\n  "stack_name": "my-production-stack",\n  "apps": {\n      "predefined": [\n        "erpnext",\n        "crm"\n      ],\n      "predefined_branches": {\n        "erpnext": "version-16",\n        "crm": "main"\n      },\n      "custom": [\n\n      ]\n    },\n  "wizard": {\n    "topology": "single-host"\n  }\n}\n'

  run cat "${metadata_path}"
  [ "${status}" -eq 0 ]
  [ "${output}"$'\n' = "${expected}" ]
}

@test "persist_stack_metadata_wizard_object preserves existing apps formatting" {
  local sandbox_root=""
  local stack_dir=""
  local metadata_path=""
  local wizard_json_object=""
  local expected=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "wizard-persist")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "wizard-persist")"
  mkdir -p "${stack_dir}"
  metadata_path="${stack_dir}/metadata.json"
  write_stack_metadata_fixture "${stack_dir}"

  wizard_json_object=$'{\n    "topology": "single-host",\n    "selection": {\n      "proxy_mode_id": "traefik-https"\n    },\n    "env": {\n      "CUSTOM_IMAGE": "production_image",\n      "CUSTOM_TAG": "v2.0.0"\n    }\n  }'

  run persist_stack_metadata_wizard_object "${stack_dir}" "${wizard_json_object}"
  [ "${status}" -eq 0 ]

  expected=$'{\n  "schema_version": 1,\n  "stack_name": "my-production-stack",\n  "setup_type": "production",\n  "frappe_branch": "version-16",\n  "created_at": "2026-04-08T16:12:09Z",\n  "apps": {\n      "predefined": [\n        "erpnext",\n        "crm"\n      ],\n      "predefined_branches": {\n        "erpnext": "version-16",\n        "crm": "main"\n      },\n      "custom": [\n        {\n          "repo": "https://github.com/example/custom-app",\n          "branch": "stable"\n        }\n      ]\n    },\n  "wizard": {\n    "topology": "single-host",\n    "selection": {\n      "proxy_mode_id": "traefik-https"\n    },\n    "env": {\n      "CUSTOM_IMAGE": "production_image",\n      "CUSTOM_TAG": "v2.0.0"\n    }\n  }\n}\n'

  run cat "${metadata_path}"
  [ "${status}" -eq 0 ]
  [ "${output}"$'\n' = "${expected}" ]
}

@test "build_stack_apps_json_content_from_metadata_apps keeps apps.json output format" {
  local sandbox_root=""
  local stack_dir=""
  local apps_json_content=""
  local expected=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "apps-json")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  write_predefined_apps_catalog "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "apps-json")"
  mkdir -p "${stack_dir}"
  write_stack_metadata_fixture "${stack_dir}"

  if ! build_stack_apps_json_content_from_metadata_apps apps_json_content "${stack_dir}"; then
    false
  fi

  expected=$'[\n  {"url": "https://github.com/frappe/erpnext", "branch": "version-16"},\n  {"url": "https://github.com/frappe/crm", "branch": "main"},\n  {"url": "https://github.com/example/custom-app", "branch": "stable"}\n]\n'

  [ "${apps_json_content}" = "${expected}" ]
}

@test "build_stack_custom_image fails clearly when jq is unavailable" {
  local sandbox_root=""
  local stack_dir=""
  local env_path=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "build-no-jq")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  write_predefined_apps_catalog "${sandbox_root}"
  write_containerfile_fixture "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "build-no-jq")"
  mkdir -p "${stack_dir}"
  write_stack_metadata_fixture "${stack_dir}"
  env_path="${stack_dir}/build-no-jq.env"

  cat >"${env_path}" <<'EOF'
CUSTOM_IMAGE=production_image
CUSTOM_TAG=v1.0.0
EOF

  get_easy_docker_jq_command() {
    return 1
  }

  run build_stack_custom_image "${stack_dir}"
  [ "${status}" -eq 25 ]
}

@test "build_stack_custom_image parses apps.json with jq before git branch checks" {
  local sandbox_root=""
  local stack_dir=""
  local env_path=""
  local git_log=""
  local docker_log=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "build-with-jq")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  write_predefined_apps_catalog "${sandbox_root}"
  write_containerfile_fixture "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "build-with-jq")"
  mkdir -p "${stack_dir}"
  write_stack_metadata_fixture "${stack_dir}"
  env_path="${stack_dir}/my-production-stack.env"

  cat >"${env_path}" <<'EOF'
CUSTOM_IMAGE=production_image
CUSTOM_TAG=v1.0.0
EOF

  git_log="${EASY_DOCKER_TEST_TMPDIR}/git.log"
  docker_log="${EASY_DOCKER_TEST_TMPDIR}/docker.log"

  # shellcheck disable=SC2016
  easy_docker_test_write_bin_command git \
    'set -euo pipefail' \
    "printf '%s\n' \"git \$*\" >>\"${git_log}\"" \
    'if [ "${1:-}" = "ls-remote" ]; then' \
    '  exit 0' \
    'fi' \
    'exit 64'

  easy_docker_test_write_bin_command docker \
    'set -euo pipefail' \
    "printf '%s\n' \"docker \$*\" >>\"${docker_log}\"" \
    'exit 0'

  easy_docker_test_write_bin_command base64 \
    'set -euo pipefail' \
    'printf "%s\n" "W3sidXJsIjogImh0dHBzOi8vZXhhbXBsZS5pbnZhbGlkL2FwcCIsICJicmFuY2giOiAidmVyc2lvbi0xNiJ9XQ=="'

  easy_docker_test_prepend_bin_dir

  run build_stack_custom_image "${stack_dir}"
  [ "${status}" -eq 0 ]

  run cat "${git_log}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'git ls-remote --exit-code --heads https://github.com/frappe/erpnext version-16'* ]]
  [[ "${output}" == *'git ls-remote --exit-code --heads https://github.com/frappe/crm main'* ]]
  [[ "${output}" == *'git ls-remote --exit-code --heads https://github.com/example/custom-app stable'* ]]

  run cat "${docker_log}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *'docker build -f '* ]]
}
