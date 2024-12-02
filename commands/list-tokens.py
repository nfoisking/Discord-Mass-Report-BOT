import discord
from discord import app_commands
import json

class StockCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open("./config.json") as f:
            self.config = json.load(f)
        self.authorized_ids = self.config.get("authorized_ids", [])

    @app_commands.command(name="list-tokens", description="Send the list of tokens.")
    async def stock(self, interaction: discord.Interaction):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        with open("./output/tokens.txt", "r") as file:
            tokens = file.read()

        await interaction.response.send_message(f"```\n{tokens}\n```", ephemeral=True)

async def setup(bot):
    await bot.add_cog(StockCommand(bot))
