Here is an updated, self contained design guide that assumes the bot itself runs in Docker and you only touch `.env` then run `docker compose up -d`.

---

## 1. Overall architecture

**Runtime**

* Bot runs as a single Docker container.
* You manage it with:

  * `.env` at the project root
  * `docker-compose.yml`
  * `docker compose up -d` and `docker compose pull` to update

**What the container does**

Inside the container:

* Discord client that listens for application commands (slash commands, maybe buttons for confirmations).
* qBittorrent client talking to your WebUI API on port 8080. ([GitHub][1])
* Docker client talking to the host Docker daemon via the mounted Docker socket.
* SnapRAID command runner that shells out to `snapraid` with a given config. ([Ubuntu Manpages][2])
* File size reporter that runs `du` on the host paths you care about via bind mounts.

**Key host paths (mounted into container)**

* `/home/ashwin/pool` (and subdirectories) for size queries.
* SnapRAID config path (for example `/etc/snapraid.conf`).
* `/var/run/docker.sock` so the bot can pause and resume containers.

You will not need to create users, change systemd units, or edit sudoers manually. All configuration goes through `.env` and the compose file.

---

## 2. Project layout

Recommended structure:

```text
server-bot/
  docker-compose.yml
  .env.example
  .env        # you create this from .env.example
  bot/
    Dockerfile
    pyproject.toml / requirements.txt
    bot_main.py
    config.py
    discord_commands/
      torrents.py
      docker_control.py
      snapraid.py
      filesystem.py
      confirm.py
    services/
      qbittorrent_client.py
      docker_client.py
      snapraid_runner.py
      filesystem_stats.py
      auth.py
      confirmations.py
```

You mostly care about `.env` and `docker-compose.yml`.

---

## 3. Environment variables

Your `.env` should contain everything needed so that no further manual configuration is required.

Example `.env`:

```dotenv
##############
# Discord
##############
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_APP_ID=your_application_id_here
DISCORD_GUILD_ID=your_home_server_guild_id_here

# Comma separated list of admin user IDs who can run dangerous commands
DISCORD_ADMIN_USER_IDS=123456789012345678,987654321098765432

##############
# qBittorrent
##############
QBITTORRENT_BASE_URL=http://qbittorrent:8080
QBITTORRENT_USERNAME=your_qb_user
QBITTORRENT_PASSWORD=your_qb_password

##############
# SnapRAID
##############
SNAPRAID_CONF_PATH=/etc/snapraid.conf

##############
# Host paths (backed by volumes)
##############
HOST_POOL_PATH=/home/ashwin/pool
HOST_MEDIA_SUBPATH=/home/ashwin/pool/media
HOST_DOWNLOADS_SUBPATH=/home/ashwin/pool/downloads

##############
# Misc
##############
LOG_LEVEL=INFO
```

Notes:

* `QBITTORRENT_BASE_URL` can be `http://qbittorrent:8080` if your qBittorrent container is on the same Docker network under service name `qbittorrent`, or `http://192.168.1.10:8080` etc if it is on bare metal.
* `SNAPRAID_CONF_PATH` should point to the config that your host already uses.

---

## 4. docker-compose.yml

Example `docker-compose.yml` that uses only variables from `.env`:

```yaml
version: "3.8"

services:
  discord-server-bot:
    build:
      context: ./bot
    container_name: discord-server-bot
    env_file:
      - .env
    restart: unless-stopped

    # Give the container access to host resources via bind mounts
    volumes:
      - ${HOST_POOL_PATH}:${HOST_POOL_PATH}:ro
      - ${SNAPRAID_CONF_PATH}:${SNAPRAID_CONF_PATH}:ro
      - /var/run/docker.sock:/var/run/docker.sock

    # Optional: constrain resources a bit
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
```

With that:

* The bot sees the same paths inside the container as on the host.
* SnapRAID commands use `SNAPRAID_CONF_PATH` as supplied in `.env`.
* Docker SDK or CLI in the container talks to `/var/run/docker.sock`.

All you do to start it:

```bash
cp .env.example .env
# edit .env
docker compose up -d
```

---

## 5. Bot internals in Docker context

### 5.1 qBittorrent client

Use the qBittorrent Web API client library (for example `qbittorrent-api` in Python) configured from env. ([qbittorrent-api.readthedocs.io][3])

* On startup, instantiate:

  ```python
  import qbittorrentapi
  from config import settings

  qbt_client = qbittorrentapi.Client(
      host=settings.qb_base_url,
      username=settings.qb_username,
      password=settings.qb_password,
  )
  qbt_client.auth_log_in()
  ```

* For adding torrents, call the `torrents_add` method which maps to `/api/v2/torrents/add`. ([GitHub][1])

