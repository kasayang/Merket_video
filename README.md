股票數據影片自動化製作系統/
├── app.py                      # Flask應用入口
├── config.yaml                 # 配置文件
├── requirements.txt            # 依賴包列表
├── README.md                   # 項目說明
├── src/
│   ├── static/                 # Flask靜態文件
│   │   ├── js/                 # JavaScript文件
│   │   │   ├── timeline.js     # 時間軸編輯器
│   │   │   ├── subtitle.js     # 字幕編輯器
│   │   │   ├── digital-human.js# 數字人模組
│   │   │   ├── media-effects.js#影音功能擴展
│   │   │   ├── text-editor.js  #添加文字功能增強
│   │   │   ├── app.js
│   │   │   └── preview.js      # 預覽控制

│   │   ├── css/                # 樣式文件
│   │   │   └── style.css
│   │   ├── img/                # 圖像資源
│   │   │   ├── default-template.jpg
│   │   │   └── default-avatar.jpg
│   │
│   ├── templates/              # Flask模板
│   │   ├── index.html          # 主頁模板
│   │   ├── editor.html         # 編輯器模板
│   │   ├── recent.html         # 近期項目頁面，管理用戶的項目
│   │   ├── help.html           # 幫助中心，提供使用指南和常見問題解答
│   │   ├── error.html          # 錯誤頁面，顯示用戶友好的錯誤訊息
│   │   ├── base.html           # 基本模板，提供共用的頁面結構
│   │   ├── templates.html  <-- 添加這個文件
│   │   └── components/         # 可複用組件
│   │
│   ├── routes/                 # Flask路由
│   │   ├── __init__.py
│   │   ├── api.py              # API路由
│   │   └── views.py            # 頁面路由
│   │
│   ├── core/                   # 核心功能模組
│   │   ├── content_processor.py # 內容處理器
│   │   ├── subtitle_manager.py  # 字幕管理器
│   │   ├── tts_controller.py    # TTS控制器
│   │   ├── sync_manager.py      # 同步管理器
│   │   └── main_controller.py   # 主控制器
│   │
│   ├── data/                   # 數據處理模組
│   │   ├── __init__.py
│   │   ├── stock_collector.py  # 股票數據收集器
│   │   ├── data_processor.py   # 數據處理器
│   │   └── cache_manager.py    # 緩存管理器
│   │
│   ├── media/                  # 媒體處理模組
│   │    ├── video_generator.py  # 視頻生成器
│   │    ├── audio_processor.py  # 音頻處理器
│   │    └── digital_human.py    # 數字人模組
│   └── utils/                  # 工具函數
│       ├── __init__.py
│       ├── config_manager.py
│       └── logging_utils.py
│
├── templates/                  # 系統模板文件
│   ├── layouts/                # 佈局模板
│   └── digital_humans/         # 數字人模板
│
├── cache/                      # 暫存目錄
│   ├── audio/
│   ├── video/
│   └── data/
├── output/                     # 輸出目錄
└── logs/                       # 日誌目錄




匯入文章：點擊「匯入文章」按鈕，選擇包含股票分析內容的文字文件
處理文章：系統會自動分析文章內容，識別股票代碼和關鍵信息
搜索股票數據：輸入股票代碼並點擊搜索，系統會自動獲取並分析股票數據
編輯字幕：使用右側編輯面板調整字幕文本和時間
生成語音：設置TTS引擎參數並生成語音
編輯時間軸：使用底部的時間軸編輯器調整媒體元素的位置和時長
預覽：點擊播放按鈕預覽當前效果
生成視頻：點擊「生成視頻」按鈕，系統將自動合成最終視頻
下載：點擊「下載」按鈕下載生成的視頻文件

字幕編輯功能：

自動生成字幕：系統自動根據文章內容生成初始字幕
設置語速：調整每個字幕段落的語速
編輯字幕文本：直接修改字幕文字內容
調整時間：調整字幕顯示的開始時間和持續時間
預覽字幕效果：即時預覽字幕效果
導出字幕文件：支援SRT、VTT格式導出

時間軸編輯功能：

添加媒體元素：將各種媒體元素（視頻、音頻、字幕）添加到時間軸
拖動調整位置：直接拖動元素調整其在時間軸中的位置
調整元素時長：拖動元素邊緣調整其持續時間
多軌道編輯：支援視頻軌、音頻軌、字幕軌多軌道編輯
時間指示器：指示當前播放位置
縮放時間軸：放大或縮小時間軸以獲得更精細的控制

後續擴展方向

多用戶支援：添加用戶認證和授權功能，支援多用戶同時使用
項目保存與加載：實現項目保存與加載功能，方便後續編輯
更多媒體效果：添加轉場效果、濾鏡效果等高級視頻效果
雲存儲整合：整合雲存儲服務，支援將成品上傳到雲端
API接口擴展：提供更豐富的API接口，方便與其他系統集成
視頻模板市場：建立模板市場，用戶可以分享和使用各種視頻模板
批量處理功能：支援批量處理多個文章或多個股票代碼

