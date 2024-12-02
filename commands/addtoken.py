import discord
from discord import app_commands
import json

class TokenCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open("./config.json") as f:
            self.config = json.load(f)
        self.authorized_ids = self.config.get("authorized_ids", [])

    @app_commands.command(name="addtoken", description="Add a new token.")
    async def addtoken(self, interaction: discord.Interaction, token: str):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        with open("./output/tokens.txt", "a") as f:
            f.write("\n" + token)

        await interaction.response.send_message("Token successfully added to **tokens.txt**.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TokenCommand(bot))
