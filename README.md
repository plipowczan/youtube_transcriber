# YouTube Transcriber

A FastAPI web application that extracts transcripts from YouTube videos using intelligent dual-method transcription.

## Features

- **Dual Transcription Strategy**:
  - Primary: Fetches existing captions via YouTube Transcript API (instant)
  - Fallback: Downloads audio and transcribes with OpenAI Whisper (when captions unavailable)
- **Modern Web Interface**: Clean, responsive UI with gradient design
- **Automatic Backup**: Saves all transcripts to local files
- **Copy & Download**: Easy transcript export options
- **Async Processing**: Non-blocking architecture for handling long videos

## Demo

Access the web interface at `http://localhost:8000` after starting the server.

## Prerequisites

- Python 3.8+
- FFmpeg (required for audio extraction)
  - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd youtube_transcriber
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the Server

```bash
python main.py
```

The application will be available at `http://localhost:8000`

### API Endpoint

**POST /api/transcribe**

Request:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

Response:
```json
{
  "transcript": "Full video transcript...",
  "video_id": "VIDEO_ID"
}
```

Error Responses:
- `400`: Invalid YouTube URL
- `500`: Transcription failed

### Testing

Test the API programmatically:
```bash
python debug_api.py
```

Test the transcription pipeline:
```bash
python debug_repro.py
```

## How It Works

1. **Video ID Extraction**: Parses YouTube URL to extract video identifier
2. **Transcription Attempt 1**: Tries to fetch existing captions via YouTube API (fast)
3. **Transcription Attempt 2**: If captions unavailable, downloads audio and transcribes with Whisper
4. **Persistence**: Saves transcript to `transcripts/{video_id}.txt`

## Project Structure

```
youtube_transcriber/
├── main.py              # FastAPI application and core logic
├── requirements.txt     # Python dependencies
├── static/
│   ├── index.html      # Web interface
│   ├── app.js          # Frontend JavaScript
│   └── style.css       # Styling
├── transcripts/         # Saved transcript files
└── debug_*.py          # Testing utilities
```

## Dependencies

- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **youtube-transcript-api**: Caption fetching
- **yt-dlp**: YouTube audio downloader
- **openai-whisper**: Speech-to-text AI model
- **torch**: PyTorch for Whisper inference

## Notes

- Whisper transcription can be slow for long videos (processes in real-time or slower)
- The "base" Whisper model is used for balance between speed and accuracy
- All transcripts are automatically backed up to the `transcripts/` directory
- Temporary audio files are cleaned up after transcription

## Troubleshooting

**FFmpeg not found**:
- Ensure FFmpeg is installed and available in system PATH
- Test with: `ffmpeg -version`

**Slow transcription**:
- Whisper processes audio at ~1x speed on CPU
- Consider upgrading to a GPU-enabled environment for faster processing

**Captions not available**:
- Some videos don't have captions; Whisper fallback will activate automatically
- Check video has audio track if transcription fails

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
