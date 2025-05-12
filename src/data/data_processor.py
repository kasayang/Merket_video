#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票數據影片自動化製作系統 - 數據處理器
"""

import os
import pandas as pd
import numpy as np
import logging
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 設置 Matplotlib 後端，避免需要 GUI
from datetime import datetime, timedelta

class DataProcessor:
    """數據處理器
    
    負責處理和分析股票數據，計算技術指標，生成圖表等。
    """
    
    def __init__(self, config=None):
        """初始化數據處理器
        
        參數:
            config (dict, 可選): 配置設定
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.cache_dir = os.path.join(os.getcwd(), 'cache', 'charts')
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 設置繪圖樣式
        plt.style.use('dark_background')
    
    def process_stock_data(self, stock_data):
        """處理股票數據
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            
        返回:
            pandas.DataFrame: 處理後的股票數據
        """
        if stock_data is None or stock_data.empty:
            self.logger.error("無效的股票數據")
            return None
            
        # 確保數據已排序
        stock_data = stock_data.sort_index()
        
        # 計算技術指標
        processed_data = self._add_technical_indicators(stock_data)
        
        self.logger.info(f"股票數據處理完成，共 {len(processed_data)} 個數據點")
        return processed_data
    
    def generate_stock_chart(self, stock_data, chart_type='candlestick', 
                             start_date=None, end_date=None, indicators=None,
                             output_file=None):
        """生成股票圖表
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            chart_type (str): 圖表類型 ('candlestick', 'line', 'ohlc')
            start_date (str/datetime, 可選): 開始日期
            end_date (str/datetime, 可選): 結束日期
            indicators (list, 可選): 技術指標列表
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            str: 圖表文件路徑
        """
        if stock_data is None or stock_data.empty:
            self.logger.error("無效的股票數據")
            return None
            
        # 設置預設指標
        if indicators is None:
            indicators = ['SMA_20', 'SMA_50', 'volume']
            
        # 設置預設輸出文件
        if output_file is None:
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"{ticker}_chart_{timestamp}.png")
            
        # 篩選日期範圍
        if start_date is not None or end_date is not None:
            stock_data = self._filter_date_range(stock_data, start_date, end_date)
            if stock_data.empty:
                self.logger.error("篩選後的數據為空")
                return None
        
        # 根據圖表類型生成圖表
        if chart_type == 'candlestick':
            self._generate_candlestick_chart(stock_data, indicators, output_file)
        elif chart_type == 'line':
            self._generate_line_chart(stock_data, indicators, output_file)
        elif chart_type == 'ohlc':
            self._generate_ohlc_chart(stock_data, indicators, output_file)
        else:
            self.logger.error(f"不支援的圖表類型: {chart_type}")
            return None
            
        return output_file
    
    def analyze_stock_performance(self, stock_data, lookback_period=30):
        """分析股票表現
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            lookback_period (int): 回顧期間（天數）
            
        返回:
            dict: 分析結果
        """
        if stock_data is None or stock_data.empty:
            self.logger.error("無效的股票數據")
            return None
            
        # 確保數據已排序
        stock_data = stock_data.sort_index()
        
        # 只分析最近的數據
        recent_data = stock_data.iloc[-lookback_period:] if len(stock_data) > lookback_period else stock_data
        
        # 計算績效指標
        try:
            # 計算價格變化
            first_price = recent_data['Close'].iloc[0]
            last_price = recent_data['Close'].iloc[-1]
            price_change = last_price - first_price
            price_change_pct = (price_change / first_price) * 100
            
            # 計算日均回報率
            daily_returns = recent_data['Close'].pct_change().dropna()
            avg_daily_return = daily_returns.mean() * 100
            
            # 計算波動率（標準差）
            volatility = daily_returns.std() * 100
            
            # 計算最大回撤
            cumulative_returns = (1 + daily_returns).cumprod()
            max_drawdown = (cumulative_returns / cumulative_returns.cummax() - 1).min() * 100
            
            # 計算成交量變化
            if 'Volume' in recent_data.columns:
                avg_volume = recent_data['Volume'].mean()
                recent_volume = recent_data['Volume'].iloc[-5:].mean()
                volume_change_pct = ((recent_volume / avg_volume) - 1) * 100
            else:
                avg_volume = 0
                volume_change_pct = 0
                
            # 計算趨勢指標
            if 'SMA_20' in recent_data.columns and 'SMA_50' in recent_data.columns:
                last_sma20 = recent_data['SMA_20'].iloc[-1]
                last_sma50 = recent_data['SMA_50'].iloc[-1]
                
                if last_sma20 > last_sma50:
                    trend = "上升趨勢" if price_change > 0 else "修正中"
                else:
                    trend = "下降趨勢" if price_change < 0 else "反彈中"
            else:
                trend = "上升" if price_change > 0 else "下降"
                
            # 計算RSI指標
            if 'RSI' in recent_data.columns:
                last_rsi = recent_data['RSI'].iloc[-1]
                
                if last_rsi >= 70:
                    rsi_signal = "超買"
                elif last_rsi <= 30:
                    rsi_signal = "超賣"
                else:
                    rsi_signal = "中性"
            else:
                last_rsi = None
                rsi_signal = None
                
            # 計算MACD指標
            if all(col in recent_data.columns for col in ['MACD', 'Signal_Line']):
                last_macd = recent_data['MACD'].iloc[-1]
                last_signal = recent_data['Signal_Line'].iloc[-1]
                
                if last_macd > last_signal:
                    macd_signal = "看漲"
                else:
                    macd_signal = "看跌"
            else:
                macd_signal = None
                
            # 組織結果
            result = {
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'avg_daily_return': avg_daily_return,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'avg_volume': avg_volume,
                'volume_change_pct': volume_change_pct,
                'trend': trend,
                'rsi': last_rsi,
                'rsi_signal': rsi_signal,
                'macd_signal': macd_signal,
                'lookback_period': lookback_period,
                'start_date': recent_data.index[0].strftime('%Y-%m-%d'),
                'end_date': recent_data.index[-1].strftime('%Y-%m-%d')
            }
            
            self.logger.info(f"股票績效分析完成: {result['trend']}, 價格變化 {result['price_change_pct']:.2f}%")
            return result
            
        except Exception as e:
            self.logger.error(f"分析股票表現時出錯: {e}")
            return None
    
    def generate_analysis_report(self, stock_data, output_file=None):
        """生成分析報告
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            dict: 報告內容和文件路徑
        """
        if stock_data is None or stock_data.empty:
            self.logger.error("無效的股票數據")
            return None
            
        # 設置預設輸出文件
        if output_file is None:
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"{ticker}_report_{timestamp}.json")
            
        # 股票基本信息
        ticker = stock_data.attrs.get('ticker', 'STOCK')
        start_date = stock_data.index[0]
        end_date = stock_data.index[-1]
        
        # 分析不同時間週期的表現
        performance_30d = self.analyze_stock_performance(stock_data, 30)
        performance_90d = self.analyze_stock_performance(stock_data, 90)
        
        # 檢測主要支撐和阻力位
        support_resistance = self._detect_support_resistance(stock_data)
        
        # 識別技術形態
        patterns = self._identify_patterns(stock_data)
        
        # 組織報告內容
        report = {
            'ticker': ticker,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'total_days': len(stock_data)
            },
            'performance': {
                '30d': performance_30d,
                '90d': performance_90d
            },
            'support_resistance': support_resistance,
            'patterns': patterns,
            'summary': self._generate_summary(stock_data, performance_30d, patterns)
        }
        
        # 保存報告
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"分析報告已生成: {output_file}")
            
            return {
                'report': report,
                'file_path': output_file
            }
            
        except Exception as e:
            self.logger.error(f"保存分析報告時出錯: {e}")
            return {
                'report': report,
                'file_path': None
            }
    
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
            
            # 計算 RSI
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # 計算 MACD
            exp1 = data['Close'].ewm(span=12, adjust=False).mean()
            exp2 = data['Close'].ewm(span=26, adjust=False).mean()
            data['MACD'] = exp1 - exp2
            data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
            data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']
            
            # 計算布林帶
            data['Bollinger_Mid'] = data['SMA_20']
            std = data['Close'].rolling(window=20).std()
            data['Bollinger_Upper'] = data['Bollinger_Mid'] + (std * 2)
            data['Bollinger_Lower'] = data['Bollinger_Mid'] - (std * 2)
            
            # 計算每日回報率
            data['Daily_Return'] = data['Close'].pct_change()
            
            # 計算波動率 (20天)
            data['Volatility'] = data['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
            
            # 添加交易量相對變化
            data['Volume_SMA_20'] = data['Volume'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume_SMA_20']
            
            # 計算動量指標 (Momentum)
            data['Momentum'] = data['Close'] / data['Close'].shift(10) - 1
            
            # 計算 ATR (Average True Range)
            tr1 = data['High'] - data['Low']
            tr2 = abs(data['High'] - data['Close'].shift())
            tr3 = abs(data['Low'] - data['Close'].shift())
            data['TR'] = pd.DataFrame([tr1, tr2, tr3]).max()
            data['ATR'] = data['TR'].rolling(window=14).mean()
            
            return data
            
        except Exception as e:
            self.logger.error(f"計算技術指標失敗: {e}")
            return data
            
    def _generate_candlestick_chart(self, stock_data, indicators, output_file):
        """生成 K 線圖
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            indicators (list): 技術指標列表
            output_file (str): 輸出文件路徑
            
        返回:
            bool: 是否成功
        """
        try:
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            
            # 創建圖表佈局
            plt.figure(figsize=(16, 10))
            
            # 創建 K 線圖
            ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=3, colspan=1)
            
            # 繪製 K 線
            for i in range(len(stock_data)):
                # 確定顏色（漲綠跌紅）
                if stock_data['Close'].iloc[i] >= stock_data['Open'].iloc[i]:
                    color = '#00FF00'  # 綠色（漲）
                else:
                    color = '#FF0000'  # 紅色（跌）
                    
                # 繪製實體
                ax1.plot([i, i], [stock_data['Low'].iloc[i], stock_data['High'].iloc[i]], color, linewidth=1)
                ax1.plot([i, i], [stock_data['Open'].iloc[i], stock_data['Close'].iloc[i]], color, linewidth=3)
            
            # 添加技術指標
            if 'SMA_20' in indicators and 'SMA_20' in stock_data.columns:
                ax1.plot(stock_data['SMA_20'], '#FF8C00', linewidth=1.5, label='SMA 20')
            if 'SMA_50' in indicators and 'SMA_50' in stock_data.columns:
                ax1.plot(stock_data['SMA_50'], '#4169E1', linewidth=1.5, label='SMA 50')
            if 'SMA_200' in indicators and 'SMA_200' in stock_data.columns:
                ax1.plot(stock_data['SMA_200'], '#800080', linewidth=1.5, label='SMA 200')
                
            # 添加布林帶
            if 'bollinger' in indicators:
                if all(col in stock_data.columns for col in ['Bollinger_Upper', 'Bollinger_Lower']):
                    ax1.plot(stock_data['Bollinger_Upper'], '#90EE90', linewidth=1, linestyle='--', label='上軌')
                    ax1.plot(stock_data['Bollinger_Lower'], '#90EE90', linewidth=1, linestyle='--', label='下軌')
                    ax1.fill_between(range(len(stock_data)), stock_data['Bollinger_Lower'], stock_data['Bollinger_Upper'], color='#90EE90', alpha=0.1)
            
            # 設置標題和標籤
            ax1.set_title(f'{ticker} K線圖', fontsize=15)
            ax1.set_ylabel('價格', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')
            
            # 交易量圖
            if 'volume' in indicators and 'Volume' in stock_data.columns:
                ax2 = plt.subplot2grid((6, 1), (3, 0), rowspan=1, colspan=1, sharex=ax1)
                
                # 繪製交易量柱狀圖
                for i in range(len(stock_data)):
                    if stock_data['Close'].iloc[i] >= stock_data['Open'].iloc[i]:
                        color = '#00FF00'  # 綠色（漲）
                    else:
                        color = '#FF0000'  # 紅色（跌）
                    ax2.bar(i, stock_data['Volume'].iloc[i], color=color, alpha=0.7)
                    
                ax2.set_ylabel('成交量', fontsize=12)
                ax2.grid(True, alpha=0.3)
                
                # 添加交易量均線
                if 'Volume_SMA_20' in stock_data.columns:
                    ax2.plot(stock_data['Volume_SMA_20'], '#FF8C00', linewidth=1, label='Vol MA 20')
                    ax2.legend(loc='upper left')
            
            # RSI 指標
            if 'rsi' in indicators and 'RSI' in stock_data.columns:
                ax3 = plt.subplot2grid((6, 1), (4, 0), rowspan=1, colspan=1, sharex=ax1)
                ax3.plot(stock_data['RSI'], '#FF4500', linewidth=1.5)
                ax3.axhline(70, color='#FF4500', linestyle='--', alpha=0.5)
                ax3.axhline(30, color='#1E90FF', linestyle='--', alpha=0.5)
                ax3.fill_between(range(len(stock_data)), 30, 70, color='#808080', alpha=0.1)
                ax3.set_ylabel('RSI', fontsize=12)
                ax3.grid(True, alpha=0.3)
                ax3.set_ylim(0, 100)
            
            # MACD 指標
            if 'macd' in indicators and all(col in stock_data.columns for col in ['MACD', 'Signal_Line', 'MACD_Histogram']):
                ax4 = plt.subplot2grid((6, 1), (5, 0), rowspan=1, colspan=1, sharex=ax1)
                ax4.plot(stock_data['MACD'], '#1E90FF', linewidth=1.5, label='MACD')
                ax4.plot(stock_data['Signal_Line'], '#FF4500', linewidth=1, label='Signal')
                
                # 繪製 MACD 柱狀圖
                for i in range(len(stock_data)):
                    hist_val = stock_data['MACD_Histogram'].iloc[i]
                    if hist_val >= 0:
                        color = '#00FF00'  # 綠色（正值）
                    else:
                        color = '#FF0000'  # 紅色（負值）
                    ax4.bar(i, hist_val, color=color, alpha=0.7)
                    
                ax4.set_ylabel('MACD', fontsize=12)
                ax4.grid(True, alpha=0.3)
                ax4.legend(loc='upper left')
            
            # 設置 x 軸
            plt.subplots_adjust(left=0.07, right=0.93, top=0.95, bottom=0.1, hspace=0.3)
            
            # 使用 stock_data 的索引作為 x 軸標籤
            dates = [d.strftime('%Y-%m-%d') for d in stock_data.index]
            
            # 調整 x 軸標籤（顯示部分日期以避免擁擠）
            step = max(1, len(dates) // 10)  # 最多顯示 10 個標籤
            ax4.set_xticks(range(0, len(dates), step))
            ax4.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45)
            
            # 保存圖表
            plt.savefig(output_file, dpi=100, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"K線圖已生成: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成K線圖失敗: {e}")
            return False
    
    def _generate_line_chart(self, stock_data, indicators, output_file):
        """生成折線圖
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            indicators (list): 技術指標列表
            output_file (str): 輸出文件路徑
            
        返回:
            bool: 是否成功
        """
        try:
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            
            # 創建圖表
            plt.figure(figsize=(16, 8))
            
            # 繪製收盤價折線
            plt.plot(stock_data.index, stock_data['Close'], color='#1E90FF', linewidth=2, label='收盤價')
            
            # 添加技術指標
            if 'SMA_20' in indicators and 'SMA_20' in stock_data.columns:
                plt.plot(stock_data.index, stock_data['SMA_20'], '#FF8C00', linewidth=1.5, label='SMA 20')
            if 'SMA_50' in indicators and 'SMA_50' in stock_data.columns:
                plt.plot(stock_data.index, stock_data['SMA_50'], '#4169E1', linewidth=1.5, label='SMA 50')
            if 'SMA_200' in indicators and 'SMA_200' in stock_data.columns:
                plt.plot(stock_data.index, stock_data['SMA_200'], '#800080', linewidth=1.5, label='SMA 200')
                
            # 添加布林帶
            if 'bollinger' in indicators:
                if all(col in stock_data.columns for col in ['Bollinger_Upper', 'Bollinger_Lower']):
                    plt.plot(stock_data.index, stock_data['Bollinger_Upper'], '#90EE90', linewidth=1, linestyle='--', label='布林上軌')
                    plt.plot(stock_data.index, stock_data['Bollinger_Lower'], '#90EE90', linewidth=1, linestyle='--', label='布林下軌')
                    plt.fill_between(stock_data.index, stock_data['Bollinger_Lower'], stock_data['Bollinger_Upper'], color='#90EE90', alpha=0.1)
            
            # 設置標題和標籤
            plt.title(f'{ticker} 價格走勢', fontsize=15)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('價格', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best')
            
            # 調整 x 軸標籤
            plt.xticks(rotation=45)
            
            # 添加圖表說明
            if 'performance' in indicators:
                # 計算表現指標
                performance = self.analyze_stock_performance(stock_data, 30)
                
                if performance:
                    explanation = f"30天變化: {performance['price_change_pct']:.2f}%, "
                    explanation += f"波動率: {performance['volatility']:.2f}%, "
                    explanation += f"趨勢: {performance['trend']}"
                    
                    plt.figtext(0.5, 0.01, explanation, ha='center', fontsize=12)
            
            # 保存圖表
            plt.tight_layout()
            plt.savefig(output_file, dpi=100)
            plt.close()
            
            self.logger.info(f"折線圖已生成: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成折線圖失敗: {e}")
            return False
    
    def _generate_ohlc_chart(self, stock_data, indicators, output_file):
        """生成 OHLC 圖
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            indicators (list): 技術指標列表
            output_file (str): 輸出文件路徑
            
        返回:
            bool: 是否成功
        """
        try:
            ticker = stock_data.attrs.get('ticker', 'STOCK')
            
            # 創建圖表佈局
            plt.figure(figsize=(16, 10))
            
            # OHLC 圖
            ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=3, colspan=1)
            
            # 繪製 OHLC 柱狀
            for i in range(len(stock_data)):
                # 繪製高低點線
                ax1.plot([i, i], [stock_data['Low'].iloc[i], stock_data['High'].iloc[i]], '#1E90FF', linewidth=1)
                
                # 繪製開盤點
                ax1.plot([i-0.1, i], [stock_data['Open'].iloc[i], stock_data['Open'].iloc[i]], '#1E90FF', linewidth=2)
                
                # 繪製收盤點
                ax1.plot([i, i+0.1], [stock_data['Close'].iloc[i], stock_data['Close'].iloc[i]], '#1E90FF', linewidth=2)
            
            # 添加技術指標
            if 'SMA_20' in indicators and 'SMA_20' in stock_data.columns:
                ax1.plot(stock_data['SMA_20'], '#FF8C00', linewidth=1.5, label='SMA 20')
            if 'SMA_50' in indicators and 'SMA_50' in stock_data.columns:
                ax1.plot(stock_data['SMA_50'], '#4169E1', linewidth=1.5, label='SMA 50')
            if 'SMA_200' in indicators and 'SMA_200' in stock_data.columns:
                ax1.plot(stock_data['SMA_200'], '#800080', linewidth=1.5, label='SMA 200')
            
            # 設置標題和標籤
            ax1.set_title(f'{ticker} OHLC圖', fontsize=15)
            ax1.set_ylabel('價格', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='upper left')
            
            # 交易量圖
            if 'volume' in indicators and 'Volume' in stock_data.columns:
                ax2 = plt.subplot2grid((6, 1), (3, 0), rowspan=1, colspan=1, sharex=ax1)
                ax2.bar(range(len(stock_data)), stock_data['Volume'], color='#1E90FF', alpha=0.7)
                ax2.set_ylabel('成交量', fontsize=12)
                ax2.grid(True, alpha=0.3)
            
            # RSI 指標
            if 'rsi' in indicators and 'RSI' in stock_data.columns:
                ax3 = plt.subplot2grid((6, 1), (4, 0), rowspan=1, colspan=1, sharex=ax1)
                ax3.plot(stock_data['RSI'], '#FF4500', linewidth=1.5)
                ax3.axhline(70, color='#FF4500', linestyle='--', alpha=0.5)
                ax3.axhline(30, color='#1E90FF', linestyle='--', alpha=0.5)
                ax3.set_ylabel('RSI', fontsize=12)
                ax3.grid(True, alpha=0.3)
                ax3.set_ylim(0, 100)
            
            # MACD 指標
            if 'macd' in indicators and all(col in stock_data.columns for col in ['MACD', 'Signal_Line']):
                ax4 = plt.subplot2grid((6, 1), (5, 0), rowspan=1, colspan=1, sharex=ax1)
                ax4.plot(stock_data['MACD'], '#1E90FF', linewidth=1.5, label='MACD')
                ax4.plot(stock_data['Signal_Line'], '#FF4500', linewidth=1, label='Signal')
                
                # 添加 MACD 柱狀圖
                if 'MACD_Histogram' in stock_data.columns:
                    for i in range(len(stock_data)):
                        hist_val = stock_data['MACD_Histogram'].iloc[i]
                        if hist_val >= 0:
                            color = '#00FF00'  # 綠色（正值）
                        else:
                            color = '#FF0000'  # 紅色（負值）
                        ax4.bar(i, hist_val, color=color, alpha=0.7)
                
                ax4.set_ylabel('MACD', fontsize=12)
                ax4.grid(True, alpha=0.3)
                ax4.legend(loc='upper left')
            
            # 設置 x 軸
            plt.subplots_adjust(left=0.07, right=0.93, top=0.95, bottom=0.1, hspace=0.3)
            
            # 使用 stock_data 的索引作為 x 軸標籤
            dates = [d.strftime('%Y-%m-%d') for d in stock_data.index]
            
            # 調整 x 軸標籤（顯示部分日期以避免擁擠）
            step = max(1, len(dates) // 10)  # 最多顯示 10 個標籤
            plt.xticks(range(0, len(dates), step), [dates[i] for i in range(0, len(dates), step)], rotation=45)
            
            # 保存圖表
            plt.savefig(output_file, dpi=100, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"OHLC圖已生成: {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成OHLC圖失敗: {e}")
            return False
    
    def _filter_date_range(self, data, start_date=None, end_date=None):
        """篩選日期範圍
        
        參數:
            data (pandas.DataFrame): 股票數據
            start_date (str/datetime, 可選): 開始日期
            end_date (str/datetime, 可選): 結束日期
            
        返回:
            pandas.DataFrame: 篩選後的數據
        """
        filtered_data = data.copy()
        
        if start_date is not None:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            filtered_data = filtered_data[filtered_data.index >= start_date]
            
        if end_date is not None:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            filtered_data = filtered_data[filtered_data.index <= end_date]
            
        return filtered_data
    
    def _detect_support_resistance(self, stock_data, window=20, threshold=0.03):
        """檢測支撐和阻力位
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            window (int): 滑動窗口大小
            threshold (float): 相似度閾值
            
        返回:
            dict: 支撐和阻力位
        """
        try:
            # 使用最近的數據
            recent_data = stock_data.iloc[-200:] if len(stock_data) > 200 else stock_data
            
            # 尋找價格極值
            highs = recent_data['High'].rolling(window, center=True).max()
            lows = recent_data['Low'].rolling(window, center=True).min()
            
            # 收集潛在的支撐位和阻力位
            potential_support = []
            potential_resistance = []
            
            # 檢測局部最低點（支撐位）
            for i in range(window, len(recent_data) - window):
                if recent_data['Low'].iloc[i] == lows.iloc[i]:
                    potential_support.append(recent_data['Low'].iloc[i])
                    
            # 檢測局部最高點（阻力位）
            for i in range(window, len(recent_data) - window):
                if recent_data['High'].iloc[i] == highs.iloc[i]:
                    potential_resistance.append(recent_data['High'].iloc[i])
            
            # 合併相近的價格水平
            support_levels = self._merge_price_levels(potential_support, threshold)
            resistance_levels = self._merge_price_levels(potential_resistance, threshold)
            
            # 按照強度排序（出現次數）
            support_levels = sorted(support_levels, key=lambda x: x[1], reverse=True)
            resistance_levels = sorted(resistance_levels, key=lambda x: x[1], reverse=True)
            
            # 選取最重要的幾個水平
            top_support = support_levels[:3] if len(support_levels) >= 3 else support_levels
            top_resistance = resistance_levels[:3] if len(resistance_levels) >= 3 else resistance_levels
            
            # 組織結果
            result = {
                'support': [{'price': level[0], 'strength': level[1]} for level in top_support],
                'resistance': [{'price': level[0], 'strength': level[1]} for level in top_resistance]
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"檢測支撐和阻力位時出錯: {e}")
            return {'support': [], 'resistance': []}
    
    def _merge_price_levels(self, price_levels, threshold):
        """合併相近的價格水平
        
        參數:
            price_levels (list): 價格水平列表
            threshold (float): 相似度閾值
            
        返回:
            list: 合併後的價格水平列表 [(價格, 出現次數), ...]
        """
        if not price_levels:
            return []
            
        # 排序價格水平
        sorted_levels = sorted(price_levels)
        
        # 合併相近的價格水平
        merged_levels = []
        current_level = sorted_levels[0]
        current_count = 1
        
        for level in sorted_levels[1:]:
            # 計算相對差異
            relative_diff = abs(level - current_level) / current_level
            
            if relative_diff <= threshold:
                # 相近水平，更新價格為平均值，增加計數
                current_level = (current_level * current_count + level) / (current_count + 1)
                current_count += 1
            else:
                # 新水平
                merged_levels.append((current_level, current_count))
                current_level = level
                current_count = 1
                
        # 添加最後一個水平
        merged_levels.append((current_level, current_count))
        
        return merged_levels
    
    def _identify_patterns(self, stock_data):
        """識別技術形態
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            
        返回:
            list: 技術形態列表
        """
        patterns = []
        
        # 使用最近的數據
        recent_data = stock_data.iloc[-60:] if len(stock_data) > 60 else stock_data
        
        # 檢測趨勢
        if 'SMA_20' in recent_data.columns and 'SMA_50' in recent_data.columns:
            # 確認上升趨勢
            if (recent_data['SMA_20'].iloc[-1] > recent_data['SMA_50'].iloc[-1] and
                recent_data['SMA_20'].iloc[-20] > recent_data['SMA_50'].iloc[-20]):
                patterns.append({
                    'name': '上升趨勢',
                    'description': 'SMA_20 持續位於 SMA_50 上方',
                    'strength': 'strong'
                })
            # 確認下降趨勢
            elif (recent_data['SMA_20'].iloc[-1] < recent_data['SMA_50'].iloc[-1] and
                  recent_data['SMA_20'].iloc[-20] < recent_data['SMA_50'].iloc[-20]):
                patterns.append({
                    'name': '下降趨勢',
                    'description': 'SMA_20 持續位於 SMA_50 下方',
                    'strength': 'strong'
                })
            # 確認趨勢轉變
            elif (recent_data['SMA_20'].iloc[-1] > recent_data['SMA_50'].iloc[-1] and
                  recent_data['SMA_20'].iloc[-20] < recent_data['SMA_50'].iloc[-20]):
                patterns.append({
                    'name': '黃金交叉',
                    'description': 'SMA_20 向上穿越 SMA_50，可能預示趨勢轉向上升',
                    'strength': 'strong'
                })
            elif (recent_data['SMA_20'].iloc[-1] < recent_data['SMA_50'].iloc[-1] and
                  recent_data['SMA_20'].iloc[-20] > recent_data['SMA_50'].iloc[-20]):
                patterns.append({
                    'name': '死亡交叉',
                    'description': 'SMA_20 向下穿越 SMA_50，可能預示趨勢轉向下降',
                    'strength': 'strong'
                })
        
        # 檢測頭肩頂/底形態
        # (實際形態檢測更複雜，這裡只作為示例)
        
        # 檢測 RSI 超買/超賣
        if 'RSI' in recent_data.columns:
            last_rsi = recent_data['RSI'].iloc[-1]
            
            if last_rsi >= 70:
                patterns.append({
                    'name': 'RSI 超買',
                    'description': f'RSI 值 {last_rsi:.1f} 處於超買區域',
                    'strength': 'medium'
                })
            elif last_rsi <= 30:
                patterns.append({
                    'name': 'RSI 超賣',
                    'description': f'RSI 值 {last_rsi:.1f} 處於超賣區域',
                    'strength': 'medium'
                })
        
        # 檢測 MACD 交叉
        if all(col in recent_data.columns for col in ['MACD', 'Signal_Line']):
            # 取得最近數據點
            macd_last = recent_data['MACD'].iloc[-1]
            macd_prev = recent_data['MACD'].iloc[-2]
            signal_last = recent_data['Signal_Line'].iloc[-1]
            signal_prev = recent_data['Signal_Line'].iloc[-2]
            
            # 檢測黃金交叉（MACD 穿越 Signal 向上）
            if macd_prev < signal_prev and macd_last > signal_last:
                patterns.append({
                    'name': 'MACD 黃金交叉',
                    'description': 'MACD 線從下方穿越信號線，可能預示上漲',
                    'strength': 'medium'
                })
            # 檢測死亡交叉（MACD 穿越 Signal 向下）
            elif macd_prev > signal_prev and macd_last < signal_last:
                patterns.append({
                    'name': 'MACD 死亡交叉',
                    'description': 'MACD 線從上方穿越信號線，可能預示下跌',
                    'strength': 'medium'
                })
        
        # 檢測布林帶擠壓和反彈
        if all(col in recent_data.columns for col in ['Bollinger_Upper', 'Bollinger_Lower']):
            # 計算布林帶寬度
            band_width = (recent_data['Bollinger_Upper'] - recent_data['Bollinger_Lower']) / recent_data['SMA_20']
            
            # 檢測布林帶擠壓（波動率低）
            if band_width.iloc[-1] < band_width.iloc[-20]:
                patterns.append({
                    'name': '布林帶擠壓',
                    'description': '布林帶寬度縮小，可能預示大幅波動即將發生',
                    'strength': 'weak'
                })
                
            # 檢測價格觸及布林帶邊界
            if recent_data['Close'].iloc[-1] >= recent_data['Bollinger_Upper'].iloc[-1]:
                patterns.append({
                    'name': '價格觸及上軌',
                    'description': '價格接近或超過布林帶上軌，可能呈現超買狀態',
                    'strength': 'weak'
                })
            elif recent_data['Close'].iloc[-1] <= recent_data['Bollinger_Lower'].iloc[-1]:
                patterns.append({
                    'name': '價格觸及下軌',
                    'description': '價格接近或低於布林帶下軌，可能呈現超賣狀態',
                    'strength': 'weak'
                })
        
        return patterns
    
    def _generate_summary(self, stock_data, performance, patterns):
        """生成摘要文字
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            performance (dict): 績效指標
            patterns (list): 技術形態
            
        返回:
            str: 摘要文字
        """
        ticker = stock_data.attrs.get('ticker', 'STOCK')
        
        # 獲取最新價格和變動
        last_close = stock_data['Close'].iloc[-1]
        prev_close = stock_data['Close'].iloc[-2]
        price_change = last_close - prev_close
        price_change_pct = (price_change / prev_close) * 100
        
        # 生成趨勢描述
        trend_description = ""
        if performance:
            trend = performance.get('trend', '')
            
            if "上升" in trend:
                trend_description = "目前處於上升趨勢"
            elif "下降" in trend:
                trend_description = "目前處於下降趨勢"
            else:
                trend_description = "趨勢不明確"
                
        # 生成技術指標描述
        indicators_desc = []
        
        if 'RSI' in stock_data.columns:
            last_rsi = stock_data['RSI'].iloc[-1]
            if last_rsi >= 70:
                indicators_desc.append(f"RSI ({last_rsi:.1f}) 處於超買區間")
            elif last_rsi <= 30:
                indicators_desc.append(f"RSI ({last_rsi:.1f}) 處於超賣區間")
            else:
                indicators_desc.append(f"RSI ({last_rsi:.1f}) 處於中性區間")
                
        if all(col in stock_data.columns for col in ['MACD', 'Signal_Line']):
            last_macd = stock_data['MACD'].iloc[-1]
            last_signal = stock_data['Signal_Line'].iloc[-1]
            
            if last_macd > last_signal:
                indicators_desc.append("MACD 顯示看漲訊號")
            else:
                indicators_desc.append("MACD 顯示看跌訊號")
        
        # 生成形態描述
        patterns_desc = []
        for pattern in patterns:
            patterns_desc.append(pattern['name'])
        
        # 組合摘要
        summary = f"{ticker} 收盤價 ${last_close:.2f}"
        
        if price_change >= 0:
            summary += f"，上漲 ${price_change:.2f} ({price_change_pct:.2f}%)"
        else:
            summary += f"，下跌 ${-price_change:.2f} ({-price_change_pct:.2f}%)"
            
        summary += f"。{trend_description}。"
        
        if indicators_desc:
            summary += f" 技術指標顯示: {', '.join(indicators_desc)}。"
            
        if patterns_desc:
            summary += f" 已識別的形態: {', '.join(patterns_desc)}。"
            
        if performance:
            lookback_period = performance.get('lookback_period', 30)
            price_change_pct_period = performance.get('price_change_pct', 0)
            
            summary += f" 在過去 {lookback_period} 個交易日，股價變動 {price_change_pct_period:.2f}%。"
            
        return summary
    
    def generate_multiple_timeframe_charts(self, stock_data, output_dir=None):
        """生成多時間週期圖表
        
        參數:
            stock_data (pandas.DataFrame): 股票數據
            output_dir (str, 可選): 輸出目錄
            
        返回:
            dict: 圖表文件路徑
        """
        if stock_data is None or stock_data.empty:
            self.logger.error("無效的股票數據")
            return None
            
        # 設置預設輸出目錄
        if output_dir is None:
            output_dir = self.cache_dir
            
        os.makedirs(output_dir, exist_ok=True)
        
        ticker = stock_data.attrs.get('ticker', 'STOCK')
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 生成不同時間週期的圖表
        charts = {}
        
        # 一週圖表
        if len(stock_data) >= 5:
            one_week_data = stock_data.iloc[-5:]
            one_week_output = os.path.join(output_dir, f"{ticker}_1week_{timestamp}.png")
            self.generate_stock_chart(one_week_data, 'candlestick', 
                                      indicators=['SMA_20', 'volume', 'rsi'], 
                                      output_file=one_week_output)
            charts['1_week'] = one_week_output
            
        # 一個月圖表
        if len(stock_data) >= 20:
            one_month_data = stock_data.iloc[-20:]
            one_month_output = os.path.join(output_dir, f"{ticker}_1month_{timestamp}.png")
            self.generate_stock_chart(one_month_data, 'candlestick', 
                                      indicators=['SMA_20', 'SMA_50', 'volume', 'rsi'], 
                                      output_file=one_month_output)
            charts['1_month'] = one_month_output
            
        # 三個月圖表
        if len(stock_data) >= 60:
            three_month_data = stock_data.iloc[-60:]
            three_month_output = os.path.join(output_dir, f"{ticker}_3months_{timestamp}.png")
            self.generate_stock_chart(three_month_data, 'candlestick', 
                                      indicators=['SMA_20', 'SMA_50', 'volume', 'rsi', 'macd'], 
                                      output_file=three_month_output)
            charts['3_months'] = three_month_output
            
        # 一年圖表
        if len(stock_data) >= 250:
            one_year_data = stock_data.iloc[-250:]
            one_year_output = os.path.join(output_dir, f"{ticker}_1year_{timestamp}.png")
            self.generate_stock_chart(one_year_data, 'candlestick', 
                                      indicators=['SMA_20', 'SMA_50', 'SMA_200', 'volume', 'macd'], 
                                      output_file=one_year_output)
            charts['1_year'] = one_year_output
            
        self.logger.info(f"多時間週期圖表已生成: {', '.join(charts.keys())}")
        return charts
    
    def compare_stocks(self, stock_data_list, output_file=None):
        """比較多檔股票
        
        參數:
            stock_data_list (list): 股票數據列表 [(股票數據, 股票代碼), ...]
            output_file (str, 可選): 輸出文件路徑
            
        返回:
            str: 圖表文件路徑
        """
        if not stock_data_list or len(stock_data_list) < 2:
            self.logger.error("需要至少兩檔股票進行比較")
            return None
            
        # 設置預設輸出文件
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = os.path.join(self.cache_dir, f"comparison_{timestamp}.png")
            
        try:
            # 創建圖表
            plt.figure(figsize=(16, 10))
            
            # 找出共同的時間範圍
            start_dates = [data.index[0] for data, _ in stock_data_list]
            end_dates = [data.index[-1] for data, _ in stock_data_list]
            
            common_start = max(start_dates)
            common_end = min(end_dates)
            
            # 計算相對表現
            normalized_data = {}
            
            for stock_data, ticker in stock_data_list:
                # 篩選共同時間範圍
                filtered_data = stock_data[(stock_data.index >= common_start) & (stock_data.index <= common_end)]
                
                if filtered_data.empty:
                    continue
                    
                # 歸一化價格（第一天 = 100）
                first_close = filtered_data['Close'].iloc[0]
                normalized_price = (filtered_data['Close'] / first_close) * 100
                
                normalized_data[ticker] = normalized_price
            
            # 繪製相對表現
            for ticker, price_series in normalized_data.items():
                plt.plot(price_series.index, price_series, linewidth=2, label=ticker)
            
            # 設置標題和標籤
            plt.title('股票相對表現比較', fontsize=15)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('相對表現 (基準=100)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend(loc='best')
            
            # 調整 x 軸標籤
            plt.xticks(rotation=45)
            
            # 計算相對表現統計
            performance_stats = []
            
            for ticker, price_series in normalized_data.items():
                last_value = price_series.iloc[-1]
                change_pct = last_value - 100
                
                # 計算波動率
                returns = price_series.pct_change().dropna()
                volatility = returns.std() * 100
                
                performance_stats.append(f"{ticker}: {change_pct:.2f}%, 波動率: {volatility:.2f}%")
            
            # 添加統計說明
            plt.figtext(0.5, 0.01, ' | '.join(performance_stats), ha='center', fontsize=12)
            
            # 保存圖表
            plt.tight_layout()
            plt.savefig(output_file, dpi=100)
            plt.close()
            
            self.logger.info(f"股票比較圖已生成: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"生成股票比較圖失敗: {e}")
            return None
    
    def correlation_analysis(self, stock_data_list):
        """相關性分析
        
        參數:
            stock_data_list (list): 股票數據列表 [(股票數據, 股票代碼), ...]
            
        返回:
            dict: 相關性分析結果
        """
        if not stock_data_list or len(stock_data_list) < 2:
            self.logger.error("需要至少兩檔股票進行相關性分析")
            return None
            
        try:
            # 找出共同的時間範圍
            start_dates = [data.index[0] for data, _ in stock_data_list]
            end_dates = [data.index[-1] for data, _ in stock_data_list]
            
            common_start = max(start_dates)
            common_end = min(end_dates)
            
            # 收集收盤價數據
            price_data = {}
            returns_data = {}
            
            for stock_data, ticker in stock_data_list:
                # 篩選共同時間範圍
                filtered_data = stock_data[(stock_data.index >= common_start) & (stock_data.index <= common_end)]
                
                if filtered_data.empty:
                    continue
                    
                price_data[ticker] = filtered_data['Close']
                returns_data[ticker] = filtered_data['Close'].pct_change().dropna()
            
            # 創建價格 DataFrame
            prices_df = pd.DataFrame(price_data)
            
            # 創建回報率 DataFrame
            returns_df = pd.DataFrame(returns_data)
            
            # 計算相關係數
            correlation_matrix = returns_df.corr()
            
            # 計算其他統計數據
            stats = {}
            
            for ticker in returns_df.columns:
                returns = returns_df[ticker]
                
                stats[ticker] = {
                    'mean': returns.mean() * 100,  # 日均回報率（%）
                    'std': returns.std() * 100,    # 標準差/波動率（%）
                    'min': returns.min() * 100,    # 最小回報率（%）
                    'max': returns.max() * 100,    # 最大回報率（%）
                    'skew': returns.skew(),        # 偏度
                    'kurt': returns.kurtosis()     # 峰度
                }
            
            result = {
                'correlation': correlation_matrix.to_dict(),
                'stats': stats,
                'period': {
                    'start': common_start.strftime('%Y-%m-%d'),
                    'end': common_end.strftime('%Y-%m-%d'),
                    'trading_days': len(returns_df)
                }
            }
            
            self.logger.info(f"相關性分析完成，共 {len(price_data)} 檔股票")
            return result
            
        except Exception as e:
            self.logger.error(f"相關性分析失敗: {e}")
            return None