#!/usr/bin/env bash

persist_stack_metadata_apps_object() {
  local stack_dir="${1}"
  local apps_json_object="${2}"
  local metadata_path=""
  local metadata_tmp_path=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ -z "${apps_json_object}" ]; then
    return 1
  fi

  if ! awk -v apps_object="${apps_json_object}" '
    BEGIN {
      in_top_level_apps = 0
      apps_depth = 0
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
      if (!in_top_level_apps && $0 ~ /^  "apps"[[:space:]]*:/) {
        flush_prev()
        print "  \"apps\": " apps_object ","
        in_top_level_apps = 1
        inserted = 1
        if ($0 ~ /{/) {
          apps_depth += gsub(/{/, "{", $0)
          apps_depth -= gsub(/}/, "}", $0)
        } else {
          apps_depth = 0
        }
        if (apps_depth <= 0) {
          in_top_level_apps = 0
        }
        next
      }

      if (in_top_level_apps) {
        apps_depth += gsub(/{/, "{", $0)
        apps_depth -= gsub(/}/, "}", $0)
        if (apps_depth <= 0) {
          in_top_level_apps = 0
        }
        next
      }

      if (!inserted && $0 ~ /^  "wizard"[[:space:]]*:/) {
        flush_prev()
        print "  \"apps\": " apps_object ","
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
        print "  \"apps\": " apps_object
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

persist_stack_metadata_wizard_object() {
  local stack_dir="${1}"
  local wizard_json_object="${2}"
  local metadata_path=""
  local metadata_tmp_path=""

  metadata_path="${stack_dir}/metadata.json"
  metadata_tmp_path="${metadata_path}.tmp"
  if [ ! -f "${metadata_path}" ]; then
    return 1
  fi

  if [ -z "${wizard_json_object}" ]; then
    return 1
  fi

  if ! awk -v wizard_object="${wizard_json_object}" '
    BEGIN {
      in_top_level_wizard = 0
      wizard_depth = 0
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
      if (!in_top_level_wizard && $0 ~ /^  "wizard"[[:space:]]*:/) {
        flush_prev()
        print "  \"wizard\": " wizard_object
        in_top_level_wizard = 1
        inserted = 1
        if ($0 ~ /{/) {
          wizard_depth += gsub(/{/, "{", $0)
          wizard_depth -= gsub(/}/, "}", $0)
        } else {
          wizard_depth = 0
        }
        if (wizard_depth <= 0) {
          in_top_level_wizard = 0
        }
        next
      }

      if (in_top_level_wizard) {
        wizard_depth += gsub(/{/, "{", $0)
        wizard_depth -= gsub(/}/, "}", $0)
        if (wizard_depth <= 0) {
          in_top_level_wizard = 0
        }
        next
      }

      if (!inserted && $0 ~ /^}/) {
        if (prev != "") {
          if (prev !~ /,[[:space:]]*$/) {
            prev = prev ","
          }
          print prev
          prev = ""
        }
        print "  \"wizard\": " wizard_object
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
