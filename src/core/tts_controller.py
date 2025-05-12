#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 語音合成控制器
"""

import os
import logging
import tempfile
import requests
from datetime import datetime
import azure.cognitiveservices.speech as speechsdk

class TTSController:
    """文本到語音控制器
    
    負責將文本轉換為語音，支援多種 TTS 引擎。
    """
    
    def __init__(self, config=None):
        """初始化 TTS 控制器
        
        參數:
            config (dict, 可選): TTS 配置
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.engine = self.config.get('engine', 'azure')
        self.voice = self.config.get('voice', 'zh-TW-YunJheNeural')
        self.speech_rate = self.config.get('rate', 1.0)
        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'audio')
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 獲取 API 密鑰
        self.api_keys = self.config.get('api_keys', {})
        
    def set_engine(self, engine):
        """設置 TTS 引擎
        
        參數:
            engine (str): TTS 引擎名稱 ('azure', 'google', 'edge')
        """
        self.engine = engine
        self.logger.info(f"已設置 TTS 引擎: {engine}")
        
    def set_voice(self, voice):
        """設置語音
        
        參數:
            voice (str): 語音名稱
        """
        self.voice = voice
        self.logger.info(f"已設置語音: {voice}")
        
    def set_speech_rate(self, rate):
        """設置語速
        
        參數:
            rate (float): 語速倍率
        """
        self.speech_rate = float(rate)
        self.logger.info(f"已設置語速: {rate}")
        
    def generate_speech(self, text, output_file=None, rate=None):
        """生成語音
        
        參數:
            text (str): 文本
            output_file (str, 可選): 輸出文件路徑
            rate (float, 可選): 語速倍率
            
        返回:
            bool: 是否成功
        """
        if not text:
            self.logger.warning("無法生成語音: 文本為空")
            return False
            
        # 設置預設輸出文件
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"speech_{timestamp}.mp3")
            
        # 使用指定的語速，如果沒有指定則使用默認值
        speech_rate = rate if rate is not None else self.speech_rate
        
        # 根據不同的引擎生成語音
        if self.engine == 'azure':
            return self._generate_azure_speech(text, output_file, speech_rate)
        elif self.engine == 'google':
            return self._generate_google_speech(text, output_file, speech_rate)
        elif self.engine == 'edge':
            return self._generate_edge_speech(text, output_file, speech_rate)
        else:
            self.logger.error(f"不支援的 TTS 引擎: {self.engine}")
            return False
            
    def _generate_azure_speech(self, text, output_file, rate=1.0):
        """使用 Azure TTS 生成語音
        
        參數:
            text (str): 文本
            output_file (str): 輸出文件路徑
            rate (float): 語速倍率
            
        返回:
            bool: 是否成功
        """
        # 檢查是否配置了 Azure API 密鑰
        subscription_key = self.api_keys.get('azure_tts')
        if not subscription_key:
            self.logger.error("無法使用 Azure TTS: 缺少 API 密鑰")
            return False
            
        # 檢查區域設置
        region = self.config.get('azure_region', 'eastasia')
        
        try:
            # 創建語音配置
            speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
            
            # 設置語音和語速
            speech_config.speech_synthesis_voice_name = self.voice
            
            # 創建語音合成器
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            # 創建 SSML 文本（支持調整語速）
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-TW">
                <voice name="{self.voice}">
                    <prosody rate="{rate}">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # 合成語音
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            # 檢查結果
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                self.logger.info(f"語音合成成功: {output_file}")
                return True
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                self.logger.error(f"語音合成取消: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    self.logger.error(f"錯誤代碼: {cancellation_details.error_code}")
                    self.logger.error(f"錯誤詳情: {cancellation_details.error_details}")
                return False
            else:
                self.logger.error(f"未知原因導致語音合成失敗: {result.reason}")
                return False
                
        except Exception as e:
            self.logger.error(f"Azure TTS 生成失敗: {str(e)}")
            return False
            
    def _generate_google_speech(self, text, output_file, rate=1.0):
        """使用 Google TTS 生成語音
        
        參數:
            text (str): 文本
            output_file (str): 輸出文件路徑
            rate (float): 語速倍率
            
        返回:
            bool: 是否成功
        """
        try:
            from gtts import gTTS
            
            # 根據當前語音設置選擇語言
            language = 'zh-tw'
            if self.voice.startswith('en-'):
                language = 'en'
            elif self.voice.startswith('ja-'):
                language = 'ja'
                
            # 生成語音
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(output_file)
            
            # 處理語速（Google TTS API 不直接支持調整語速，需要使用外部工具）
            if rate != 1.0 and rate > 0:
                try:
                    from pydub import AudioSegment
                    
                    # 載入音頻
                    sound = AudioSegment.from_mp3(output_file)
                    
                    # 調整速度（通過更改採樣率）
                    new_sound = sound.set_frame_rate(int(sound.frame_rate * rate))
                    
                    # 保存調整後的音頻
                    new_sound.export(output_file, format="mp3")
                    
                except Exception as e:
                    self.logger.warning(f"調整語速失敗，使用原始速度: {str(e)}")
            
            self.logger.info(f"Google TTS 語音合成成功: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Google TTS 生成失敗: {str(e)}")
            return False
            
    def _generate_edge_speech(self, text, output_file, rate=1.0):
        """使用 Microsoft Edge TTS 生成語音
        
        參數:
            text (str): 文本
            output_file (str): 輸出文件路徑
            rate (float): 語速倍率
            
        返回:
            bool: 是否成功
        """
        try:
            # Edge TTS 相關依賴
            import edge_tts
            import asyncio
            
            async def synthesize_speech():
                # 創建 TTS 通信對象
                communicate = edge_tts.Communicate(text, self.voice)
                
                # 調整語速
                if rate != 1.0:
                    options = {
                        "rate": f"+{int((rate-1)*50)}%" if rate > 1 else f"{int((rate-1)*50)}%"
                    }
                    communicate = edge_tts.Communicate(text, self.voice, options=options)
                
                # 合成語音
                await communicate.save(output_file)
            
            # 運行異步任務
            asyncio.run(synthesize_speech())
            
            self.logger.info(f"Edge TTS 語音合成成功: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Edge TTS 生成失敗: {str(e)}")
            return False
            
    def generate_subtitles_with_timing(self, text, character_rate=5.0):
        """生成帶時間的字幕
        
        參數:
            text (str): 文本內容
            character_rate (float): 每秒鐘的字符數
            
        返回:
            list: 字幕列表，每項包含 text, startTime, endTime 和 duration
        """
        # 分割文本為段落或句子
        if '\n' in text:
            segments = [s for s in text.split('\n') if s.strip()]
        else:
            # 按標點符號分割
            segments = []
            current_segment = ""
            
            for char in text:
                current_segment += char
                if char in ['。', '！', '？', '…', '.', '!', '?']:
                    if current_segment.strip():
                        segments.append(current_segment.strip())
                    current_segment = ""
            
            # 添加最後一段
            if current_segment.strip():
                segments.append(current_segment.strip())
        
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
            max_duration = 10.0  # 最長 10 秒
            if duration > max_duration:
                duration = max_duration
            
            # 創建字幕項
            subtitle = {
                'text': segment,
                'startTime': current_time,
                'duration': duration,
                'endTime': current_time + duration
            }
            
            subtitles.append(subtitle)
            
            # 更新時間
            current_time += duration
        
        return subtitles
    
    def batch_generate_speech(self, subtitles, output_dir=None, prefix="speech"):
        """批量生成語音文件
        
        參數:
            subtitles (list): 字幕列表
            output_dir (str, 可選): 輸出目錄
            prefix (str): 輸出文件前綴
            
        返回:
            list: 生成的音頻文件列表
        """
        if output_dir is None:
            output_dir = self.cache_dir
            
        os.makedirs(output_dir, exist_ok=True)
        
        audio_files = []
        
        for i, subtitle in enumerate(subtitles):
            # 檢查字幕是否有文本
            if not subtitle.get('text'):
                continue
                
            # 生成輸出文件路徑
            output_file = os.path.join(output_dir, f"{prefix}_{i+1:03d}.mp3")
            
            # 生成語音
            success = self.generate_speech(subtitle['text'], output_file)
            
            if success:
                # 添加音頻文件路徑到字幕數據
                subtitle['audio_file'] = output_file
                audio_files.append(output_file)
            
        return audio_files