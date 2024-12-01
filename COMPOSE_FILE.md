# Compose File

You can just combine multiple compose files into one with the `docker compose` command. This is useful when you have a base compose file and you want to add additional services or configurations to it. (current situation)

## Use this command to combine the compose files

```bash
docker compose -f compose.yaml -f overrides/compose.mariadb.yaml -f overrides/compose.redis.yaml -f overrides/compose.noproxy.yaml config > docker-compose.yaml
```

# Use this command to start the services

```bash
docker compose --env-file ~/ -f docker-compose.yaml up -d
```

P.S.: Do not forget to fill the `.env` file with the necessary environment variables. You can use `.env.example` as a template.
