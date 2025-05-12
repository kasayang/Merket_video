#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 視頻生成器
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 設置 Matplotlib 後端，避免需要 GUI
import logging
from datetime import datetime
from pydub import AudioSegment
import pandas as pd
import threading
import queue

class VideoGenerator:
    """視頻生成器
    
    負責將資料、圖表、字幕和音頻合成為完整的視頻。
    """
    
    def __init__(self, config=None, output_dir='output'):
        """初始化視頻生成器
        
        參數:
            config (dict, 可選): 配置設定
            output_dir (str): 輸出目錄
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.output_dir = output_dir
        self.frames_queue = queue.Queue(maxsize=100)  # 用於多執行緒處理的佇列
        
        # 確保輸出目錄存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 從配置中讀取設定
        self.width = self.config.get('width', 1920)
        self.height = self.config.get('height', 1080)
        self.fps = self.config.get('fps', 30)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.watermark = self.config.get('watermark', True)
        
    def create_stock_video(self, stock_data, subtitle_data, audio_file=None, output_file=None, digital_human=None):
        """創建股票分析視頻
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            subtitle_data (list): 字幕數據列表
            audio_file (str, 可選): 音頻文件路徑
            output_file (str, 可選): 輸出文件路徑
            digital_human (dict, 可選): 數字人設定
            
        返回:
            str: 生成的視頻檔案路徑
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            output_file = os.path.join(self.output_dir, f"{ticker}_{timestamp}.mp4")
            
        self.logger.info(f"開始生成股票視頻: {output_file}")
        
        # 準備音頻
        audio_duration = 0
        if audio_file and os.path.exists(audio_file):
            try:
                audio = AudioSegment.from_file(audio_file)
                audio_duration = len(audio) / 1000.0  # 轉換為秒
            except Exception as e:
                self.logger.error(f"讀取音頻文件失敗: {e}")
                audio_duration = 0
        
        # 如果沒有音頻，使用字幕持續時間
        if audio_duration == 0 and subtitle_data:
            audio_duration = max([sub['endTime'] for sub in subtitle_data])
        
        # 如果仍然沒有持續時間，使用預設值
        if audio_duration == 0:
            audio_duration = 60  # 預設 60 秒
            
        # 計算總幀數
        total_frames = int(audio_duration * self.fps)
        
        # 初始化視頻寫入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(output_file, fourcc, self.fps, (self.width, self.height))
        
        # 啟動圖表生成執行緒
        chart_thread = threading.Thread(target=self._generate_stock_frames, 
                                        args=(stock_data, total_frames, subtitle_data, digital_human))
        chart_thread.start()
        
        # 主執行緒從佇列獲取圖表並寫入視頻
        frames_processed = 0
        while frames_processed < total_frames:
            try:
                frame = self.frames_queue.get(timeout=30)  # 最多等待 30 秒
                video_writer.write(frame)
                frames_processed += 1
                
                # 更新進度
                if frames_processed % 30 == 0:
                    self.logger.info(f"視頻生成進度: {frames_processed}/{total_frames} 幀 ({frames_processed/total_frames*100:.1f}%)")
                    
                self.frames_queue.task_done()
            except queue.Empty:
                self.logger.warning("等待圖表生成逾時，可能發生執行緒死鎖或效能問題")
                break
        
        # 釋放資源
        video_writer.release()
        
        # 檢查圖表執行緒是否仍在運行
        if chart_thread.is_alive():
            self.logger.warning("圖表生成執行緒仍在運行，等待它完成...")
            chart_thread.join(timeout=30)
        
        # 如果音頻存在，將音頻添加到視頻
        if audio_file and os.path.exists(audio_file):
            output_with_audio = self._add_audio_to_video(output_file, audio_file)
            if output_with_audio:
                # 如果添加音頻成功，替換原始視頻
                if os.path.exists(output_file):
                    os.remove(output_file)
                output_file = output_with_audio
        
        self.logger.info(f"股票視頻生成完成: {output_file}")
        return output_file
        
    def _generate_stock_frames(self, stock_data, total_frames, subtitle_data, digital_human=None):
        """生成股票視頻的每一幀
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            total_frames (int): 總幀數
            subtitle_data (list): 字幕數據
            digital_human (dict, 可選): 數字人設定
        """
        try:
            # 股票數據相關變數
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            dates = stock_data.index
            prices = stock_data['Close']
            
            # 生成視頻幀
            for frame_idx in range(total_frames):
                # 計算當前時間點
                current_time = frame_idx / self.fps
                
                # 創建空白畫布
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                
                # 填充背景
                frame[:, :] = (30, 30, 30)  # 深灰色背景
                
                # 繪製邊框和標題
                self._draw_frame_border(frame)
                self._draw_title(frame, f"{ticker} 股票分析")
                
                # 繪製股票圖表
                chart_image = self._generate_stock_chart(stock_data, current_time)
                if chart_image is not None:
                    chart_h, chart_w, _ = chart_image.shape
                    y_offset = 120  # 標題下方的位置
                    x_offset = (self.width - chart_w) // 2
                    frame[y_offset:y_offset+chart_h, x_offset:x_offset+chart_w] = chart_image
                
                # 繪製當前字幕
                current_subtitle = self._get_current_subtitle(subtitle_data, current_time)
                if current_subtitle:
                    subtitle_y = self.height - 150  # 底部位置
                    self._draw_subtitle(frame, current_subtitle['text'], subtitle_y)
                
                # 添加數字人
                if digital_human and 'frames' in digital_human:
                    dh_frame_idx = int(current_time * digital_human.get('fps', 30)) % len(digital_human['frames'])
                    dh_frame = digital_human['frames'][dh_frame_idx]
                    self._overlay_digital_human(frame, dh_frame, digital_human.get('position', 'bottom_right'))
                
                # 添加水印
                if self.watermark:
                    self._add_watermark(frame)
                
                # 添加到佇列
                self.frames_queue.put(frame)
                
        except Exception as e:
            self.logger.error(f"生成圖表幀時出錯: {e}")
            # 確保即使發生錯誤，佇列中也有足夠的幀
            remaining_frames = total_frames - frame_idx - 1
            for _ in range(remaining_frames):
                # 創建錯誤幀
                error_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                error_frame[:, :] = (30, 30, 30)  # 深灰色背景
                cv2.putText(error_frame, "圖表生成錯誤", (self.width//2-150, self.height//2), 
                            self.font, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
                self.frames_queue.put(error_frame)
    
    def _generate_stock_chart(self, stock_data, current_time):
        """為特定時間點生成股票圖表
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            current_time (float): 當前時間點 (秒)
            
        返回:
            numpy.ndarray: 圖表圖像
        """
        try:
            # 根據當前時間計算數據索引
            # 設計一個動畫效果：逐漸展示更多數據
            progress = min(1.0, current_time / 20.0)  # 20秒內完整顯示
            chart_width = 1600
            chart_height = 800
            
            # 創建圖表
            plt.figure(figsize=(chart_width/100, chart_height/100), dpi=100)
            plt.style.use('dark_background')
            
            # 獲取數據
            dates = stock_data.index
            close_prices = stock_data['Close']
            
            # 計算顯示多少數據
            data_len = len(dates)
            display_len = max(10, int(data_len * progress))
            
            # 價格圖
            ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=3, colspan=1)
            ax1.plot(dates[-display_len:], close_prices[-display_len:], color='#1E90FF', linewidth=2)
            
            # 添加移動平均線
            if 'SMA_20' in stock_data.columns:
                ax1.plot(dates[-display_len:], stock_data['SMA_20'][-display_len:], color='#FF8C00', linewidth=1, label='SMA 20')
            if 'SMA_50' in stock_data.columns:
                ax1.plot(dates[-display_len:], stock_data['SMA_50'][-display_len:], color='#FF4500', linewidth=1, label='SMA 50')
            if 'SMA_200' in stock_data.columns:
                ax1.plot(dates[-display_len:], stock_data['SMA_200'][-display_len:], color='#9400D3', linewidth=1, label='SMA 200')
                
            ax1.set_title('價格走勢', color='white')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 交易量圖
            ax2 = plt.subplot2grid((6, 1), (3, 0), rowspan=1, colspan=1, sharex=ax1)
            if 'Volume' in stock_data.columns:
                ax2.bar(dates[-display_len:], stock_data['Volume'][-display_len:], color='#1E90FF', alpha=0.7)
                ax2.set_title('交易量', color='white')
                ax2.grid(True, alpha=0.3)
            
            # RSI 指標
            ax3 = plt.subplot2grid((6, 1), (4, 0), rowspan=1, colspan=1, sharex=ax1)
            if 'RSI' in stock_data.columns:
                ax3.plot(dates[-display_len:], stock_data['RSI'][-display_len:], color='#FF4500', linewidth=1.5)
                ax3.axhline(70, color='#FF4500', linestyle='--', alpha=0.5)
                ax3.axhline(30, color='#1E90FF', linestyle='--', alpha=0.5)
                ax3.set_title('RSI', color='white')
                ax3.grid(True, alpha=0.3)
                ax3.set_ylim(0, 100)
            
            # MACD 指標
            ax4 = plt.subplot2grid((6, 1), (5, 0), rowspan=1, colspan=1, sharex=ax1)
            if all(col in stock_data.columns for col in ['MACD', 'Signal_Line', 'MACD_Histogram']):
                ax4.plot(dates[-display_len:], stock_data['MACD'][-display_len:], color='#1E90FF', linewidth=1.5, label='MACD')
                ax4.plot(dates[-display_len:], stock_data['Signal_Line'][-display_len:], color='#FF4500', linewidth=1, label='Signal')
                
                # 繪製 MACD 柱狀圖
                hist = stock_data['MACD_Histogram'][-display_len:].values
                for i, date in enumerate(dates[-display_len:]):
                    if i < len(hist):
                        if hist[i] >= 0:
                            ax4.bar(date, hist[i], color='#00FF00', alpha=0.5)
                        else:
                            ax4.bar(date, hist[i], color='#FF4500', alpha=0.5)
                
                ax4.set_title('MACD', color='white')
                ax4.legend(loc='upper left')
                ax4.grid(True, alpha=0.3)
            
            # 隱藏 x 軸標籤 (除了最後一個子圖)
            plt.setp([a.get_xticklabels() for a in [ax1, ax2, ax3]], visible=False)
            plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1, hspace=0.3)
            
            # 將圖表轉換為圖像
            plt.savefig('temp_chart.png', transparent=False)
            plt.close()
            
            chart_image = cv2.imread('temp_chart.png')
            
            # 刪除臨時檔案
            if os.path.exists('temp_chart.png'):
                os.remove('temp_chart.png')
                
            return chart_image
            
        except Exception as e:
            self.logger.error(f"生成股票圖表時出錯: {e}")
            return None
    
    def _draw_frame_border(self, frame):
        """繪製視頻邊框
        
        參數:
            frame (numpy.ndarray): 視頻幀
        """
        # 頂部和底部邊框
        cv2.rectangle(frame, (0, 0), (self.width, 80), (40, 40, 40), -1)
        cv2.rectangle(frame, (0, self.height-100), (self.width, self.height), (40, 40, 40), -1)
        
        # 分隔線
        cv2.line(frame, (0, 80), (self.width, 80), (60, 60, 60), 2)
        cv2.line(frame, (0, self.height-100), (self.width, self.height-100), (60, 60, 60), 2)
    
    def _draw_title(self, frame, title):
        """繪製視頻標題
        
        參數:
            frame (numpy.ndarray): 視頻幀
            title (str): 標題文字
        """
        cv2.putText(frame, title, (20, 50), self.font, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
        
        # 添加時間戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        text_size = cv2.getTextSize(timestamp, self.font, 0.7, 1)[0]
        cv2.putText(frame, timestamp, (self.width - text_size[0] - 20, 50), self.font, 0.7, (200, 200, 200), 1, cv2.LINE_AA)
    
    def _draw_subtitle(self, frame, text, y_pos):
        """繪製字幕
        
        參數:
            frame (numpy.ndarray): 視頻幀
            text (str): 字幕文字
            y_pos (int): 垂直位置
        """
        # 計算文字大小以居中
        text_size = cv2.getTextSize(text, self.font, 1.0, 2)[0]
        x_pos = (self.width - text_size[0]) // 2
        
        # 繪製字幕背景
        cv2.rectangle(frame, (x_pos - 10, y_pos - 10), (x_pos + text_size[0] + 10, y_pos + text_size[1] + 10), (0, 0, 0), -1)
        cv2.rectangle(frame, (x_pos - 10, y_pos - 10), (x_pos + text_size[0] + 10, y_pos + text_size[1] + 10), (80, 80, 80), 1)
        
        # 繪製字幕文字
        cv2.putText(frame, text, (x_pos, y_pos + text_size[1]), self.font, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    
    def _get_current_subtitle(self, subtitle_data, current_time):
        """獲取當前時間點的字幕
        
        參數:
            subtitle_data (list): 字幕數據列表
            current_time (float): 當前時間點 (秒)
            
        返回:
            dict: 當前字幕數據
        """
        if not subtitle_data:
            return None
            
        for sub in subtitle_data:
            if sub['startTime'] <= current_time <= sub['endTime']:
                return sub
                
        return None
    
    def _overlay_digital_human(self, frame, dh_frame, position='bottom_right'):
        """疊加數字人畫面
        
        參數:
            frame (numpy.ndarray): 視頻幀
            dh_frame (numpy.ndarray): 數字人視頻幀
            position (str): 位置 ('bottom_right', 'bottom_left', 'top_right', 'top_left')
        """
        if dh_frame is None:
            return
            
        # 調整數字人大小
        dh_height = self.height // 3
        dh_width = int(dh_frame.shape[1] * (dh_height / dh_frame.shape[0]))
        dh_frame_resized = cv2.resize(dh_frame, (dh_width, dh_height))
        
        # 確定位置
        if position == 'bottom_right':
            x_offset = self.width - dh_width - 20
            y_offset = self.height - dh_height - 120
        elif position == 'bottom_left':
            x_offset = 20
            y_offset = self.height - dh_height - 120
        elif position == 'top_right':
            x_offset = self.width - dh_width - 20
            y_offset = 100
        elif position == 'top_left':
            x_offset = 20
            y_offset = 100
        else:
            x_offset = self.width - dh_width - 20
            y_offset = self.height - dh_height - 120
        
        # 疊加畫面 (需要考慮 alpha 通道)
        if dh_frame_resized.shape[2] == 4:  # 帶 alpha 通道
            alpha = dh_frame_resized[:, :, 3] / 255.0
            alpha = np.expand_dims(alpha, axis=2)
            dh_rgb = dh_frame_resized[:, :, :3]
            
            # 選擇框架中的相應區域
            roi = frame[y_offset:y_offset+dh_height, x_offset:x_offset+dh_width]
            
            # 混合圖像
            blended = (dh_rgb * alpha + roi * (1 - alpha)).astype(np.uint8)
            frame[y_offset:y_offset+dh_height, x_offset:x_offset+dh_width] = blended
        else:  # 無 alpha 通道，直接覆蓋
            frame[y_offset:y_offset+dh_height, x_offset:x_offset+dh_width] = dh_frame_resized
    
    def _add_watermark(self, frame):
        """添加浮水印
        
        參數:
            frame (numpy.ndarray): 視頻幀
        """
        watermark_text = "自動生成"
        text_size = cv2.getTextSize(watermark_text, self.font, 0.5, 1)[0]
        
        # 浮水印位置：右下角
        x = self.width - text_size[0] - 10
        y = self.height - 10
        
        # 半透明背景
        alpha = 0.5
        overlay = frame.copy()
        cv2.putText(overlay, watermark_text, (x, y), self.font, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    def _add_audio_to_video(self, video_file, audio_file):
        """將音頻添加到視頻
        
        參數:
            video_file (str): 視頻文件路徑
            audio_file (str): 音頻文件路徑
            
        返回:
            str: 帶音頻的視頻檔案路徑
        """
        output_file = os.path.splitext(video_file)[0] + "_with_audio.mp4"
        
        try:
            import subprocess
            
            # 使用 ffmpeg 合併視頻和音頻
            cmd = [
                'ffmpeg',
                '-i', video_file,
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-shortest',
                output_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.info(f"成功將音頻添加到視頻: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"添加音頻到視頻時出錯: {e}")
            return None
    
    def load_digital_human(self, video_path):
        """載入數字人視頻
        
        參數:
            video_path (str): 數字人視頻路徑
            
        返回:
            dict: 數字人數據
        """
        if not os.path.exists(video_path):
            self.logger.error(f"找不到數字人視頻: {video_path}")
            return None
            
        try:
            dh_frames = []
            cap = cv2.VideoCapture(video_path)
            
            # 獲取視頻信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 讀取所有幀
            for _ in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break
                dh_frames.append(frame)
                
            cap.release()
            
            self.logger.info(f"成功載入數字人視頻: {len(dh_frames)} 幀, {fps} FPS")
            
            return {
                'frames': dh_frames,
                'fps': fps,
                'frame_count': frame_count
            }
            
        except Exception as e:
            self.logger.error(f"載入數字人視頻時出錯: {e}")
            return None
    # 在video_generator.py中添加方法
    def replace_media_element(self, timeline, track_type, item_id, new_file):
        """替換時間軸中的媒體元素
        
        參數:
            timeline (dict): 時間軸數據
            track_type (str): 軌道類型 ('video', 'audio')
            item_id (str): 項目ID
            new_file (str): 新文件路徑
            
        返回:
            bool: 是否成功
        """
        for item in timeline.get(track_type, []):
            if item.get('id') == item_id:
                # 備份原始文件信息
                original_file = item.get('file')
                
                # 更新文件路徑
                item['file'] = new_file
                
                self.logger.info(f"已替換 {track_type} 軌道中的媒體元素: {item_id}")
                return True
                
        self.logger.warning(f"找不到要替換的媒體元素: {track_type}/{item_id}")
        return False