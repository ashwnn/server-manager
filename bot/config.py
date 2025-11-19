import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Discord
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_APP_ID = os.getenv("DISCORD_APP_ID")
    DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
    DISCORD_ADMIN_USER_IDS = {
        int(x) for x in os.getenv("DISCORD_ADMIN_USER_IDS", "").split(",") if x.strip()
    }

    # qBittorrent
    QBITTORRENT_BASE_URL = os.getenv("QBITTORRENT_BASE_URL")
    QBITTORRENT_USERNAME = os.getenv("QBITTORRENT_USERNAME")
    QBITTORRENT_PASSWORD = os.getenv("QBITTORRENT_PASSWORD")

    # SnapRAID
    SNAPRAID_CONF_PATH = os.getenv("SNAPRAID_CONF_PATH")

    # Host paths
    HOST_POOL_PATH = os.getenv("HOST_POOL_PATH")
    HOST_MEDIA_SUBPATH = os.getenv("HOST_MEDIA_SUBPATH")
    HOST_DOWNLOADS_SUBPATH = os.getenv("HOST_DOWNLOADS_SUBPATH")

    # Misc
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
