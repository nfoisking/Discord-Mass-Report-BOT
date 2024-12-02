import discord
from discord import app_commands
import requests
import json
import threading
from colorama import Fore
from datetime import datetime

class ReportCommand(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.lock = threading.Lock()
        self.success_count = 0
        self.failed_count = 0

    def load_config(self):
        with open('./config.json', 'r') as config_file:
            config = json.load(config_file)
            self.log_channel_id = int(config['logs_ID'])
            self.authorized_ids = config.get("authorized_ids", [])

    report_reasons = {
        7: "GENERIC_SUBMIT",
        54: "SETTINGS_UPSELLS_SUCCESS",
        56: "UNDERAGE_NEEDS_MORE_INFO",
        57: "ABUSE_OR_HARASSMENT",
        60: "SHARING_PII",
        61: "SOMETHING_ELSE",
        66: "NSFW_UNWANTED",
        68: "NSFW_MINOR",
        70: "THREAT_IRL",
        71: "UNDERAGE_USER",
        73: "SELF_HARM",
        74: "EVASION_RAID",
        75: "MISINFO_EXTREMISM",
        76: "SPREADING_MISINFO",
        78: "MESSAGE_DISLIKE",
        79: "MESSAGE_SPAM",
        82: "MESSAGE_VERBAL_HARASSMENT",
        83: "MESSAGE_VULGAR_LANG",
        86: "MESSAGE_HATE_IDENTITY",
        87: "MESSAGE_GORE",
        88: "MESSAGE_NSFW_UNWANTED",
        89: "MESSAGE_NSFW_DEGRADING",
        90: "MESSAGE_REVENGE_NCP",
        91: "MESSAGE_LOLI",
        92: "MESSAGE_SEXUALIZING_MINOR",
        93: "MESSAGE_ICWM",
        94: "MESSAGE_ICAAM",
        95: "MESSAGE_CSAM",
        96: "MESSAGE_THREAT_IRL",
        97: "MESSAGE_GLORIFY_VIOLENCE",
        100: "MESSAGE_FRAUD",
        102: "MESSAGE_ATO",
        103: "MESSAGE_ILLICIT_GOODS",
        105: "MESSAGE_HACKS_CHEATS",
        106: "MESSAGE_UNDERAGE_CONFIRM",
        107: "MESSAGE_SELF_HARM_ENCOURAGE",
        108: "MESSAGE_RAID_THREAT",
        109: "MESSAGE_ACTIVE_RAID",
        110: "MESSAGE_SERVER_BAN_EVASION",
        111: "MESSAGE_USER_BAN_EVASION",
        112: "MESSAGE_HARMFUL_MISINFO",
        113: "MESSAGE_SELF_HARM_RISK",
        135: "SELF_HARM_INTERSTITIAL",
        136: "MESSAGE_IMPERSONATE_USER",
        137: "MESSAGE_IMPERSONATE_PUBLIC_FIGURE",
        138: "MESSAGE_IMPERSONATE_COMPANY",
        139: "MESSAGE_IMPERSONATE_DISCORD_EMPLOYEE",
        140: "MESSAGE_SCAM_SOCIAL_ENGINEERING"
    }

    @app_commands.command(name="report", description="Report a server with multiple tokens.")
    async def report(self, interaction: discord.Interaction, channel_id: str, message_id: str, reason_id: int, num_reports: int):
        if str(interaction.user.id) not in self.authorized_ids:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if reason_id not in self.report_reasons:
            await interaction.response.send_message("Invalid reason.", ephemeral=True)
            return

        num_tokens = len(open('./output/tokens.txt').readlines())
        embed = discord.Embed(
            description=f"**{num_reports}** reports are being sent. Using {num_tokens} tokens.",
            color=0x2b2d31
        )
        embed.set_footer(text=f"REPORT-X | github.com/nfoisking")
        await interaction.response.send_message(embed=embed, ephemeral=True)

        tokens = self.load_tokens()
        url = "https://discord.com/api/v9/reporting/message"
        data = {
            "version": "1.0",
            "variant": "6_settings_upsells_experiment",
            "language": "en",
            "breadcrumbs": [3, reason_id],
            "channel_id": channel_id,
            "message_id": message_id,
            "name": "message"
        }

        threads = []
        for _ in range(num_reports):
            for token in tokens:
                thread = threading.Thread(target=self.send_report, args=(token, url, data))
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

        await self.log_report(interaction, channel_id, message_id, reason_id)

    def load_tokens(self):
        with open('./output/tokens.txt', 'r') as file:
            return [line.strip() for line in file.readlines()]

    def send_report(self, token, url, data):
        headers = {"Content-Type": "application/json", "Authorization": token}
        response = requests.post(url, headers=headers, json=data)

        with self.lock:
            if response.status_code == 204 or response.status_code == 200:
                self.success_count += 1
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.GREEN}[SUCCESS] Report sent successfully using token: {Fore.LIGHTBLACK_EX}{token[:36]}*****")
            elif response.status_code == 429:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.YELLOW}[RATELIMIT] Token in ratelimit: {Fore.LIGHTBLACK_EX}{token[:36]}*****")
            elif response.status_code == 401:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.RED}[ERROR] Invalid token: {Fore.LIGHTBLACK_EX}{token[:36]}*****")
            else:
                print(f"{Fore.LIGHTBLACK_EX}> {Fore.RED}[ERROR] Unexpected response code with token: {Fore.LIGHTBLACK_EX}{token[:36]}*****")

    async def log_report(self, interaction, channel_id, message_id, reason_id):
        log_channel = self.bot.get_channel(self.log_channel_id)

        tokens = self.load_tokens()
        server_name = None
        if tokens:
            server_name = self.get_guild_name(tokens[0], channel_id)

        if server_name is None:
            server_name = "?"

        num_tokens = len(open('./output/tokens.txt').readlines())

        if log_channel:
            embed = discord.Embed(color=0x2b2d31)
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
            embed.set_footer(text=f"REPORT-X | github.com/nfoisking | Reported in {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            embed.add_field(name="Server:", value=f"{server_name}", inline=False)
            embed.add_field(name="Reason:", value=f"{self.report_reasons[reason_id]}", inline=False)
            embed.add_field(name="Amount of tokens:", value=f"{num_tokens}", inline=False)
            embed.add_field(name="Amount of reports:", value=f"{self.success_count}", inline=False)
            embed.add_field(name="Status:", value=":white_check_mark: ", inline=False)

            await log_channel.send(embed=embed)

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

async def setup(bot):
    await bot.add_cog(ReportCommand(bot))
