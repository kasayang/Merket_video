// preview.js - 視頻預覽功能

/**
 * 預覽控制器類
 * 負責管理視頻預覽功能
 */
class PreviewController {
    constructor(options) {
        this.videoElement = options.videoElement;
        this.timelineController = options.timelineController;
        this.callbacks = {};
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化預覽控制器
     */
    init() {
        if (!this.videoElement) return;
        
        // 綁定視頻事件
        this.bindVideoEvents();
        
        // 設置預設屬性
        this.currentTime = 0;
        this.duration = 0;
        
        // 初始化播放控制按鈕
        this.initPlaybackControls();
    }
    
    /**
     * 綁定視頻事件
     */
    bindVideoEvents() {
        // 時間更新事件
        this.videoElement.addEventListener('timeupdate', () => {
            this.currentTime = this.videoElement.currentTime;
            
            // 通知時間軸更新
            if (this.timelineController) {
                this.timelineController.setCurrentTime(this.currentTime);
            }
            
            // 觸發時間更新事件
            this.trigger('timeUpdate', this.currentTime);
        });
        
        // 載入完成事件
        this.videoElement.addEventListener('loadedmetadata', () => {
            this.duration = this.videoElement.duration;
            this.trigger('durationChange', this.duration);
        });
        
        // 播放事件
        this.videoElement.addEventListener('play', () => {
            this.trigger('play');
        });
        
        // 暫停事件
        this.videoElement.addEventListener('pause', () => {
            this.trigger('pause');
        });
        
        // 結束事件
        this.videoElement.addEventListener('ended', () => {
            this.trigger('ended');
        });
    }
    
    /**
     * 初始化播放控制按鈕
     */
    initPlaybackControls() {
        // 播放/暫停按鈕
        const playBtn = document.querySelector('.d-flex.justify-content-center .btn:nth-child(2)');
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                this.togglePlay();
            });
        }
        
        // 向前跳轉按鈕
        const forwardBtn = document.querySelector('.d-flex.justify-content-center .btn:nth-child(3)');
        if (forwardBtn) {
            forwardBtn.addEventListener('click', () => {
                this.seekForward();
            });
        }
        
        // 向後跳轉按鈕
        const backwardBtn = document.querySelector('.d-flex.justify-content-center .btn:nth-child(1)');
        if (backwardBtn) {
            backwardBtn.addEventListener('click', () => {
                this.seekBackward();
            });
        }
    }
    
    /**
     * 載入視頻
     * @param {string} url - 視頻 URL
     */
    loadVideo(url) {
        if (!this.videoElement) return;
        
        this.videoElement.src = url;
        this.videoElement.load();
        
        // 觸發載入事件
        this.trigger('videoLoaded', url);
    }
    
    /**
     * 播放
     */
    play() {
        if (!this.videoElement) return;
        
        this.videoElement.play();
        
        // 更新播放按鈕
        const playBtn = document.querySelector('.d-flex.justify-content-center .btn:nth-child(2)');
        if (playBtn) {
            playBtn.innerHTML = '<i class="bi bi-pause"></i>';
        }
    }
    
    /**
     * 暫停
     */
    pause() {
        if (!this.videoElement) return;
        
        this.videoElement.pause();
        
        // 更新播放按鈕
        const playBtn = document.querySelector('.d-flex.justify-content-center .btn:nth-child(2)');
        if (playBtn) {
            playBtn.innerHTML = '<i class="bi bi-play"></i>';
        }
    }
    
    /**
     * 切換播放狀態
     */
    togglePlay() {
        if (!this.videoElement) return;
        
        if (this.videoElement.paused) {
            this.play();
        } else {
            this.pause();
        }
    }
    
    /**
     * 前進
     * @param {number} seconds - 前進秒數，預設 5 秒
     */
    seekForward(seconds = 5) {
        if (!this.videoElement) return;
        
        const newTime = Math.min(this.videoElement.currentTime + seconds, this.videoElement.duration);
        this.seekTo(newTime);
    }
    
    /**
     * 後退
     * @param {number} seconds - 後退秒數，預設 5 秒
     */
    seekBackward(seconds = 5) {
        if (!this.videoElement) return;
        
        const newTime = Math.max(this.videoElement.currentTime - seconds, 0);
        this.seekTo(newTime);
    }
    
    /**
     * 跳轉到指定時間
     * @param {number} time - 目標時間（秒）
     */
    seekTo(time) {
        if (!this.videoElement) return;
        
        this.videoElement.currentTime = time;
        
        // 觸發跳轉事件
        this.trigger('seek', time);
    }
    
    /**
     * 設置播放速度
     * @param {number} rate - 播放速度倍率
     */
    setPlaybackRate(rate) {
        if (!this.videoElement) return;
        
        this.videoElement.playbackRate = rate;
    }
    
    /**
     * 獲取當前播放時間
     * @return {number} 當前時間（秒）
     */
    getCurrentTime() {
        if (!this.videoElement) return 0;
        
        return this.videoElement.currentTime;
    }
    
    /**
     * 獲取視頻總時長
     * @return {number} 總時長（秒）
     */
    getDuration() {
        if (!this.videoElement) return 0;
        
        return this.videoElement.duration;
    }
    
    /**
     * 檢查是否正在播放
     * @return {boolean} 是否正在播放
     */
    isPlaying() {
        if (!this.videoElement) return false;
        
        return !this.videoElement.paused;
    }
    
    /**
     * 設置視頻容器大小
     * @param {number} width - 寬度
     * @param {number} height - 高度
     */
    setSize(width, height) {
        if (!this.videoElement) return;
        
        this.videoElement.style.width = width + 'px';
        this.videoElement.style.height = height + 'px';
    }
    
    /**
     * 預覽字幕
     * @param {object} subtitle - 字幕對象
     */
    previewSubtitle(subtitle) {
        if (!this.videoElement) return;
        
        // 跳轉到字幕開始時間
        this.seekTo(subtitle.startTime);
        
        // 顯示預覽字幕
        this.showSubtitleOverlay(subtitle.text);
        
        // 3秒後移除預覽字幕
        setTimeout(() => {
            this.hideSubtitleOverlay();
        }, 3000);
    }
    
    /**
     * 顯示字幕覆蓋層
     * @param {string} text - 字幕文字
     */
    showSubtitleOverlay(text) {
        // 檢查是否已存在字幕覆蓋層
        let overlayEl = document.getElementById('subtitle-overlay');
        if (!overlayEl) {
            // 創建覆蓋層
            overlayEl = document.createElement('div');
            overlayEl.id = 'subtitle-overlay';
            overlayEl.style.position = 'absolute';
            overlayEl.style.bottom = '50px';
            overlayEl.style.left = '0';
            overlayEl.style.width = '100%';
            overlayEl.style.textAlign = 'center';
            overlayEl.style.color = 'white';
            overlayEl.style.textShadow = '0 0 2px black';
            overlayEl.style.fontSize = '20px';
            overlayEl.style.padding = '10px';
            overlayEl.style.zIndex = '1000';
            
            // 添加到視頻容器
            const videoContainer = this.videoElement.parentElement;
            videoContainer.style.position = 'relative';
            videoContainer.appendChild(overlayEl);
        }
        
        // 設置字幕文字
        overlayEl.textContent = text;
        overlayEl.style.display = 'block';
    }
    
    /**
     * 隱藏字幕覆蓋層
     */
    hideSubtitleOverlay() {
        const overlayEl = document.getElementById('subtitle-overlay');
        if (overlayEl) {
            overlayEl.style.display = 'none';
        }
    }
    
    /**
     * 顯示圖表預覽圖
     * @param {string} chartUrl - 圖表圖片 URL
     */
    showChartPreview(chartUrl) {
        if (!this.videoElement) return;
        
        // 隱藏視頻元素
        this.videoElement.style.display = 'none';
        
        // 創建圖片元素
        let previewImg = document.getElementById('chart-preview');
        if (!previewImg) {
            previewImg = document.createElement('img');
            previewImg.id = 'chart-preview';
            previewImg.style.width = '100%';
            previewImg.style.height = '100%';
            previewImg.style.objectFit = 'contain';
            
            // 添加到視頻容器
            this.videoElement.parentElement.appendChild(previewImg);
        }
        
        // 設置圖片來源
        previewImg.src = chartUrl;
        previewImg.style.display = 'block';
    }
    
    /**
     * 隱藏圖表預覽圖
     */
    hideChartPreview() {
        const previewImg = document.getElementById('chart-preview');
        if (previewImg) {
            previewImg.style.display = 'none';
        }
        
        // 顯示視頻元素
        if (this.videoElement) {
            this.videoElement.style.display = 'block';
        }
    }
    
    /**
     * 訂閱事件
     * @param {string} event - 事件名稱
     * @param {function} callback - 回調函數
     */
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }
    
    /**
     * 觸發事件
     * @param {string} event - 事件名稱
     * @param {*} data - 事件數據
     */
    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }
}

