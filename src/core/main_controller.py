#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 主控制器
"""

import os
import logging
import json
from datetime import datetime
import threading
import queue

from src.core.content_processor import ContentProcessor
from src.core.subtitle_manager import SubtitleManager
from src.core.tts_controller import TTSController
from src.core.sync_manager import SyncManager
from src.data.stock_collector import StockDataCollector
from src.data.data_processor import DataProcessor
from src.media.video_generator import VideoGenerator
from src.media.digital_human import DigitalHuman

class MainController:
    """主控制器類
    
    負責協調各個模組和組件，實現整個系統的流程控制。
    """
    
    def __init__(self, config=None):
        """初始化主控制器
        
        參數:
            config (dict, 可選): 配置設定
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.output_dir = self.config.get('output_dir', 'output')
        
        # 確保輸出目錄存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化各個模組
        self.content_processor = ContentProcessor()
        self.subtitle_manager = SubtitleManager()
        self.tts_controller = TTSController(self.config.get('tts', {}))
        self.sync_manager = SyncManager()
        self.stock_collector = StockDataCollector(self.config.get('api_keys', {}))
        self.data_processor = DataProcessor()
        self.video_generator = VideoGenerator(self.config.get('video', {}))
        self.digital_human = DigitalHuman(self.config.get('digital_human', {}))
        
        # 初始化任務隊列
        self.task_queue = queue.Queue()
        self.tasks = {}
        self.task_worker_thread = None
        self.is_worker_running = False
        
        # 啟動任務處理線程
        self.start_task_worker()
    
    def process_article(self, article_text, options=None):
        """處理文章
        
        參數:
            article_text (str): 文章文本
            options (dict, 可選): 處理選項
            
        返回:
            dict: 處理結果
        """
        if not article_text:
            self.logger.error("文章文本為空")
            return None
            
        if options is None:
            options = {}
            
        # 合併選項
        strategy = options.get('strategy', 'sentence')
        character_rate = float(options.get('character_rate', 5.0))
        
        self.logger.info(f"開始處理文章，使用策略: {strategy}, 字符速率: {character_rate}")
        
        try:
            # 處理文章內容
            content_result = self.content_processor.process_article(article_text, strategy)
            
            # 生成字幕
            subtitles = self.subtitle_manager.generate_from_text(
                "\n".join(content_result['segments']),
                character_rate=character_rate
            )
            
            # 整合處理結果
            result = {
                'title': content_result.get('title', '未命名文章'),
                'segments': content_result['segments'],
                'stock_codes': content_result['stock_codes'],
                'keywords': content_result['keywords'],
                'sentiment': content_result['sentiment'],
                'subtitles': subtitles
            }
            
            self.logger.info(f"文章處理完成: {len(result['segments'])} 個段落, {len(subtitles)} 條字幕")
            return result
            
        except Exception as e:
            self.logger.error(f"處理文章時出錯: {e}")
            return None
    
    def generate_stock_video(self, ticker, subtitles, options=None):
        """生成股票視頻
        
        參數:
            ticker (str): 股票代碼
            subtitles (list): 字幕列表
            options (dict, 可選): 生成選項
            
        返回:
            str: 任務 ID
        """
        if not ticker:
            self.logger.error("股票代碼為空")
            return None
            
        if options is None:
            options = {}
            
        # 創建任務 ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{ticker}"
        
        # 創建任務
        task = {
            'id': task_id,
            'type': 'stock_video',
            'status': 'waiting',
            'ticker': ticker,
            'subtitles': subtitles,
            'options': options,
            'progress': 0,
            'result': None,
            'error': None,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 添加到任務字典
        self.tasks[task_id] = task
        
        # 添加到任務隊列
        self.task_queue.put(task)
        
        self.logger.info(f"已創建股票視頻生成任務: {task_id}")
        return task_id
    
    def start_task_worker(self):
        """啟動任務處理線程"""
        if self.is_worker_running:
            return
            
        self.is_worker_running = True
        self.task_worker_thread = threading.Thread(target=self._task_worker)
        self.task_worker_thread.daemon = True
        self.task_worker_thread.start()
        
        self.logger.info("任務處理線程已啟動")
    
    def stop_task_worker(self):
        """停止任務處理線程"""
        self.is_worker_running = False
        if self.task_worker_thread:
            self.task_worker_thread.join(timeout=1.0)
            self.task_worker_thread = None
            
        self.logger.info("任務處理線程已停止")
    
    def _task_worker(self):
        """任務處理線程"""
        while self.is_worker_running:
            try:
                # 嘗試獲取任務，超時 1 秒
                task = self.task_queue.get(timeout=1.0)
                
                # 更新任務狀態
                task['status'] = 'processing'
                self.tasks[task['id']] = task
                
                # 根據任務類型執行不同處理
                if task['type'] == 'stock_video':
                    self._process_stock_video_task(task)
                else:
                    self.logger.warning(f"未知的任務類型: {task['type']}")
                    task['status'] = 'failed'
                    task['error'] = f"未知的任務類型: {task['type']}"
                    
                # 標記任務完成
                self.task_queue.task_done()
                
            except queue.Empty:
                # 隊列為空，繼續等待
                continue
                
            except Exception as e:
                self.logger.error(f"處理任務時出錯: {e}")
                if 'task' in locals() and task:
                    task['status'] = 'failed'
                    task['error'] = str(e)
                    self.tasks[task['id']] = task
    
    def _process_stock_video_task(self, task):
        """處理股票視頻生成任務
        
        參數:
            task (dict): 任務信息
        """
        try:
            ticker = task['ticker']
            subtitles = task['subtitles']
            options = task['options']
            
            # 更新進度
            self._update_task_progress(task['id'], 5, "獲取股票數據")
            
            # 獲取股票數據
            stock_data = self.stock_collector.get_stock_data(ticker)
            if stock_data is None or stock_data.empty:
                raise ValueError(f"無法獲取股票數據: {ticker}")
                
            # 處理股票數據
            self._update_task_progress(task['id'], 10, "處理股票數據")
            processed_data = self.data_processor.process_stock_data(stock_data)
            
            # 生成字幕文件
            self._update_task_progress(task['id'], 15, "生成字幕文件")
            subtitle_file = None
            if subtitles:
                subtitle_format = options.get('subtitle_format', 'srt')
                subtitle_file = os.path.join(self.output_dir, f"{ticker}_subtitles.{subtitle_format}")
                
                if subtitle_format == 'srt':
                    self.subtitle_manager.export_to_srt(subtitles, subtitle_file)
                elif subtitle_format == 'vtt':
                    self.subtitle_manager.export_to_vtt(subtitles, subtitle_file)
                else:
                    self.logger.warning(f"不支援的字幕格式: {subtitle_format}")
            
            # 生成音頻
            self._update_task_progress(task['id'], 20, "生成語音")
            audio_files = []
            if subtitles and options.get('enable_tts', True):
                # 設置 TTS 引擎
                tts_engine = options.get('tts_engine', 'azure')
                tts_voice = options.get('tts_voice', 'zh-TW-YunJheNeural')
                tts_rate = float(options.get('tts_rate', 1.0))
                
                self.tts_controller.set_engine(tts_engine)
                self.tts_controller.set_voice(tts_voice)
                self.tts_controller.set_speech_rate(tts_rate)
                
                # 批量生成語音
                audio_files = self.tts_controller.batch_generate_speech(
                    subtitles,
                    os.path.join(self.output_dir, 'audio'),
                    f"{ticker}_speech"
                )
            
            # 合併音頻
            self._update_task_progress(task['id'], 30, "合併音頻")
            merged_audio = None
            if audio_files:
                # 準備音頻文件和時間點
                audio_with_times = []
                for i, audio_file in enumerate(audio_files):
                    if i < len(subtitles):
                        audio_with_times.append((audio_file, subtitles[i]['startTime']))
                
                # 合併音頻
                merged_audio = self.sync_manager.merge_audio_files(
                    audio_with_times,
                    os.path.join(self.output_dir, f"{ticker}_merged_audio.mp3")
                )
            
            # 處理數位人
            digital_human_video = None
            if options.get('enable_digital_human', False):
                self._update_task_progress(task['id'], 40, "生成數位人視頻")
                template_name = options.get('digital_human_template', 'default_avatar')
                
                if merged_audio:
                    digital_human_video = self.digital_human.generate_video(
                        template_name,
                        merged_audio,
                        os.path.join(self.output_dir, f"{ticker}_digital_human.mp4")
                    )
            
            # 生成股票視頻
            self._update_task_progress(task['id'], 60, "生成股票視頻")
            stock_video = self.video_generator.create_stock_video(
                processed_data,
                subtitles,
                merged_audio,
                os.path.join(self.output_dir, f"{ticker}_stock_video.mp4"),
                digital_human_video
            )
            
            if not stock_video:
                raise ValueError("生成股票視頻失敗")
                
            # 創建時間軸數據
            self._update_task_progress(task['id'], 90, "完成視頻生成")
            timeline = self.sync_manager.create_timeline(subtitles, audio_files)
            
            # 保存時間軸
            timeline_file = os.path.join(self.output_dir, f"{ticker}_timeline.json")
            self.sync_manager.save_timeline(timeline_file)
            
            # 完成任務
            task['status'] = 'completed'
            task['progress'] = 100
            task['result'] = {
                'video_file': stock_video,
                'subtitle_file': subtitle_file,
                'audio_file': merged_audio,
                'timeline_file': timeline_file,
                'digital_human_video': digital_human_video
            }
            
            self.tasks[task['id']] = task
            self.logger.info(f"股票視頻生成任務完成: {task['id']}")
            
        except Exception as e:
            self.logger.error(f"生成股票視頻時出錯: {e}")
            task['status'] = 'failed'
            task['error'] = str(e)
            self.tasks[task['id']] = task
    
    def _update_task_progress(self, task_id, progress, message):
        """更新任務進度
        
        參數:
            task_id (str): 任務 ID
            progress (int): 進度百分比 (0-100)
            message (str): 進度消息
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task['progress'] = progress
            task['progress_message'] = message
            self.tasks[task_id] = task
            
            self.logger.debug(f"任務 {task_id} 進度更新: {progress}%, {message}")
    
    def get_task_status(self, task_id):
        """獲取任務狀態
        
        參數:
            task_id (str): 任務 ID
            
        返回:
            dict: 任務狀態
        """
        if task_id in self.tasks:
            return self.tasks[task_id]
        return None
    
    def get_all_tasks(self):
        """獲取所有任務
        
        返回:
            list: 任務列表
        """
        return list(self.tasks.values())
    
    def cancel_task(self, task_id):
        """取消任務
        
        參數:
            task_id (str): 任務 ID
            
        返回:
            bool: 是否成功
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task['status'] in ['waiting', 'processing']:
                task['status'] = 'cancelled'
                self.tasks[task_id] = task
                self.logger.info(f"任務已取消: {task_id}")
                return True
        return False
    
    def save_project(self, project_data, output_file=None):
        """保存項目
        
        參數:
            project_data (dict): 項目數據
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            str: 文件路徑
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.output_dir, f"project_{timestamp}.json")
            
        try:
            # 添加時間戳
            project_data['saved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"項目已保存: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"保存項目時出錯: {e}")
            return None
    
    def load_project(self, project_file):
        """載入項目
        
        參數:
            project_file (str): 項目文件路徑
            
        返回:
            dict: 項目數據
        """
        if not os.path.exists(project_file):
            self.logger.error(f"找不到項目文件: {project_file}")
            return None
            
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
                
            self.logger.info(f"項目已載入: {project_file}")
            return project_data
            
        except Exception as e:
            self.logger.error(f"載入項目時出錯: {e}")
            return None
    
    def process_batch(self, batch_data):
        """批次處理多個任務
        
        參數:
            batch_data (list): 批次任務數據列表
            
        返回:
            list: 任務 ID 列表
        """
        task_ids = []
        
        for item in batch_data:
            task_type = item.get('type')
            
            if task_type == 'stock_video':
                ticker = item.get('ticker')
                subtitles = item.get('subtitles')
                options = item.get('options')
                
                task_id = self.generate_stock_video(ticker, subtitles, options)
                if task_id:
                    task_ids.append(task_id)
                    
            elif task_type == 'article_process':
                article_text = item.get('article')
                options = item.get('options')
                
                # 處理文章是同步的，直接返回結果
                result = self.process_article(article_text, options)
                
                # 儲存結果為任務
                if result:
                    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_article"
                    task = {
                        'id': task_id,
                        'type': 'article_process',
                        'status': 'completed',
                        'progress': 100,
                        'result': result,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.tasks[task_id] = task
                    task_ids.append(task_id)
            else:
                self.logger.warning(f"未知的任務類型: {task_type}")
        
        self.logger.info(f"批次處理已創建 {len(task_ids)} 個任務")
        return task_ids
    
    def get_recent_projects(self, limit=10):
        """獲取最近的項目
        
        參數:
            limit (int): 最大數量
            
        返回:
            list: 項目列表
        """
        projects = []
        
        try:
            # 掃描輸出目錄
            for filename in os.listdir(self.output_dir):
                if filename.startswith('project_') and filename.endswith('.json'):
                    file_path = os.path.join(self.output_dir, filename)
                    
                    # 獲取文件信息
                    stat = os.stat(file_path)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    # 嘗試讀取項目標題
                    title = filename.replace('project_', '').replace('.json', '')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'title' in data:
                                title = data['title']
                    except:
                        pass
                    
                    projects.append({
                        'file_path': file_path,
                        'title': title,
                        'modified_time': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'size': stat.st_size
                    })
            
            # 按修改時間排序
            projects.sort(key=lambda x: x['modified_time'], reverse=True)
            
            # 限制數量
            return projects[:limit]
            
        except Exception as e:
            self.logger.error(f"獲取最近項目時出錯: {e}")
            return []
    
    def search_stock(self, keyword):
        """搜索股票
        
        參數:
            keyword (str): 關鍵字或股票代碼
            
        返回:
            list: 搜索結果
        """
        try:
            # 如果關鍵字看起來像股票代碼，則直接搜索
            if len(keyword) <= 5 and (keyword.isalpha() or keyword.isdigit()):
                try:
                    stock_data = self.stock_collector.get_stock_data(keyword)
                    if stock_data is not None and not stock_data.empty:
                        return [{
                            'ticker': keyword,
                            'name': stock_data.attrs.get('name', keyword),
                            'market': stock_data.attrs.get('market', 'unknown'),
                            'last_price': stock_data['Close'].iloc[-1],
                            'change': stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2],
                            'change_percent': (stock_data['Close'].iloc[-1] / stock_data['Close'].iloc[-2] - 1) * 100
                        }]
                except Exception as e:
                    self.logger.warning(f"直接搜索股票失敗: {e}")
            
            # 使用關鍵字搜索
            search_results = self.stock_collector.search_stocks(keyword)
            return search_results
            
        except Exception as e:
            self.logger.error(f"搜索股票時出錯: {e}")
            return []
    
    def generate_report(self, ticker, period='1y', report_type='basic'):
        """生成報告
        
        參數:
            ticker (str): 股票代碼
            period (str): 時間範圍
            report_type (str): 報告類型 ('basic', 'technical', 'comprehensive')
            
        返回:
            dict: 報告數據
        """
        if not ticker:
            self.logger.error("股票代碼為空")
            return None
            
        try:
            # 獲取股票數據
            stock_data = self.stock_collector.get_stock_data(ticker, period=period)
            if stock_data is None or stock_data.empty:
                raise ValueError(f"無法獲取股票數據: {ticker}")
                
            # 處理股票數據
            processed_data = self.data_processor.process_stock_data(stock_data)
            
            # 生成報告
            if report_type == 'basic':
                report = self._generate_basic_report(processed_data)
            elif report_type == 'technical':
                report = self._generate_technical_report(processed_data)
            elif report_type == 'comprehensive':
                report = self._generate_comprehensive_report(processed_data)
            else:
                raise ValueError(f"不支援的報告類型: {report_type}")
                
            self.logger.info(f"已生成 {report_type} 報告: {ticker}")
            return report
            
        except Exception as e:
            self.logger.error(f"生成報告時出錯: {e}")
            return None
    
    def _generate_basic_report(self, stock_data):
        """生成基本報告
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            
        返回:
            dict: 報告數據
        """
        # 獲取基本信息
        ticker = stock_data.attrs.get('ticker', 'UNKNOWN')
        last_price = stock_data['Close'].iloc[-1]
        prev_price = stock_data['Close'].iloc[-2]
        price_change = last_price - prev_price
        price_change_pct = (price_change / prev_price) * 100
        
        # 計算統計指標
        summary = {
            'ticker': ticker,
            'name': stock_data.attrs.get('name', ticker),
            'date': stock_data.index[-1].strftime('%Y-%m-%d'),
            'last_price': last_price,
            'price_change': price_change,
            'price_change_pct': price_change_pct,
            'volume': stock_data['Volume'].iloc[-1] if 'Volume' in stock_data.columns else None,
            'high_52w': stock_data['High'].max(),
            'low_52w': stock_data['Low'].min(),
            'avg_20d': stock_data['Close'].iloc[-20:].mean() if len(stock_data) >= 20 else None
        }
        
        # 生成圖表
        chart_file = self.data_processor.generate_stock_chart(stock_data, 'line')
        
        # 合成報告
        report = {
            'summary': summary,
            'chart_file': chart_file,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'basic'
        }
        
        return report
    
    def _generate_technical_report(self, stock_data):
        """生成技術分析報告
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            
        返回:
            dict: 報告數據
        """
        # 生成基本報告
        basic_report = self._generate_basic_report(stock_data)
        
        # 分析技術指標
        performance = self.data_processor.analyze_stock_performance(stock_data, 30)
        
        # 檢測支撐和阻力位
        support_resistance = self.data_processor._detect_support_resistance(stock_data)
        
        # 識別技術形態
        patterns = self.data_processor._identify_patterns(stock_data)
        
        # 生成多時間週期圖表
        charts = self.data_processor.generate_multiple_timeframe_charts(stock_data)
        
        # 合成報告
        report = {
            **basic_report,
            'performance': performance,
            'support_resistance': support_resistance,
            'patterns': patterns,
            'charts': charts,
            'type': 'technical'
        }
        
        return report
    
    def _generate_comprehensive_report(self, stock_data):
        """生成綜合報告
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            
        返回:
            dict: 報告數據
        """
        # 生成技術分析報告
        technical_report = self._generate_technical_report(stock_data)
        
        # 獲取基本面信息
        ticker = stock_data.attrs.get('ticker', 'UNKNOWN')
        stock_info = self.stock_collector.get_stock_info(ticker)
        
        # 獲取最新新聞
        news = self.stock_collector.get_latest_news(ticker)
        
        # 獲取市場指數
        market_data = None
        try:
            index_symbol = "^GSPC"  # S&P 500
            if ticker.endswith('.TW'):
                index_symbol = "^TWII"  # 台灣加權指數
            elif ticker.endswith('.HK'):
                index_symbol = "^HSI"  # 恆生指數
                
            market_data = self.stock_collector.get_market_index(index_symbol)
        except Exception as e:
            self.logger.warning(f"獲取市場指數失敗: {e}")
        
        # 合成報告
        report = {
            **technical_report,
            'info': stock_info,
            'news': news,
            'market_data': market_data.attrs if market_data is not None else None,
            'type': 'comprehensive'
        }
        
        return report
    
    def shutdown(self):
        """關閉控制器"""
        self.stop_task_worker()
        self.logger.info("控制器已關閉")