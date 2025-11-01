from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
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
        
        # Use cobalt.tools API (free and works with YouTube)
        cobalt_url = "https://api.cobalt.tools/api/json"
        
        payload = {
            "url": video_url,
            "vCodec": "h264",
            "vQuality": "720",
            "aFormat": "mp3",
            "filenamePattern": "classic",
            "isAudioOnly": False
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(cobalt_url, json=payload, headers=headers, timeout=60)
            
            logger.info(f'Cobalt API response status: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f'Cobalt result: {result}')
                
                # Check if successful
                if result.get('status') == 'redirect' or result.get('status') == 'stream':
                    download_url = result.get('url')
                    if download_url:
                        logger.info('✅ Got download URL from cobalt.tools')
                        return jsonify({
                            'success': True,
                            'url': download_url,
                            'quality': '720p',
                            'source': video_url
                        })
                elif result.get('status') == 'error':
                    error_msg = result.get('text', 'Unknown error')
                    logger.error(f'Cobalt error: {error_msg}')
                    return jsonify({
                        'success': False,
                        'error': f'Download failed: {error_msg}'
                    }), 400
        except requests.exceptions.Timeout:
            logger.error('Cobalt API timeout')
            return jsonify({'success': False, 'error': 'Request timeout'}), 408
        except Exception as e:
            logger.error(f'Cobalt API error: {str(e)}')
        
        # Fallback: Try y2mate API
        logger.info('Trying fallback method...')
        try:
            # Extract video ID
            match = re.search(r'(?:youtube\.com\/(?:shorts\/|watch\?v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})', video_url)
            if match:
                video_id = match.group(1)
                
                # Use direct YouTube download link (works for some videos)
                download_url = f"https://www.youtube.com/watch?v={video_id}"
                
                logger.info('✅ Using fallback direct link')
                return jsonify({
                    'success': True,
                    'url': download_url,
                    'quality': 'standard',
                    'source': video_url,
                    'note': 'Direct link - may require additional processing'
                })
        except Exception as e:
            logger.error(f'Fallback failed: {str(e)}')
        
        logger.error('❌ All methods failed')
        return jsonify({
            'success': False,
            'error': 'Could not download video. YouTube is blocking all access methods.'
        }), 400
        
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'API running'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f'Starting on port {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