// 增強預覽控制器
class EnhancedPreviewController extends PreviewController {
    constructor(options) {
        super(options);
        
        // 添加字幕層
        this.subtitleLayer = document.createElement('div');
        this.subtitleLayer.className = 'preview-subtitle-layer';
        if (this.videoElement && this.videoElement.parentElement) {
            this.videoElement.parentElement.appendChild(this.subtitleLayer);
        }
        
        // 音頻播放列表
        this.audioPlayers = [];
        this.subtitles = [];
    }
    
    // 設置預覽內容
    setContent(timeline) {
        // 清除現有內容
        this.clearContent();
        
        // 載入視頻段落
        if (timeline.video && timeline.video.length > 0) {
            // 載入第一個視頻作為預覽
            this.loadVideo(timeline.video[0].file);
        }
        
        // 載入字幕
        if (timeline.subtitles) {
            this.subtitles = timeline.subtitles;
        }
        
        // 準備音頻播放器
        if (timeline.audio) {
            timeline.audio.forEach(audio => {
                const player = new Audio(audio.file);
                player.currentTime = 0;
                player.dataset.startTime = audio.startTime;
                player.dataset.endTime = audio.startTime + audio.duration;
                
                this.audioPlayers.push(player);
            });
        }
    }
    
    // 清除內容
    clearContent() {
        // 停止所有音頻
        this.audioPlayers.forEach(player => {
            player.pause();
            player.currentTime = 0;
        });
        this.audioPlayers = [];
        
        // 清除字幕
        this.subtitles = [];
        this.subtitleLayer.innerHTML = '';
        
        // 重置視頻
        if (this.videoElement) {
            this.videoElement.src = '';
        }
    }
    
