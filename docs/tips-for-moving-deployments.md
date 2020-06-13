# Tips for moving deployments

- Take regular automatic backups and push the files to S3 compatible cloud. Setup backup and push with cronjobs
    - Use regular cron for single machine installs
    - Use [swarm-cronjob](https://github.com/crazy-max/swarm-cronjob) for docker swarm
    - Use Kubernetes CronJob
- It makes it easy to transfer data from cloud to any new deployment.
- They are just [site operations](site-operations.md) that can be manually pipelined as per need.
- Remember to restore encryption keys and other custom configuration from `site_config.json`.
- Steps to move deployment:
    - [Take backup](site-operations.md#backup-sites)
    - [Push backup to cloud](site-operations.md#push-backup-to-s3-compatible-storage)
    - Create new deployment type anywhere
    - [Restore backup from cloud](site-operations.md#restore-backups)
    - [Restore `site_config.json` from cloud](site-operations.md#edit-configs)
