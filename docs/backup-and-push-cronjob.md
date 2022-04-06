Create backup service or stack.

```yaml
# backup-job.yml
version: "3.7"
services:
  backup:
    image: frappe/erpnext-worker:v13
    entrypoint: ["bash", "-c"]
    command: |
      for $SITE in $(/home/frappe/frappe-bench/env/bin/python -c "import frappe;print(' '.join(frappe.utils.get_sites()))")
      do
        bench --site $SITE backup --with-files
        push-backup \
          --site $SITE \
          --bucket $BUCKET_NAME \
          --region-name $REGION \
          --endpoint-url $ENDPOINT_URL \
          --aws-access-key-id $ACCESS_KEY_ID \
          --aws-secret-access-key $SECRET_ACCESS_KEY
      done
    environment:
      - BUCKET_NAME=erpnext
      - REGION=us-east-1
      - ACCESS_KEY_ID=RANDOMACCESSKEY
      - SECRET_ACCESS_KEY=RANDOMSECRETKEY
      - ENDPOINT_URL=https://endpoint.url
    volumes:
      - "sites-vol:/home/frappe/frappe-bench/sites"
    networks:
      - erpnext-network

networks:
  erpnext-network:
    external: true
    name: <your_frappe_docker_project_name>_default

volumes:
  sites-vol:
    external: true
    name: <your_frappe_docker_project_name>_sites-vol
```

In case of single docker host setup, add crontab entry for backup every 6 hours.

```
0 */6 * * * /usr/local/bin/docker-compose -f /path/to/backup-job.yml up -d > /dev/null
```

Notes:

- Change the cron string as per need.