### 5.2 Docker client

Inside the container, use the Docker SDK for Python configured to use the mounted socket:

```python
import docker

docker_client = docker.from_env()   # this picks up /var/run/docker.sock
```

Your pause and resume functions will operate on `docker_client.containers.list()`.

### 5.3 SnapRAID runner

Inside the container, run the SnapRAID commands via `subprocess`:

```python
import subprocess
from config import settings

def run_snapraid_command(*args: str) -> subprocess.CompletedProcess:
  cmd = ["snapraid", "-c", settings.snapraid_conf_path, *args]
  return subprocess.run(
      cmd,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True,
      check=False,
  )
```

Supported commands, as per the manpage: `status`, `smart`, `up`, `down`, `sync`, `scrub`, `fix`. ([Ubuntu Manpages][2])

The bot will expose only a safe subset directly, and gate the heavy ones through confirmation.

### 5.4 Filesystem stats

Because `/home/ashwin/pool` is bind mounted read only, you can safely run `du` inside the container:

```python
def du_h(path: str) -> str:
  result = subprocess.run(
      ["du", "-sh", path],
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True,
      check=False,
  )
  return result.stdout.strip()
```

---

## 6. Discord command design (Docker aware)

All commands are Discord application commands. You register them in code for a single guild ID from `.env` so they appear instantly on your home server.

### 6.1 Torrent commands

**Command**: `/torrent add_link`

* Options:

  * `url` (string, required)
    Accepts `magnet:`, `http`, and `https` URLs. The Web API supports these URL types directly. ([GitHub][1])
  * `category` (string, optional).
  * `save_path` (string, optional).

* Behavior:

  * Validate that the user is authorized.
  * Use qBittorrent `torrents_add` with `urls=url`, `category`, `save_path` as provided.
  * Reply with a short status: either `Ok` or the returned error.

This is not dangerous, so it does not require confirmation.

**Command**: `/torrent add_file`

* Options:

  * `file` (attachment, required).
  * `category`, `save_path` optional.

* Behavior:

  * Download the attachment content using Discord HTTP client.
  * Forward the bytes to qBittorrent via `torrents_add(torrent_files=[...])`.
  * Short success or error message.

Still safe, no confirmation required.

Optional extra commands like `/torrent list` or `/torrent remove` can be added. Deletion with `delete_data` should require confirmation if you implement it.

---

### 6.2 Docker control commands

These are resource affecting, so they must use the confirmation flow.

**Command**: `/docker pause_all`

* First step:

  * Check user is admin.

  * Instead of pausing immediately, create a pending action in an in memory store:

    ```python
    pending.add(
      user_id=ctx.user.id,
      action_type="docker_pause_all",
      data={},
      expires_at=now + 2 minutes,
    )
    ```

  * Reply ephemerally with a message and components:

    * Text:
      `This will pause all running Docker containers on the host. Confirm?`
    * Buttons:

      * `Confirm` with custom ID `confirm:docker_pause_all`
      * `Cancel` with custom ID `cancel:docker_pause_all`

* Second step:

  * When a button interaction comes in:

    * Look up pending action for that user and action type.

    * If exists and not expired, execute the heavy operation:

      ```python
      for c in docker_client.containers.list():
          if c.status == "running":
              c.pause()
      ```

    * Edit the original ephemeral message to show success status and number of containers affected.

**Command**: `/docker resume_all`

Identical flow, but unpause:

```python
for c in docker_client.containers.list(all=True):
    if c.status == "paused":
        c.unpause()
```

Both of these count as dangerous, so you always go through the two step button confirmation.

---

### 6.3 Filesystem size commands

These are read only and safe.

**Command**: `/fs size`

* Options:

  * `target` (choice: `pool`, `jellyfin_media`, `qbittorrent_downloads`).

* Mapping to host paths:

  * `pool` → `${HOST_POOL_PATH}`
  * `jellyfin_media` → `${HOST_MEDIA_SUBPATH}`
  * `qbittorrent_downloads` → `${HOST_DOWNLOADS_SUBPATH}`

* Backend:

  ```python
  if target == "pool":
      path = settings.host_pool_path
  elif target == "jellyfin_media":
      path = settings.host_media_subpath
  elif target == "qbittorrent_downloads":
      path = settings.host_downloads_subpath

  size_str = du_h(path)
  ```

* Response:

  `Size of /home/ashwin/pool/media: 3.2T` etc.

No confirmation necessary.

---

### 6.4 SnapRAID commands

SnapRAID exposes commands like `status`, `smart`, `sync`, `scrub`, `fix` that operate against your configured array. ([Ubuntu Manpages][2])

