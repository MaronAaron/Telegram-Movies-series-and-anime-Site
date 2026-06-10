import json
import os
import re
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events

# --- 1. FLASK WEB SERVER SETUP (FOR RENDER FREE TIER) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Movie Sync Hub Engine is Running Alive!", 200

# --- 2. YOUR TELEGRAM CONFIGURATION ---
API_ID = 32798857
API_HASH = 'df61f3f6569ad955338ab767c9a6b4c0'
CHANNEL_USERNAME = 'Moviesseriesandanime'
TMDB_API_KEY = '9c4809193b9f263678368bb602af9433'

JSON_FILE = 'movies.json'

client = TelegramClient('media_hub_session', API_ID, API_HASH)

def clean_title(filename):
    name = re.sub(r'\.(mkv|mp4|avi|WEBRip|WEB-HD|720p|1080p|x264|x265|Dual\.Audio|Pahe).*$', '', filename, flags=re.IGNORECASE)
    name = name.replace('.', ' ').replace('_', ' ')
    is_series = bool(re.search(r'S\d+E\d+|Season\s*\d+', name, re.IGNORECASE))
    return name.strip(), is_series

def fetch_tmdb_data(title, is_series):
    search_type = "tv" if is_series else "movie"
    url = f"https://api.themoviedb.org/3/search/{search_type}"
    params = {"api_key": TMDB_API_KEY, "query": title, "language": "en-US"}
    try:
        response = requests.get(url, params=params).json()
        if response.get('results'):
            result = response['results'][0]
            poster_path = result.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=400"
            date_key = 'first_air_date' if is_series else 'release_date'
            year = result.get(date_key, "2026")[:4] if result.get(date_key) else "2026"
            return poster_url, year
    except Exception as e:
        print(f"Error connecting to TMDB: {e}")
    return "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=400", "2026"

@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def my_event_handler(event):
    if event.message.media and hasattr(event.message.media, 'document'):
        msg_id = event.message.id
        attributes = event.message.media.document.attributes
        
        filename = "Unknown Title"
        for attr in attributes:
            if hasattr(attr, 'file_name'):
                filename = attr.file_name
                break
        
        print(f"🎬 New file detected: {filename}")
        clean_name, is_series = clean_title(filename)
        category = "series" if is_series else "movies"
        if "anime" in filename.lower() or "naruto" in filename.lower(): 
            category = "anime"
            
        quality = "1080p WEB-HD" if "1080p" in filename else "720p WEB-HD"
        poster_image, year = fetch_tmdb_data(clean_name, is_series)
        tg_link = f"https://t.me/{CHANNEL_USERNAME}/{msg_id}"
        
        new_entry = {
            "title": clean_name,
            "category": category,
            "year": year,
            "quality": quality,
            "image": poster_image,
            "tgLink": tg_link
        }
        
        data = []
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                try: data = json.load(f)
                except json.JSONDecodeError: data = []
                    
        data.insert(0, new_entry)
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"✅ Successfully added {clean_name} to the website database!")

# Run Telegram Client in a background thread so it doesn't block the web server
def run_telegram():
    client.start()
    client.run_until_disconnected()

if __name__ == '__main__':
    t = threading.Thread(target=run_telegram)
    t.start()
    # Port configuration for Render deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
