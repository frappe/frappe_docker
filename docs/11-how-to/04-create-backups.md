---
title: Create Backups
---

# Create backups

Create backup service or stack.

Use the same image and tag as your running bench, including any custom apps. Set `PROJECT_NAME` in your environment file to the bench's Compose project name. This example uses its default network and named `sites` volume; adjust the external network and volume names if your deployment uses different names.

```yaml
# backup-job.yml
services:
  backup:
    image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-$ERPNEXT_VERSION}
    entrypoint: ["bash", "-ec"]
    command:
      - |
        bench --site all backup
        ## Uncomment for restic snapshots.
        # restic snapshots || restic init
        # restic backup sites
        ## Uncomment to keep only last n=30 snapshots.
        # restic forget --group-by=paths --keep-last=30 --prune
    environment:
      # Set correct environment variables for restic
      - RESTIC_REPOSITORY=s3:https://s3.endpoint.com/restic
      - AWS_ACCESS_KEY_ID=access_key
      - AWS_SECRET_ACCESS_KEY=secret_access_key
      - RESTIC_PASSWORD=restic_password
    volumes:
      - "sites:/home/frappe/frappe-bench/sites"
    networks:
      - frappe-network

networks:
  frappe-network:
    external: true
    name: ${PROJECT_NAME:-erpnext}_default

volumes:
  sites:
    external: true
    name: ${PROJECT_NAME:-erpnext}_sites
```

The `bench` command above creates database backups. Add `--with-files` to include uploaded public and private files, as in the direct backup example below. The optional restic commands snapshot the `sites` directory.

In case of single docker host setup, add crontab entry for backup every 6 hours.

```
0 */6 * * * docker compose --env-file /path/to/bench.env -f /path/to/backup-job.yml run --rm -T backup > /dev/null
```

Alternatively, run backups in the existing `backend` container instead of using a separate backup service. The command below includes uploaded files with `--with-files`. It does not run the optional restic commands above.

```
0 */6 * * * docker compose -p erpnext -f /path/to/compose.yml exec -T backend bench --site all backup --with-files > /dev/null
```

Notes:

- Make sure `docker compose` is available in path during execution.
- Replace `/path/to/bench.env` with the bench environment file and `/path/to/compose.yml` with the rendered Compose file for the running stack. The separate backup service runs as a [one-off container](https://docs.docker.com/reference/cli/docker/compose/run/) and is removed after completion; `-T` disables terminal allocation for cron.
- Change the cron string as per need.
- Set the correct project name in place of `erpnext`.
- For Docker Swarm add it as a [swarm-cronjob](https://github.com/crazy-max/swarm-cronjob)
- Add it as a `CronJob` in case of Kubernetes cluster.
