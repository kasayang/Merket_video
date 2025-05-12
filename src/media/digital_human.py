#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 數位人模組
"""

import os
import cv2
import json
import logging
import numpy as np
from datetime import datetime
import subprocess
import tempfile

class DigitalHuman:
    """數位人模組
    
    負責處理數位人視頻和音頻同步，生成數位主播內容。
    """
    
    def __init__(self, config=None):
        """初始化數位人模組
        
        參數:
            config (dict, 可選): 配置設定
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.templates_dir = self.config.get('templates_dir', 'templates/digital_humans')
        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'digital_humans')
        
        # 確保目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 載入預設設定
        self.default_settings = {
            'scaling': 0.3,          # 數位人大小比例
            'position': 'bottom_right',  # 位置
            'audio_offset': 0.0,     # 音頻偏移（秒）
            'background_color': (0, 0, 0)  # 背景顏色（黑色）
        }
    
    def list_templates(self):
        """列出可用的數位人模板
        
        返回:
            list: 模板列表
        """
        templates = []
        
        if not os.path.exists(self.templates_dir):
            self.logger.warning(f"模板目錄不存在: {self.templates_dir}")
            return templates
            
        # 掃描模板目錄
        for template_name in os.listdir(self.templates_dir):
            # 檢查是否是視頻文件
            if template_name.endswith(('.mp4', '.avi', '.mov')):
                template_path = os.path.join(self.templates_dir, template_name)
                
                # 檢查對應的元數據
                metadata_path = os.path.join(self.templates_dir, 
                                            os.path.splitext(template_name)[0] + '.json')
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception as e:
                        self.logger.warning(f"讀取模板元數據失敗: {metadata_path}, {e}")
                        metadata = {}
                else:
                    metadata = {}
                
                # 準備模板信息
                template_info = {
                    'name': os.path.splitext(template_name)[0],
                    'file_path': template_path,
                    'metadata_path': metadata_path if os.path.exists(metadata_path) else None,
                    'description': metadata.get('description', ''),
                    'gender': metadata.get('gender', 'neutral'),
                    'language': metadata.get('language', 'zh-TW'),
                    'preview': metadata.get('preview', '')
                }
                
                templates.append(template_info)
        
        self.logger.info(f"找到 {len(templates)} 個數位人模板")
        return templates
    
    def generate_video(self, template_name, audio_file, output_file=None, settings=None):
        """生成數位人視頻
        
        參數:
            template_name (str): 模板名稱
            audio_file (str): 音頻文件路徑
            output_file (str, 可選): 輸出文件路徑
            settings (dict, 可選): 設定
            
        返回:
            str: 生成的視頻檔案路徑
        """
        # 設置預設輸出檔案
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"{template_name}_{timestamp}.mp4")
            
        # 合併設定
        if settings is None:
            settings = {}
        combined_settings = {**self.default_settings, **settings}
        
        # 查找模板
        template_path = os.path.join(self.templates_dir, f"{template_name}.mp4")
        if not os.path.exists(template_path):
            # 嘗試其他副檔名
            for ext in ['.avi', '.mov']:
                alt_path = os.path.join(self.templates_dir, f"{template_name}{ext}")
                if os.path.exists(alt_path):
                    template_path = alt_path
                    break
                    
        if not os.path.exists(template_path):
            self.logger.error(f"找不到數位人模板: {template_name}")
            return None
            
        # 檢查音頻文件
        if not os.path.exists(audio_file):
            self.logger.error(f"找不到音頻文件: {audio_file}")
            return None
            
        try:
            # 讀取音頻長度
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_file)
            audio_duration = len(audio) / 1000.0  # 轉換為秒
            
            # 讀取模板視頻
            cap = cv2.VideoCapture(template_path)
            
            # 獲取視頻信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            template_duration = frame_count / fps
            
            # 計算循環次數
            loop_count = int(np.ceil(audio_duration / template_duration))
            
            # 創建輸出視頻
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            
            # 循環視頻模板以匹配音頻長度
            for loop in range(loop_count):
                # 重置視頻讀取位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                
                # 計算當前循環需要的幀數
                remaining_time = audio_duration - (loop * template_duration)
                frames_needed = int(min(template_duration, remaining_time) * fps)
                
                # 讀取並寫入幀
                for _ in range(frames_needed):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    out.write(frame)
            
            # 釋放資源
            cap.release()
            out.release()
            
            # 使用 FFmpeg 合併視頻和音頻
            temp_output = output_file.replace('.mp4', '_temp.mp4')
            os.rename(output_file, temp_output)
            
            # 使用 FFmpeg 合併視頻和音頻
            cmd = [
                'ffmpeg',
                '-i', temp_output,
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-map', '0:v',
                '-map', '1:a',
                '-shortest',
                output_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 刪除臨時文件
            if os.path.exists(temp_output):
                os.remove(temp_output)
                
            self.logger.info(f"數位人視頻已生成: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"生成數位人視頻失敗: {e}")
            return None
    
    def extract_frames(self, template_path, output_dir=None):
        """從模板視頻中提取幀
        
        參數:
            template_path (str): 模板視頻路徑
            output_dir (str, 可選): 輸出目錄
            
        返回:
            dict: 幀信息
        """
        if not os.path.exists(template_path):
            self.logger.error(f"找不到模板視頻: {template_path}")
            return None
            
        # 設置預設輸出目錄
        if output_dir is None:
            template_name = os.path.splitext(os.path.basename(template_path))[0]
            output_dir = os.path.join(self.cache_dir, f"{template_name}_frames")
            
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 讀取視頻
            cap = cv2.VideoCapture(template_path)
            
            # 獲取視頻信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            # 提取幀
            frames_info = {
                'template_name': os.path.basename(template_path),
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'frames_dir': output_dir,
                'frames': []
            }
            
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:06d}.png")
                cv2.imwrite(frame_path, frame)
                
                frames_info['frames'].append({
                    'idx': frame_idx,
                    'path': frame_path,
                    'time': frame_idx / fps
                })
                
                frame_idx += 1
                
            cap.release()
            
            self.logger.info(f"已提取 {frame_idx} 幀到 {output_dir}")
            return frames_info
            
        except Exception as e:
            self.logger.error(f"提取幀失敗: {e}")
            return None
    
    def overlay_on_background(self, digital_human_video, background_video, output_file=None, position='bottom_right', scale=0.3):
        """將數位人視頻疊加在背景視頻上
        
        參數:
            digital_human_video (str): 數位人視頻路徑
            background_video (str): 背景視頻路徑
            output_file (str, 可選): 輸出文件路徑
            position (str): 位置 ('bottom_right', 'bottom_left', 'top_right', 'top_left')
            scale (float): 縮放比例
            
        返回:
            str: 輸出文件路徑
        """
        if not os.path.exists(digital_human_video):
            self.logger.error(f"找不到數位人視頻: {digital_human_video}")
            return None
            
        if not os.path.exists(background_video):
            self.logger.error(f"找不到背景視頻: {background_video}")
            return None
            
        # 設置預設輸出檔案
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"overlay_{timestamp}.mp4")
            
        try:
            # 創建 FFmpeg 過濾器字符串，根據位置調整
            position_map = {
                'bottom_right': 'main_w-overlay_w-10:main_h-overlay_h-10',
                'bottom_left': '10:main_h-overlay_h-10',
                'top_right': 'main_w-overlay_w-10:10',
                'top_left': '10:10',
                'center': '(main_w-overlay_w)/2:(main_h-overlay_h)/2'
            }
            
            position_str = position_map.get(position, position_map['bottom_right'])
            
            # 使用 FFmpeg 添加透明度支持並疊加視頻
            cmd = [
                'ffmpeg',
                '-i', background_video,
                '-i', digital_human_video,
                '-filter_complex', 
                f'[1:v]scale=iw*{scale}:-1[overlay];[0:v][overlay]overlay={position_str}:shortest=1',
                '-c:a', 'copy',
                '-shortest',
                output_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.info(f"疊加視頻已生成: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"疊加視頻失敗: {e}")
            return None
    
    def create_animation_from_images(self, image_dir, output_file=None, fps=24, pattern='*.png'):
        """從圖像序列創建動畫
        
        參數:
            image_dir (str): 圖像目錄
            output_file (str, 可選): 輸出文件路徑
            fps (int): 幀率
            pattern (str): 圖像文件模式
            
        返回:
            str: 輸出文件路徑
        """
        if not os.path.exists(image_dir):
            self.logger.error(f"找不到圖像目錄: {image_dir}")
            return None
            
        # 設置預設輸出檔案
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"animation_{timestamp}.mp4")
            
        try:
            # 使用 FFmpeg 創建視頻
            cmd = [
                'ffmpeg',
                '-framerate', str(fps),
                '-pattern_type', 'glob',
                '-i', os.path.join(image_dir, pattern),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                output_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.logger.info(f"從圖像序列創建的動畫已生成: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"創建動畫失敗: {e}")
            return None
    
    def create_custom_digital_human(self, template_path, subtitles, audio_file, output_file=None, settings=None):
        """創建自定義數位人視頻
        
        參數:
            template_path (str): 模板視頻路徑
            subtitles (list): 字幕列表
            audio_file (str): 音頻文件路徑
            output_file (str, 可選): 輸出文件路徑
            settings (dict, 可選): 設定
            
        返回:
            str: 輸出文件路徑
        """
        if not os.path.exists(template_path):
            self.logger.error(f"找不到模板視頻: {template_path}")
            return None
            
        if not os.path.exists(audio_file):
            self.logger.error(f"找不到音頻文件: {audio_file}")
            return None
            
        # 設置預設輸出檔案
        if output_file is None:
            template_name = os.path.splitext(os.path.basename(template_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"{template_name}_custom_{timestamp}.mp4")
            
        # 合併設定
        if settings is None:
            settings = {}
        combined_settings = {**self.default_settings, **settings}
        
        try:
            # 創建臨時字幕文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
                srt_file = f.name
                
                for i, subtitle in enumerate(subtitles):
                    # 格式化時間
                    start_time = self._format_time_srt(subtitle['startTime'])
                    end_time = self._format_time_srt(subtitle['endTime'])
                    
                    # 寫入 SRT 格式
                    f.write(f"{i+1}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{subtitle['text']}\n\n")
            
            # 生成基本數位人視頻
            basic_video = self.generate_video(
                os.path.basename(template_path).split('.')[0],
                audio_file
            )
            
            if not basic_video:
                self.logger.error("生成基本數位人視頻失敗")
                return None
                
            # 使用 FFmpeg 添加字幕
            cmd = [
                'ffmpeg',
                '-i', basic_video,
                '-vf', f"subtitles={srt_file}",
                '-c:a', 'copy',
                output_file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 刪除臨時文件
            if os.path.exists(srt_file):
                os.remove(srt_file)
                
            if os.path.exists(basic_video) and basic_video != output_file:
                os.remove(basic_video)
                
            self.logger.info(f"自定義數位人視頻已生成: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"創建自定義數位人視頻失敗: {e}")
            return None
    
    def _format_time_srt(self, seconds):
        """格式化時間為 SRT 格式
        
        參數:
            seconds (float): 秒數
            
        返回:
            str: 格式化的時間字串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02}:{minutes:02}:{secs:02},{millisecs:03}"