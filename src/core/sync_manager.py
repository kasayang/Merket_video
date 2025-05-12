#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 同步管理器
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from pydub import AudioSegment
import subprocess

class SyncManager:
    """同步管理器
    
    負責同步視頻、音頻和字幕的時間軸，處理多媒體元素的時間對齊。
    """
    
    def __init__(self, config=None):
        """初始化同步管理器
        
        參數:
            config (dict, 可選): 配置設定
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.timeline = []  # 時間軸數據
        self.total_duration = 0
        self.temp_dir = os.path.join(os.getcwd(), 'cache', 'temp')
        
        # 確保臨時目錄存在
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def create_timeline(self, subtitles, audio_files=None, video_segments=None):
        """創建項目時間軸
        
        參數:
            subtitles (list): 字幕列表
            audio_files (list, 可選): 音頻文件列表
            video_segments (list, 可選): 視頻片段列表
            
        返回:
            dict: 時間軸數據
        """
        self.logger.info("創建時間軸")
        
        # 初始化時間軸
        self.timeline = {
            'subtitles': [],
            'audio': [],
            'video': [],
            'total_duration': 0
        }
        
        # 添加字幕軌道
        if subtitles:
            for i, subtitle in enumerate(subtitles):
                self.timeline['subtitles'].append({
                    'id': f'subtitle_{i+1}',
                    'text': subtitle['text'],
                    'startTime': subtitle['startTime'],
                    'endTime': subtitle['endTime'],
                    'duration': subtitle['duration']
                })
                
            # 更新總時長
            self.total_duration = max(self.total_duration, 
                                      max(sub['endTime'] for sub in self.timeline['subtitles']))
        
        # 添加音頻軌道
        if audio_files:
            for i, audio_file in enumerate(audio_files):
                # 獲取音頻時長
                audio_duration = self._get_audio_duration(audio_file)
                
                # 如果字幕和音頻一一對應
                start_time = 0
                if i < len(self.timeline['subtitles']):
                    start_time = self.timeline['subtitles'][i]['startTime']
                
                self.timeline['audio'].append({
                    'id': f'audio_{i+1}',
                    'file': audio_file,
                    'startTime': start_time,
                    'duration': audio_duration,
                    'endTime': start_time + audio_duration
                })
                
            # 更新總時長
            if self.timeline['audio']:
                self.total_duration = max(self.total_duration, 
                                        max(audio['endTime'] for audio in self.timeline['audio']))
        
        # 添加視頻軌道
        if video_segments:
            for i, segment in enumerate(video_segments):
                self.timeline['video'].append({
                    'id': f'video_{i+1}',
                    'file': segment.get('file', ''),
                    'startTime': segment.get('startTime', 0),
                    'duration': segment.get('duration', 0),
                    'endTime': segment.get('startTime', 0) + segment.get('duration', 0),
                    'type': segment.get('type', 'stock_chart')
                })
                
            # 更新總時長
            if self.timeline['video']:
                self.total_duration = max(self.total_duration, 
                                        max(video['endTime'] for video in self.timeline['video']))
        
        # 設置時間軸總時長
        self.timeline['total_duration'] = self.total_duration
        
        self.logger.info(f"時間軸創建完成，總時長: {self.total_duration:.2f} 秒")
        return self.timeline
    
    def adjust_subtitle_timing(self, subtitles, scale_factor=1.0, offset=0.0):
        """調整字幕時間
        
        參數:
            subtitles (list): 字幕列表
            scale_factor (float): 時間縮放因子
            offset (float): 時間偏移量（秒）
            
        返回:
            list: 調整後的字幕列表
        """
        adjusted_subtitles = []
        
        for subtitle in subtitles:
            new_start = subtitle['startTime'] * scale_factor + offset
            new_duration = subtitle['duration'] * scale_factor
            
            adjusted_subtitle = subtitle.copy()
            adjusted_subtitle['startTime'] = new_start
            adjusted_subtitle['duration'] = new_duration
            adjusted_subtitle['endTime'] = new_start + new_duration
            
            adjusted_subtitles.append(adjusted_subtitle)
        
        self.logger.info(f"調整字幕時間: 縮放 {scale_factor}, 偏移 {offset} 秒")
        return adjusted_subtitles
    
    def merge_audio_files(self, audio_files, output_file=None, crossfade=0.5):
        """合併多個音頻文件
        
        參數:
            audio_files (list): 音頻文件列表 [(文件路徑, 開始時間), ...]
            output_file (str, 可選): 輸出文件路徑
            crossfade (float): 交叉淡入淡出時間（秒）
            
        返回:
            str: 合併後的音頻文件路徑
        """
        if not audio_files:
            self.logger.warning("沒有音頻文件可合併")
            return None
            
        # 設置預設輸出文件
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.temp_dir, f"merged_audio_{timestamp}.mp3")
        
        try:
            # 根據開始時間排序音頻文件
            sorted_audio = sorted(audio_files, key=lambda x: x[1])
            
            # 計算總時長
            max_end_time = 0
            for file_path, start_time in sorted_audio:
                if os.path.exists(file_path):
                    audio_duration = self._get_audio_duration(file_path)
                    max_end_time = max(max_end_time, start_time + audio_duration)
            
            # 創建空白背景
            total_duration_ms = int(max_end_time * 1000)  # 轉換為毫秒
            merged_audio = AudioSegment.silent(duration=total_duration_ms)
            
            # 疊加每個音頻
            for file_path, start_time in sorted_audio:
                if os.path.exists(file_path):
                    try:
                        audio = AudioSegment.from_file(file_path)
                        position_ms = int(start_time * 1000)
                        merged_audio = merged_audio.overlay(audio, position=position_ms)
                    except Exception as e:
                        self.logger.error(f"處理音頻文件時出錯: {file_path}, {e}")
            
            # 導出合併後的音頻
            merged_audio.export(output_file, format="mp3")
            self.logger.info(f"音頻文件合併完成: {output_file}")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"合併音頻文件時出錯: {e}")
            return None
    
    def generate_ffmpeg_script(self, timeline, output_file, input_files=None):
        """生成 FFMPEG 腳本
        
        參數:
            timeline (dict): 時間軸數據
            output_file (str): 輸出文件路徑
            input_files (dict, 可選): 輸入文件字典
            
        返回:
            str: FFMPEG 命令
        """
        if input_files is None:
            input_files = {}
            
        # 收集所有輸入文件
        inputs = []
        filter_complex = []
        
        # 視頻軌道
        video_inputs = []
        for i, video in enumerate(timeline.get('video', [])):
            if 'file' in video and os.path.exists(video['file']):
                video_inputs.append(f"-i \"{video['file']}\"")
                input_files[f'v{i}'] = video['file']
                
                # 時間偏移和持續時間
                start_time = video.get('startTime', 0)
                duration = video.get('duration', 0)
                
                # 添加過濾器
                filter_complex.append(f"[{i}:v]setpts=PTS-STARTPTS+{start_time}/TB[v{i}]")
        
        # 音頻軌道
        audio_inputs = []
        for i, audio in enumerate(timeline.get('audio', [])):
            if 'file' in audio and os.path.exists(audio['file']):
                audio_inputs.append(f"-i \"{audio['file']}\"")
                input_files[f'a{i}'] = audio['file']
                
                # 時間偏移和持續時間
                start_time = audio.get('startTime', 0)
                
                # 添加過濾器
                filter_complex.append(f"[{len(video_inputs)+i}:a]adelay={int(start_time*1000)}|{int(start_time*1000)}[a{i}]")
        
        # 組合所有視頻
        if len(video_inputs) > 1:
            video_overlays = []
            for i in range(len(video_inputs)):
                video_overlays.append(f"[v{i}]")
            filter_complex.append(f"{' '.join(video_overlays)}overlay=shortest=1[outv]")
        elif len(video_inputs) == 1:
            filter_complex.append(f"[v0]copy[outv]")
        
        # 組合所有音頻
        if len(audio_inputs) > 1:
            audio_mixings = []
            for i in range(len(audio_inputs)):
                audio_mixings.append(f"[a{i}]")
            filter_complex.append(f"{' '.join(audio_mixings)}amix=inputs={len(audio_inputs)}[outa]")
        elif len(audio_inputs) == 1:
            filter_complex.append(f"[a0]acopy[outa]")
        
        # 組合 FFMPEG 命令
        cmd = [
            "ffmpeg",
            " ".join(video_inputs),
            " ".join(audio_inputs)
        ]
        
        if filter_complex:
            cmd.append(f"-filter_complex \"{'; '.join(filter_complex)}\"")
            
        if len(video_inputs) > 0:
            cmd.append("-map \"[outv]\"")
        
        if len(audio_inputs) > 0:
            cmd.append("-map \"[outa]\"")
            
        # 添加字幕
        subtitle_file = self._generate_subtitle_file(timeline.get('subtitles', []))
        if subtitle_file:
            cmd.append(f"-vf \"subtitles={subtitle_file}\"")
            
        # 添加輸出設置
        cmd.append(f"-c:v libx264 -preset medium -crf 23")
        cmd.append(f"-c:a aac -b:a 192k")
        cmd.append(f"-shortest")
        cmd.append(f"\"{output_file}\"")
        
        return " ".join(cmd)
    
    def execute_ffmpeg_command(self, command):
        """執行 FFMPEG 命令
        
        參數:
            command (str): FFMPEG 命令
            
        返回:
            bool: 是否成功
        """
        try:
            self.logger.info(f"執行 FFMPEG 命令: {command}")
            
            # 執行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # 獲取輸出
            stdout, stderr = process.communicate()
            
            # 檢查執行結果
            if process.returncode == 0:
                self.logger.info("FFMPEG 命令執行成功")
                return True
            else:
                self.logger.error(f"FFMPEG 命令執行失敗: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"執行 FFMPEG 命令時出錯: {e}")
            return False
    
    def save_timeline(self, file_path=None):
        """保存時間軸數據
        
        參數:
            file_path (str, 可選): 文件路徑
            
        返回:
            str: 文件路徑
        """
        if not self.timeline:
            self.logger.warning("沒有時間軸數據可保存")
            return None
            
        # 設置預設輸出文件
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = os.path.join(self.temp_dir, f"timeline_{timestamp}.json")
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.timeline, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"時間軸數據已保存: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"保存時間軸數據時出錯: {e}")
            return None
    
    def load_timeline(self, file_path):
        """載入時間軸數據
        
        參數:
            file_path (str): 文件路徑
            
        返回:
            dict: 時間軸數據
        """
        if not os.path.exists(file_path):
            self.logger.error(f"找不到時間軸文件: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                timeline = json.load(f)
                
            self.timeline = timeline
            self.total_duration = timeline.get('total_duration', 0)
            
            self.logger.info(f"載入時間軸數據: {file_path}")
            return self.timeline
            
        except Exception as e:
            self.logger.error(f"載入時間軸數據時出錯: {e}")
            return None
    
    def add_item_to_timeline(self, track_type, item):
        """添加項目到時間軸
        
        參數:
            track_type (str): 軌道類型 ('subtitle', 'audio', 'video')
            item (dict): 項目數據
            
        返回:
            bool: 是否成功
        """
        if not self.timeline:
            self.logger.warning("時間軸尚未初始化")
            return False
            
        if track_type not in ['subtitles', 'audio', 'video']:
            self.logger.error(f"無效的軌道類型: {track_type}")
            return False
            
        # 確保項目有必要的屬性
        required_attrs = ['id', 'startTime', 'duration']
        for attr in required_attrs:
            if attr not in item:
                self.logger.error(f"項目缺少必要的屬性: {attr}")
                return False
                
        # 計算結束時間
        item['endTime'] = item['startTime'] + item['duration']
        
        # 添加到相應軌道
        self.timeline[track_type].append(item)
        
        # 更新總時長
        if item['endTime'] > self.total_duration:
            self.total_duration = item['endTime']
            self.timeline['total_duration'] = self.total_duration
            
        self.logger.info(f"項目已添加到軌道 {track_type}: {item['id']}")
        return True
    
    def remove_item_from_timeline(self, track_type, item_id):
        """從時間軸移除項目
        
        參數:
            track_type (str): 軌道類型 ('subtitle', 'audio', 'video')
            item_id (str): 項目ID
            
        返回:
            bool: 是否成功
        """
        if not self.timeline:
            self.logger.warning("時間軸尚未初始化")
            return False
            
        if track_type not in ['subtitles', 'audio', 'video']:
            self.logger.error(f"無效的軌道類型: {track_type}")
            return False
            
        # 查找項目
        item_index = -1
        for i, item in enumerate(self.timeline[track_type]):
            if item.get('id') == item_id:
                item_index = i
                break
                
        if item_index == -1:
            self.logger.warning(f"在軌道 {track_type} 中找不到項目 {item_id}")
            return False
            
        # 移除項目
        self.timeline[track_type].pop(item_index)
        
        # 更新總時長
        self._update_total_duration()
        
        self.logger.info(f"項目已從軌道 {track_type} 移除: {item_id}")
        return True
    
    def update_item_timing(self, track_type, item_id, start_time=None, duration=None):
        """更新項目時間
        
        參數:
            track_type (str): 軌道類型 ('subtitle', 'audio', 'video')
            item_id (str): 項目ID
            start_time (float, 可選): 開始時間
            duration (float, 可選): 持續時間
            
        返回:
            bool: 是否成功
        """
        if not self.timeline:
            self.logger.warning("時間軸尚未初始化")
            return False
            
        if track_type not in ['subtitles', 'audio', 'video']:
            self.logger.error(f"無效的軌道類型: {track_type}")
            return False
            
        # 查找項目
        item_index = -1
        for i, item in enumerate(self.timeline[track_type]):
            if item.get('id') == item_id:
                item_index = i
                break
                
        if item_index == -1:
            self.logger.warning(f"在軌道 {track_type} 中找不到項目 {item_id}")
            return False
            
        # 更新時間
        if start_time is not None:
            self.timeline[track_type][item_index]['startTime'] = start_time
            
        if duration is not None:
            self.timeline[track_type][item_index]['duration'] = duration
            
        # 計算結束時間
        self.timeline[track_type][item_index]['endTime'] = (
            self.timeline[track_type][item_index]['startTime'] + 
            self.timeline[track_type][item_index]['duration']
        )
        
        # 更新總時長
        self._update_total_duration()
        
        self.logger.info(f"項目 {item_id} 時間已更新")
        return True
    
    def _update_total_duration(self):
        """更新時間軸總時長"""
        max_duration = 0
        
        # 檢查所有軌道的結束時間
        for track_type in ['subtitles', 'audio', 'video']:
            if self.timeline.get(track_type):
                track_max = max(item['endTime'] for item in self.timeline[track_type])
                max_duration = max(max_duration, track_max)
                
        self.total_duration = max_duration
        self.timeline['total_duration'] = max_duration
    
    def _get_audio_duration(self, file_path):
        """獲取音頻文件時長
        
        參數:
            file_path (str): 文件路徑
            
        返回:
            float: 時長（秒）
        """
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # 轉換為秒
        except Exception as e:
            self.logger.error(f"獲取音頻時長失敗: {e}")
            return 0
    
    def _generate_subtitle_file(self, subtitles, format='srt'):
        """生成字幕文件
        
        參數:
            subtitles (list): 字幕列表
            format (str): 字幕格式 ('srt', 'vtt')
            
        返回:
            str: 字幕文件路徑
        """
        if not subtitles:
            return None
            
        # 創建字幕內容
        if format == 'srt':
            content = ""
            for i, subtitle in enumerate(subtitles):
                # 序號
                content += f"{i+1}\n"
                
                # 時間範圍
                start_time = self._format_time_srt(subtitle['startTime'])
                end_time = self._format_time_srt(subtitle['endTime'])
                content += f"{start_time} --> {end_time}\n"
                
                # 文本
                content += f"{subtitle['text']}\n\n"
                
            # 保存到文件
            file_path = os.path.join(self.temp_dir, "subtitles.srt")
            
        elif format == 'vtt':
            content = "WEBVTT\n\n"
            for i, subtitle in enumerate(subtitles):
                # 序號 (可選)
                content += f"{i+1}\n"
                
                # 時間範圍
                start_time = self._format_time_vtt(subtitle['startTime'])
                end_time = self._format_time_vtt(subtitle['endTime'])
                content += f"{start_time} --> {end_time}\n"
                
                # 文本
                content += f"{subtitle['text']}\n\n"
                
            # 保存到文件
            file_path = os.path.join(self.temp_dir, "subtitles.vtt")
            
        else:
            self.logger.error(f"不支援的字幕格式: {format}")
            return None
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.logger.info(f"字幕文件已生成: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"生成字幕文件時出錯: {e}")
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
    
    def _format_time_vtt(self, seconds):
        """格式化時間為 WebVTT 格式
        
        參數:
            seconds (float): 秒數
            
        返回:
            str: 格式化的時間字串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02}:{minutes:02}:{secs:02}.{millisecs:03}"