#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 內容處理器
"""

import re
import logging
import jieba
import jieba.analyse
import pandas as pd
from datetime import datetime

class ContentProcessor:
    """內容處理器
    
    負責解析、分析文章內容，識別股票代碼和關鍵信息。
    """
    
    def __init__(self):
        """初始化內容處理器"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化結巴分詞
        try:
            jieba.initialize()
            self.jieba_available = True
        except:
            self.logger.warning("結巴分詞初始化失敗，將使用簡單的文本分析方法")
            self.jieba_available = False
        
    def process_article(self, article_text, strategy='sentence'):
        """處理文章內容
        
        參數:
            article_text (str): 文章文本
            strategy (str): 分割策略，可以是'sentence', 'paragraph', 或'length'
            
        返回:
            dict: 處理結果
        """
        self.logger.info(f"處理文章 (策略: {strategy})")
        
        # 分析文章結構
        structure = self._analyze_structure(article_text)
        
        # 分割內容
        segments = self._split_content(article_text, strategy)
        
        # 提取股票代碼
        stock_codes = self._extract_stock_codes(article_text)
        
        # 提取關鍵詞
        keywords = self._extract_keywords(article_text)
        
        # 情感分析
        sentiment = self._analyze_sentiment(article_text)
        
        # 時間相關信息
        date_info = self._extract_date_info(article_text)
        
        # 組織結果
        result = {
            'title': structure.get('title', ''),
            'structure': structure,
            'segments': segments,
            'stock_codes': stock_codes,
            'keywords': keywords,
            'sentiment': sentiment,
            'date_info': date_info,
            'main_ticker': stock_codes['us'][0] if stock_codes['us'] else None
        }
        
        self.logger.info(f"文章處理完成，共 {len(segments)} 個段落, {len(stock_codes['all'])} 個股票代碼")
        return result
        
    def _analyze_structure(self, text):
        """分析文章結構
        
        參數:
            text (str): 文章文本
            
        返回:
            dict: 結構信息
        """
        lines = text.split('\n')
        
        # 檢測標題 (通常是第一行非空行)
        title = ""
        for line in lines:
            if line.strip():
                title = line.strip()
                break
                
        # 檢測段落
        paragraphs = self._split_content(text, 'paragraph')
        
        # 分割章節（假設標題為短句且不以標點結尾）
        sections = []
        current_section = {'title': '引言', 'content': []}
        
        for para in paragraphs:
            para_stripped = para.strip()
            # 短句可能是標題
            if len(para_stripped) < 40 and not para_stripped.endswith(('.', '。', '!', '！', '?', '？')):
                # 保存之前的章節
                if current_section['content']:
                    sections.append(current_section)
                # 創建新章節
                current_section = {'title': para_stripped, 'content': []}
            else:
                current_section['content'].append(para_stripped)
                
        # 添加最後一個章節
        if current_section['content']:
            sections.append(current_section)
            
        return {
            'title': title,
            'paragraphs': paragraphs,
            'sections': sections,
            'word_count': len(text)
        }
        
    def _split_content(self, text, strategy):
        """根據策略分割文章內容
        
        參數:
            text (str): 文章文本
            strategy (str): 分割策略
            
        返回:
            list: 分割後的內容列表
        """
        if strategy == 'sentence':
            # 分割為句子
            sentences = re.split(r'([。！？\.!?])', text)
            result = []
            
            # 重組句子，保留標點
            i = 0
            while i < len(sentences) - 1:
                if i + 1 < len(sentences):
                    if sentences[i+1] in '。！？.!?':
                        result.append(sentences[i] + sentences[i+1])
                        i += 2
                    else:
                        result.append(sentences[i])
                        i += 1
                else:
                    result.append(sentences[i])
                    i += 1
                    
            return [s.strip() for s in result if s.strip()]
            
        elif strategy == 'paragraph':
            # 分割為段落
            paragraphs = text.split('\n\n')
            return [p.strip() for p in paragraphs if p.strip()]
            
        elif strategy == 'length':
            # 分割為固定長度
            max_length = 100  # 每段最大字符數
            sentences = self._split_content(text, 'sentence')
            
            result = []
            current_segment = ""
            
            for sentence in sentences:
                if len(current_segment) + len(sentence) <= max_length:
                    current_segment += sentence
                else:
                    if current_segment:
                        result.append(current_segment)
                    current_segment = sentence
                    
            if current_segment:
                result.append(current_segment)
                
            return result
            
        else:
            self.logger.warning(f"未知的分割策略: {strategy}，使用整篇文章")
            return [text]
        
    def _extract_stock_codes(self, text):
        """提取文章中的股票代碼
        
        參數:
            text (str): 文章文本
            
        返回:
            dict: 股票代碼字典
        """
        # 美股代碼（通常為2-5個大寫字母）
        us_pattern = r'\b[A-Z]{2,5}\b'
        
        # 台股代碼（通常為4位數字）
        tw_pattern = r'\b\d{4}\b'
        
        # 港股代碼（通常為5位數字，前面加0）
        hk_pattern = r'\b0\d{4}\b'
        
        # 常見非股票代碼（避免誤判）
        common_words = ["CEO", "CFO", "CTO", "COO", "USA", "GDP", "CPI", "USD", "AI", "ML", "AR", "VR", 
                        "IOT", "API", "HTTPS", "LGBT", "NASA", "FBI", "CIA", "NBA", "NFL", "WHO", 
                        "COVID", "WINDOWS", "APPLE", "THE", "FOR", "AND", "BUT"]
        
        # 提取代碼
        us_codes = re.findall(us_pattern, text)
        us_codes = [code for code in us_codes if code not in common_words]
        
        tw_codes = re.findall(tw_pattern, text)
        hk_codes = re.findall(hk_pattern, text)
        
        # 去重
        us_codes = list(set(us_codes))
        tw_codes = list(set(tw_codes))
        hk_codes = list(set(hk_codes))
        
        all_codes = us_codes + tw_codes + hk_codes
        
        return {
            'us': us_codes,
            'tw': tw_codes,
            'hk': hk_codes,
            'all': all_codes
        }
        
    def _extract_keywords(self, text, top_k=20):
        """提取文章關鍵詞
        
        參數:
            text (str): 文章文本
            top_k (int): 返回的關鍵詞數量
            
        返回:
            list: 關鍵詞列表 [(詞, 權重), ...]
        """
        # 使用結巴分詞進行提取
        if self.jieba_available:
            try:
                keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
                return keywords
            except Exception as e:
                self.logger.error(f"使用結巴提取關鍵詞失敗: {e}")
                
        # 退回到簡單的詞頻分析
        words = {}
        
        # 分詞（簡單按空格分割，不適合中文）
        for word in text.split():
            word = word.strip(',.!?;:()[]{}"\'"。，！？；：（）【】「」『』""''')
            if len(word) > 1:  # 忽略單字符
                words[word] = words.get(word, 0) + 1
                
        # 排序
        sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:top_k]
        
    def _analyze_sentiment(self, text):
        """分析文章情感傾向
        
        參數:
            text (str): 文章文本
            
        返回:
            dict: 情感分析結果
        """
        # 正面詞彙
        positive_words = ["上漲", "增長", "上升", "看好", "樂觀", "強勁", "突破", 
                         "利好", "機會", "成功", "優勢", "提升", "獲利"]
                         
        # 負面詞彙
        negative_words = ["下跌", "下降", "減少", "看空", "悲觀", "疲軟", "跌破",
                         "利空", "風險", "失敗", "劣勢", "下滑", "虧損"]
                         
        # 計算詞彙出現次數
        positive_count = sum(text.count(word) for word in positive_words)
        negative_count = sum(text.count(word) for word in negative_words)
        total_count = positive_count + negative_count
        
        # 計算情感得分
        sentiment_score = 0
        if total_count > 0:
            sentiment_score = (positive_count - negative_count) / total_count
            
        # 確定情感標籤
        if sentiment_score > 0.2:
            sentiment_label = "positive"
        elif sentiment_score < -0.2:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
            
        return {
            "score": sentiment_score,
            "label": sentiment_label,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total_count": total_count
        }
        
    def _extract_date_info(self, text):
        """提取文章中的日期信息
        
        參數:
            text (str): 文章文本
            
        返回:
            dict: 日期信息
        """
        # 日期模式
        date_patterns = [
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日號]?',  # YYYY-MM-DD, YYYY/MM/DD, YYYY年MM月DD日
            r'\d{1,2}[-/月]\d{1,2}[日號]?',  # MM-DD, MM/DD, MM月DD日
            r'昨天|今天|明天',  # 相對日期
            r'上週|本週|下週',
            r'上個月|這個月|下個月',
            r'上季度|本季度|下季度',
            r'去年|今年|明年'
        ]
        
        # 合併所有模式
        combined_pattern = '|'.join(f'({p})' for p in date_patterns)
        
        # 提取日期
        dates = re.findall(combined_pattern, text)
        # 扁平化結果
        extracted_dates = [date for sublist in dates for date in sublist if date]
        
        # 識別文章日期（假設是第一個找到的日期）
        article_date = None
        if extracted_dates:
            article_date = extracted_dates[0]
            
        # 統計日期類型分布
        date_distribution = {
            'absolute_dates': 0,  # 絕對日期 (YYYY-MM-DD)
            'relative_dates': 0,  # 相對日期 (昨天, 今天, 明天)
            'periods': 0  # 時間段 (本月, 本季度)
        }
        
        for date in extracted_dates:
            if re.match(r'\d{4}[-/年]', date):
                date_distribution['absolute_dates'] += 1
            elif re.match(r'昨天|今天|明天|上週|本週|下週', date):
                date_distribution['relative_dates'] += 1
            else:
                date_distribution['periods'] += 1
                
        return {
            'extracted_dates': extracted_dates,
            'article_date': article_date,
            'date_distribution': date_distribution
        }