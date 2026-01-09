import requests
import json

url = "http://localhost:8000/api/transcribe"
payload = {"url": "https://www.youtube.com/watch?v=qA6zfVDuXmI"}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, timeout=600)  # Long timeout for transcription
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
        data = response.json()
        print(f"Transcript Preview: {data.get('transcript')[:100]}")
    else:
        print("Failed!")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