    // 重寫播放方法
    play() {
        super.play();
        
        // 同步播放所有音頻
        this.syncAudioPlayback();
    }
    
    // 重寫暫停方法
    pause() {
        super.pause();
        
        // 暫停所有音頻
        this.audioPlayers.forEach(player => {
            player.pause();
        });
    }
// 重寫跳轉方法
seekTo(time) {
    super.seekTo(time);
    
    // 更新音頻位置
    this.syncAudioPlayback();
    
    // 更新字幕顯示
    this.updateSubtitle(time);
}

// 同步音頻播放
syncAudioPlayback() {
    const currentTime = this.getCurrentTime();
    
    this.audioPlayers.forEach(player => {
        const startTime = parseFloat(player.dataset.startTime);
        const endTime = parseFloat(player.dataset.endTime);
        
        if (currentTime >= startTime && currentTime <= endTime) {
            if (player.paused) {
                player.currentTime = currentTime - startTime;
                player.play();
            }
        } else {
            player.pause();
        }
    });
}

// 更新字幕顯示
updateSubtitle(time) {
    // 清除當前字幕
    this.subtitleLayer.innerHTML = '';
    
    // 查找當前時間點的字幕
    const currentSubtitles = this.subtitles.filter(sub => 
        time >= sub.startTime && time <= (sub.startTime + sub.duration)
    );
    
    // 顯示字幕
    if (currentSubtitles.length > 0) {
        const subtitleEl = document.createElement('div');
        subtitleEl.className = 'active-subtitle';
        subtitleEl.textContent = currentSubtitles[0].text;
        this.subtitleLayer.appendChild(subtitleEl);
    }
}
}

// 在文檔加載完成後初始化預覽控制器
document.addEventListener('DOMContentLoaded', () => {
// 查找視頻元素
const videoElement = document.getElementById('previewVideo');
if (!videoElement) return;

// 獲取時間軸控制器（由 timeline.js 創建）
const timelineController = window.timeline;

// 創建增強版預覽控制器實例
window.previewController = new EnhancedPreviewController({
    videoElement: videoElement,
    timelineController: timelineController
});

// 監聽時間軸的事件
if (timelineController) {
    timelineController.on('timeChange', (time) => {
        window.previewController.seekTo(time);
    });
    
    timelineController.on('playStateChange', (isPlaying) => {
        if (isPlaying) {
            window.previewController.play();
        } else {
            window.previewController.pause();
        }
    });
    
    // 監聽選擇變更事件，以便預覽
    timelineController.on('selectionChange', (item) => {
        if (item) {
            // 根據項目類型進行不同處理
            if (item.trackId === 'videoTrack' && item.file) {
                window.previewController.loadVideo(item.file);
                window.previewController.seekTo(item.startTime);
            } else if (item.trackId === 'audioTrack' && item.file) {
                // 預覽音頻
                const audio = new Audio(item.file);
                audio.currentTime = 0;
                audio.play();
            } else if (item.trackId === 'subtitleTrack' && item.text) {
                // 預覽字幕
                window.previewController.previewSubtitle(item);
            }
        }
    });
}

// 載入時間軸數據到預覽器
function loadTimelineToPreview() {
    if (window.timeline && window.previewController) {
        // 準備時間軸數據
        const timelineData = {
            video: window.timeline.tracks.find(t => t.id === 'videoTrack')?.items || [],
            audio: window.timeline.tracks.find(t => t.id === 'audioTrack')?.items || [],
            subtitles: window.timeline.tracks.find(t => t.id === 'subtitleTrack')?.items || []
        };
        
        // 設置預覽內容
        window.previewController.setContent(timelineData);
    }
}

// 監聽時間軸更新事件
if (timelineController) {
    timelineController.on('tracksUpdated', () => {
        loadTimelineToPreview();
    });
}

// 初始載入
setTimeout(loadTimelineToPreview, 1000);
});

