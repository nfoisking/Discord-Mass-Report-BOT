import discord
from discord import app_commands
import requests
import json
import os
from colorama import Fore
from discord import Embed


class TokenChecker(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open('./config.json', 'r') as config_file:
            config = json.load(config_file)
            self.authorized_ids = config.get("authorized_ids", [])

    @app_commands.command(name="checker", description="Check all tokens and remove invalid ones.")
    async def checker(self, interaction: discord.Interaction):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.send_message("Starting token verification...", ephemeral=True)

        valid_tokens = []
        with open('./output/tokens.txt', 'r') as file:
            tokens = [line.strip() for line in file.readlines()]

        for token in tokens:
            if self.is_token_valid(token):
                valid_tokens.append(token)
            else:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.GREEN}[SUCCESS] Invalid token removed: {Fore.LIGHTBLACK_EX}{token[:36]}*****")

        with open('./output/tokens.txt', 'w') as file:
            for token in valid_tokens:
                file.write("\n" + token)

        embed = Embed(
            description=f"Remaining valid tokens: {len(valid_tokens)}.",
            color=0x2b2d31
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

    def is_token_valid(self, token):
        headers = {"Authorization": token}
        response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
        return response.status_code == 200

async def setup(bot):
    await bot.add_cog(TokenChecker(bot))
