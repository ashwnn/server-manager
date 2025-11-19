# Bepo Discord Bot

## Overview
Bepo is a Discord bot that runs inside a Docker container and provides a set of slash commands to manage:

* **qBittorrent** – add torrents via magnet links or torrent files.  
* **Docker** – pause or resume all containers on the host.  
* **SnapRAID** – view status, SMART stats, and run dangerous operations (sync, scrub, fix) with a confirmation flow.  
* **Filesystem** – query disk usage for configured host paths.

All configuration is driven by a single `.env` file; the bot itself requires no manual host‑side setup beyond Docker, SnapRAID, and a running qBittorrent instance.

## Features
| Feature | Description |
|---------|-------------|
| **Slash commands** | Native Discord application commands, instantly available in the configured guild. |
| **Admin gating** | Dangerous commands are limited to user IDs listed in `DISCORD_ADMIN_USER_IDS`. |
| **Confirmation flow** | `pause`, `resume`, and SnapRAID destructive commands require an explicit confirm/cancel button. |
| **Docker socket access** | The container mounts `/var/run/docker.sock` to control host Docker. |
| **Environment‑driven** | All secrets and paths are read from `.env`. |
| **Extensible** | Services are isolated in `bot/services/` and can be extended with additional cogs. |

## Prerequisites
* Docker Engine (>= 20.10) and `docker compose` installed on the host.  
* A running qBittorrent Web UI reachable from the container.  
* SnapRAID installed and configured on the host (if you intend to use SnapRAID commands).  
* A Discord application with a bot token and the required OAuth scopes (`applications.commands`, `bot`). 

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bepo-discord.git
   cd bepo-discord
   ```

2. **Create the environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials and paths
   ```

3. **Build and start the container**
   ```bash
   docker compose up --build -d
   ```

4. **Verify the bot is running**
   ```bash
   docker logs -f discord-server-bot
   ```
   You should see a line similar to `Logged in as <BotName>#1234`.

## Configuration (`.env`)

| Variable | Description |
|----------|-------------|
| `DISCORD_BOT_TOKEN` | Bot token from the Discord developer portal. |
| `DISCORD_APP_ID` | Application (client) ID. |
| `DISCORD_GUILD_ID` | ID of the guild where the bot registers commands (for instant availability). |
| `DISCORD_ADMIN_USER_IDS` | Comma‑separated list of Discord user IDs allowed to run dangerous commands. |
| `QBITTORRENT_BASE_URL` | URL of the qBittorrent Web UI (e.g., `http://qbittorrent:8080`). |
| `QBITTORRENT_USERNAME` / `QBITTORRENT_PASSWORD` | Credentials for the qBittorrent API. |
| `SNAPRAID_CONF_PATH` | Absolute path to the SnapRAID configuration file on the host. |
| `HOST_POOL_PATH`, `HOST_MEDIA_SUBPATH`, `HOST_DOWNLOADS_SUBPATH` | Host directories mounted into the container for size queries. |
| `LOG_LEVEL` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

## Usage (Discord Slash Commands)

| Command | Options | Description |
|---------|---------|-------------|
| `/torrent add_link` | `url` (magnet or HTTP), optional `category`, `save_path` | Adds a torrent to qBittorrent. |
| `/torrent add_file` | `file` (attachment), optional `category`, `save_path` | Uploads a `.torrent` file and adds it. |
| `/fs size` | `target` (`pool`, `jellyfin_media`, `qbittorrent_downloads`) | Returns the size of the selected host path. |
| `/docker pause_all` | – | Pauses all running Docker containers (admin only, requires confirmation). |
| `/docker resume_all` | – | Resumes all paused Docker containers (admin only, requires confirmation). |
| `/snapraid status` | – | Shows SnapRAID status output. |
| `/snapraid smart` | – | Shows SMART statistics. |
| `/snapraid sync` | – | Runs a full SnapRAID sync (admin only, confirmation required). |
| `/snapraid scrub` | – | Runs a SnapRAID scrub (admin only, confirmation required). |
| `/snapraid fix` | – | Attempts to fix parity errors (admin only, confirmation required). |

All commands are scoped to the guild defined in `DISCORD_GUILD_ID`. Dangerous commands present an **Confirm** / **Cancel** button; only the user who initiated the command can confirm.

## Development
* **Python version**: 3.11 (specified in `bot/requirements.txt`).  
* **Dependencies** are installed inside the Docker image via `pip install -r requirements.txt`.  
* To add a new command, create a new cog in `bot/discord_commands/` and register it in `bot_main.py`. 

## Contributing
1. Fork the repository.  
2. Create a feature branch.  
3. Ensure code follows the existing style (PEP 8, type hints).  
4. Add or update tests under a `tests/` directory (if applicable).  
5. Submit a pull request with a clear description of changes.

## License
This project is licensed under the MIT License. See `LICENSE` for details.