import asyncio
import logging
import sys
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

async def run_test():
    try:
        from main import extract_video_id, download_audio
        from youtube_transcript_api import YouTubeTranscriptApi
        
        url = "https://www.youtube.com/watch?v=qA6zfVDuXmI"
        logger.info(f"Testing URL: {url}")
        
        video_id = extract_video_id(url)
        logger.info(f"Video ID: {video_id}")
        
        try:
            logger.info("Trying YouTubeTranscriptApi...")
            YouTubeTranscriptApi.get_transcript(video_id)
            logger.info("YouTubeTranscriptApi succeeded.")
        except Exception as e:
            logger.error(f"YouTubeTranscriptApi failed: {e}")
            logger.info("Falling back to download...")
            try:
                path = await asyncio.to_thread(download_audio, url)
                logger.info(f"Download succeeded: {path}")
                
                logger.info("Starting Whisper transcription...")
                from main import transcribe_audio
                transcript = await asyncio.to_thread(transcribe_audio, path)
                logger.info("Transcription succeeded!")
                print(transcript[:100] + "...")
            except Exception as e2:
                logger.error(f"Download failed: {e2}")
                traceback.print_exc()
                
    except Exception as outer_e:
        logger.error(f"Outer error: {outer_e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
