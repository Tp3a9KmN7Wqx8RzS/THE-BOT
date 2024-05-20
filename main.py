from keep_alive import keep_alive
keep_alive()

import os
import discord
from discord.ext import commands
import requests
import base64
import random

# Fetch tokens from environment variables
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Ensure the tokens are not None
if not DISCORD_BOT_TOKEN or not GITHUB_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN or GITHUB_TOKEN is not set in the environment variables.")

# Define the repository details
REPO_OWNER = 'Tp3a9KmN7Wqx8RzS'  # GitHub username or organization
REPO_NAME = 'List'  # Repository name
FILE_PATH = 'Whitelist'  # File path within the repository
BRANCH_NAME = 'main'  # Branch name

# Define the channel ID where the bot should listen
ALLOWED_CHANNEL_ID = 1240916482192576542  # Replace with your channel ID

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_github_content():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Discord-Bot'
    }
    response = requests.get(url, headers=headers)
    print(f"GitHub API response status code: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"Failed to fetch GitHub content: {response.status_code} {response.text}")
    data = response.json()
    print(f"GitHub API response data: {data}")
    content = base64.b64decode(data['content']).decode('utf-8')
    sha = data['sha']
    return content, sha

def update_github_content(content, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Discord-Bot'
    }
    updated_content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {
        'message': 'Automated update of whitelist',
        'content': updated_content_base64,
        'sha': sha,
        'branch': BRANCH_NAME
    }
    response = requests.put(url, headers=headers, json=payload)
    print(f"GitHub update response status code: {response.status_code}")
    print(f"GitHub update response data: {response.text}")
    if response.status_code != 200:
        raise Exception(f"Failed to update GitHub content: {response.status_code} {response.text}")
    return response.json()

def generate_key(length=18):
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    return ''.join(random.choice(characters) for i in range(length))

def parse_content(content):
    content_dict = {
        "whitelistedHWIDs": [],
        "keys": []
    }
    lines = content.split("\n")
    current_key = None
    for line in lines:
        line = line.strip()
        if line.startswith("whitelistedHWIDs"):
            current_key = "whitelistedHWIDs"
        elif line.startswith("keys"):
            current_key = "keys"
        elif line.startswith("}") or line == "":
            continue
        elif current_key and line.endswith(","):
            line = line[:-1]
            content_dict[current_key].append(line.strip('"'))
    return content_dict

def dict_to_content(content_dict):
    content = "return {\n"
    for key, values in content_dict.items():
        content += f"  {key} = {{\n"
        for value in values:
            content += f'    "{value}",\n'
        content += "  },\n"
    content += "}\n"
    return content

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

def check_channel(ctx):
    return ctx.channel.id == ALLOWED_CHANNEL_ID

@bot.command(name='addhwid')
@commands.check(check_channel)
async def add_hwid(ctx, hwid: str, key: str):
    try:
        content, sha = fetch_github_content()
        data = parse_content(content)

        if key in data['keys']:
            if hwid not in data['whitelistedHWIDs']:
                data['whitelistedHWIDs'].append(hwid)
                data['keys'].remove(key)  # Remove the key after use
                updated_content = dict_to_content(data)
                update_github_content(updated_content, sha)
                await ctx.send(f"HWID {hwid} has been added to the whitelist.")
            else:
                await ctx.send(f"HWID {hwid} already exists in the whitelist.")
        else:
            await ctx.send(f"Invalid key.")
    except Exception as e:
        await ctx.send(f"Failed to add HWID: {str(e)}")

@bot.command(name='genkey')
@commands.check(check_channel)
async def gen_key(ctx):
    try:
        new_key = generate_key()
        content, sha = fetch_github_content()
        data = parse_content(content)

        data['keys'].append(new_key)
        updated_content = dict_to_content(data)
        update_github_content(updated_content, sha)
        await ctx.send(f"Generated new key: {new_key}")
    except Exception as e:
        await ctx.send(f"Failed to generate key: {str(e)}")

@add_hwid.error
async def permission_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You are not authorized to use this command in this channel.")

# Listen for messages and trigger the addhwid command
@bot.event
async def on_message(message):
    if message.channel.id == ALLOWED_CHANNEL_ID and message.author.bot:
        if message.content.startswith("!addhwid "):
            parts = message.content.split(" ")
            if len(parts) == 3:
                hwid = parts[1]
                key = parts[2]
                ctx = await bot.get_context(message)
                await add_hwid(ctx, hwid, key)
    await bot.process_commands(message)

bot.run(DISCORD_BOT_TOKEN)
