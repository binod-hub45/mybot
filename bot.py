import discord
from discord.ext import commands
import random
import os

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

@bot.command(name="startguess")
@commands.has_permissions(manage_channels=True)
async def startguess(ctx, min_num: int = 1, max_num: int = 50000):
    """Start a guess-the-number event. Usage: !startguess 1 50000"""
    global secret_number, game_channel_id, game_active

    if game_active:
        await ctx.send("A guess event is already running!")
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
            f"**Range:** `{min_num}` – `{max_num}`\n\n"
            f"Type a number in this channel to guess.\n"
            f"First person to guess correctly wins and the channel will be locked!"
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)
    print(f"[DEBUG] Secret number: {secret_number}")  # Only visible in logs

@bot.event
async def on_message(message):
    global game_active, secret_number, game_channel_id

    if message.author.bot:
        return

    # Process guesses only when game is active in the correct channel
    if game_active and message.channel.id == game_channel_id:
        content = message.content.strip()

        if content.isdigit():
            guess = int(content)

            if guess == secret_number:
                # Correct guess!
                await message.channel.send(
                    f"{message.author.mention} you've guessed correct **{secret_number}**.\n"
                    f"Guess event ended. Channel is locked now."
                )

                # Lock the channel for @everyone
                overwrite = message.channel.overwrites_for(message.guild.default_role)
                overwrite.send_messages = False
                await message.channel.set_permissions(
                    message.guild.default_role, overwrite=overwrite
                )

                # Reset game state
                game_active = False
                secret_number = None
                game_channel_id = None
                return

    # Always process commands
    await bot.process_commands(message)

# Run the bot
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set!")
bot.run(TOKEN)
