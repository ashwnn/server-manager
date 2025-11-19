import discord
from discord.ext import commands
from discord.commands import slash_command, Option
from config import settings
from services.qbittorrent_client import qbt_client
import aiohttp

class Torrents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_authorized(self, ctx):
        # Basic check: is admin?
        # Spec says: "Validate that the user is authorized."
        # "Torrent add commands: allow admin and optionally anyone with a specific role."
        # For now, let's restrict to admins as per the strictest interpretation, or maybe allow all if not specified?
        # Spec: "DISCORD_ADMIN_USER_IDS"
        # Let's allow admins.
        return ctx.author.id in settings.DISCORD_ADMIN_USER_IDS

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Add a torrent from a URL")
    async def torrent_add_link(
        self,
        ctx,
        url: Option(str, "Magnet link or HTTP/HTTPS URL"),
        category: Option(str, "Category", required=False, default=None),
        save_path: Option(str, "Save path", required=False, default=None)
    ):
        if not self.is_authorized(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        try:
            result = qbt_client.add_link(url, category, save_path)
            # qbittorrentapi returns 'Ok.' string on success usually, or raises exception?
            # It actually returns text "Ok." if successful.
            if result == "Ok.":
                await ctx.respond("Ok", ephemeral=True)
            else:
                await ctx.respond(f"Result: {result}", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error: {str(e)}", ephemeral=True)

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Add a torrent from a file")
    async def torrent_add_file(
        self,
        ctx,
        file: Option(discord.Attachment, "Torrent file"),
        category: Option(str, "Category", required=False, default=None),
        save_path: Option(str, "Save path", required=False, default=None)
    ):
        if not self.is_authorized(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        if not file.filename.endswith(".torrent"):
            await ctx.respond("Please upload a .torrent file.", ephemeral=True)
            return

        try:
            file_content = await file.read()
            result = qbt_client.add_file(file_content, category, save_path)
            if result == "Ok.":
                await ctx.respond("Ok", ephemeral=True)
            else:
                await ctx.respond(f"Result: {result}", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error: {str(e)}", ephemeral=True)

def setup(bot):
    bot.add_cog(Torrents(bot))
