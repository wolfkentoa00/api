import os
import subprocess
import sys
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Search Configuration
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

def get_video_id(query):
    """Finds the Video ID for a given query"""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch1:{query} official audio"
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info and len(info['entries']) > 0:
                return {
                    'id': info['entries'][0]['id'],
                    'title': info['entries'][0]['title'],
                    'duration': info['entries'][0].get('duration')
                }
    except Exception as e:
        print(f"Search Error: {e}")
    return None

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    print(f"Searching for: {query}")
    info = get_video_id(query)
    
    if info:
        # Force HTTPS for the return URL to prevent Mixed Content errors
        base_url = request.host_url.replace('http://', 'https://')
        return jsonify({
            'title': info['title'],
            'url': f"{base_url}stream?v={info['id']}",
            'duration': info['duration']
        })
    else:
        return jsonify({'error': 'Not found'}), 404

@app.route('/stream', methods=['GET'])
def stream():
    """
    Proxies the audio stream using yt-dlp (like your command line example)
    """
    video_id = request.args.get('v')
    if not video_id:
        return "No video ID", 400

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    def generate():
        # FORCE M4A format for compatibility with all browsers (Safari/iOS especially)
        cmd = [
            'yt-dlp', 
            '-o', '-', 
            '-f', 'bestaudio[ext=m4a]/best', 
            '--quiet',
            '--no-warnings',
            video_url
        ]
        
        # Start the process
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Read chunks and yield to client
        try:
            while True:
                chunk = process.stdout.read(4096) # 4KB chunks
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            print(f"Stream Error: {e}")
        finally:
            process.terminate()

    # Use proper audio/mp4 mime type
    return Response(stream_with_context(generate()), mimetype='audio/mp4')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Listen on all addresses
    app.run(host='0.0.0.0', port=port)
