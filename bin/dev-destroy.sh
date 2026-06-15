#!/bin/bash
docker compose \
  -p ranch \
  -f compose.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.postgres.yaml \
  -f overrides/compose.proxy.yaml \
  -f compose.my-local-dev.yaml \
  down --volumes --remove-orphans
