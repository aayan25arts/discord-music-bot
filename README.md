# Discord Music Bot

A Discord bot that plays audio from YouTube (via `yt-dlp`) in a voice channel, with a per-server song queue.

## Features

- Slash commands, synced both globally and to a configured guild for fast local testing
- `/play` — search YouTube and play a song, or add it to the queue if something is already playing
- `/skip` — skip the current song
- `/pause` / `/resume` — pause and resume playback
- `/stop` — stop playback, clear the queue, and disconnect from voice
- Per-guild song queues, so multiple servers can play independently

## Requirements

- Python 3.12+
- [ffmpeg](https://ffmpeg.org/) (a Windows build is bundled under [bin/ffmpeg/](bin/ffmpeg/))
- A Discord bot application/token with the `applications.commands` and `bot` scopes, and the **Message Content** privileged intent enabled

## Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your bot token:

   ```
   DISCORD_TOKEN=your-bot-token-here
   ```

4. Set `GUILD_ID` in [bot.py](bot.py) to your test server's ID (used for fast per-guild slash command sync).

5. Update the `executable` path passed to `discord.FFmpegOpusAudio` in [bot.py](bot.py) if your `ffmpeg.exe` lives somewhere other than [bin/ffmpeg/ffmpeg.exe](bin/ffmpeg/ffmpeg.exe).

## Running

```powershell
.venv\Scripts\python.exe bot.py
```

## Usage

Join a voice channel in your server, then use the slash commands:

| Command | Description |
|---|---|
| `/play <song_query>` | Search and play a song, or queue it if one is already playing |
| `/skip` | Skip the currently playing song |
| `/pause` | Pause playback |
| `/resume` | Resume paused playback |
| `/stop` | Stop playback, clear the queue, and leave the voice channel |

## Project Structure

- [bot.py](bot.py) — bot entry point, slash commands, and playback/queue logic
- [requirements.txt](requirements.txt) — Python dependencies
- [bin/ffmpeg/](bin/ffmpeg/) — bundled ffmpeg binaries used for audio transcoding
- `.env` — local secrets (not committed; holds `DISCORD_TOKEN`)
