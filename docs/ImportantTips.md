# Important Tips

## Hot Reloading

In general, any changes you make to the API code base (REST API) or the Streamlit app code should be *hot reloaded* when the files are saved — the changes should be immediately available without restarting containers.

- Don't forget to click the **Always Rerun** button in the browser tab of the Streamlit app for it to reload with changes.
- Sometimes, a bug in the code will cause a container to crash. Fix the bug in the code, then restart the `app` container in Docker Desktop or restart all containers with `docker compose restart` (no `-d` flag).

## The MySQL Container

The MySQL container behaves differently from the app and API containers — be aware of the following:

- The MySQL container has **no persistent volume** in this project. Every time a fresh `db` container is *created*, MySQL initializes itself by executing the `.sql` files in `./database-files/` in **alphabetical order** (name them accordingly — e.g. `01_schema.sql`, `02_data.sql`).
- This matches how the app behaves in production (Coolify): every redeploy starts with a fresh database seeded from the SQL files in your repo. The seed files are the source of truth — there is no separate "production data" that drifts from what's in the repo.
- **Implication:** rows you insert through the Streamlit UI (e.g. saved articles, journalist notes, or trader watchlist entries) live only inside the running container until you recreate the database. To ship default data with the repo, add it to `database-files/*.sql`.

### When you change a SQL file

You must **recreate** the `db` container, not just restart it. Restarting reuses the same container with the same already-initialized data dir. Recreating gives you a clean container that runs the init scripts again.

```bash
docker compose down db && docker compose up db -d
```

- `docker compose down db` stops and removes the MySQL container.
- `docker compose up db -d` creates a new container and re-runs all files in `database-files/`.

(There's no `-v` flag because there's no volume to wipe.)

### Reading the logs

The MySQL container's log files are your friend. In Docker Desktop, select the `mysql_db` container and click the **Logs** tab. If there are errors in your `.sql` files, they appear here. Use the search 🔍 to look for `Error` to find them quickly. Common culprits: typos, foreign-key references to tables not yet created, duplicate primary keys.
