# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Transcriber is a FastAPI web application that extracts transcripts from YouTube videos using two approaches:
1. **Primary**: YouTube Transcript API for videos with existing captions
2. **Fallback**: yt-dlp + OpenAI Whisper for audio transcription when captions aren't available

## Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the FastAPI server
python main.py
# Server runs on http://localhost:8000

# Alternative: Run with Uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Test the API endpoint
python debug_api.py

# Test the transcription pipeline
python debug_repro.py
```

## Architecture

### Core Flow (main.py)
The application follows a two-tier transcription strategy:

1. **Video ID Extraction** (`extract_video_id()`): Parses YouTube URLs using regex patterns
2. **Transcription Attempt 1** (YouTube API):
   - Uses `YouTubeTranscriptApi.get_transcript()` to fetch existing captions
   - Fast, no downloads required
3. **Transcription Attempt 2** (Whisper fallback):
   - Downloads audio via `yt-dlp` to temporary file (`download_audio()`)
   - Transcribes using OpenAI Whisper base model (`transcribe_audio()`)
   - Runs in thread pools via `asyncio.to_thread()` to avoid blocking
   - Cleans up temporary audio files after transcription

### Key Design Decisions

- **Dual Transcription Strategy**: The `/api/transcribe` endpoint catches ANY exception from the YouTube API (not just specific errors) and immediately falls back to Whisper. This ensures maximum success rate.

- **Async Thread Execution**: Both `download_audio()` and `transcribe_audio()` are CPU/IO-bound blocking operations wrapped with `asyncio.to_thread()` to prevent blocking the FastAPI event loop.

- **Transcript Persistence**: All transcripts are automatically saved to `transcripts/{video_id}.txt` for backup via `save_transcript_to_file()`.

- **Temporary File Management**: Audio files are downloaded to system temp directory and cleaned up in the `finally` block of the endpoint.

### API Endpoint

**POST /api/transcribe**
- Request: `{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}`
- Response: `{"transcript": "...", "video_id": "VIDEO_ID"}`
- Errors: 400 for invalid URLs, 500 for transcription failures

### Frontend Structure

- `static/index.html`: Single-page UI with gradient background
- `static/app.js`: Handles API calls, copy/download functionality
- `static/style.css`: Modern styling with gradient theme

### Logging

Comprehensive logging throughout main.py:
- Application startup events
- Transcription method attempts (API vs Whisper)
- File save operations
- Exception details

Logs are configured to stream to stdout with timestamps and severity levels.

### Dependencies

- **FastAPI + Uvicorn**: Web framework and ASGI server
- **youtube-transcript-api**: Fetches existing video captions
- **yt-dlp**: Downloads YouTube audio (requires FFmpeg)
- **openai-whisper**: Speech-to-text transcription model
- **torch**: Required by Whisper (CPU inference)

**Note**: FFmpeg must be installed separately and available in system PATH for yt-dlp to extract audio.

## Development Notes

- The Whisper "base" model is used for balance between speed and accuracy
- Transcription can be slow for long videos (Whisper processes audio in real-time or slower)
- The application expects FFmpeg to be installed for audio extraction
- Debug scripts (`debug_api.py`, `debug_repro.py`) are for manual testing
