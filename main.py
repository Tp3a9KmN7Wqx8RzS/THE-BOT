from keep_alive import keep_alive
keep_alive()

import os
import discord
from discord.ext import commands

# Get the bot token from the environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True  # You need this intent to send DMs
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.command()
async def dm(ctx, user_id: int, *, message: str):
    user = await bot.fetch_user(user_id)
    if user:
        try:
            await user.send(message)
            await ctx.send(f'Message sent to {user.name}')
        except discord.Forbidden:
            await ctx.send('I do not have permission to send a message to this user.')
        except discord.HTTPException:
            await ctx.send('Failed to send the message due to an unknown error.')
    else:
        await ctx.send('User not found.')

# Run the bot
bot.run(TOKEN)
