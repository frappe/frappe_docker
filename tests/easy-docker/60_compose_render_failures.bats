#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_core_render_modules
}

teardown() {
  easy_docker_test_end
}

write_docker_stub() {
  local body="${1}"

  easy_docker_test_write_bin_command docker \
    'set -euo pipefail' \
    "${body}"
  easy_docker_test_prepend_bin_dir
}

@test "render_stack_compose_from_metadata fails when metadata.json is missing" {
  local sandbox_root=""
  local stack_dir=""
  local generated_compose_path=""
  local docker_log=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "render-missing-metadata")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "render-missing-metadata")"
  mkdir -p "${stack_dir}"

  # shellcheck disable=SC2016
  write_docker_stub 'echo "docker should not have been called" >&2; exit 99'

  generated_compose_path="${stack_dir}/compose.generated.yaml"
  docker_log="${EASY_DOCKER_TEST_TMPDIR}/docker.log"

  run render_stack_compose_from_metadata "${stack_dir}"
  [ "${status}" -eq 1 ]
  [ ! -f "${generated_compose_path}" ]
  [ ! -f "${generated_compose_path}.tmp" ]
  [ ! -f "${docker_log}" ]
}

@test "render_stack_compose_from_metadata fails when the env file is missing" {
  local sandbox_root=""
  local stack_dir=""
  local generated_compose_path=""
  local docker_log=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "render-missing-env")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "render-missing-env")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "render-missing-env",
  "compose_files": [
    "compose.yaml"
  ]
}
EOF

  # shellcheck disable=SC2016
  write_docker_stub 'echo "docker should not have been called" >&2; exit 99'

  generated_compose_path="${stack_dir}/compose.generated.yaml"
  docker_log="${EASY_DOCKER_TEST_TMPDIR}/docker.log"

  run render_stack_compose_from_metadata "${stack_dir}"
  [ "${status}" -eq 1 ]
  [ ! -f "${generated_compose_path}" ]
  [ ! -f "${generated_compose_path}.tmp" ]
  [ ! -f "${docker_log}" ]
}

@test "render_stack_compose_from_metadata fails when compose_files are missing" {
  local sandbox_root=""
  local stack_dir=""
  local generated_compose_path=""
  local docker_log=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "render-missing-compose-files")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "render-missing-compose-files")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "render-missing-compose-files"
}
EOF

  cat >"${stack_dir}/render-missing-compose-files.env" <<'EOF'
ERPNEXT_VERSION=15.9.0-test
EOF

  # shellcheck disable=SC2016
  write_docker_stub 'echo "docker should not have been called" >&2; exit 99'

  generated_compose_path="${stack_dir}/compose.generated.yaml"
  docker_log="${EASY_DOCKER_TEST_TMPDIR}/docker.log"

  run render_stack_compose_from_metadata "${stack_dir}"
  [ "${status}" -eq 1 ]
  [ ! -f "${generated_compose_path}" ]
  [ ! -f "${generated_compose_path}.tmp" ]
  [ ! -f "${docker_log}" ]
}

@test "render_stack_compose_from_metadata fails when a referenced compose file is missing" {
  local sandbox_root=""
  local stack_dir=""
  local generated_compose_path=""
  local docker_log=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "render-missing-source")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "render-missing-source")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "render-missing-source",
  "compose_files": [
    "compose.yaml",
    "overrides/compose.proxy.yaml"
  ]
}
EOF

  cat >"${stack_dir}/render-missing-source.env" <<'EOF'
ERPNEXT_VERSION=15.9.0-test
EOF

  cat >"${sandbox_root}/compose.yaml" <<'EOF'
services:
  backend:
    image: frappe/backend
EOF

  # shellcheck disable=SC2016
  write_docker_stub 'echo "docker should not have been called" >&2; exit 99'

  generated_compose_path="${stack_dir}/compose.generated.yaml"
  docker_log="${EASY_DOCKER_TEST_TMPDIR}/docker.log"

  run render_stack_compose_from_metadata "${stack_dir}"
  [ "${status}" -eq 1 ]
  [ ! -f "${generated_compose_path}" ]
  [ ! -f "${generated_compose_path}.tmp" ]
  [ ! -f "${docker_log}" ]
}

@test "render_stack_compose_from_metadata removes its temporary file after a docker config failure" {
  local sandbox_root=""
  local stack_dir=""
  local generated_compose_path=""
  local docker_log=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "render-docker-failure")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "render-docker-failure")"
  mkdir -p "${stack_dir}"

  cat >"${stack_dir}/metadata.json" <<'EOF'
{
  "stack_name": "render-docker-failure",
  "compose_files": [
    "compose.yaml",
    "overrides/compose.proxy.yaml"
  ]
}
EOF

  cat >"${stack_dir}/render-docker-failure.env" <<'EOF'
ERPNEXT_VERSION=15.9.0-test
EOF

  cat >"${sandbox_root}/compose.yaml" <<'EOF'
services:
  backend:
    image: frappe/backend
EOF
  mkdir -p "${sandbox_root}/overrides"
  cat >"${sandbox_root}/overrides/compose.proxy.yaml" <<'EOF'
services:
  frontend:
    image: frappe/frontend
EOF

  # shellcheck disable=SC2016
  write_docker_stub 'printf "%s\n" "docker $*" >>"${EASY_DOCKER_TEST_TMPDIR}/docker.log"; if [ "${*: -1}" = "config" ]; then echo "simulated docker compose config failure" >&2; exit 23; fi; exit 0'

  generated_compose_path="${stack_dir}/compose.generated.yaml"
  docker_log="${EASY_DOCKER_TEST_TMPDIR}/docker.log"

  run render_stack_compose_from_metadata "${stack_dir}"
  [ "${status}" -eq 1 ]
  [ ! -f "${generated_compose_path}" ]
  [ ! -f "${generated_compose_path}.tmp" ]
  [ -f "${docker_log}" ]
  [ "$(cat "${docker_log}")" != "" ]
}
