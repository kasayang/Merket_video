#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 字幕管理器
"""

import os
import re
import json
import logging
from datetime import datetime

class SubtitleManager:
    """字幕管理器
    
    負責生成、編輯和匯出字幕。
    """
    
    def __init__(self, config=None):
        """初始化字幕管理器
        
        參數:
            config (dict, 可選): 配置設定
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.subtitle_styles = self.config.get('styles', {
            'default': {
                'font': 'Noto Sans TC',
                'fontsize': 40,
                'color': 'white',
                'background': 'rgba(0, 0, 0, 0.6)',
                'position': 'bottom'
            }
        })
        
    def generate_from_text(self, text, character_rate=5.0):
        """從文本生成字幕
        
        參數:
            text (str): 文本內容
            character_rate (float): 每秒鐘的字符數
            
        返回:
            list: 字幕列表，每項包含 text, startTime, endTime 和 duration
        """
        self.logger.info(f"從文本生成字幕，字符速率: {character_rate} 字/秒")
        
        # 分割文本
        segments = self._split_text(text)
        
        # 生成字幕時間
        subtitles = []
        current_time = 0.0
        
        for segment in segments:
            # 計算持續時間（基於字符數）
            duration = len(segment) / character_rate
            
            # 確保最短持續時間
            min_duration = 1.5  # 最短 1.5 秒
            if duration < min_duration:
                duration = min_duration
                
            # 最長持續時間
            max_duration = 8.0  # 最長 8 秒
            if duration > max_duration:
                duration = max_duration
            
            # 創建字幕項
            subtitle = {
                'text': segment,
                'startTime': current_time,
                'duration': duration,
                'endTime': current_time + duration,
                'style': 'default'
            }
            
            subtitles.append(subtitle)
            
            # 更新時間
            current_time += duration
        
        self.logger.info(f"生成了 {len(subtitles)} 條字幕")
        return subtitles
        
    def _split_text(self, text):
        """分割文本為字幕段落
        
        參數:
            text (str): 文本內容
            
        返回:
            list: 文本段落列表
        """
        # 先按自然段分割
        if '\n' in text:
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            # 如果段落太長，再進一步分割
            segments = []
            for paragraph in paragraphs:
                if len(paragraph) > 50:  # 段落太長
                    segments.extend(self._split_by_punctuation(paragraph))
                else:
                    segments.append(paragraph)
            
            return segments
        else:
            # 按標點符號分割
            return self._split_by_punctuation(text)
        
    def _split_by_punctuation(self, text):
        """按標點符號分割文本
        
        參數:
            text (str): 文本內容
            
        返回:
            list: 文本段落列表
        """
        # 定義終止標點
        end_marks = ['。', '！', '？', '…', '.', '!', '?', '\n']
        
        segments = []
        current_segment = ""
        
        for char in text:
            current_segment += char
            if char in end_marks:
                if current_segment.strip():
                    segments.append(current_segment.strip())
                current_segment = ""
        
        # 添加最後一段
        if current_segment.strip():
            segments.append(current_segment.strip())
            
        return segments
        
    def export_to_srt(self, subtitles, output_file=None):
        """匯出為 SRT 格式
        
        參數:
            subtitles (list): 字幕列表
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            str: SRT 內容或文件路徑
        """
        if not subtitles:
            self.logger.warning("沒有字幕可匯出")
            return ""
            
        # 生成 SRT 內容
        srt_content = ""
        
        for i, subtitle in enumerate(subtitles):
            # 序號
            srt_content += f"{i+1}\n"
            
            # 時間範圍
            start_time = self._format_time_srt(subtitle['startTime'])
            end_time = self._format_time_srt(subtitle['endTime'])
            srt_content += f"{start_time} --> {end_time}\n"
            
            # 文本
            srt_content += f"{subtitle['text']}\n\n"
        
        # 如果指定了輸出文件，則寫入文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                self.logger.info(f"字幕已匯出為 SRT 格式: {output_file}")
                return output_file
            except Exception as e:
                self.logger.error(f"匯出 SRT 文件失敗: {e}")
                return srt_content
        
        return srt_content
        
    def export_to_vtt(self, subtitles, output_file=None):
        """匯出為 WebVTT 格式
        
        參數:
            subtitles (list): 字幕列表
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            str: WebVTT 內容或文件路徑
        """
        if not subtitles:
            self.logger.warning("沒有字幕可匯出")
            return ""
            
        # 生成 WebVTT 內容
        vtt_content = "WEBVTT\n\n"
        
        for i, subtitle in enumerate(subtitles):
            # 序號 (可選)
            vtt_content += f"{i+1}\n"
            
            # 時間範圍
            start_time = self._format_time_vtt(subtitle['startTime'])
            end_time = self._format_time_vtt(subtitle['endTime'])
            vtt_content += f"{start_time} --> {end_time}\n"
            
            # 文本
            vtt_content += f"{subtitle['text']}\n\n"
        
        # 如果指定了輸出文件，則寫入文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(vtt_content)
                self.logger.info(f"字幕已匯出為 WebVTT 格式: {output_file}")
                return output_file
            except Exception as e:
                self.logger.error(f"匯出 WebVTT 文件失敗: {e}")
                return vtt_content
        
        return vtt_content
    
    def export_to_json(self, subtitles, output_file=None):
        """匯出為 JSON 格式
        
        參數:
            subtitles (list): 字幕列表
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            str: JSON 內容或文件路徑
        """
        if not subtitles:
            self.logger.warning("沒有字幕可匯出")
            return ""
            
        # 生成 JSON 內容
        json_content = json.dumps(subtitles, ensure_ascii=False, indent=2)
        
        # 如果指定了輸出文件，則寫入文件
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                self.logger.info(f"字幕已匯出為 JSON 格式: {output_file}")
                return output_file
            except Exception as e:
                self.logger.error(f"匯出 JSON 文件失敗: {e}")
                return json_content
        
        return json_content
    
    def load_from_file(self, file_path):
        """從文件載入字幕
        
        參數:
            file_path (str): 文件路徑
            
        返回:
            list: 字幕列表
        """
        if not os.path.exists(file_path):
            self.logger.error(f"找不到字幕文件: {file_path}")
            return []
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.json':
                # 載入 JSON 格式
                with open(file_path, 'r', encoding='utf-8') as f:
                    subtitles = json.load(f)
                return subtitles
            elif file_ext == '.srt':
                # 載入 SRT 格式
                return self._parse_srt_file(file_path)
            elif file_ext == '.vtt':
                # 載入 WebVTT 格式
                return self._parse_vtt_file(file_path)
            else:
                self.logger.error(f"不支援的字幕文件格式: {file_ext}")
                return []
        except Exception as e:
            self.logger.error(f"載入字幕文件失敗: {e}")
            return []
    
    def _parse_srt_file(self, file_path):
        """解析 SRT 文件
        
        參數:
            file_path (str): 文件路徑
            
        返回:
            list: 字幕列表
        """
        subtitles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 移除 BOM 標記
            if content.startswith('\ufeff'):
                content = content[1:]
                
            # 按字幕塊分割
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                    
                # 解析時間行
                time_line = lines[1]
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
                
                if not time_match:
                    continue
                    
                start_time_str, end_time_str = time_match.groups()
                
                # 轉換時間格式
                start_time = self._parse_srt_time(start_time_str)
                end_time = self._parse_srt_time(end_time_str)
                
                # 獲取文本（可能是多行）
                text = '\n'.join(lines[2:])
                
                # 創建字幕項
                subtitle = {
                    'text': text,
                    'startTime': start_time,
                    'endTime': end_time,
                    'duration': end_time - start_time,
                    'style': 'default'
                }
                
                subtitles.append(subtitle)
                
            self.logger.info(f"從 SRT 文件載入了 {len(subtitles)} 條字幕")
            return subtitles
            
        except Exception as e:
            self.logger.error(f"解析 SRT 文件失敗: {e}")
            return []
    
    def _parse_vtt_file(self, file_path):
        """解析 WebVTT 文件
        
        參數:
            file_path (str): 文件路徑
            
        返回:
            list: 字幕列表
        """
        subtitles = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查 WebVTT 頭部
            if not content.strip().startswith('WEBVTT'):
                self.logger.error(f"無效的 WebVTT 文件: {file_path}")
                return []
                
            # 按字幕塊分割
            # 忽略頭部的 WEBVTT 行
            header_end = content.find('\n\n')
            if header_end == -1:
                return []
                
            content = content[header_end:].strip()
            blocks = re.split(r'\n\s*\n', content)
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 2:
                    continue
                    
                # 解析時間行（VTT 文件的第一行可能是序號，也可能是時間行）
                time_line_idx = 0
                if not lines[0].strip().replace('-', '').replace('>', '').replace('.', '').replace(':', '').isdigit():
                    # 如果不是時間行，則第二行是時間行
                    time_line_idx = 1
                    if len(lines) < 3:  # 確保還有文本行
                        continue
                
                time_line = lines[time_line_idx]
                time_match = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', time_line)
                
                if not time_match:
                    # 嘗試其他可能的時間格式
                    time_match = re.match(r'(\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}\.\d{3})', time_line)
                    if not time_match:
                        continue
                
                start_time_str, end_time_str = time_match.groups()
                
                # 轉換時間格式
                start_time = self._parse_vtt_time(start_time_str)
                end_time = self._parse_vtt_time(end_time_str)
                
                # 獲取文本（可能是多行）
                text = '\n'.join(lines[time_line_idx+1:])
                
                # 創建字幕項
                subtitle = {
                    'text': text,
                    'startTime': start_time,
                    'endTime': end_time,
                    'duration': end_time - start_time,
                    'style': 'default'
                }
                
                subtitles.append(subtitle)
                
            self.logger.info(f"從 WebVTT 文件載入了 {len(subtitles)} 條字幕")
            return subtitles
            
        except Exception as e:
            self.logger.error(f"解析 WebVTT 文件失敗: {e}")
            return []
    
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
    
    def _parse_srt_time(self, time_str):
        """解析 SRT 格式的時間字串
        
        參數:
            time_str (str): 時間字串，格式為 "HH:MM:SS,mmm"
            
        返回:
            float: 秒數
        """
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        
        sec_parts = parts[2].split(',')
        seconds = int(sec_parts[0])
        milliseconds = int(sec_parts[1])
        
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    
    def _parse_vtt_time(self, time_str):
        """解析 WebVTT 格式的時間字串
        
        參數:
            time_str (str): 時間字串，格式為 "HH:MM:SS.mmm" 或 "MM:SS.mmm"
            
        返回:
            float: 秒數
        """
        parts = time_str.split(':')
        
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours = int(parts[0])
            minutes = int(parts[1])
            
            sec_parts = parts[2].split('.')
            seconds = int(sec_parts[0])
            milliseconds = int(sec_parts[1])
            
            return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        else:  # MM:SS.mmm
            minutes = int(parts[0])
            
            sec_parts = parts[1].split('.')
            seconds = int(sec_parts[0])
            milliseconds = int(sec_parts[1])
            
            return minutes * 60 + seconds + milliseconds / 1000