import subprocess
from config import settings

def get_disk_usage(path_key: str) -> str:
    path = None
    if path_key == "pool":
        path = settings.HOST_POOL_PATH
    elif path_key == "jellyfin_media":
        path = settings.HOST_MEDIA_SUBPATH
    elif path_key == "qbittorrent_downloads":
        path = settings.HOST_DOWNLOADS_SUBPATH
    
    if not path:
        return "Invalid path key."

    try:
        # Using 'du -sh' to get summary in human readable format
        result = subprocess.run(
            ["du", "-sh", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return "du command not found."
    except Exception as e:
        return f"Error checking disk usage: {str(e)}"