You separate them into:

* Low risk read only:

  * `status`
  * `smart`
  * `diff` (if you choose to support it)
* Heavy or dangerous:

  * `sync`
  * `scrub`
  * `fix`

**Command**: `/snapraid status`

* Calls `run_snapraid_command("status")`.
* Returns stdout truncated to a reasonable length in a code block.

**Command**: `/snapraid smart`

* Calls `run_snapraid_command("smart")`.
* Output usually fits nicely in a code block.

These run directly, no confirmation. `status` and `smart` only report information. ([Ubuntu Manpages][2])

**Command**: `/snapraid sync`

* Uses confirmation flow, similar to `/docker pause_all`:

  1. First invocation:

     * Check admin user.
     * Insert pending action `snapraid_sync`.
     * Ephemeral reply with buttons:

       Text example:
       `snapraid sync may run for a long time and will rewrite parity. Confirm?`

  2. On `Confirm` button:

     * Run `run_snapraid_command("sync")` asynchronously in a background task.
     * Immediately update the button message to say `sync started in background`.
     * When finished, send a new ephemeral follow up with summary status.

Similar pattern for `/snapraid scrub` and `/snapraid fix` with appropriate warnings. The docs stress that `fix` will revert changes back to the last sync snapshot, so it should definitely be guarded. ([snapraid.it][4])

If you want a generic command:

**Command**: `/snapraid run`

* Options:

  * `command` (choice: `status`, `smart`, `diff`, `sync`, `scrub`, `fix`).
* Internally:

  * If chosen command is in safe list, run directly.
  * If in dangerous list, switch to the confirmation workflow.

---

## 7. Confirmation and safety layer

Design a dedicated `ConfirmationManager` so that all expensive or dangerous commands go through a single mechanism.

**In memory store**

Basic interface:

```python
class ConfirmationManager:
    def create(self, user_id, action_type, payload) -> str:
        # return token or use (user_id, action_type) as key

    def get(self, user_id, token_or_action_type):
        # return action object if not expired

    def consume(self, user_id, token_or_action_type):
        # mark as used and return action
```

You can keep it in a dict, expiring entries based on `expires_at`.

**When to require confirmation**

Always:

* `/docker pause_all`
* `/docker resume_all`
* `/snapraid sync`
* `/snapraid scrub`
* `/snapraid fix`
* Any future commands that stop services, delete files, or modify parity.

Optional but reasonable:

* Any qBittorrent command that deletes torrents with payload data.

---

## 8. Permissions and roles in Discord

All inside the container, no host changes.

* At startup, parse:

  ```python
  admin_ids = {int(x) for x in os.getenv("DISCORD_ADMIN_USER_IDS", "").split(",") if x.strip()}
  ```

* Utility:

  ```python
  def is_admin(user_id: int) -> bool:
      return user_id in admin_ids
  ```

* Command gates:

  * Torrent add commands: allow admin and optionally anyone with a specific role.
  * Filesystem size: safe to expose to more users.
  * Docker and SnapRAID heavy commands: admin only.

You can also register commands as guild commands restricted to roles, but that is optional if you already have checks in code.

---

## 9. Setup checklist for you

Given this design, your actual steps on the host are:

1. Clone or create the project directory that includes:

   * `docker-compose.yml`
   * `.env.example`
   * `bot/` with Dockerfile and code

2. Create `.env` from `.env.example` and fill:

   * Discord tokens and IDs
   * qBittorrent URL and credentials
   * SnapRAID config path
   * Host pool path values if they differ from the defaults

3. From the project directory:

   ```bash
   docker compose build
   docker compose up -d
   ```

No further host level configuration should be necessary as long as:

* SnapRAID is already configured and its config lives at `SNAPRAID_CONF_PATH`.
* Docker is running and the daemon is reachable via `/var/run/docker.sock`.
* qBittorrent WebUI is running and reachable at `QBITTORRENT_BASE_URL`.

If you want, next I can sketch the actual `Dockerfile` and a minimal Python skeleton that wires together the env variables, mounts, and slash commands so you can drop it straight into a repo.

[1]: https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-%28qBittorrent-4.1%29?utm_source=chatgpt.com "WebUI API (qBittorrent 4.1)"
[2]: https://manpages.ubuntu.com/manpages/jammy/man1/snapraid.1.html?utm_source=chatgpt.com "SnapRAID Backup For Disk Arrays"
[3]: https://qbittorrent-api.readthedocs.io/en/v2021.2.17/apidoc/torrents.html?utm_source=chatgpt.com "Torrents — qbittorrent-api documentation"
[4]: https://www.snapraid.it/manual?utm_source=chatgpt.com "Manual"
