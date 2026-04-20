#!/usr/bin/env bash

refresh_stack_generated_compose_with_feedback() {
  local stack_dir="${1}"
  local generated_compose_path=""
  local render_compose_status=0

  generated_compose_path="$(get_stack_generated_compose_path "${stack_dir}")"
  if render_stack_compose_from_metadata "${stack_dir}"; then
    show_warning_and_wait "Generated compose refreshed successfully: ${generated_compose_path}" 3
    return 0
  fi

  render_compose_status=$?
  show_warning_and_wait "The image build succeeded, but generated compose could not be refreshed (${render_compose_status}) for ${generated_compose_path}." 4
  return "${render_compose_status}"
}

run_build_stack_custom_image_with_feedback() {
  local stack_name="${1}"
  local stack_dir="${2}"
  local build_image_status=0

  show_warning_message "Starting docker build for stack: ${stack_name}"
  if build_stack_custom_image "${stack_dir}"; then
    show_warning_and_wait "Custom image build finished successfully for stack: ${stack_name}" 3
    refresh_stack_generated_compose_with_feedback "${stack_dir}" || true
    return 0
  else
    build_image_status=$?
  fi
  case "${build_image_status}" in
  11)
    show_warning_and_wait "Custom image build failed: missing metadata.json in ${stack_dir}." 4
    ;;
  12)
    show_warning_and_wait "Custom image build failed: stack env file not found in ${stack_dir}." 4
    ;;
  13)
    show_warning_and_wait "Custom image build failed: CUSTOM_IMAGE is missing in stack env file." 4
    ;;
  14)
    show_warning_and_wait "Custom image build failed: CUSTOM_TAG is missing in stack env file." 4
    ;;
  15)
    show_warning_and_wait "Custom image build failed: frappe_branch missing in metadata.json." 4
    ;;
  16)
    show_warning_and_wait "Custom image build failed: could not generate apps.json from metadata app selection." 4
    ;;
  17)
    show_warning_and_wait "Custom image build failed: apps.json not found after generation." 4
    ;;
  18)
    show_warning_and_wait "Custom image build failed: base64 command is not available in this environment." 4
    ;;
  19)
    show_warning_and_wait "Custom image build failed: apps.json could not be base64-encoded." 4
    ;;
  20)
    show_warning_and_wait "Custom image build failed: images/layered/Containerfile not found." 4
    ;;
  21)
    show_warning_and_wait "Custom image build failed: docker build returned an error. Check the output above." 4
    ;;
  22)
    show_warning_and_wait "Custom image build failed: git is required for app branch precheck (git ls-remote)." 4
    ;;
  23)
    show_warning_and_wait "Custom image build failed: could not parse app entries from apps.json." 4
    ;;
  24)
    show_warning_and_wait "Custom image build failed: app branch precheck failed -> ${EASY_DOCKER_BUILD_ERROR_DETAIL}" 6
    ;;
  25)
    show_warning_and_wait "Custom image build failed: jq is required for stack metadata and apps.json processing." 4
    ;;
  *)
    show_warning_and_wait "Custom image build failed (${build_image_status})." 4
    ;;
  esac

  return "${build_image_status}"
}
