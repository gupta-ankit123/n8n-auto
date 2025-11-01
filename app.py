from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import logging
import sys
import os
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'ok', 'message': 'YouTube Downloader API running'})

@app.route('/get-download-url', methods=['POST'])
def get_download_url():
    try:
        data = request.json
        video_url = data.get('url')
        
        if not video_url:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        logger.info(f'Processing: {video_url}')
        
        # Extract video ID
        match = re.search(r'(?:youtube\.com\/(?:shorts\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})', video_url)
        if not match:
            return jsonify({'success': False, 'error': 'Invalid YouTube URL'}), 400
        
        video_id = match.group(1)
        logger.info(f'Video ID: {video_id}')
        
        # Method 1: Use yt-dlp with cookies from browser
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', 'best[ext=mp4]',
                    '--get-url',
                    '-q',
                    '--cookies-from-browser', 'firefox',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f'Method 1 (with cookies) - Return code: {result.returncode}')
            
            if result.returncode == 0 and result.stdout.strip():
                download_url = result.stdout.strip().split('\n')[0]
                if download_url:
                    logger.info('✅ Got download URL with browser cookies')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': 'best',
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 1 failed: {str(e)}')
        
        # Method 2: Use yt-dlp with user-agent spoofing and retry
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', 'best[ext=mp4]',
                    '--get-url',
                    '-q',
                    '-U', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    '--socket-timeout', '30',
                    '--retries', '5',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=90
            )
            
            logger.info(f'Method 2 (with retries) - Return code: {result.returncode}')
            
            if result.returncode == 0 and result.stdout.strip():
                download_url = result.stdout.strip().split('\n')[0]
                if download_url:
                    logger.info('✅ Got download URL with retries')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': 'best',
                        'source': video_url
                    })
            else:
                logger.error(f'Method 2 stderr: {result.stderr[:300]}')
        except Exception as e:
            logger.warning(f'Method 2 failed: {str(e)}')
        
        # Method 3: Use Invidious API (alternative YouTube frontend)
        try:
            import urllib.request
            invidious_instance = 'https://invidious.io'
            api_url = f'{invidious_instance}/api/v1/videos/{video_id}'
            
            logger.info(f'Trying Invidious API: {api_url}')
            
            with urllib.request.urlopen(api_url, timeout=15) as response:
                import json
                data = json.loads(response.read().decode())
                
                # Get the best quality format URL
                if 'formatStreams' in data and len(data['formatStreams']) > 0:
                    # Sort by quality
                    streams = sorted(data['formatStreams'], 
                                   key=lambda x: int(x.get('qualityLabel', '0p').replace('p', '')), 
                                   reverse=True)
                    download_url = streams[0]['url']
                    quality = streams[0].get('qualityLabel', 'best')
                    
                    logger.info(f'✅ Got download URL from Invidious')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': quality,
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 3 (Invidious) failed: {str(e)}')
        
        # All methods failed
        logger.error('❌ All extraction methods failed')
        logger.error(f'Video URL: {video_url}')
        
        return jsonify({
            'success': False,
            'error': 'Could not extract download URL. YouTube is blocking automated access. Try with a different video or check if it\'s age-restricted.'
        }), 400
        
    except subprocess.TimeoutExpired:
        logger.error('Request timeout')
        return jsonify({'success': False, 'error': 'Request timeout'}), 408
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=5)
        yt_dlp_version = result.stdout.strip() if result.returncode == 0 else 'Not installed'
    except:
        yt_dlp_version = 'Not installed'
    
    return jsonify({'status': 'ok', 'yt_dlp_version': yt_dlp_version})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f'Starting on port {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
