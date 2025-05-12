#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 配置管理器
"""

import os
import json
import yaml
import logging

class ConfigManager:
    """配置管理器類
    
    負責加載、保存和管理系統配置，包括API密鑰、輸出設置、視覺風格等。
    """
    
    def __init__(self, config_path=None):
        """初始化配置管理器
        
        參數:
            config_path (str, 可選): 配置文件路徑，默認為'config.yaml'
        """
        self.config_path = config_path or os.path.join(os.getcwd(), 'config.yaml')
        self.logger = logging.getLogger(__name__)
        self.config = self.load_config()
        
    def load_config(self):
        """加載配置文件
        
        返回:
            dict: 配置字典
        """
        if not os.path.exists(self.config_path):
            # 創建默認配置
            default_config = self._create_default_config()
            self.save_config(default_config)
            return default_config
            
        # 讀取現有配置
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"讀取配置文件時出錯: {e}")
            # 如果讀取失敗，則創建默認配置
            default_config = self._create_default_config()
            self.save_config(default_config)
            return default_config
            
    def _create_default_config(self):
        """創建默認配置"""
        default_config = {
            'api_keys': {
                'alpha_vantage': '',
                'finnhub': '',
                'newsapi': '',
                'openai': '',
                'azure_tts': ''
            },
            'output': {
                'directory': 'output',
                'format': 'mp4',
                'resolution': {
                    'width': 1920,
                    'height': 1080
                },
                'fps': 30
            },
            'style': {
                'theme': 'dark',
                'font': '',
                'colors': {
                    'up': '#00FF7F',
                    'down': '#FF4500',
                    'neutral': '#1E90FF'
                }
            },
            # 這裡添加每種模組的特定配置
            'modules': {
                'stock': {
                    'sections': [
                        'intro',
                        'price',
                        'technical',
                        'signals',
                        'conclusion'
                    ],
                    'duration': {
                        'intro': 5,
                        'price': 10,
                        'technical': 12,
                        'signals': 8,
                        'conclusion': 5
                    }
                },
                'travel': {
                    'sections': [
                        'intro',
                        'highlights',
                        'details',
                        'tips',
                        'conclusion'
                    ],
                    'duration': {
                        'intro': 5,
                        'highlights': 15,
                        'details': 20,
                        'tips': 10,
                        'conclusion': 5
                    }
                },
                'education': {
                    'sections': [
                        'intro',
                        'concept',
                        'examples',
                        'practice',
                        'summary'
                    ],
                    'duration': {
                        'intro': 5,
                        'concept': 15,
                        'examples': 20,
                        'practice': 15,
                        'summary': 5
                    }
                }
            },
            'watermark': {
                'enabled': True,
                'text': '自動生成',
                'position': 'bottom-right'
            },
            'audio': {
                'background_music': '',
                'volume': 0.3,
                'enable_tts': True,
                'tts_voice': 'zh-TW-YunJheNeural'
            },
            'article': {
                'auto_extract_ticker': True,
                'max_paragraphs_per_scene': 3,
                'highlight_keywords': True
            },
            'digital_human': {
                'enabled': False,
                'avatar_template': 'templates/digital_humans/default_avatar.mp4',
                'size_ratio': 0.3,
                'layout': 'pip_bottom_right'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': True
            }
        }
        return default_config
            
    def save_config(self, config=None):
        """保存配置到文件
        
        參數:
            config (dict, 可選): 要保存的配置，默認為當前配置
            
        返回:
            bool: 是否保存成功
        """
        if config is None:
            config = self.config
            
        try:
            # 確保輸出目錄存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                    
            self.config = config
            self.logger.info(f"配置保存到 {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件時出錯: {e}")
            return False
            
    # 獲取配置的便捷方法
    def get_api_keys(self):
        """獲取API密鑰"""
        return self.config.get('api_keys', {})
        
    def get_output_settings(self):
        """獲取輸出設置"""
        return self.config.get('output', {})
        
    def get_style_settings(self):
        """獲取樣式設置"""
        return self.config.get('style', {})
        
    def get_content_settings(self):
        """獲取內容設置"""
        return self.config.get('content', {})
        
    def get_watermark_settings(self):
        """獲取水印設置"""
        return self.config.get('watermark', {})
        
    def get_audio_settings(self):
        """獲取音頻設置"""
        return self.config.get('audio', {})
        
    def get_article_settings(self):
        """獲取文章處理設置"""
        return self.config.get('article', {})
        
    def get_digital_human_settings(self):
        """獲取數字人設置"""
        return self.config.get('digital_human', {})
        
    def get_server_settings(self):
        """獲取服務器設置"""
        return self.config.get('server', {})
        
    # 更新配置的便捷方法
    def update_api_key(self, provider, key):
        """更新API密鑰
        
        參數:
            provider (str): API提供者名稱
            key (str): API密鑰
            
        返回:
            bool: 是否更新成功
        """
        if 'api_keys' not in self.config:
            self.config['api_keys'] = {}
            
        self.config['api_keys'][provider] = key
        return self.save_config()
        
    def update_section(self, section_name, section_data):
        """更新配置章節
        
        參數:
            section_name (str): 章節名稱
            section_data (dict): 章節數據
            
        返回:
            bool: 是否更新成功
        """
        self.config[section_name] = section_data
        return self.save_config()
    
    def get_module_settings(self, module_name):
        """獲取特定模組的設置
        
        參數:
            module_name (str): 模組名稱，如 'stock', 'travel', 'education'
            
        返回:
            dict: 模組設置
        """
        return self.config.get('modules', {}).get(module_name, {})
    
    def update_module_settings(self, module_name, settings):
        """更新特定模組的設置
        
        參數:
            module_name (str): 模組名稱
            settings (dict): 模組設置
            
        返回:
            bool: 是否更新成功
        """
        if 'modules' not in self.config:
            self.config['modules'] = {}
            
        self.config['modules'][module_name] = settings
        return self.save_config()