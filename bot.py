import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import asyncio


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1539972951149908018

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    try:
        test_guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=test_guild)
    except discord.Forbidden:
        print(f"Could not sync commands to guild {GUILD_ID}: missing access. "
              "Re-invite the bot with the 'applications.commands' scope, or verify GUILD_ID.")
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="play", description="Play a song or add it to the queue")
@app_commands.describe(song_query="Search query for the song to play")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()
    voice_channel = interaction.user.voice.channel
    if voice_channel is None:
        await interaction.followup.send("You are not connected to a voice channel.")
        return
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    ydl_opts = {
        'format': 'bestaudio[abr<=96]/bestaudio',
        'noplaylist': True,
        'youtube_include_dash_manifest': False,
        'youtube_include_hls_manifest': False,
    }

    query = f"ytsearch1:{song_query}"
    result = await search_ytdlp_async(query, ydl_opts)
    tracks = result.get('entries', [])

    if not tracks:
        await interaction.followup.send("No results found.")
        return

    first_track = tracks[0]
    url = first_track['url']
    title = first_track.get('title', 'Unknown Title')

    headers = first_track.get('http_headers') or {}
    header_lines = ''.join(f'{key}: {value}\r\n' for key, value in headers.items())

    before_options = ['-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5']
    if header_lines:
        before_options += ['-headers', header_lines]

    ffmepg_options = {
        'before_options': before_options,
        'options': '-vn',
    }

    def after_playing(error):
        if error:
            print(f"Playback error: {error}")

    source = discord.FFmpegOpusAudio(
        url,
        bitrate=96,
        **ffmepg_options,
        executable=r"D:\discordproject\bin\ffmpeg\ffmpeg.exe",
    )
    voice_client.play(source, after=after_playing)
    await interaction.followup.send(f"Now playing: {title}")


bot.run(TOKEN)