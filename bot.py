import discord
from discord.ext import commands
import random
import os
import re

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Game state
secret_number = None
game_channel_id = None
game_active = False

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Bot is ready!")

@bot.command(name="setnumber")
@commands.has_permissions(manage_channels=True)
async def setnumber(ctx, number: int):
    """Set a specific number and start the event. Usage: !setnumber 69420"""
    global secret_number, game_channel_id, game_active
    if game_active:
        await ctx.send("A guess event is already running! Use !stopguess first.")
        return
    secret_number = number
    game_channel_id = ctx.channel.id
    game_active = True
    embed = discord.Embed(
        title="🎯 Guess the Number Event Started!",
        description=(
            f"A secret number has been set.\n\n"
            f"**Rules:**\n"
            f"• Only pure numbers are allowed\n"
            f"• Anything else will be deleted\n"
            f"• First correct guess wins and channel gets locked!"
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    print(f"[DEBUG] Secret number set to: {secret_number}")

@bot.command(name="setrandom")
@commands.has_permissions(manage_channels=True)
async def setrandom(ctx, min_num: int = 1, max_num: int = 50000):
    """Bot chooses a random number in the given range. Usage: !setrandom 1 50000"""
    global secret_number, game_channel_id, game_active
    if game_active:
        await ctx.send("A guess event is already running! Use !stopguess first.")
        return
    if min_num >= max_num:
        await ctx.send("Min number must be smaller than max number.")
        return
    secret_number = random.randint(min_num, max_num)
    game_channel_id = ctx.channel.id
    game_active = True
    embed = discord.Embed(
        title="🎯 Guess the Number Event Started!",
        description=(
            f"**Range:** {min_num} – {max_num}\n\n"
            f"**Rules:**\n"
            f"• Only pure numbers are allowed\n"
            f"• Anything else will be deleted\n"
            f"• First correct guess wins and channel gets locked!"
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    print(f"[DEBUG] Secret number set to: {secret_number}")

@bot.command(name="stopguess")
@commands.has_permissions(manage_channels=True)
async def stopguess(ctx):
    """Stop the current guess event and lock the channel."""
    global secret_number, game_channel_id, game_active
    if not game_active:
        await ctx.send("There is no active guess event.")
        return
    # Lock the channel
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(
        f"🛑 Guess event stopped by {ctx.author.mention}.\n"
        f"The secret number was **{secret_number}**.\n"
        f"Channel has been locked."
    )
    # Reset game state
    game_active = False
    secret_number = None
    game_channel_id = None

@bot.command(name="ping")
async def ping(ctx):
    """Check if bot is responding"""
    await ctx.send(f"Pong! Latency: {round(bot.latency * 1000)}ms")

@bot.event
async def on_message(message):
    global game_active, secret_number, game_channel_id
    
    if message.author.bot:
        return
    
    # First, check if it's a command
    if message.content.startswith('!'):
        await bot.process_commands(message)
        return
    
    # Only enforce rules if game is active in this channel
    if game_active and message.channel.id == game_channel_id:
        # Allow people with Manage Channels permission to talk freely
        if message.author.guild_permissions.manage_channels:
            return
        
        content = message.content.strip()
        
        # Check if the message is a pure number (only digits)
        is_pure_number = bool(re.fullmatch(r"\d+", content))
        
        # Also block attachments, stickers, embeds, etc.
        has_extra = (
            len(message.attachments) > 0 or
            len(message.stickers) > 0 or
            len(message.embeds) > 0
        )
        
        if not is_pure_number or has_extra:
            try:
                await message.delete()
            except:
                pass
            return
        
        # It's a pure number → check if correct
        guess = int(content)
        if guess == secret_number:
            await message.channel.send(
                f"{message.author.mention} you've guessed correct **{secret_number}**.\n"
                f"Guess event ended. Channel is locked now."
            )
            # Lock the channel
            overwrite = message.channel.overwrites_for(message.guild.default_role)
            overwrite.send_messages = False
            await message.channel.set_permissions(
                message.guild.default_role, overwrite=overwrite
            )
            # Reset game
            game_active = False
            secret_number = None
            game_channel_id = None
            return

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set!")
bot.run(TOKEN)
