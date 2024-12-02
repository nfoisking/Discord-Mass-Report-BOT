import discord
from discord import app_commands
import json

class AddIDCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open("./config.json") as f:
            self.config = json.load(f)
        self.authorized_ids = self.config.get("authorized_ids", [])

    def save_config(self):
        with open("./config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    @app_commands.command(name="add-adm", description="Add a new admin.")
    async def add_id(self, interaction: discord.Interaction, new_id: str):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if new_id in self.authorized_ids:
            await interaction.response.send_message("This ID is already an administrator.", ephemeral=True)
            return

        self.authorized_ids.append(new_id)
        self.config["authorized_ids"] = self.authorized_ids
        self.save_config()

        await interaction.response.send_message(f"ID **{new_id}** added to admin list successfully!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AddIDCommand(bot))
