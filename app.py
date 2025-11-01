from flask import Flask, request, jsonify
from flask_cors import CORS
from pytubefix import YouTube
import logging
import sys
import os

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
        
        try:
            # Create YouTube object
            yt = YouTube(video_url)
            
            logger.info(f'Title: {yt.title}')
            
            # Get highest quality progressive stream (video + audio)
            # Progressive streams are downloadable directly
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            
            if not stream:
                # Fallback: Get best quality video
                stream = yt.streams.get_highest_resolution()
            
            if stream:
                download_url = stream.url
                quality = stream.resolution if hasattr(stream, 'resolution') else 'best'
                
                logger.info(f'✅ Got download URL - Quality: {quality}')
                
                return jsonify({
                    'success': True,
                    'url': download_url,
                    'quality': quality,
                    'title': yt.title,
                    'source': video_url
                })
            else:
                logger.error('No stream found')
                return jsonify({
                    'success': False,
                    'error': 'No downloadable stream found for this video'
                }), 400
                
        except Exception as e:
            logger.error(f'YouTube error: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Could not process video: {str(e)}'
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
