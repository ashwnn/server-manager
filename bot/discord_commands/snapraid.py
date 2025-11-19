import discord
from discord.ext import commands
from discord.commands import slash_command, Option
from discord.ui import View, Button
from config import settings
from services.snapraid_runner import run_snapraid_command
from services.confirmations import confirmation_manager
import asyncio

class SnapRAIDConfirmationView(View):
    def __init__(self, token: str, action_type: str):
        super().__init__(timeout=120)
        self.token = token
        self.action_type = action_type

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_snapraid")
    async def confirm_callback(self, button, interaction):
        action = confirmation_manager.consume(self.token)
        if not action:
            await interaction.response.edit_message(content="Action expired or already used.", view=None)
            return

        if interaction.user.id != action["user_id"]:
             await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
             return

        await interaction.response.edit_message(content=f"{self.action_type} started in background...", view=None)
        
        # Run in background
        # We need to run this asynchronously so we don't block the bot
        # run_snapraid_command is blocking, so run it in executor
        loop = asyncio.get_running_loop()
        
        # We can't easily update the ephemeral message after a long time if the token expires or something?
        # Actually interaction webhooks are valid for 15 mins. SnapRAID sync can take HOURS.
        # So we should probably just say "Started" and maybe DM the user or post to a channel?
        # The spec says: "When finished, send a new ephemeral follow up with summary status."
        # Ephemeral follow-ups might not work after a long time.
        # But let's try to use the interaction.followup if possible, or just accept that for very long tasks it might fail to notify.
        # For now, we'll try interaction.followup.send() which works for 15 mins. 
        # If it takes longer, we might need a different approach, but let's stick to spec.
        
        try:
            result = await loop.run_in_executor(None, run_snapraid_command, self.action_type)
            # Truncate result if too long
            if len(result) > 1900:
                result = result[:1900] + "\n... (truncated)"
            
            await interaction.followup.send(f"**SnapRAID {self.action_type} Finished**\n```\n{result}\n```", ephemeral=True)
        except Exception as e:
             await interaction.followup.send(f"SnapRAID {self.action_type} failed: {e}", ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_snapraid")
    async def cancel_callback(self, button, interaction):
        confirmation_manager.consume(self.token)
        await interaction.response.edit_message(content="Action cancelled.", view=None)

class SnapRAID(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, ctx):
        return ctx.author.id in settings.DISCORD_ADMIN_USER_IDS

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Get SnapRAID status")
    async def snapraid_status(self, ctx):
        # Safe command
        await ctx.defer(ephemeral=True)
        result = await asyncio.to_thread(run_snapraid_command, "status")
        if len(result) > 1900:
            result = result[:1900] + "\n... (truncated)"
        await ctx.respond(f"```\n{result}\n```", ephemeral=True)

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Get SnapRAID SMART stats")
    async def snapraid_smart(self, ctx):
        # Safe command
        await ctx.defer(ephemeral=True)
        result = await asyncio.to_thread(run_snapraid_command, "smart")
        if len(result) > 1900:
            result = result[:1900] + "\n... (truncated)"
        await ctx.respond(f"```\n{result}\n```", ephemeral=True)

    async def _dangerous_command(self, ctx, command_name: str, warning: str):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        token = confirmation_manager.create(ctx.author.id, command_name)
        view = SnapRAIDConfirmationView(token, command_name)
        await ctx.respond(f"{warning} Confirm?", view=view, ephemeral=True)

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Run SnapRAID sync")
    async def snapraid_sync(self, ctx):
        await self._dangerous_command(ctx, "sync", "SnapRAID sync may run for a long time and will rewrite parity.")

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Run SnapRAID scrub")
    async def snapraid_scrub(self, ctx):
        await self._dangerous_command(ctx, "scrub", "SnapRAID scrub checks data integrity.")

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Run SnapRAID fix")
    async def snapraid_fix(self, ctx):
        await self._dangerous_command(ctx, "fix", "SnapRAID fix will attempt to restore files. Ensure you know what you are doing!")

def setup(bot):
    bot.add_cog(SnapRAID(bot))
