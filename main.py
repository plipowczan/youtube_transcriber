from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re
import os
import tempfile
import asyncio
import yt_dlp
import whisper
import logging
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    force=True  # Override Uvicorn logging
)
logger = logging.getLogger(__name__)
logger.info("--- LOGGING SYSTEM INITIALIZED ---")

app = FastAPI(title="YouTube Transcriber")

# Ensure transcripts directory exists
TRANSCRIPTS_DIR = "transcripts"
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class TranscribeRequest(BaseModel):
    url: str


class TranscribeResponse(BaseModel):
    transcript: str
    video_id: str


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Invalid YouTube URL")


def download_audio(video_url: str) -> str:
    """Download audio from YouTube video and return the file path."""
    # Create a temporary file for the audio
    temp_dir = tempfile.gettempdir()
    output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')
    
    # Proper HTTP headers to mimic browser requests
    http_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.youtube.com/'
    }
    
    # Configuration to bypass restrictions and improve compatibility
    # Skip web client that requires JavaScript runtime - use alternative extractors instead
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'http_headers': http_headers,
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'continue_dl': True,
        # Use android and ios clients to avoid JavaScript requirement
        'extractor_args': {
            'youtube': {
                'skip': ['webpage'],  # Skip web client that requires JavaScript
            }
        },
    }
    
    # Retry logic with exponential backoff and strategy switching
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_id = info['id']
                audio_file = os.path.join(temp_dir, f"{video_id}.mp3")
            return audio_file
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            # Check if it's a temporary error (403, 429, connection timeout)
            is_temp_error = any(code in error_msg for code in ['403', '429', 'timed out', 'connection', 'temporary'])
            
            if attempt < max_retries - 1 and is_temp_error:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Download attempt {attempt + 1} failed with '{error_msg}'. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Download failed after {attempt + 1} attempt(s): {error_msg}")
                raise


def transcribe_audio(file_path: str) -> str:
    """Transcribe audio file using Whisper model."""
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]


def save_transcript_to_file(video_id: str, transcript: str):
    """Save transcript to a text file for backup."""
    file_path = os.path.join(TRANSCRIPTS_DIR, f"{video_id}.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        logger.info(f"Transcript saved to {file_path}")
    except Exception as e:
        logger.error(f"Failed to save transcript to {file_path}: {e}")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.on_event("startup")
async def startup_event():
    logger.info("Application is starting up...")
    logger.info(f"Transcripts will be saved to: {os.path.abspath(TRANSCRIPTS_DIR)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Check server logs for details."},
    )


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_video(request: TranscribeRequest):
    """Transcribe a YouTube video from its URL."""
    audio_file = None
    try:
        # Extract video ID
        video_id = extract_video_id(request.url)
        logger.info(f"Received transcription request for video: {video_id}")
        
        try:
            # Try to get transcript using YouTube API first
            logger.info(f"Attempting to fetch captions from YouTube API for {video_id}...")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info("Successfully fetched captions from YouTube API")
            
            # Combine all text segments
            full_transcript = " ".join([entry['text'] for entry in transcript_list])
            
            # Save backup
            save_transcript_to_file(video_id, full_transcript)
            
            return TranscribeResponse(
                transcript=full_transcript,
                video_id=video_id
            )
        
        except Exception as api_err:
            # Fallback: Download audio and transcribe with Whisper for ANY API error
            logger.warning(f"YouTube API failed for {video_id} ({type(api_err).__name__}). Falling back to Whisper...")
            
            # Download audio (blocking operation, run in thread)
            logger.info("Downloading audio from YouTube...")
            audio_file = await asyncio.to_thread(download_audio, request.url)
            logger.info(f"Audio downloaded to {audio_file}. Loading Whisper model...")
            
            # Transcribe audio (blocking operation, run in thread)
            logger.info("Starting Whisper transcription (this may take a while)...")
            full_transcript = await asyncio.to_thread(transcribe_audio, audio_file)
            logger.info("Whisper transcription complete")
            
            # Save backup
            save_transcript_to_file(video_id, full_transcript)
            
            return TranscribeResponse(
                transcript=full_transcript,
                video_id=video_id
            )
        
    except ValueError as e:
        logger.error(f"Invalid request error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unhandled error transcribing video {request.url}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred: {str(e)}"
        )
    finally:
        # Clean up temporary audio file
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception:
                pass  # Ignore cleanup errors


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
