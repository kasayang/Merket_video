#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 股票數據收集器
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime, timedelta
import os

class StockDataCollector:
    """股票數據收集器
    
    負責從各種來源獲取股票數據和相關信息。
    """
    
    def __init__(self, api_keys=None):
        """初始化股票數據收集器
        
        參數:
            api_keys (dict, 可選): API密鑰字典
        """
        self.api_keys = api_keys or {}
        self.logger = logging.getLogger(__name__)
        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'data')
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def get_stock_data(self, ticker, period="1y", interval="1d", use_cache=True):
        """獲取股票數據
        
        參數:
            ticker (str): 股票代碼
            period (str): 時間範圍（例如: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
            interval (str): 數據間隔（例如: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo）
            use_cache (bool): 是否使用緩存
            
        返回:
            pandas.DataFrame: 股票數據
        """
        self.logger.info(f"獲取股票數據: {ticker}, 週期: {period}, 間隔: {interval}")
        
        # 檢查緩存
        if use_cache:
            cache_path = self._get_cache_path(ticker, period, interval)
            if os.path.exists(cache_path):
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
                # 如果緩存不超過1天，則使用緩存
                if cache_age.days < 1:
                    try:
                        self.logger.info(f"使用緩存數據: {cache_path}")
                        return pd.read_pickle(cache_path)
                    except Exception as e:
                        self.logger.warning(f"讀取緩存失敗: {e}")
        
        # 嘗試從Yahoo Finance獲取數據
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval=interval)
            
            # 檢查是否成功獲取數據
            if data.empty:
                self.logger.warning(f"無法從Yahoo Finance獲取數據: {ticker}")
                return self._create_default_data(ticker)
                
            # 計算技術指標
            data = self._add_technical_indicators(data)
            
            # 儲存到緩存
            if use_cache:
                cache_path = self._get_cache_path(ticker, period, interval)
                data.to_pickle(cache_path)
                self.logger.info(f"數據已緩存到: {cache_path}")
                
            return data
            
        except Exception as e:
            self.logger.error(f"從Yahoo Finance獲取數據失敗: {e}")
            return self._create_default_data(ticker)
            
    def get_stock_info(self, ticker, use_cache=True):
        """獲取股票基本信息
        
        參數:
            ticker (str): 股票代碼
            use_cache (bool): 是否使用緩存
            
        返回:
            dict: 股票基本信息
        """
        self.logger.info(f"獲取股票信息: {ticker}")
        
        # 檢查緩存
        if use_cache:
            cache_path = os.path.join(self.cache_dir, f"{ticker}_info.pkl")
            if os.path.exists(cache_path):
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
                # 如果緩存不超過1天，則使用緩存
                if cache_age.days < 1:
                    try:
                        self.logger.info(f"使用緩存數據: {cache_path}")
                        return pd.read_pickle(cache_path)
                    except Exception as e:
                        self.logger.warning(f"讀取緩存失敗: {e}")
        
        # 嘗試從Yahoo Finance獲取數據
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 處理過大的字符串字段
            if 'longBusinessSummary' in info and len(info['longBusinessSummary']) > 1000:
                info['longBusinessSummary'] = info['longBusinessSummary'][:997] + "..."
                
            # 儲存到緩存
            if use_cache:
                cache_path = os.path.join(self.cache_dir, f"{ticker}_info.pkl")
                pd.to_pickle(info, cache_path)
                self.logger.info(f"信息已緩存到: {cache_path}")
                
            return info
            
        except Exception as e:
            self.logger.error(f"獲取股票信息失敗: {e}")
            return {"symbol": ticker, "error": str(e)}
            
    def get_latest_news(self, ticker, max_items=5, use_cache=True):
        """獲取最新股票相關新聞
        
        參數:
            ticker (str): 股票代碼
            max_items (int): 最大新聞條數
            use_cache (bool): 是否使用緩存
            
        返回:
            list: 新聞列表
        """
        self.logger.info(f"獲取股票新聞: {ticker}")
        
        # 檢查緩存
        if use_cache:
            cache_path = os.path.join(self.cache_dir, f"{ticker}_news.pkl")
            if os.path.exists(cache_path):
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
                # 如果緩存不超過4小時，則使用緩存
                if cache_age.seconds < 4 * 60 * 60:
                    try:
                        self.logger.info(f"使用緩存數據: {cache_path}")
                        return pd.read_pickle(cache_path)
                    except Exception as e:
                        self.logger.warning(f"讀取緩存失敗: {e}")
        
        # 嘗試從Yahoo Finance獲取數據
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            # 格式化新聞數據
            formatted_news = []
            for item in news[:max_items]:
                news_item = {
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', ''),
                    'publishedAt': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    'summary': item.get('summary', '')
                }
                
                # 添加縮略圖（如果有）
                if 'thumbnail' in item and 'resolutions' in item['thumbnail'] and len(item['thumbnail']['resolutions']) > 0:
                    news_item['thumbnail'] = item['thumbnail']['resolutions'][0].get('url', '')
                    
                formatted_news.append(news_item)
                
            # 儲存到緩存
            if use_cache:
                cache_path = os.path.join(self.cache_dir, f"{ticker}_news.pkl")
                pd.to_pickle(formatted_news, cache_path)
                self.logger.info(f"新聞已緩存到: {cache_path}")
                
            return formatted_news
            
        except Exception as e:
            self.logger.error(f"獲取股票新聞失敗: {e}")
            return []
            
    def get_market_index(self, index_symbol="^GSPC", period="1y", interval="1d", use_cache=True):
        """獲取市場指數數據
        
        參數:
            index_symbol (str): 指數代碼（例如: ^GSPC為S&P 500, ^DJI為道瓊斯, ^IXIC為納斯達克）
            period (str): 時間範圍
            interval (str): 數據間隔
            use_cache (bool): 是否使用緩存
            
        返回:
            pandas.DataFrame: 指數數據
        """
        self.logger.info(f"獲取市場指數: {index_symbol}")
        
        # 使用與股票數據相同的方法，但檢查不同的緩存路徑
        cache_key = f"{index_symbol.replace('^', 'IDX_')}"
        return self.get_stock_data(index_symbol, period, interval, use_cache)
    
    def _add_technical_indicators(self, data):
        """添加技術指標
        
        參數:
            data (pandas.DataFrame): 原始股票數據
            
        返回:
            pandas.DataFrame: 添加技術指標後的數據
        """
        if data.empty:
            return data
            
        try:
            # 計算移動平均線
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            
            # 計算RSI
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # 計算MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']
            
            # 計算布林帶
            data['Bollinger_Upper'] = data['SMA_20'] + (data['Close'].rolling(window=20).std() * 2)
            data['Bollinger_Lower'] = data['SMA_20'] - (data['Close'].rolling(window=20).std() * 2)
            
            # 計算每日回報率
            data['Daily_Return'] = data['Close'].pct_change()
            
            # 計算波動率 (20天)
            data['Volatility'] = data['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
            
            # 添加交易量相對變化
            data['Volume_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_SMA_20']
            
            return data
            
        except Exception as e:
            self.logger.error(f"計算技術指標失敗: {e}")
            return data
            
    def _create_default_data(self, ticker):
        """創建默認數據（當無法獲取真實數據時）
        
        參數:
            ticker (str): 股票代碼
            
        返回:
            pandas.DataFrame: 模擬股票數據
        """
        self.logger.info(f"創建 {ticker} 的模擬數據")
        
        # 創建日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # 生成模擬價格數據
        n = len(dates)
        close = 100 + np.cumsum(np.random.normal(0, 1, n)) / 10
        high = close + np.random.uniform(0, 3, n)
        low = close - np.random.uniform(0, 3, n)
        open_price = low + np.random.uniform(0, high - low, n)
        volume = np.random.randint(100000, 1000000, n)
        
        # 創建DataFframe
        df = pd.DataFrame({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume
        }, index=dates)
        
        # 添加技術指標
        df = self._add_technical_indicators(df)
        
        # 標記為模擬數據
        df.attrs['is_simulated'] = True
        df.attrs['ticker'] = ticker
        
        return df
        
    def _get_cache_path(self, ticker, period, interval):
        """獲取緩存文件路徑
        
        參數:
            ticker (str): 股票代碼
            period (str): 時間範圍
            interval (str): 數據間隔
            
        返回:
            str: 緩存文件路徑
        """
        cache_filename = f"{ticker}_{period}_{interval}.pkl"
        return os.path.join(self.cache_dir, cache_filename)