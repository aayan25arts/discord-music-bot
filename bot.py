import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
import asyncio
from collections import deque


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1539972951149908018

SONG_QUEUE = {}

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

    guild_id = str(interaction.guild.id)
    if SONG_QUEUE.get(guild_id) is None:
        SONG_QUEUE[guild_id] = deque()

    SONG_QUEUE[guild_id].append((url, title, header_lines))

    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: {title}")
    else:
        await interaction.followup.send(f"Now playing: {title}")
        await play_next_song(voice_client, guild_id, interaction.channel)

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipping the current song.")    
    else:
        await interaction.response.send_message("No song is currently playing.")


@bot.tree.command(name="pause", description="Pause the music.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("The bot is not connected to a voice channel.")

    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")

    voice_client.pause()
    await interaction.response.send_message("Paused the music.")

@bot.tree.command(name="resume", description="Resume the paused music.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("The bot is not connected to a voice channel.")

    if not voice_client.is_paused():
        return await interaction.response.send_message("The music is not paused.")

    voice_client.resume()
    await interaction.response.send_message("Resumed the music.")

@bot.tree.command(name="stop", description="Stop the music and clear the queue.")
async def stop(interaction: discord.Interaction):   
    await interaction.response.defer()
    voice_client = interaction.guild.voice_client

    if not voice_client or not voice_client.is_connected():
        return await interaction.followup.send("The bot is not connected to a voice channel.")

    guild_id_str = str(interaction.guild.id)
    if guild_id_str in SONG_QUEUE:
        SONG_QUEUE[guild_id_str].clear()

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await voice_client.disconnect()
    await interaction.followup.send("Stopped the music")

async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUE[guild_id]:
        url, title, header_lines = SONG_QUEUE[guild_id].popleft()

        before_options = ['-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5']
        if header_lines:
            before_options += ['-headers', header_lines]

        ffmepg_options = {
                'before_options': before_options,
                'options': '-vn',
            }

        source = discord.FFmpegOpusAudio(
                url,
                bitrate=96,
                **ffmepg_options,
                executable=r"D:\discordproject\bin\ffmpeg\ffmpeg.exe",
            )

        def after_playing(error):
            if error:
                print(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_playing)
        asyncio.create_task(channel.send(f"Now playing: {title}"))

    else:
        await voice_client.disconnect()
        SONG_QUEUE[guild_id] = deque()

bot.run(TOKEN)