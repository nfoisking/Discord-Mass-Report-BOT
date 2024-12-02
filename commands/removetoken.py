import discord
from discord import app_commands
import json

class RemoveTokenCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open("./config.json") as f:
            self.config = json.load(f)
        self.authorized_ids = self.config.get("authorized_ids", [])

    @app_commands.command(name="removetoken", description="Remove an existing token.")
    async def removetoken(self, interaction: discord.Interaction, token: str):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        with open("./output/tokens.txt", "r") as f:
            tokens = f.readlines()

        if token + "\n" not in tokens:
            await interaction.response.send_message("This token was not found in **tokens.txt**.", ephemeral=True)
            return

        tokens = [t for t in tokens if t.strip() != token]

        with open("./output/tokens.txt", "w") as f:
            for t in tokens:
                f.write(t)

        await interaction.response.send_message("The token was successfully removed from **tokens.txt**.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RemoveTokenCommand(bot))
