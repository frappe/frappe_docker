docker compose -f compose.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.noproxy.yaml \
  config > ~/gitops/docker-compose.yaml