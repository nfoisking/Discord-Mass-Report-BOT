import discord
from discord import app_commands
import concurrent.futures
import random
import string
import tls_client
import json

class Joiner:
    def __init__(self, data) -> None:
        self.session = data['client']
        self.session.headers = data['headers']
        self.get_cookies()
        self.instance = data

    def rand_str(self, length: int) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_cookies(self) -> None:
        site = self.session.get("https://discord.com")
        self.session.cookies = site.cookies

    def get_account_info(self) -> dict:
        self.session.headers.update({"Authorization": self.instance['token']})
        result = self.session.get("https://discord.com/api/v9/users/@me")
        return result.json()

    def join(self) -> bool:
        self.session.headers.update({"Authorization": self.instance['token']})
        result = self.session.post(f"https://discord.com/api/v9/invites/{self.instance['invite']}", json={
            'session_id': self.rand_str(32),
        })

        if result.status_code == 200:
            return True
        elif result.status_code == 404:
            return False
        elif result.status_code == 401:
            return False
        else:
            return False

class JoinServerCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open("./config.json") as f:
            self.config = json.load(f)
        self.authorized_ids = self.config.get("authorized_ids", [])

    @app_commands.command(name="joinserver", description="Join a server using an invite link.")
    async def joinserver(self, interaction: discord.Interaction, invite: str):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        with open("./output/tokens.txt") as file:
            tokens = [line.strip() for line in file]

        instances = []
        max_threads = 5

        invite_code = invite.split("/")[-1]

        for token_ in tokens:
            header = {
                "User-Agent": f"DiscordBot {random.randint(110, 115)}"
            }
            instances.append({
                'client': tls_client.Session(
                    client_identifier=f"chrome_{random.randint(110, 115)}",
                    random_tls_extension_order=True,
                ),
                'token': token_,
                'headers': header,
                'invite': invite_code,
            })

        success_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_instance = {executor.submit(Joiner(i).join): i for i in instances}
            for future in concurrent.futures.as_completed(future_to_instance):
                if future.result():
                    success_count += 1

        await interaction.response.send_message(f"Amount of tokens that managed to enter the server: **{success_count}**", ephemeral=True)

async def setup(bot):
    await bot.add_cog(JoinServerCommand(bot))
