#!/bin/bash

echo "Checking bash scripts with shellcheck" >&2

while IFS= read -r shellfile; do
  shellcheck --check-sourced --severity=style --color=always --exclude=SC2164,SC2086,SC2012,SC2016 ${shellfile}
done < <(find ./build -name "*.sh")
