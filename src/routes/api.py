from flask import Blueprint, request, jsonify
import json
import os
import traceback
from datetime import datetime
import logging
from flask_caching import Cache
from flask_cors import CORS
from flask import Flask
from src.core.content_processor import ContentProcessor
from src.core.subtitle_manager import SubtitleManager
from src.core.tts_controller import TTSController
from src.core.sync_manager import SyncManager
from src.core.main_controller import MainController
from src.data.stock_collector import StockDataCollector
from src.data.data_processor import DataProcessor
from src.media.video_generator import VideoGenerator
from src.media.digital_human import DigitalHuman

# 創建藍圖
api_bp = Blueprint('api', __name__)

# 初始化主控制器
main_controller = MainController()

# API路由
@api_bp.route('/process_article', methods=['POST'])
def process_article():
    """處理文章內容"""
    try:
        if 'article' not in request.files and 'text' not in request.form:
            return jsonify({'error': '無文章內容'}), 400
            
        article_text = ""
        if 'article' in request.files:
            article_file = request.files['article']
            article_text = article_file.read().decode('utf-8')
        else:
            article_text = request.form['text']
            
        # 處理選項
        options = {
            'strategy': request.form.get('strategy', 'sentence'),
            'character_rate': float(request.form.get('character_rate', 5.0))
        }
            
        # 使用主控制器處理文章
        result = main_controller.process_article(article_text, options)
        
        if not result:
            return jsonify({'error': '處理文章失敗'}), 500
            
        return jsonify({
            'segments': result['segments'],
            'stock_codes': result['stock_codes']['all'],
            'keywords': result['keywords'],
            'sentiment': result['sentiment'],
            'subtitles': result['subtitles']
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/generate_speech', methods=['POST'])
def generate_speech():
    """生成語音"""
    try:
        if 'text' not in request.form:
            return jsonify({'error': '無文字內容'}), 400
            
        text = request.form['text']
        engine = request.form.get('engine', 'azure')
        voice = request.form.get('voice', 'zh-TW-YunJheNeural')
        rate = float(request.form.get('rate', 1.0))
        
        # 使用TTS控制器
        tts_controller = TTSController()
        tts_controller.set_engine(engine)
        tts_controller.set_voice(voice)
        
        # 生成唯一的輸出文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"cache/audio/speech_{timestamp}.mp3"
        
        # 確保目錄存在
        os.makedirs("cache/audio", exist_ok=True)
        
        # 生成語音
        success = tts_controller.generate_speech(text, output_file, rate)
        
        if success:
            return jsonify({
                'success': True,
                'audio_path': output_file
            })
        else:
            return jsonify({'error': '語音生成失敗'}), 500
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500
@api_bp.route('/batch_generate_speech', methods=['POST'])
def batch_generate_speech():
    """批量生成語音"""
    try:
        data = request.get_json()
        
        if not data or 'subtitles' not in data:
            return jsonify({'error': '無字幕數據'}), 400
        # 檢查是否有重複請求標識
        request_id = data.get('requestId')
        if request_id:
            # 可以在這裡使用緩存或資料庫檢查是否處理過相同的請求
            cache_key = f"speech_request_{request_id}"
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"檢測到重複請求 ID: {request_id}，返回緩存結果")
                return jsonify(cached_result)
                    
        subtitles = data['subtitles']
        engine = data.get('engine', 'edge')
        voice = data.get('voice', 'zh-TW-YunJheNeural')
        rate = float(data.get('rate', 1.0))
        
        # 設置TTS控制器
        tts_controller = TTSController()
        tts_controller.set_engine(engine)
        tts_controller.set_voice(voice)
        tts_controller.set_speech_rate(rate)
        
        # 准備輸出目錄
        output_dir = os.path.join(os.getcwd(), 'cache', 'audio')
        os.makedirs(output_dir, exist_ok=True)
        
        # 批量生成語音
        audio_files = []
        
        for i, subtitle in enumerate(subtitles):
            if 'text' not in subtitle:
                continue
                
            # 生成時間戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S") + f"_{i:03d}"
            output_file = os.path.join(output_dir, f"speech_{timestamp}.mp3")
            
            # 生成語音
            success = tts_controller.generate_speech(subtitle['text'], output_file, rate)
            
            if success:
                audio_files.append(output_file)
                
        # 返回結果
        return jsonify({
            'success': True,
            'audio_files': audio_files,
            'count': len(audio_files)
        })
            
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500
@api_bp.route('/get_stock_data', methods=['GET'])
def get_stock_data():
    """獲取股票數據"""
    try:
        ticker = request.args.get('ticker')
        if not ticker:
            return jsonify({'error': '無股票代碼'}), 400
            
        period = request.args.get('period', '1y')
        interval = request.args.get('interval', '1d')
            
        # 獲取股票數據
        stock_collector = StockDataCollector()
        stock_data = stock_collector.get_stock_data(ticker, period=period, interval=interval)
        
        if stock_data is None or stock_data.empty:
            return jsonify({'error': f'找不到股票數據: {ticker}'}), 404
            
        # 處理數據
        data_processor = DataProcessor()
        processed_data = data_processor.process_stock_data(stock_data)
        
        # 處理數據為JSON格式
        json_data = {
            'dates': processed_data.index.strftime('%Y-%m-%d').tolist(),
            'prices': {
                'open': processed_data['Open'].tolist(),
                'high': processed_data['High'].tolist(),
                'low': processed_data['Low'].tolist(),
                'close': processed_data['Close'].tolist()
            },
            'volume': processed_data['Volume'].tolist() if 'Volume' in processed_data else []
        }
        
        # 添加技術指標
        indicators = {}
        
        if 'SMA_20' in processed_data:
            indicators['sma20'] = processed_data['SMA_20'].tolist()
        if 'SMA_50' in processed_data:
            indicators['sma50'] = processed_data['SMA_50'].tolist()
        if 'SMA_200' in processed_data:
            indicators['sma200'] = processed_data['SMA_200'].tolist()
        if 'RSI' in processed_data:
            indicators['rsi'] = processed_data['RSI'].tolist()
        if 'MACD' in processed_data:
            indicators['macd'] = processed_data['MACD'].tolist()
        if 'Signal_Line' in processed_data:
            indicators['signal'] = processed_data['Signal_Line'].tolist()
        if 'MACD_Histogram' in processed_data:
            indicators['histogram'] = processed_data['MACD_Histogram'].tolist()
        if 'Bollinger_Upper' in processed_data:
            indicators['bollinger_upper'] = processed_data['Bollinger_Upper'].tolist()
        if 'Bollinger_Lower' in processed_data:
            indicators['bollinger_lower'] = processed_data['Bollinger_Lower'].tolist()
            
        json_data['indicators'] = indicators
            
        return jsonify(json_data)
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/search_stock', methods=['GET'])
def search_stock():
    """搜索股票"""
    try:
        keyword = request.args.get('keyword')
        if not keyword:
            return jsonify({'error': '無搜索關鍵字'}), 400
            
        # 使用主控制器搜索股票
        results = main_controller.search_stock(keyword)
        
        return jsonify({
            'count': len(results),
            'results': results
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/generate_video', methods=['POST'])
def generate_video():
    """生成視頻"""
    try:
        # 檢查必要參數
        if 'ticker' not in request.form:
            return jsonify({'error': '缺少股票代碼'}), 400
            
        ticker = request.form['ticker']
        
        # 解析字幕數據
        subtitles = []
        if 'subtitles' in request.form:
            try:
                subtitles = json.loads(request.form['subtitles'])
            except:
                return jsonify({'error': '無效的字幕數據格式'}), 400
                
        # 解析選項
        options = {}
        if 'options' in request.form:
            try:
                options = json.loads(request.form['options'])
            except:
                options = {}
                
        # 使用主控制器生成視頻
        task_id = main_controller.generate_stock_video(ticker, subtitles, options)
        
        if not task_id:
            return jsonify({'error': '創建視頻生成任務失敗'}), 500
            
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '視頻生成任務已創建'
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """獲取任務狀態"""
    try:
        # 獲取任務狀態
        task = main_controller.get_task_status(task_id)
        
        if not task:
            return jsonify({'error': f'找不到任務: {task_id}'}), 404
            
        # 返回任務狀態
        return jsonify({
            'id': task['id'],
            'type': task['type'],
            'status': task['status'],
            'progress': task['progress'],
            'progress_message': task.get('progress_message', ''),
            'created_at': task['created_at'],
            'error': task.get('error'),
            'result': task.get('result')
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/cancel_task/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消任務"""
    try:
        # 取消任務
        success = main_controller.cancel_task(task_id)
        
        if not success:
            return jsonify({'error': f'無法取消任務: {task_id}'}), 400
            
        return jsonify({
            'success': True,
            'message': f'任務 {task_id} 已取消'
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/save_project', methods=['POST'])
def save_project():
    """保存專案"""
    try:
        # 檢查項目數據
        if 'project_data' not in request.form:
            return jsonify({'error': '無專案數據'}), 400
            
        try:
            project_data = json.loads(request.form['project_data'])
        except:
            return jsonify({'error': '無效的專案數據格式'}), 400
            
        # 專案文件名
        output_file = None
        if 'output_file' in request.form:
            output_file = request.form['output_file']
            
        # 保存專案
        file_path = main_controller.save_project(project_data, output_file)
        
        if not file_path:
            return jsonify({'error': '保存專案失敗'}), 500
            
        return jsonify({
            'success': True,
            'file_path': file_path
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/load_project', methods=['POST'])
def load_project():
    """載入專案"""
    try:
        # 檢查文件
        if 'project_file' not in request.files:
            return jsonify({'error': '無專案文件'}), 400
            
        project_file = request.files['project_file']
        
        # 保存到臨時文件
        temp_dir = 'cache/temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file = os.path.join(temp_dir, project_file.filename)
        project_file.save(temp_file)
        
        # 載入專案
        project_data = main_controller.load_project(temp_file)
        
        if not project_data:
            return jsonify({'error': '載入專案失敗'}), 500
            
        return jsonify({
            'success': True,
            'project_data': project_data
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/recent_projects', methods=['GET'])
def get_recent_projects():
    """獲取最近專案"""
    try:
        # 獲取最近專案
        limit = int(request.args.get('limit', 10))
        projects = main_controller.get_recent_projects(limit)
        
        return jsonify({
            'count': len(projects),
            'projects': projects
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/list_templates', methods=['GET'])
def list_templates():
    """列出可用模板"""
    try:
        template_type = request.args.get('type', 'all')
        
        # 列出數位人模板
        if template_type == 'digital_human' or template_type == 'all':
            digital_human = DigitalHuman()
            dh_templates = digital_human.list_templates()
        else:
            dh_templates = []
            
        # 更多模板類型可在此添加
        
        return jsonify({
            'digital_humans': dh_templates,
            # 其他模板類型...
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/generate_chart', methods=['POST'])
def generate_chart():
    """生成股票圖表"""
    try:
        # 檢查股票代碼
        if 'ticker' not in request.form:
            return jsonify({'error': '缺少股票代碼'}), 400
            
        ticker = request.form['ticker']
        chart_type = request.form.get('chart_type', 'candlestick')
        period = request.form.get('period', '1y')
        interval = request.form.get('interval', '1d')
        
        # 解析技術指標
        indicators = None
        if 'indicators' in request.form:
            try:
                indicators = request.form['indicators'].split(',')
            except:
                indicators = None
                
        # 獲取股票數據
        stock_collector = StockDataCollector()
        stock_data = stock_collector.get_stock_data(ticker, period=period, interval=interval)
        
        if stock_data is None or stock_data.empty:
            return jsonify({'error': f'找不到股票數據: {ticker}'}), 404
            
        # 處理數據
        data_processor = DataProcessor()
        processed_data = data_processor.process_stock_data(stock_data)
        
        # 生成圖表
        output_file = data_processor.generate_stock_chart(
            processed_data, chart_type, indicators=indicators
        )
        
        if not output_file or not os.path.exists(output_file):
            return jsonify({'error': '生成圖表失敗'}), 500
            
        # 返回圖表文件路徑
        return jsonify({
            'success': True,
            'chart_file': output_file
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/generate_report', methods=['GET'])
def generate_report():
    """生成股票報告"""
    try:
        # 檢查股票代碼
        ticker = request.args.get('ticker')
        if not ticker:
            return jsonify({'error': '無股票代碼'}), 400
            
        period = request.args.get('period', '1y')
        report_type = request.args.get('type', 'basic')
        
        # 生成報告
        report = main_controller.generate_report(ticker, period, report_type)
        
        if not report:
            return jsonify({'error': '生成報告失敗'}), 500
            
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500
# 在API中添加媒體庫功能
@api_bp.route('/media_library', methods=['GET'])
def get_media_library():
    """獲取媒體庫內容"""
    try:
        # 獲取媒體類型
        media_type = request.args.get('type', 'all')
        
        # 媒體庫目錄
        library_dir = os.path.join(os.getcwd(), 'media_library')
        
        # 確保目錄存在
        os.makedirs(library_dir, exist_ok=True)
        
        # 子目錄
        image_dir = os.path.join(library_dir, 'images')
        video_dir = os.path.join(library_dir, 'videos')
        audio_dir = os.path.join(library_dir, 'audio')
        
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        
        # 收集媒體文件
        media_files = {}
        
        if media_type in ['all', 'image']:
            media_files['images'] = _get_media_files(image_dir, ['jpg', 'jpeg', 'png', 'gif'])
            
        if media_type in ['all', 'video']:
            media_files['videos'] = _get_media_files(video_dir, ['mp4', 'webm', 'mov'])
            
        if media_type in ['all', 'audio']:
            media_files['audio'] = _get_media_files(audio_dir, ['mp3', 'wav', 'ogg'])
            
        return jsonify(media_files)
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

def _get_media_files(directory, extensions):
    """獲取指定目錄中的媒體文件"""
    files = []
    
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if any(filename.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, directory)
                
                # 獲取文件信息
                stat = os.stat(file_path)
                
                files.append({
                    'name': filename,
                    'path': rel_path,
                    'full_path': file_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return files
@api_bp.route('/replace_media', methods=['POST'])
def replace_media():
    """替換媒體元素"""
    try:
        # 檢查請求參數
        if 'track_type' not in request.form:
            return jsonify({'error': '缺少軌道類型'}), 400
            
        if 'item_id' not in request.form:
            return jsonify({'error': '缺少項目ID'}), 400
            
        if 'media_file' not in request.files:
            return jsonify({'error': '缺少媒體文件'}), 400
            
        track_type = request.form['track_type']
        item_id = request.form['item_id']
        media_file = request.files['media_file']
        keep_timing = request.form.get('keep_timing', 'true') == 'true'
        
        # 檢查軌道類型
        if track_type not in ['video', 'audio']:
            return jsonify({'error': f'不支援的軌道類型: {track_type}'}), 400
            
        # 確保目錄存在
        output_dir = os.path.join(os.getcwd(), 'cache', track_type)
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_ext = os.path.splitext(media_file.filename)[1].lower()
        output_file = os.path.join(output_dir, f"{item_id}_{timestamp}{file_ext}")
        
        # 保存文件
        media_file.save(output_file)
        
        # 獲取媒體時長
        duration = None
        if not keep_timing:
            if track_type == 'video':
                # 使用OpenCV獲取視頻時長
                import cv2
                cap = cv2.VideoCapture(output_file)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps
                    cap.release()
            elif track_type == 'audio':
                # 使用pydub獲取音頻時長
                from pydub import AudioSegment
                audio = AudioSegment.from_file(output_file)
                duration = len(audio) / 1000.0
        
        return jsonify({
            'success': True,
            'file_path': output_file,
            'duration': duration
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500
    
@api_bp.route('/upload_template', methods=['POST'])
def upload_template():
    """上傳模板"""
    try:
        # 檢查必要參數
        if 'type' not in request.form:
            return jsonify({'error': '缺少模板類型'}), 400
            
        if 'name' not in request.form:
            return jsonify({'error': '缺少模板名稱'}), 400
            
        if 'template_file' not in request.files:
            return jsonify({'error': '缺少模板文件'}), 400
            
        template_type = request.form['type']
        template_name = request.form['name']
        template_file = request.files['template_file']
        description = request.form.get('description', '')
        
        # 檢查模板類型
        if template_type not in ['layout', 'digitalHuman']:
            return jsonify({'error': f'不支援的模板類型: {template_type}'}), 400
            
        # 準備目錄
        templates_dir = os.path.join(os.getcwd(), 'templates')
        if template_type == 'layout':
            target_dir = os.path.join(templates_dir, 'layouts')
        else:
            target_dir = os.path.join(templates_dir, 'digital_humans')
            
        os.makedirs(target_dir, exist_ok=True)
        
        # 生成模板ID
        template_id = f"{template_type}_{template_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 處理模板文件
        file_ext = os.path.splitext(template_file.filename)[1].lower()
        if template_type == 'layout' and file_ext != '.json':
            return jsonify({'error': '布局模板必須是 JSON 文件'}), 400
            
        if template_type == 'digitalHuman' and file_ext not in ['.mp4', '.mov', '.avi']:
            return jsonify({'error': '數位人模板必須是視頻文件 (MP4, MOV, AVI)'}), 400
            
        # 保存模板文件
        template_filename = f"{template_id}{file_ext}"
        template_path = os.path.join(target_dir, template_filename)
        template_file.save(template_path)
        
        # 處理預覽圖
        preview_path = None
        if 'preview_file' in request.files:
            preview_file = request.files['preview_file']
            if preview_file.filename:
                preview_ext = os.path.splitext(preview_file.filename)[1].lower()
                preview_filename = f"{template_id}_preview{preview_ext}"
                preview_path = os.path.join(target_dir, preview_filename)
                preview_file.save(preview_path)
        
        # 創建元數據
        metadata = {
            'id': template_id,
            'name': template_name,
            'description': description,
            'file_path': template_path,
            'preview': preview_path,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 添加數位人特定屬性
        if template_type == 'digitalHuman':
            metadata['gender'] = request.form.get('gender', 'neutral')
            metadata['language'] = request.form.get('language', 'zh-TW')
        
        # 保存元數據
        metadata_path = os.path.join(target_dir, f"{template_id}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'template_id': template_id
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500

@api_bp.route('/get_template', methods=['GET'])
def get_template():
    """獲取模板詳情"""
    try:
        template_type = request.args.get('type')
        template_id = request.args.get('id')
        
        if not template_type or not template_id:
            return jsonify({'error': '缺少模板類型或ID'}), 400
            
        # 準備目錄
        templates_dir = os.path.join(os.getcwd(), 'templates')
        if template_type == 'layout':
            target_dir = os.path.join(templates_dir, 'layouts')
        else:
            target_dir = os.path.join(templates_dir, 'digital_humans')
            
        # 尋找元數據文件
        metadata_path = os.path.join(target_dir, f"{template_id}.json")
        
        if not os.path.exists(metadata_path):
            return jsonify({'error': f'找不到模板: {template_id}'}), 404
            
        # 讀取元數據
        with open(metadata_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
            
        return jsonify({
            'success': True,
            'template': template
        })
        
    except Exception as e:
        error_details = traceback.format_exc()
        return jsonify({'error': str(e), 'details': error_details}), 500