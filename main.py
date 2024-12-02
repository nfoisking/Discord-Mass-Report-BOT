import discord
from discord.ext import commands
import json
import os
from colorama import Fore, Style, init

with open('config.json') as f:
    config = json.load(f)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), application_id="1301651648476745818")

    async def setup_hook(self):
        for filename in os.listdir('./commands'):
            if filename.endswith('.py'):
                await self.load_extension(f'commands.{filename[:-3]}')

        await self.tree.sync()

bot = MyBot()
author = "github.com/nfoisking"

@bot.event
async def on_ready():
    os.system("cls && title REPORT-X ^| Connected")
    print(f"""
        {Fore.RED}██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗  {Fore.YELLOW}██╗  ██╗
        {Fore.RED}██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝  {Fore.YELLOW}╚██╗██╔
        {Fore.RED}██████╔╝█████╗  ██████╔╝██║   ██║██████╔╝   ██║█████╗{Fore.YELLOW}╚███╔╝
        {Fore.RED}██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██╔══██╗   ██║╚════╝{Fore.YELLOW}██╔██╗
        {Fore.RED}██║  ██║███████╗██║     ╚██████╔╝██║  ██║   ██║     {Fore.YELLOW}██╔╝ ██
        {Fore.RED}╚═╝  ╚═╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝     {Fore.YELLOW}╚═╝  ╚═╝
                                                        """)
    print(f"         {Fore.LIGHTBLACK_EX}> {Fore.WHITE}Connected on {Fore.YELLOW}{bot.user.name}")
    print(f"         {Fore.LIGHTBLACK_EX}> {Fore.WHITE}Created and developed by {Fore.YELLOW}{author}")
    print("\n")
    game = discord.Game("REPORT-X")
    await bot.change_presence(activity=game)

bot.run(config['token'])
