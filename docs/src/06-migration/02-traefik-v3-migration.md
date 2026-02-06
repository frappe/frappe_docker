# Migrate an existing Traefik v2 instance to v3

Use this guide if you already run Traefik v2 with `frappe_docker` and want to upgrade to v3. It focuses on the image upgrade and the v3 routing rule changes that affect existing setups.

> Note: The Traefik v2 -> v3 migration is complete. The provided overrides no longer set `core.defaultRuleSyntax` or per-router `ruleSyntax` labels, because v3 is the default rule syntax.
> Note: If you have a system that must continue to run on v2 despite EOL, you can pin v2 rule syntax with `--core.defaultRuleSyntax=v2` in your Traefik service.

### Before you start

Before migrating anything, it is always recommended to create a backup. Better safe than sorry. In particular, compose and .env should be backed up.

### Quick upgrade summary

1. Pull the updated repo
2. Update env variables especially the updated `SITES` to `SITES_RULE`
3. Regenerate the compose config and restart the stack

#### Multiple hostnames

v2 allowed comma-separated host lists inside `Host(...)`. In v3 Traefik uses logical OR.

**Before (v2):**

```
Host(`a.example.com`,`b.example.com`)
```

**After (v3):**

```
Host(`a.example.com`) || Host(`b.example.com`)
```

### Step 1: Replace `SITES` with `SITES_RULE`

All Traefik routing for HTTPS and multi-bench setups now uses `SITES_RULE`, which is a full v3 rule expression.

**Single site:**

```
SITES_RULE=Host(`erp.example.com`)
```

**Multiple sites:**

```
SITES_RULE=Host(`a.example.com`) || Host(`b.example.com`)
```

### Step 2: Regenerate and start your compose config

Example for HTTPS:

```sh
docker compose --env-file .env \
  -f compose.yaml \
  -f overrides/compose.mariadb.yaml \
  -f overrides/compose.redis.yaml \
  -f overrides/compose.https.yaml \
  config > ~/gitops/docker-compose.yml
```

```sh
docker compose --project-name <project-name> -f ~/gitops/docker-compose.yml up -d
```

See [Single Server Example](../02-setup/07-single-server-example.md)

### Step 3: Verify Traefik

After restarting, Traefik will be used in the new supported version 3.6 and the same URLs will be used for the instances when making adjustments. After that, the pages should be accessible as before via the proxy and, if using HTTPS, via HTTPS.

### Rollback

If you need to rollback:

1. Revert Traefik image to `v2.11`
2. Restore the old `SITES` variable format and v2 rules
3. Regenerate the compose config and restart
