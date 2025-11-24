# Bepo Discord Bot

Bepo is a Discord bot designed to manage and monitor multiple homelab servers. It runs in a Docker container and connects to remote servers via SSH to control services like Docker, SnapRAID, qBittorrent, and the filesystem.

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Installation](#installation)
* [Usage](#usage)
* [Configuration](#configuration)
* [Project Structure](#project-structure)
* [Examples](#examples)
* [Contributing](#contributing)
* [License](#license)

## Overview

Bepo solves the problem of managing scattered homelab services by centralizing control into a Discord interface. Instead of logging into multiple servers or exposing various web UIs, you can perform common maintenance tasks and checks directly from your Discord server. It is designed to be secure, using SSH keys for connectivity and restricting sensitive commands to authorized admin users.

## Features

*   **Multi-Server Management**: Control multiple servers defined in a central configuration file.
*   **SSH Connectivity**: Securely connects to remote hosts using SSH keys without exposing Docker sockets or other ports.
*   **Docker Management**: Pause and resume all containers on a host (useful for maintenance).
*   **SnapRAID Integration**: Check status, SMART stats, and run sync/scrub/fix commands with safety confirmations.
*   **qBittorrent Control**: Add torrents via magnet links or file uploads.
*   **Filesystem Monitoring**: Check disk usage for specific configured paths across your servers.
*   **Admin Gating**: Restrict dangerous commands to specific Discord user IDs.
*   **Confirmation Flows**: Interactive buttons to confirm destructive or disruptive actions.

## Installation

Follow these steps to get Bepo running locally or on your server.

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/bepo-discord.git
    cd bepo-discord
    ```

2.  **Generate SSH Keys**
    The bot needs an SSH key to connect to your servers.
    ```bash
    # Generate a keypair (no passphrase recommended for automation)
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/bepo_bot_key
    ```
    *Add the public key (`~/.ssh/bepo_bot_key.pub`) to the `~/.ssh/authorized_keys` file on every server you want the bot to manage.*

3.  **Configure Environment Variables**
    ```bash
    cp .env.example .env
    # Edit .env with your Discord Token and Admin IDs
    ```

4.  **Configure Servers**
    ```bash
    cp servers.json.example servers.json
    # Edit servers.json to define your servers and their capabilities
    ```

5.  **Start the Bot**
    ```bash
    docker compose up --build -d
    ```

## Usage

Interact with Bepo using Discord Slash Commands.

| Command | Description |
| :--- | :--- |
| `/torrent add_link [url]` | Add a torrent via magnet link or URL. |
| `/torrent add_file [file]` | Upload a `.torrent` file. |
| `/fs size [target]` | Check disk usage of a configured path (e.g., pool, downloads). |
| `/docker pause_all` | Pause all containers on a specific server (Admin only). |
| `/docker resume_all` | Resume all containers on a specific server (Admin only). |
| `/snapraid status` | Show SnapRAID status. |
| `/snapraid smart` | Show SMART statistics. |
| `/snapraid sync` | Run SnapRAID sync (Admin only). |
| `/snapraid scrub` | Run SnapRAID scrub (Admin only). |

## Configuration

### Environment Variables (`.env`)

| Variable | Description |
| :--- | :--- |
| `DISCORD_BOT_TOKEN` | Your Discord Bot Token. |
| `DISCORD_APP_ID` | Your Discord Application ID. |
| `DISCORD_GUILD_ID` | The Guild ID where commands will be registered. |
| `DISCORD_ADMIN_USER_IDS` | Comma-separated list of User IDs allowed to run admin commands. |
| `LOG_LEVEL` | Logging level (e.g., INFO, DEBUG). |

### Server Configuration (`servers.json`)

Define your servers in `servers.json`. Each server object includes connection details and enabled features.

```json
{
  "servers": [
    {
      "name": "homelab",
      "display_name": "🏠 Homelab",
      "connection": {
        "host": "192.168.1.100",
        "user": "user",
        "key_path": "/app/.ssh/id_rsa"
      },
      "features": ["docker", "snapraid", "filesystem"],
      "config": {
        "filesystem": {
          "paths": {
             "pool": "/mnt/pool"
          }
        }
      }
    }
  ]
}
```

## Project Structure

```
bepo-discord/
  ├── bot/
  │   ├── discord_commands/  # Cog implementations for slash commands
  │   ├── services/          # Core logic for Docker, SnapRAID, etc.
  │   ├── bot_main.py        # Entry point
  │   └── config.py          # Configuration loading
  ├── docker-compose.yml     # Docker deployment config
  ├── servers.json.example   # Template for server config
  └── .env.example           # Template for environment variables
```

## Examples

**Checking Disk Space**
Run `/fs size target:pool` to see the available space on your configured storage pool.

**Maintenance Mode**
1.  Run `/docker pause_all` and select the target server.
2.  Confirm the action by clicking the **Confirm** button.
3.  Perform your maintenance.
4.  Run `/docker resume_all` to bring services back online.

## Contributing

Contributions are welcome!

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## License

Licensed under the [CC BY‑NC‑SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/) license.