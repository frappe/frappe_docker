#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_core_render_modules
  easy_docker_test_install_jq_stub
  unset ERPNEXT_VERSION
  unset FRAPPE_BRANCH
}

teardown() {
  easy_docker_test_end
}

@test "is_valid_stack_name accepts safe names" {
  local name=""

  for name in alpha alpha-1 alpha_1 alpha.1; do
    run is_valid_stack_name "${name}"
    [ "${status}" -eq 0 ]
  done
}

@test "is_valid_stack_name rejects empty and unsafe names" {
  local name=""

  for name in "" "bad name" "bad/name" "bad:name" "bad*name"; do
    run is_valid_stack_name "${name}"
    [ "${status}" -eq 1 ]
  done
}

@test "get_env_file_key_value parses exported and quoted values" {
  local sandbox_root=""
  local stack_dir=""
  local env_file=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "env-parse")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "env-parse")"
  mkdir -p "${stack_dir}"
  env_file="${stack_dir}/stack.env"

  cat >"${env_file}" <<'EOF'
# comment
export ERPNEXT_VERSION=15.9.0-test
STACK_NAME="My Stack"
IGNORED=value
EOF

  run get_env_file_key_value "${env_file}" ERPNEXT_VERSION
  [ "${status}" -eq 0 ]
  [ "${output}" = "15.9.0-test" ]

  run get_env_file_key_value "${env_file}" STACK_NAME
  [ "${status}" -eq 0 ]
  [ "${output}" = "My Stack" ]
}

@test "get_stack_compose_project_name normalizes metadata stack names" {
  local sandbox_root=""
  local stack_dir=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "project-name")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "project-name")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "My Stack! 01"
}
EOF

  run get_stack_compose_project_name "${stack_dir}"
  [ "${status}" -eq 0 ]
  [ "${output}" = "easydocker-my-stack-01" ]
}

@test "get_metadata_compose_files_lines returns compose file entries" {
  local sandbox_root=""
  local stack_dir=""
  local expected=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "compose-lines")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "compose-lines")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "compose-lines",
  "compose_files": [
    "compose.yaml",
    "overrides/compose.proxy.yaml",
    "overrides/compose.redis.yaml"
  ]
}
EOF

  expected=$'compose.yaml\noverrides/compose.proxy.yaml\noverrides/compose.redis.yaml'

  run get_metadata_compose_files_lines "${stack_dir}/metadata.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected}" ]
}

@test "get_metadata_compose_files_lines keeps the first compose_files array only" {
  local sandbox_root=""
  local stack_dir=""
  local expected=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "compose-lines-first-array")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "compose-lines-first-array")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "compose-lines-first-array",
  "compose_files": [
    "compose.yaml",
    "overrides/compose.proxy.yaml"
  ],
  "wizard": {
    "compose_files": [
      "should-not-appear.yaml"
    ]
  }
}
EOF

  expected=$'compose.yaml\noverrides/compose.proxy.yaml'

  run get_metadata_compose_files_lines "${stack_dir}/metadata.json"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${expected}" ]
}

@test "render_stack_compose_from_metadata writes generated compose with stubbed docker config" {
  local sandbox_root=""
  local stack_dir=""
  local env_path=""
  local generated_compose_path=""
  local invocation_log=""

  easy_docker_test_install_docker_stub

  sandbox_root="$(easy_docker_test_create_repo_sandbox "render-smoke")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "render-smoke")"
  mkdir -p "${stack_dir}"

  cat >"${sandbox_root}/compose.yaml" <<'EOF'
services:
  backend:
    image: frappe/backend
EOF

  cat >"${sandbox_root}/overrides/compose.proxy.yaml" <<'EOF'
services:
  frontend:
    image: frappe/frontend
EOF

  cat >"${sandbox_root}/overrides/compose.redis.yaml" <<'EOF'
services:
  redis-cache:
    image: redis:7
EOF

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "My Stack! 01",
  "compose_files": [
    "compose.yaml",
    "overrides/compose.proxy.yaml",
    "overrides/compose.redis.yaml"
  ]
}
EOF

  env_path="${stack_dir}/My Stack! 01.env"
  cat >"${env_path}" <<'EOF'
DB_HOST=localhost
EOF

  generated_compose_path="${stack_dir}/compose.generated.yaml"
  invocation_log="${EASY_DOCKER_TEST_TMPDIR}/docker.invocations"

  export ERPNEXT_VERSION="15.9.0-test"

  run render_stack_compose_from_metadata "${stack_dir}"
  [ "${status}" -eq 0 ]
  [ -f "${generated_compose_path}" ]
  [ ! -f "${generated_compose_path}.tmp" ]

  run cat "${generated_compose_path}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"invocation=docker compose --project-name easydocker-my-stack-01 --env-file ${env_path}"* ]]
  [[ "${output}" == *"-f ${sandbox_root}/compose.yaml"* ]]
  [[ "${output}" == *"-f ${sandbox_root}/overrides/compose.proxy.yaml"* ]]
  [[ "${output}" == *"-f ${sandbox_root}/overrides/compose.redis.yaml"* ]]
  [[ "${output}" == *"erpnext=15.9.0-test"* ]]

  run cat "${invocation_log}"
  [ "${status}" -eq 0 ]
  [[ "${output}" == *"docker compose --project-name easydocker-my-stack-01 --env-file ${env_path} -f "* ]]
  [[ "${output}" == *"config"* ]]
}
