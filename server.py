import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Allows your HTML file to talk to this Python script

# Configure yt-dlp to find the best audio stream
# UPDATED: Added anti-bot configuration
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'extract_flat': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'player_skip': ['js'],
        }
    },
    'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
}

def get_audio_url(query):
    try:
        # 1. Search for the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # REVERTED: Switched back to standard ytsearch which is more universally supported
            # The extractor_args above will handle the bot protection
            search_query = f"ytsearch1:{query} official audio"
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info and len(info['entries']) > 0:
                video_url = info['entries'][0]['url']
                
                # 2. Extract the actual stream URL from the specific video
                # We need a new instance to get the direct stream link
                ctx_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True, 
                    'noplaylist': True,
                    'extractor_args': ydl_opts['extractor_args'] # Pass the anti-bot args here too
                }
                with yt_dlp.YoutubeDL(ctx_opts) as ctx:
                    video_info = ctx.extract_info(video_url, download=False)
                    return {
                        'title': video_info.get('title'),
                        'url': video_info.get('url'), # The direct audio stream
                        'duration': video_info.get('duration')
                    }
    except Exception as e:
        print(f"Error: {e}")
        return None
    return None

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    print(f"Searching for: {query}")
    result = get_audio_url(query)
    
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    # Use the PORT environment variable if available (Render provides this)
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Spotify Backend on port {port}")
    # Listen on all addresses (0.0.0.0) so Render can reach the app
    app.run(host='0.0.0.0', port=port, debug=False)
