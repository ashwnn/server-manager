import qbittorrentapi
from config import settings

class QBittorrentClient:
    def __init__(self):
        self.client = qbittorrentapi.Client(
            host=settings.QBITTORRENT_BASE_URL,
            username=settings.QBITTORRENT_USERNAME,
            password=settings.QBITTORRENT_PASSWORD,
        )
        try:
            self.client.auth_log_in()
        except qbittorrentapi.LoginFailed as e:
            print(f"Failed to login to qBittorrent: {e}")

    def add_link(self, url: str, category: str = None, save_path: str = None):
        kwargs = {}
        if category:
            kwargs['category'] = category
        if save_path:
            kwargs['save_path'] = save_path
        
        return self.client.torrents_add(urls=url, **kwargs)

    def add_file(self, file_content: bytes, category: str = None, save_path: str = None):
        kwargs = {}
        if category:
            kwargs['category'] = category
        if save_path:
            kwargs['save_path'] = save_path

        return self.client.torrents_add(torrent_files=file_content, **kwargs)

qbt_client = QBittorrentClient()
