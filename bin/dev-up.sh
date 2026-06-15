#!/bin/bash
docker compose \
  --env-file .env \
  -f compose.yaml \
  -p ranch \
  -f overrides/compose.redis.yaml \
	-f overrides/compose.mariadb.yaml \
  -f overrides/compose.proxy.yaml \
  -f compose.my-local-dev.yaml \
  up
