#!/usr/bin/env bash

persist_stack_metadata_top_level_object() {
  local stack_dir="${1}"
  local object_key="${2}"
  local object_json="${3}"
  local insert_before_key="${4:-}"
  local metadata_path=""
  local metadata_tmp_path=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ -z "${object_json}" ]; then
    return 1
  fi

  if ! awk -v object_key="${object_key}" -v object_json="${object_json}" -v insert_before_key="${insert_before_key}" '
    BEGIN {
      target_regex = "^  \"" object_key "\"[[:space:]]*:"
      before_regex = ""
      if (insert_before_key != "") {
        before_regex = "^  \"" insert_before_key "\"[[:space:]]*:"
      }
      in_target = 0
      target_depth = 0
      inserted = 0
      prev = ""
    }
    function flush_prev() {
      if (prev != "") {
        print prev
        prev = ""
      }
    }
    {
      if (!in_target && $0 ~ target_regex) {
        flush_prev()
        if (object_key == "wizard") {
          print "  \"" object_key "\": " object_json
        } else {
          print "  \"" object_key "\": " object_json ","
        }
        in_target = 1
        inserted = 1
        if ($0 ~ /{/) {
          target_depth += gsub(/{/, "{", $0)
          target_depth -= gsub(/}/, "}", $0)
        } else {
          target_depth = 0
        }
        if (target_depth <= 0) {
          in_target = 0
        }
        next
      }

      if (in_target) {
        target_depth += gsub(/{/, "{", $0)
        target_depth -= gsub(/}/, "}", $0)
        if (target_depth <= 0) {
          in_target = 0
        }
        next
      }

      if (!inserted && before_regex != "" && $0 ~ before_regex) {
        flush_prev()
        print "  \"" object_key "\": " object_json ","
        inserted = 1
      }

      if (!inserted && $0 ~ /^}/) {
        if (prev != "") {
          if (prev !~ /,[[:space:]]*$/) {
            prev = prev ","
          }
          print prev
          prev = ""
        }
        print "  \"" object_key "\": " object_json
        inserted = 1
        print $0
        next
      }

      flush_prev()
      prev = $0
    }
    END {
      flush_prev()
      if (!inserted) {
        exit 2
      }
    }
  ' "${metadata_path}" >"${metadata_tmp_path}"; then
    rm -f -- "${metadata_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  if ! mv -- "${metadata_tmp_path}" "${metadata_path}"; then
    rm -f -- "${metadata_tmp_path}" >/dev/null 2>&1 || true
    return 1
  fi

  return 0
}

persist_stack_metadata_apps_object() {
  local stack_dir="${1}"
  local apps_json_object="${2}"

  persist_stack_metadata_top_level_object "${stack_dir}" "apps" "${apps_json_object}" "wizard"
}

persist_stack_metadata_wizard_object() {
  local stack_dir="${1}"
  local wizard_json_object="${2}"

  persist_stack_metadata_top_level_object "${stack_dir}" "wizard" "${wizard_json_object}"
}
