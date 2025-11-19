import subprocess
from config import settings

def run_snapraid_command(*args: str) -> str:
    cmd = ["snapraid", "-c", settings.SNAPRAID_CONF_PATH, *args]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return "SnapRAID binary not found."
    except Exception as e:
        return f"Error running SnapRAID: {str(e)}"
