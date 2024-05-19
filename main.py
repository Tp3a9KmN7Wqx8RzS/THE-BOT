import os
import discord
from discord.ext import commands
import requests
import base64

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

def update_github_whitelist(hwid):
    try:
        # Construct the URL for the GitHub API request
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        print(f"Fetching file from URL: {url}")

        # Set up headers with authorization
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Discord-Bot'
        }

        # Get the current file content from GitHub
        response = requests.get(url, headers=headers)
        data = response.json()
        print(f"Received response from GitHub: {data}")

        # Decode the current content from base64
        current_content = base64.b64decode(data['content']).decode('utf-8')

        # Check if the HWID already exists
        if hwid in current_content:
            return False  # HWID already exists

        # Replace the first occurrence of ENTERHWIDHERE with the new HWID without extra quotes
        updated_content = current_content.replace("ENTERHWIDHERE", hwid, 1)

        # Encode the updated content to base64
        updated_content_base64 = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')

        # Prepare the payload for the update request
        payload = {
            'message': 'Automated update of whitelist',
            'content': updated_content_base64,
            'sha': data['sha'],
            'branch': BRANCH_NAME
        }

        # Send the update request to GitHub
        update_response = requests.put(url, headers=headers, json=payload)
        print(f"Update response from GitHub: {update_response.json()}")
        return True  # HWID added successfully
    except Exception as e:
        print(f"Error in updating GitHub whitelist: {e}")
        raise

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

def check_channel(ctx):
    return ctx.channel.id == ALLOWED_CHANNEL_ID

@bot.command(name='addhwid')
@commands.check(check_channel)
async def add_hwid(ctx, hwid: str):
    print(f"Command received: addhwid {hwid}")
    try:
        if update_github_whitelist(hwid):
            await ctx.send(f"HWID {hwid} has been added to the whitelist.")
            print(f"HWID {hwid} approved and added to the whitelist.")
        else:
            await ctx.send(f"HWID {hwid} already exists in the whitelist.")
            print(f"HWID {hwid} already exists in the whitelist.")
    except Exception as e:
        await ctx.send(f"Failed to add HWID: {str(e)}")
        print(f"Error while adding HWID {hwid}: {str(e)}")

@add_hwid.error
async def permission_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("This command cannot be used in this channel.")

bot.run(DISCORD_BOT_TOKEN)
