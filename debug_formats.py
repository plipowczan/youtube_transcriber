import yt_dlp

http_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Referer': 'https://www.youtube.com/',
}

ydl_opts = {
    'http_headers': http_headers,
    'quiet': False,
    'no_warnings': False,
    # Skip web client that requires JavaScript
    'extractor_args': {
        'youtube': {
            'skip': ['webpage'],
        }
    },
}

# Check what formats are available
for vid in ['MAhkbZHcbLA', 'fOY0_WCR3eY']:
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={vid}', download=False)
            print(f'{vid}: Video accessible')
            num_formats = len(info.get('formats', []))
            print(f'  Available formats: {num_formats}')
            if num_formats > 0:
                print(f'  First format: {info["formats"][0]}')
    except Exception as e:
        print(f'{vid}: {type(e).__name__}: {str(e)[:150]}')
