from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
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
        
        # Try method 1: Get the best available video+audio combination
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', '137+140',  # 1080p video + audio
                    '--get-url',
                    '--no-warnings',
                    '-q',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f'Method 1 (1080p) - Return code: {result.returncode}')
            if result.stderr:
                logger.info(f'Method 1 stderr: {result.stderr[:200]}')
            
            if result.returncode == 0 and result.stdout.strip():
                urls = result.stdout.strip().split('\n')
                download_url = urls[0] if urls else None
                if download_url:
                    logger.info('✅ Got 1080p video URL')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': '1080p',
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 1 (1080p) failed: {str(e)}')
        
        # Try method 2: Get 720p video + audio
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', '136+140',  # 720p video + audio
                    '--get-url',
                    '--no-warnings',
                    '-q',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f'Method 2 (720p) - Return code: {result.returncode}')
            if result.stderr:
                logger.info(f'Method 2 stderr: {result.stderr[:200]}')
            
            if result.returncode == 0 and result.stdout.strip():
                urls = result.stdout.strip().split('\n')
                download_url = urls[0] if urls else None
                if download_url:
                    logger.info('✅ Got 720p video URL')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': '720p',
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 2 (720p) failed: {str(e)}')
        
        # Try method 3: Get 480p video + audio
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', '135+140',  # 480p video + audio
                    '--get-url',
                    '--no-warnings',
                    '-q',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f'Method 3 (480p) - Return code: {result.returncode}')
            if result.stderr:
                logger.info(f'Method 3 stderr: {result.stderr[:200]}')
            
            if result.returncode == 0 and result.stdout.strip():
                urls = result.stdout.strip().split('\n')
                download_url = urls[0] if urls else None
                if download_url:
                    logger.info('✅ Got 480p video URL')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': '480p',
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 3 (480p) failed: {str(e)}')
        
        # Try method 4: Get format 18 (standard - usually works)
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', '18',  # Format 18 is usually available
                    '--get-url',
                    '--no-warnings',
                    '-q',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f'Method 4 (format 18) - Return code: {result.returncode}')
            if result.stderr:
                logger.info(f'Method 4 stderr: {result.stderr[:200]}')
            
            if result.returncode == 0 and result.stdout.strip():
                download_url = result.stdout.strip().split('\n')[0]
                if download_url:
                    logger.info('✅ Got format 18 URL')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': 'standard',
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 4 (format 18) failed: {str(e)}')
        
        # Final fallback: Just try to get any best format
        try:
            result = subprocess.run(
                [
                    'yt-dlp',
                    '-f', 'best',
                    '--get-url',
                    '--no-warnings',
                    '-q',
                    video_url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f'Method 5 (best) - Return code: {result.returncode}')
            if result.stderr:
                logger.info(f'Method 5 stderr: {result.stderr[:200]}')
            
            if result.returncode == 0 and result.stdout.strip():
                download_url = result.stdout.strip().split('\n')[0]
                if download_url:
                    logger.info('✅ Got best available format')
                    return jsonify({
                        'success': True,
                        'url': download_url,
                        'quality': 'best',
                        'source': video_url
                    })
        except Exception as e:
            logger.warning(f'Method 5 (best) failed: {str(e)}')
        
        # All methods failed - log detailed error info
        logger.error('❌ All extraction methods failed')
        logger.error(f'Video URL: {video_url}')
        
        return jsonify({
            'success': False,
            'error': 'Could not extract download URL. The video might be unavailable, restricted, or age-gated.'
        }), 400
        
    except subprocess.TimeoutExpired:
        logger.error(f'⏱️ Request timeout for {video_url}')
        return jsonify({'success': False, 'error': 'Request timeout'}), 408
    except Exception as e:
        logger.error(f'❌ Unexpected error: {str(e)}')
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
