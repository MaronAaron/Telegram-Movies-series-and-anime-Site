import json
import os
import re
import requests
from telethon import TelegramClient, events

# 1. SETUP YOUR CREDENTIALS
API_ID = 32798857 
API_HASH = 'df61f3f6569ad955338ab767c9a6b4c0'
CHANNEL_USERNAME = 'Moviesseriesandanime'

# ⚠️ REPLACE THIS WITH YOUR REAL TMDB KEY FROM THE TMDB WEBSITE
TMDB_API_KEY = 'YOUR_ACTUAL_TMDB_API_KEY_HERE'

JSON_FILE = 'movies.json'

# Initialize Telegram Client
client = TelegramClient('media_hub_session', API_ID, API_HASH)

def clean_title(filename):
    """Cleans up torrent-like filenames to extract a clean movie/series title."""
    # Remove extensions and common scene tags
    name = re.sub(r'\.(mkv|mp4|avi|WEBRip|WEB-HD|720p|1080p|x264|x265|Dual\.Audio|Pahe).*$', '', filename, flags=re.IGNORECASE)
    # Replace dots and underscores with spaces
    name = name.replace('.', ' ').replace('_', ' ')
    # Extract season/episode if present to help filter category
    is_series = bool(re.search(r'S\d+E\d+|Season\s*\d+', name, re.IGNORECASE))
    return name.strip(), is_series

def fetch_tmdb_data(title, is_series):
    """Searches TMDB to get the official poster path and release year."""
    search_type = "tv" if is_series else "movie"
    url = f"https://api.themoviedb.org/3/search/{search_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US"
    }
    try:
        response = requests.get(url, params=params).json()
        if response.get('results'):
            result = response['results'][0]
            poster_path = result.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=400"
            
            # Get release year
            date_key = 'first_air_date' if is_series else 'release_date'
            year = result.get(date_key, "2026")[:4] if result.get(date_key) else "2026"
            
            return poster_url, year
    except Exception as e:
        print(f"Error connecting to TMDB: {e}")
    
    return "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=400", "2026"

@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def my_event_handler(event):
    # Check if the message has a document/video file
    if event.message.media and hasattr(event.message.media, 'document'):
        msg_id = event.message.id
        attributes = event.message.media.document.attributes
        
        # Try to find the actual file name
        filename = "Unknown Title"
        for attr in attributes:
            if hasattr(attr, 'file_name'):
                filename = attr.file_name
                break
        
        print(f"🎬 New file detected: {filename}")
        
        # Clean title and guess if it's a Movie, Series, or Anime
        clean_name, is_series = clean_title(filename)
        category = "series" if is_series else "movies"
        if "anime" in filename.lower() or "naruto" in filename.lower(): 
            category = "anime"
            
        # Extract quality strings
        quality = "1080p WEB-HD" if "1080p" in filename else "720p WEB-HD"
        
        # Fetch the real movie poster automatically
        poster_image, year = fetch_tmdb_data(clean_name, is_series)
        
        # Generate the beautiful public deep link directly to this exact telegram post
        tg_link = f"https://t.me/{CHANNEL_USERNAME}/{msg_id}"
        
        # Structure the entry
        new_entry = {
            "title": clean_name,
            "category": category,
            "year": year,
            "quality": quality,
            "image": poster_image,
            "tgLink": tg_link
        }
        
        # Update our movies.json database file
        data = []
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                    
        # Put newest uploads at the top
        data.insert(0, new_entry)
        
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            
        print(f"✅ Successfully added {clean_name} to the website database!")

print("⚡ Movie Sync Engine is running... Post a movie file to your channel to test.")
client.start()
client.run_until_disconnected()
