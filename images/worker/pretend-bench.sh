#!/bin/bash
set -e

# shellcheck disable=SC2068
~/frappe-bench/env/bin/python /usr/local/bin/patched_bench_helper.py frappe $@
