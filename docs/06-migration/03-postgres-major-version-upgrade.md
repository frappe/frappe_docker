# PostgreSQL Major Version Upgrade (v13 to v15)

Upgrading PostgreSQL from version 13 to 15 is a major version jump. Since PostgreSQL does not support in-place data directory upgrades, existing users must manually migrate their data using `pg_dump`.

### **Migration Steps**

1. **Backup Existing Data (Version 13):**
   Before updating your compose file, ensure your containers are running and perform a dump of all databases.

   ```bash
   docker exec -it <project_name>-db-1 pg_dumpall -U postgres > full_dump.sql
   ```

2. **Stop and Remove Containers:**

   ```bash
   docker compose down
   ```

3. **Delete Old Data Volume:**
   PostgreSQL 15 cannot read data created by version 13. You must remove the existing volume (Warning: this deletes the old data directory).

   ```bash
   docker volume rm <project_name>_db-data
   ```

4. **Update Image and Start (Version 15):**
   Update your `overrides/compose.postgres.yaml` (or pull the latest changes) and start the containers.

   ```bash
   docker compose up -d
   ```

5. **Restore Data:**
   Restore the dump into the new PostgreSQL 15 instance.

   ```bash
   cat full_dump.sql | docker exec -i <project_name>-db-1 psql -U postgres
   ```

6. **Verify and Clean Up:**
   Ensure your sites are working correctly with `bench migrate` and then remove the `full_dump.sql` file.
   ```bash
   docker exec -it <project_name>-backend-1 bench --site all migrate
   ```
