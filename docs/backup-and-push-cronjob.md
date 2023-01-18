Create backup service or stack.

```yaml
# backup-job.yml
version: "3.7"
services:
  backup:
    image: frappe/erpnext:${VERSION}
    entrypoint: ["bash", "-c"]
    command:
      - |
        bench backup-all-sites
        ## Uncomment following to snapshot sites
        # restic snapshots || restic init
        # restic backup sites
    environment:
      # Set correct environment variables for restic
      - RESTIC_REPOSITORY=s3:https://s3.endpoint.com/restic
      - AWS_ACCESS_KEY_ID=access_key
      - AWS_SECRET_ACCESS_KEY=secret_access_key
      - RESTIC_PASSWORD=restic_password
    volumes:
      - "sites:/home/frappe/frappe-bench/sites"
    networks:
      - erpnext-network

networks:
  erpnext-network:
    external: true
    name: ${PROJECT_NAME:-erpnext}_default

volumes:
  sites:
    external: true
    name: ${PROJECT_NAME:-erpnext}_sites
```

In case of single docker host setup, add crontab entry for backup every 6 hours.

```
0 */6 * * * /usr/local/bin/docker-compose -f /path/to/backup-job.yml up -d > /dev/null
```

Or

```
0 */6 * * * docker compose -p erpnext exec backend bench --site all backup --with-files > /dev/null
```

Notes:

- Make sure `docker-compose` or `docker compose` is available in path during execution.
- Change the cron string as per need.
- Set the correct project name in place of `erpnext`.
