import discord
from discord import app_commands, Embed
import requests
import json
import re
import threading
import asyncio
from colorama import Fore
from datetime import datetime

class MonitorCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.lock = threading.Lock()

    def load_config(self):
        with open('./config.json', 'r') as config_file:
            config = json.load(config_file)
            self.log_channel_id = int(config['logs_ID'])
            self.authorized_ids = config.get("authorized_ids", [])

    @app_commands.command(name="monitor", description="Monitor a server and report messages..")
    async def monitorar(self, interaction: discord.Interaction, channel_id: str):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        num_tokens = len(open('./output/tokens.txt').readlines())

        embed = discord.Embed(
            description=f"Monitoring started! Using: **{num_tokens}** tokens.",
            color=0x2b2d31
        )
        embed.set_footer(text=f"REPORT-X | github.com/nfoisking")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        await self.start_monitoring(channel_id)

    async def start_monitoring(self, channel_id):
        while True:
            await self.check_messages(channel_id)
            await asyncio.sleep(10)

    async def check_messages(self, channel_id):
        tokens = self.load_tokens()
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"

        for token in tokens:
            headers = {"Authorization": token}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                messages = response.json()
                for message in messages:
                    await self.process_message(message)
            else:
                print(f"{Fore.RED}[ERROR] Unable to get messages: {response.status_code} using token {token[:36]}*****")
                if response.status_code == 404:
                    print(f"{Fore.RED}The channel may not exist or may be inaccessible.")
                elif response.status_code == 403:
                    print(f"{Fore.RED}The token may not have permission to access this channel.")

    async def process_message(self, message):
        author = message.get('author', {})
        if author.get('bot', False):
            return

        content = message.get('content', '').lower()
        message_id = message.get('id')

        if self.check_for_underage(content):
            await self.report(message.get('channel_id'), content, 71, message_id)
        elif self.check_for_doxxing(content):
            await self.report(message.get('channel_id'), content, 60, message_id)
        elif self.check_for_illicit_goods(content):
            await self.report(message.get('channel_id'), content, 103, message_id)

    def check_for_underage(self, content):
        return re.search(r'\b(0?[0-9]|1[0-2])\s*anos?\b', content) is not None

    def check_for_doxxing(self, content):
        return re.search(r'(cpf|nome|endereço|telefone|e-mail|rg):?\s*\S+', content) is not None

    def check_for_illicit_goods(self, content):
        return re.search(r'\b(vendo|compro|troco|negócio)\b', content) is not None

    async def report(self, channel_id, content, reason_id, message_id):
        tokens = self.load_tokens()
        url = "https://discord.com/api/v9/reporting/message"

        threads = []
        for token in tokens:
            thread = threading.Thread(target=self.send_report, args=(token, url, channel_id, reason_id, content, message_id))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def load_tokens(self):
        with open('./output/tokens.txt', 'r') as file:
            return [line.strip() for line in file.readlines()]

    def send_report(self, token, url, channel_id, reason_id, content, message_id):
        headers = {"Content-Type": "application/json", "Authorization": token}
        guild_name = self.get_guild_name(token, channel_id)

        data = {
            "version": "1.0",
            "variant": "6_settings_upsells_experiment",
            "language": "en",
            "breadcrumbs": [3, reason_id],
            "channel_id": channel_id,
            "message_id": message_id,
            "name": "message"
        }

        response = requests.post(url, headers=headers, json=data)

        with self.lock:
            if response.status_code == 204 or response.status_code == 200:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.GREEN}[SUCCESS] Report sent successfully using token: {Fore.LIGHTBLACK_EX}{token[:36]}*****")
                if guild_name:
                    asyncio.run_coroutine_threadsafe(self.log_report(guild_name, channel_id, reason_id, content), self.bot.loop)
            elif response.status_code == 429:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.YELLOW}[RATELIMIT] Token in ratelimit: {Fore.LIGHTBLACK_EX}{token[:36]}*****")
            elif response.status_code == 401:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.RED}[ERROR] Invalid token: {Fore.LIGHTBLACK_EX}{token[:36]}*****")
            else:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.RED}[ERROR] Unexpected response code with token: {Fore.LIGHTBLACK_EX}{token[:36]}***** {response.text}")

    def get_guild_name(self, token, channel_id):
        headers = {"Authorization": token}
        url = f"https://discord.com/api/v9/channels/{channel_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            channel_data = response.json()
            guild_id = channel_data.get("guild_id")
            if guild_id:
                guild_url = f"https://discord.com/api/v9/guilds/{guild_id}"
                guild_response = requests.get(guild_url, headers=headers)
                if guild_response.status_code == 200:
                    guild_data = guild_response.json()
                    return guild_data.get("name")
        return None

    async def log_report(self, server_name, channel_id, reason_id, content):
        log_channel = self.bot.get_channel(self.log_channel_id)
        num_tokens = len(open('./output/tokens.txt').readlines())


        if log_channel:
            embed = discord.Embed(color=0x2b2d31)
            embed.add_field(name="Server:", value=server_name, inline=False)
            embed.add_field(name="Channel:", value=f"<#{channel_id}>", inline=False)
            embed.add_field(name="Reason:", value=self.get_reason_name(reason_id), inline=False)
            embed.add_field(name="Amount of tokens:", value=f"{num_tokens}", inline=False)
            embed.add_field(name="Content:", value=content, inline=False)
            embed.add_field(name="Status:", value=":white_check_mark: ", inline=False)
            embed.set_footer(text=f"REPORT-X | github.com/nfoisking | Reported in {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            await log_channel.send(embed=embed)

    def get_reason_name(self, reason_id):
        reason_mapping = {
            71: "UNDERAGE_USER",
            60: "SHARING_PII",
            103: "MESSAGE_ILLICIT_GOODS"
        }
        return reason_mapping.get(reason_id, "xd")

async def setup(bot):
    await bot.add_cog(MonitorCommand(bot))