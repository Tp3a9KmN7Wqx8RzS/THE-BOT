from keep_alive import keep_alive
keep_alive()

import os
import discord
from discord.ext import commands
import requests
import base64
import json
import secrets
import string

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
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        content = base64.b64decode(data['content']).decode('utf-8')
        sha = data['sha']
        return content, sha
    except requests.exceptions.RequestException as e:
        print(f"HTTP error occurred: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def update_github_content(content, sha):
    try:
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
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"HTTP error occurred: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def generate_key(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for i in range(length))

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

def check_channel(ctx):
    return ctx.channel.id == ALLOWED_CHANNEL_ID

@bot.command(name='addhwid')
@commands.check(check_channel)
async def add_hwid(ctx, hwid: str, key: str):
    print(f"Command received: addhwid {hwid} with key {key}")
    try:
        content, sha = fetch_github_content()
        data = json.loads(content)
        
        # Initialize lists if not present
        if 'whitelistedHWIDs' not in data:
            data['whitelistedHWIDs'] = []
        if 'keys' not in data:
            data['keys'] = []
        
        if key in data['keys']:
            if hwid not in data['whitelistedHWIDs']:
                data['whitelistedHWIDs'].append(hwid)
                data['keys'].remove(key)  # Remove the key after use
                update_github_content(json.dumps(data, indent=2), sha)
                await ctx.send(f"HWID {hwid} has been added to the whitelist.")
                print(f"HWID {hwid} approved and added to the whitelist.")
            else:
                await ctx.send(f"HWID {hwid} already exists in the whitelist.")
                print(f"HWID {hwid} already exists in the whitelist.")
        else:
            await ctx.send(f"Invalid key.")
            print(f"Invalid key used: {key}")
    except Exception as e:
        await ctx.send(f"Failed to add HWID: {str(e)}")
        print(f"Error while adding HWID {hwid}: {str(e)}")

@bot.command(name='genkey')
@commands.check(check_channel)
async def gen_key(ctx):
    print("Command received: genkey")
    try:
        new_key = generate_key()
        content, sha = fetch_github_content()
        data = json.loads(content)
        
        # Initialize lists if not present
        if 'whitelistedHWIDs' not in data:
            data['whitelistedHWIDs'] = []
        if 'keys' not in data:
            data['keys'] = []
        
        data['keys'].append(new_key)
        update_github_content(json.dumps(data, indent=2), sha)
        await ctx.send(f"Generated new key: {new_key}")
        print(f"Generated new key: {new_key}")
    except Exception as e:
        await ctx.send(f"Failed to generate key: {str(e)}")
        print(f"Error while generating key: {str(e)}")

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
