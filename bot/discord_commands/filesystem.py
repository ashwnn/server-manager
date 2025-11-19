import discord
from discord.ext import commands
from discord.commands import slash_command, Option
from config import settings
from services.filesystem_stats import get_disk_usage

class Filesystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Check filesystem size")
    async def fs_size(
        self,
        ctx,
        target: Option(str, "Target path", choices=["pool", "jellyfin_media", "qbittorrent_downloads"])
    ):
        # Safe command, no auth needed per spec (or maybe implied?)
        # Spec: "Filesystem size: safe to expose to more users."
        
        size_str = get_disk_usage(target)
        
        # Map target to friendly name for display
        path_map = {
            "pool": settings.HOST_POOL_PATH,
            "jellyfin_media": settings.HOST_MEDIA_SUBPATH,
            "qbittorrent_downloads": settings.HOST_DOWNLOADS_SUBPATH
        }
        friendly_path = path_map.get(target, target)
        
        await ctx.respond(f"Size of `{friendly_path}`: {size_str}", ephemeral=True)

def setup(bot):
    bot.add_cog(Filesystem(bot))