// 初始化時間軸
document.addEventListener('DOMContentLoaded', () => {
    // 查找時間軸容器
    const container = document.querySelector('.timeline-editor');
    if (!container) return;
    
    // 創建時間軸實例 - 使用增強版時間軸
    window.timeline = new EnhancedTimeline({
        container: container,
        duration: 180, // 3分鐘預設時長
        scale: 10,     // 每秒10像素
        tracks: [
            { id: 'videoTrack', name: '視頻軌', type: 'video', items: [] },
            { id: 'audioTrack', name: '音訊軌', type: 'audio', items: [] },
            { id: 'subtitleTrack', name: '字幕軌', type: 'subtitle', items: [] }
        ],
        onChange: function() {
            // 時間軸變更時的回調
            handleTimelineChange();
        }
    });
    
    // 初始化預覽播放器
    initPreviewPlayer(window.timeline);
});

// 處理時間軸變更
    function handleTimelineChange() {
        // 顯示當前選中項目的屬性
        displaySelectedItemProperties(window.timeline.selectedItem);
        
        // 更新預覽
        updatePreview();
}

    // 初始化預覽播放器
    function initPreviewPlayer(timeline) {
        const previewVideo = document.getElementById('previewVideo');
        if (!previewVideo) return;
        
        // 創建增強型預覽控制器
        window.previewController = new EnhancedPreviewController({
            videoElement: previewVideo,
            timelineController: timeline
        });
        
        // 監聽播放控制事件
        document.getElementById('playPauseBtn')?.addEventListener('click', () => {
            window.previewController.togglePlay();
        });
    }
    
    document.getElementById('stopBtn')?.addEventListener('click', () => {
        window.previewController.pause();
        window.previewController.seekTo(0);
    }); 
    // 定義 updatePreview 函數
    function updatePreview() {
        if (!window.timeline || !window.previewController) return;
        
        // 獲取當前時間點的視頻項目
        const currentTime = window.timeline.currentTime;
        const videoTrack = window.timeline.tracks.find(t => t.id === 'videoTrack');
        
        if (!videoTrack) return;
        
        // 查找當前時間點的項目
        const activeItems = videoTrack.items.filter(item => 
            item.startTime <= currentTime && 
            item.startTime + item.duration > currentTime
        );
        
        // 如果找到視頻項目，更新預覽
        if (activeItems.length > 0) {
            const activeItem = activeItems[0];
            // 找到對應的媒體
            // 這裡需要訪問媒體庫，具體實現取決於您的應用架構
        }
    }

    // 定義 displaySelectedItemProperties 函數
    function displaySelectedItemProperties(item) {
        // 獲取屬性面板元素
        const propertiesPanel = document.getElementById('clipPropertiesForm');
        const noSelectionInfo = document.getElementById('noClipSelected');
        
        if (!propertiesPanel || !noSelectionInfo) return;
        
        if (!item) {
            // 未選擇項目，顯示提示
            noSelectionInfo.style.display = 'block';
            propertiesPanel.style.display = 'none';
            return;
        }
        
        // 選擇了項目，顯示屬性面板
        noSelectionInfo.style.display = 'none';
        propertiesPanel.style.display = 'block';
        
        // 填充表單數據
        document.getElementById('clipName').value = item.name || '';
        document.getElementById('clipStartTime').value = item.startTime.toFixed(2);
        document.getElementById('clipDuration').value = item.duration.toFixed(2);
        
        if (item.volume !== undefined) {
            document.getElementById('clipVolume').value = item.volume;
        }
        
        if (item.speed !== undefined) {
            document.getElementById('clipSpeed').value = item.speed;
        }
    }
