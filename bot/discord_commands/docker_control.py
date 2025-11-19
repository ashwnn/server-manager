import discord
from discord.ext import commands
from discord.commands import slash_command
from discord.ui import View, Button
from config import settings
from services.docker_client import docker_service
from services.confirmations import confirmation_manager

class ConfirmationView(View):
    def __init__(self, token: str, action_type: str):
        super().__init__(timeout=120)
        self.token = token
        self.action_type = action_type

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm_action")
    async def confirm_callback(self, button, interaction):
        # Verify ownership of the action
        action = confirmation_manager.consume(self.token)
        if not action:
            await interaction.response.edit_message(content="Action expired or already used.", view=None)
            return

        if interaction.user.id != action["user_id"]:
             await interaction.response.send_message("You cannot confirm this action.", ephemeral=True)
             return

        await interaction.response.defer() # Acknowledge interaction

        # Execute action
        if self.action_type == "docker_pause_all":
            count = docker_service.pause_all()
            await interaction.edit_original_response(content=f"Success: Paused {count} containers.", view=None)
        elif self.action_type == "docker_resume_all":
            count = docker_service.resume_all()
            await interaction.edit_original_response(content=f"Success: Resumed {count} containers.", view=None)
        else:
             await interaction.edit_original_response(content="Unknown action.", view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_action")
    async def cancel_callback(self, button, interaction):
        confirmation_manager.consume(self.token) # Consume to invalidate
        await interaction.response.edit_message(content="Action cancelled.", view=None)


class DockerControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, ctx):
        return ctx.author.id in settings.DISCORD_ADMIN_USER_IDS

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Pause all Docker containers")
    async def docker_pause_all(self, ctx):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        token = confirmation_manager.create(ctx.author.id, "docker_pause_all")
        view = ConfirmationView(token, "docker_pause_all")
        await ctx.respond("This will pause all running Docker containers on the host. Confirm?", view=view, ephemeral=True)

    @slash_command(guild_ids=[settings.DISCORD_GUILD_ID], description="Resume all Docker containers")
    async def docker_resume_all(self, ctx):
        if not self.is_admin(ctx):
            await ctx.respond("You are not authorized to use this command.", ephemeral=True)
            return

        token = confirmation_manager.create(ctx.author.id, "docker_resume_all")
        view = ConfirmationView(token, "docker_resume_all")
        await ctx.respond("This will resume all paused Docker containers on the host. Confirm?", view=view, ephemeral=True)

def setup(bot):
    bot.add_cog(DockerControl(bot))
