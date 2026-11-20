#!/usr/bin/env bats

load 'test_helper.bash'

setup() {
  easy_docker_test_begin
  easy_docker_test_source_core_render_modules
  easy_docker_test_install_jq_stub
}

teardown() {
  easy_docker_test_end
}

@test "create_stack_directory_with_metadata writes metadata and returns the stack directory" {
  local sandbox_root=""
  local stack_dir=""
  local result_stack_dir=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "create-metadata")"
  easy_docker_test_override_repo_root "${sandbox_root}"

  if ! create_stack_directory_with_metadata result_stack_dir "demo-stack" "production" "version-15"; then
    false
  fi

  stack_dir="$(easy_docker_test_stack_dir "demo-stack")"
  [ "${result_stack_dir}" = "${stack_dir}" ]
  [ -d "${result_stack_dir}" ]
  [ "$(get_metadata_string_field "${result_stack_dir}/metadata.json" "stack_name")" = "demo-stack" ]
  [ "$(get_metadata_string_field "${result_stack_dir}/metadata.json" "setup_type")" = "production" ]
  [ "$(get_metadata_string_field "${result_stack_dir}/metadata.json" "frappe_branch")" = "version-15" ]
  [ -n "$(get_metadata_string_field "${result_stack_dir}/metadata.json" "created_at")" ]
}

@test "create_stack_directory_with_metadata rejects duplicate stack directories" {
  local sandbox_root=""
  local result_stack_dir=""
  local metadata_path=""
  local status_code=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "duplicate-stack")"
  easy_docker_test_override_repo_root "${sandbox_root}"

  if ! create_stack_directory_with_metadata result_stack_dir "duplicate-stack" "production" "version-15"; then
    false
  fi

  metadata_path="${result_stack_dir}/metadata.json"
  printf '%s\n' "original" >"${metadata_path}"

  result_stack_dir=""
  if create_stack_directory_with_metadata result_stack_dir "duplicate-stack" "production" "version-15"; then
    status_code=0
  else
    status_code=$?
  fi
  [ "${status_code}" -eq 2 ]
  [ "${result_stack_dir}" = "" ]
  [ "$(cat "${metadata_path}")" = "original" ]
}

@test "create_stack_directory_with_metadata does not leave a partial stack behind when frappe_branch is missing" {
  local sandbox_root=""
  local stack_dir=""
  local result_stack_dir=""
  local status_code=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "missing-frappe-branch")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "missing-frappe-branch")"

  if create_stack_directory_with_metadata result_stack_dir "missing-frappe-branch" "production" ""; then
    status_code=0
  else
    status_code=$?
  fi

  [ "${status_code}" -eq 1 ]
  [ "${result_stack_dir}" = "" ]
  [ ! -d "${stack_dir}" ]
}

@test "rollback_stack_directory removes managed stack directories" {
  local sandbox_root=""
  local stack_dir=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "rollback-stack")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stack_dir="$(easy_docker_test_stack_dir "rollback-stack")"
  mkdir -p "${stack_dir}/nested"
  printf '%s\n' "payload" >"${stack_dir}/nested/file.txt"

  if ! rollback_stack_directory "${stack_dir}"; then
    false
  fi
  [ ! -d "${stack_dir}" ]
}

@test "rollback_stack_directory rejects paths outside the managed stacks tree" {
  local sandbox_root=""
  local outside_dir=""
  local status_code=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "rollback-outside")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  outside_dir="$(mktemp -d)"

  if rollback_stack_directory "${outside_dir}"; then
    status_code=0
  else
    status_code=$?
  fi
  [ "${status_code}" -eq 2 ]
  [ -d "${outside_dir}" ]

  rm -rf "${outside_dir}"
}

@test "get_stack_dir_by_name returns the matching stack directory and ignores junk entries" {
  local sandbox_root=""
  local stacks_dir=""
  local matching_stack_dir=""
  local junk_dir=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "stack-lookup")"
  easy_docker_test_override_repo_root "${sandbox_root}"
  stacks_dir="${sandbox_root}/.easy-docker/stacks"

  junk_dir="${stacks_dir}/not-a-stack"
  matching_stack_dir="${stacks_dir}/target-stack"

  mkdir -p "${junk_dir}" "${matching_stack_dir}"
  printf '%s\n' '{ "stack_name": "target-stack" }' >"${matching_stack_dir}/metadata.json"

  run get_stack_dir_by_name "target-stack"
  [ "${status}" -eq 0 ]
  [ "${output}" = "${matching_stack_dir}" ]
}

@test "get_stack_dir_by_name fails when the stack is absent" {
  local sandbox_root=""

  sandbox_root="$(easy_docker_test_create_repo_sandbox "stack-missing")"
  easy_docker_test_override_repo_root "${sandbox_root}"

  run get_stack_dir_by_name "missing-stack"
  [ "${status}" -eq 1 ]
  [ -z "${output}" ]
}
