# Easy-Frappe-Docker

Easy installation script for Frappe Docker for development and production

## Run

```bash
bash easy-docker.sh
```

## Dependencies

- `gum` is used for the TUI
- The script checks required dependencies on startup
- Missing dependencies are installed automatically when possible
- If package manager installation for `gum` fails, the script can use a GitHub binary fallback

## Options

- `-h`, `--help`
  - Shows usage and exits without starting the TUI
- `--no-github-binary-fallback`
  - Disables GitHub binary fallback for `gum`
  - If package manager installation fails, the script exits with manual installation guidance
