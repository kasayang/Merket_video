// timeline.js - 時間軸基本類別和增強功能

/**
 * 基本時間軸類別
 */
class Timeline {
    constructor(options) {
        // 設置預設值
        this.container = options.container || document.createElement('div');
        this.tracks = options.tracks || [];
        this.duration = options.duration || 60; // 預設時間軸長度為 60 秒
        this.scale = options.scale || 10; // 每秒的像素數
        this.currentTime = 0;
        this.isPlaying = false;
        this.playbackRate = 1.0;
        
        // 回調函數
        this.onChange = options.onChange || function() {};
        this.onPlay = options.onPlay || function() {};
        this.onPause = options.onPause || function() {};
        this.onTimeUpdate = options.onTimeUpdate || function() {};
        
        // 選中項目
        this.selectedItem = null;
        this.dragState = null;
        
        // 播放計時器
        this.playbackTimer = null;
        
        // 回调存储
        this.callbacks = {};
        
        // 初始化時間軸
        this.init();
    }
    
    // 初始化時間軸
    init() {
        // 清空容器
        this.container.innerHTML = '';
        this.container.classList.add('timeline');
        window.timeline = new EnhancedTimeline({
            container: container,
            duration: 180, // 3分鐘預設時長
            scale: 10,     // 每秒10像素
            tracks: [
                { id: 'videoTrack', name: '視頻軌', type: 'video', items: [] },
                { id: 'audioTrack', name: '音訊軌', type: 'audio', items: [] },
                { id: 'subtitleTrack', name: '字幕軌', type: 'subtitle', items: [] },
                { id: 'digitalHumanTrack', name: '數字人軌', type: 'digitalHuman', items: [] }
            ],
            onChange: function() {
                // 時間軸變更時的回調
                handleTimelineChange();
            }
        });   
        // 創建時間尺
        this.createTimeRuler();
        
        // 創建軌道
        this.createTracks();
        
        // 創建時間指示器
        this.createTimeIndicator();
        
        // 綁定事件
        this.bindEvents();
    }
    
    // 創建時間尺
    createTimeRuler() {
        const ruler = document.createElement('div');
        ruler.className = 'time-ruler';
        
        // 計算刻度間隔（每秒一個刻度）
        const interval = 1;
        const numMarks = Math.ceil(this.duration / interval);
        
        // 添加刻度
        for (let i = 0; i <= numMarks; i++) {
            const mark = document.createElement('div');
            mark.className = 'ruler-mark';
            mark.style.left = `${i * interval * this.scale}px`;
            
            // 添加時間標籤
            const time = i * interval;
            const minutes = Math.floor(time / 60);
            const seconds = Math.floor(time % 60);
            mark.innerHTML = `<span>${minutes}:${seconds.toString().padStart(2, '0')}</span>`;
            
            ruler.appendChild(mark);
        }
        
        this.container.appendChild(ruler);
    }
    
    // 創建軌道
    createTracks() {
        this.tracks.forEach(track => {
            const trackElement = document.createElement('div');
            trackElement.className = 'timeline-track';
            trackElement.dataset.id = track.id;
            
            // 軌道標籤
            const label = document.createElement('div');
            label.className = 'track-label';
            label.textContent = track.name;
            
            // 軌道內容區
            const content = document.createElement('div');
            content.className = 'track-content';
            
            // 添加項目
            track.items.forEach(item => {
                const itemElement = this.createItemElement(item);
                content.appendChild(itemElement);
            });
            
            trackElement.appendChild(label);
            trackElement.appendChild(content);
            this.container.appendChild(trackElement);
        });
    }
    
    // 創建項目元素
    createItemElement(item) {
        const itemElement = document.createElement('div');
        itemElement.className = 'track-item';
        itemElement.dataset.id = item.id;
        
        // 設置位置和大小
        itemElement.style.left = `${item.startTime * this.scale}px`;
        itemElement.style.width = `${item.duration * this.scale}px`;
        
        // 設置顏色
        itemElement.style.backgroundColor = item.color || '#007bff';
        
        // 如果有選中項目，添加選中樣式
        if (this.selectedItem && this.selectedItem.id === item.id) {
            itemElement.classList.add('selected');
        }
        
        // 左側調整手柄
        const leftHandle = document.createElement('div');
        leftHandle.className = 'item-handle item-handle-left';
        leftHandle.dataset.handle = 'left';
        
        // 項目標籤
        const label = document.createElement('div');
        label.className = 'item-label';
        label.textContent = item.name || '未命名項目';
        
        // 右側調整手柄
        const rightHandle = document.createElement('div');
        rightHandle.className = 'item-handle item-handle-right';
        rightHandle.dataset.handle = 'right';
        
        itemElement.appendChild(leftHandle);
        itemElement.appendChild(label);
        itemElement.appendChild(rightHandle);
        
        return itemElement;
    }
    
    // 創建時間指示器
    createTimeIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'time-indicator';
        indicator.style.left = `${100 + this.currentTime * this.scale}px`; // 加上軌道標籤的寬度
        
        this.container.appendChild(indicator);
        this.timeIndicator = indicator;
    }
    
    // 綁定事件
    bindEvents() {
        // 點擊時間軸設置當前時間
        this.container.addEventListener('click', (e) => {
            // 忽略點擊項目、手柄等的事件
            if (e.target.closest('.track-item') || e.target.closest('.item-handle')) {
                return;
            }
            
            const trackContent = e.target.closest('.track-content');
            if (!trackContent) return;
            
            const rect = trackContent.getBoundingClientRect();
            const relativeX = e.clientX - rect.left;
            
            // 計算時間
            const time = relativeX / this.scale;
            
            // 設置當前時間
            this.setCurrentTime(time);
        });
        
        // 點擊項目選中
        this.container.addEventListener('click', (e) => {
            const itemElement = e.target.closest('.track-item');
            if (!itemElement) return;
            
            const itemId = itemElement.dataset.id;
            this.selectItemById(itemId);
        });
        
        // 拖動項目或調整大小
        this.container.addEventListener('mousedown', (e) => {
            const itemElement = e.target.closest('.track-item');
            if (!itemElement) return;
            
            const itemId = itemElement.dataset.id;
            const trackElement = itemElement.closest('.timeline-track');
            const trackId = trackElement.dataset.id;
            
            // 找到對應的項目
            const track = this.tracks.find(t => t.id === trackId);
            if (!track) return;
            
            const item = track.items.find(i => i.id === itemId);
            if (!item) return;
            
            // 選中此項目
            this.selectItem(item);
            
            // 判斷是拖動項目還是調整大小
            const handle = e.target.closest('.item-handle');
            
            if (handle) {
                // 調整大小
                this.dragState = {
                    type: 'resize',
                    item: item,
                    handle: handle.dataset.handle,
                    startX: e.clientX,
                    startTime: item.startTime,
                    startDuration: item.duration
                };
            } else {
                // 移動項目
                this.dragState = {
                    type: 'move',
                    item: item,
                    startX: e.clientX,
                    startTime: item.startTime
                };
            }
            
            // 添加臨時事件監聽
            document.addEventListener('mousemove', this.handleMouseMove);
            document.addEventListener('mouseup', this.handleMouseUp);
            
            e.preventDefault(); // 防止文本選擇
        });
        
        // 鼠標移動處理
        this.handleMouseMove = (e) => {
            if (!this.dragState) return;
            
            const deltaX = e.clientX - this.dragState.startX;
            const deltaTime = deltaX / this.scale;
            
            if (this.dragState.type === 'move') {
                // 移動項目
                let newTime = Math.max(0, this.dragState.startTime + deltaTime);
                
                // 移動項目
                this.moveItem(this.dragState.item, newTime);
            } else if (this.dragState.type === 'resize') {
                // 調整大小
                if (this.dragState.handle === 'left') {
                    // 左側調整（改變起始時間和持續時間）
                    const maxDelta = this.dragState.startDuration - 0.1; // 保留最小持續時間 0.1 秒
                    const clampedDelta = Math.min(maxDelta, deltaTime);
                    
                    let newStartTime = Math.max(0, this.dragState.startTime + clampedDelta);
                    let newDuration = this.dragState.startDuration - (newStartTime - this.dragState.startTime);
                    
                    // 更新項目
                    this.dragState.item.startTime = newStartTime;
                    this.dragState.item.duration = newDuration;
                } else if (this.dragState.handle === 'right') {
                    // 右側調整（僅改變持續時間）
                    let newDuration = Math.max(0.1, this.dragState.startDuration + deltaTime);
                    
                    // 更新項目
                    this.dragState.item.duration = newDuration;
                }
                
                // 重繪軌道
                this.drawTracks();
            }
        };
        
        // 鼠標釋放處理
        this.handleMouseUp = (e) => {
            // 移除臨時事件監聽
            document.removeEventListener('mousemove', this.handleMouseMove);
            document.removeEventListener('mouseup', this.handleMouseUp);
            
            // 清除拖動狀態
            this.dragState = null;
            
            // 通知變化
            this.onChange();
            this.trigger('trackChanged');
        };
    }
    
    // 選擇項目
    selectItem(item) {
        this.selectedItem = item;
        this.drawTracks();
        
        // 通知變化
        this.onChange();
        this.trigger('selectionChange', item);
    }
    
    // 根據 ID 選擇項目
    selectItemById(itemId) {
        let foundItem = null;
        
        // 查找項目
        for (const track of this.tracks) {
            for (const item of track.items) {
                if (item.id === itemId) {
                    foundItem = item;
                    break;
                }
            }
            if (foundItem) break;
        }
        
        if (foundItem) {
            this.selectItem(foundItem);
        }
    }
    
    // 移動項目
    moveItem(item, newTime) {
        if (newTime !== undefined) {
            item.startTime = newTime;
        }
        
        // 重繪軌道
        this.drawTracks();
    }
    
    // 調整項目大小
    resizeItem(item, newDuration) {
        if (newDuration !== undefined) {
            item.duration = newDuration;
        }
        
        // 重繪軌道
        this.drawTracks();
    }
    
    // 設置當前時間
    setCurrentTime(time) {
        this.currentTime = Math.min(Math.max(0, time), this.duration);
        
        // 更新時間指示器位置
        if (this.timeIndicator) {
            this.timeIndicator.style.left = `${100 + this.currentTime * this.scale}px`;
        }
        
        // 觸發時間更新事件
        this.onTimeUpdate();
        this.trigger('timeChange', this.currentTime);
    }
    
    // 設置時間軸縮放比例
    setScale(scale) {
        this.scale = scale;
        
        // 重繪時間軸
        this.drawTracks();
        this.drawTimeRuler();
        
        // 更新時間指示器位置
        if (this.timeIndicator) {
            this.timeIndicator.style.left = `${100 + this.currentTime * this.scale}px`;
        }
    }
    
    // 設置時間軸長度
    setDuration(duration) {
        this.duration = duration;
        
        // 重繪時間軸
        this.drawTimeRuler();
    }
    
    // 更新軌道數據
    updateTracks(tracks) {
        this.tracks = tracks;
        
        // 重繪時間軸
        this.drawTracks();
        this.trigger('tracksUpdated', tracks);
    }
    
    // 重繪軌道
    drawTracks() {
        // 選擇所有軌道
        const trackElements = this.container.querySelectorAll('.timeline-track');
        
        // 更新每個軌道
        trackElements.forEach(trackElement => {
            const trackId = trackElement.dataset.id;
            const track = this.tracks.find(t => t.id === trackId);
            
            if (!track) return;
            
            // 清空軌道內容
            const content = trackElement.querySelector('.track-content');
            content.innerHTML = '';
            
            // 添加項目
            track.items.forEach(item => {
                const itemElement = this.createItemElement(item);
                content.appendChild(itemElement);
                item.element = itemElement; // 保存元素引用
            });
        });
    }
    
    // 重繪時間尺
    drawTimeRuler() {
        // 移除舊的時間尺
        const oldRuler = this.container.querySelector('.time-ruler');
        if (oldRuler) {
            this.container.removeChild(oldRuler);
        }
        
        // 創建新的時間尺
        this.createTimeRuler();
        
        // 確保時間尺始終在頂部
        this.container.insertBefore(
            this.container.querySelector('.time-ruler'),
            this.container.firstChild
        );
    }
    
    // 播放時間軸
    play() {
        if (this.isPlaying) return;
        
        this.isPlaying = true;
        const startTime = performance.now();
        const startPosition = this.currentTime;
        
        // 創建播放循環
        const playbackLoop = (timestamp) => {
            if (!this.isPlaying) return;
            
            // 計算經過的時間
            const elapsed = (timestamp - startTime) / 1000 * this.playbackRate;
            const newTime = startPosition + elapsed;
            
            // 檢查是否到達時間軸結尾
            if (newTime >= this.duration) {
                this.setCurrentTime(this.duration);
                this.pause();
                return;
            }
            
            // 更新時間
            this.setCurrentTime(newTime);
            
            // 繼續循環
            this.playbackTimer = requestAnimationFrame(playbackLoop);
        };
        
        // 開始循環
        this.playbackTimer = requestAnimationFrame(playbackLoop);
        
        // 觸發播放事件
        this.onPlay();
        this.trigger('playStateChange', true);
    }
    
    // 暫停時間軸
    pause() {
        if (!this.isPlaying) return;
        
        this.isPlaying = false;
        
        // 取消播放定時器
        if (this.playbackTimer) {
            cancelAnimationFrame(this.playbackTimer);
            this.playbackTimer = null;
        }
        
        // 觸發暫停事件
        this.onPause();
        this.trigger('playStateChange', false);
    }
    
    // 新增物件到軌道
    addItem(trackId, item) {
        const track = this.tracks.find(t => t.id === trackId);
        if (!track) {
            console.error(`找不到軌道: ${trackId}`);
            return null;
        }

        // 檢查是否已存在相同ID的項目
        const existingItemIndex = track.items.findIndex(i => i.id === item.id);
        if (existingItemIndex >= 0) {
            track.items[existingItemIndex] = {
                ...track.items[existingItemIndex],
                ...item,
                element: null // 重置元素，以便重新創建
            };
            console.log(`更新項目 ${item.id} 在軌道 ${trackId}`);
        } else {
            // 添加新項目
            const newItem = {
                id: item.id || `item_${Date.now()}`,
                name: item.name || '項目',
                startTime: item.startTime || 0,
                duration: item.duration || 5,
                data: item.data || {},
                color: item.color || track.color,
                trackId: trackId,
                file: item.file || null,
                text: item.text || ''
            };
            
            // 確保不超出時間軸
            if (newItem.startTime < 0) newItem.startTime = 0;
            if (newItem.startTime + newItem.duration > this.duration) {
                this.duration = newItem.startTime + newItem.duration + 10; // 自動延長時間軸
            }
            
            track.items.push(newItem);
            console.log(`添加項目 ${newItem.id} 到軌道 ${trackId}`);
        }
        
        // 重繪軌道
        this.drawTracks();
        
        return track.items[track.items.length - 1];
    }
    
    // 事件訂閱
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    // 觸發事件
    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }
    
    // 強制更新視圖
    updateView() {
        // 重繪時間軸
        this.drawRuler();
        this.drawTracks();
        
        // 更新指示器位置
        if (this.timeIndicator) {
            this.timeIndicator.style.left = `${this.currentTime * this.scale}px`;
        }
        
        console.log('時間軸視圖已更新');
    }
}
/**
 * 增強型時間軸類別
 */
class EnhancedTimeline extends Timeline {
    constructor(options) {
        super(options);
        
        // 額外屬性
        this.selectedTrack = null;
        this.clipboard = null;
        this.snapToGrid = true;
        this.gridSize = 0.5; // 秒
        this.history = []; // 操作歷史
        this.historyIndex = -1; // 歷史指針
        
        // 初始化額外功能
        this.initEnhancedFeatures();
    }
    
    initEnhancedFeatures() {
        // 添加控制按鈕
        this.addTimelineControls();
        
        // 添加快捷鍵支持
        this.setupKeyboardShortcuts();
        
        // 添加右鍵菜單
        this.setupContextMenu();
    }
    
    addTimelineControls() {
        // 創建控制面板
        const controlsPanel = document.createElement('div');
        controlsPanel.className = 'timeline-controls mb-2';
        controlsPanel.innerHTML = `
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-secondary" id="tlCutBtn" title="分割">
                    <i class="bi bi-scissors"></i>
                </button>
                <button class="btn btn-outline-secondary" id="tlDeleteBtn" title="刪除">
                    <i class="bi bi-trash"></i>
                </button>
                <button class="btn btn-outline-secondary" id="tlCopyBtn" title="複製">
                    <i class="bi bi-files"></i>
                </button>
                <button class="btn btn-outline-secondary" id="tlPasteBtn" title="貼上">
                    <i class="bi bi-clipboard"></i>
                </button>
            </div>
            <div class="btn-group btn-group-sm ms-2">
                <button class="btn btn-outline-secondary" id="tlUndoBtn" title="復原">
                    <i class="bi bi-arrow-counterclockwise"></i>
                </button>
                <button class="btn btn-outline-secondary" id="tlRedoBtn" title="重做">
                    <i class="bi bi-arrow-clockwise"></i>
                </button>
            </div>
            <div class="btn-group btn-group-sm ms-2">
                <button class="btn btn-outline-secondary" id="tlZoomInBtn" title="放大">
                    <i class="bi bi-zoom-in"></i>
                </button>
                <button class="btn btn-outline-secondary" id="tlZoomOutBtn" title="縮小">
                    <i class="bi bi-zoom-out"></i>
                </button>
                <button class="btn btn-outline-secondary" id="tlFitBtn" title="適應">
                    <i class="bi bi-aspect-ratio"></i>
                </button>
            </div>
            <div class="form-check form-switch ms-2 d-inline-block">
                <input class="form-check-input" type="checkbox" id="tlSnapToggle" checked>
                <label class="form-check-label" for="tlSnapToggle">吸附</label>
            </div>
        `;
        
        // 插入到時間軸之前
        this.container.parentNode.insertBefore(controlsPanel, this.container);
        
        // 綁定按鈕事件
        document.getElementById('tlCutBtn').addEventListener('click', () => this.cutSelectedItem());
        document.getElementById('tlDeleteBtn').addEventListener('click', () => this.deleteSelectedItem());
        document.getElementById('tlCopyBtn').addEventListener('click', () => this.copySelectedItem());
        document.getElementById('tlPasteBtn').addEventListener('click', () => this.pasteItem());
        document.getElementById('tlUndoBtn').addEventListener('click', () => this.undo());
        document.getElementById('tlRedoBtn').addEventListener('click', () => this.redo());
        document.getElementById('tlZoomInBtn').addEventListener('click', () => this.zoomIn());
        document.getElementById('tlZoomOutBtn').addEventListener('click', () => this.zoomOut());
        document.getElementById('tlFitBtn').addEventListener('click', () => this.fitToView());
        document.getElementById('tlSnapToggle').addEventListener('change', (e) => this.snapToGrid = e.target.checked);
    }
    
    // 分割選中項目
    cutSelectedItem() {
        if (!this.selectedItem) return;
        
        const item = this.selectedItem;
        const track = this.tracks.find(t => t.id === item.trackId);
        if (!track) return;
        
        // 計算分割點
        const splitTime = this.currentTime;
        
        // 檢查分割點是否在項目內
        if (splitTime <= item.startTime || splitTime >= item.startTime + item.duration) {
            alert('請將時間指示器移動到要分割的位置');
            return;
        }
        
        // 保存操作供撤銷
        this.saveHistoryState();
        
        // 創建兩個新項目
        const firstItem = {
            ...item,
            id: `${item.id}_1`,
            duration: splitTime - item.startTime
        };
        
        const secondItem = {
            ...item,
            id: `${item.id}_2`,
            startTime: splitTime,
            duration: item.startTime + item.duration - splitTime
        };
        
        // 從軌道中移除原項目
        const itemIndex = track.items.findIndex(i => i.id === item.id);
        if (itemIndex !== -1) {
            track.items.splice(itemIndex, 1);
        }
        
        // 添加新項目
        track.items.push(firstItem);
        track.items.push(secondItem);
        
        // 重繪軌道
        this.drawTracks();
        
        // 選擇第二個項目
        this.selectItem(secondItem);
    }
    
    // 刪除選中項目
    deleteSelectedItem() {
        if (!this.selectedItem) return;
        
        // 保存操作供撤銷
        this.saveHistoryState();
        
        const item = this.selectedItem;
        const track = this.tracks.find(t => t.id === item.trackId);
        if (!track) return;
        
        // 尋找項目索引
        const itemIndex = track.items.findIndex(i => i.id === item.id);
        if (itemIndex === -1) return;
        
        // 從軌道中移除
        track.items.splice(itemIndex, 1);
        
        // 清除選擇
        this.selectedItem = null;
        
        // 重繪軌道
        this.drawTracks();
    }
    
    // 複製選中項目
    copySelectedItem() {
        if (!this.selectedItem) return;
        
        // 創建深拷貝
        this.clipboard = JSON.parse(JSON.stringify(this.selectedItem));
    }
    
    // 貼上項目
    pasteItem() {
        if (!this.clipboard) return;
        
        // 保存操作供撤銷
        this.saveHistoryState();
        
        // 創建新項目
        const newItem = {
            ...this.clipboard,
            id: `${this.clipboard.id}_copy_${Date.now()}`,
            startTime: this.currentTime
        };
        
        // 添加到原軌道
        const track = this.tracks.find(t => t.id === this.clipboard.trackId);
        if (!track) return;
        
        track.items.push(newItem);
        
        // 重繪軌道
        this.drawTracks();
        
        // 選擇新項目
        this.selectItem(newItem);
    }
    
    // 保存歷史狀態
    saveHistoryState() {
        // 只保留當前狀態之前的歷史
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        
        // 保存當前狀態的深拷貝
        const currentState = JSON.parse(JSON.stringify({
            tracks: this.tracks,
            duration: this.duration
        }));
        
        this.history.push(currentState);
        this.historyIndex = this.history.length - 1;
    }
    
    // 復原操作
    undo() {
        if (this.historyIndex <= 0) {
            console.log('沒有可復原的操作');
            return;
        }
        
        this.historyIndex--;
        const prevState = this.history[this.historyIndex];
        
        // 恢復狀態
        this.tracks = prevState.tracks;
        this.duration = prevState.duration;
        
        // 重新繪製
        this.drawTracks();
    }
    
    // 重做操作
    redo() {
        if (this.historyIndex >= this.history.length - 1) {
            console.log('沒有可重做的操作');
            return;
        }
        
        this.historyIndex++;
        const nextState = this.history[this.historyIndex];
        
        // 恢復狀態
        this.tracks = nextState.tracks;
        this.duration = nextState.duration;
        
        // 重新繪製
        this.drawTracks();
    }
    
    // 縮放功能
    zoomIn() {
        this.setScale(this.scale * 1.2);
    }
    
    zoomOut() {
        this.setScale(this.scale / 1.2);
    }
    
    fitToView() {
        // 計算合適的縮放比例
        const containerWidth = this.container.clientWidth - 100; // 減去軌道標籤寬度
        const timelineWidth = this.duration;
        
        if (timelineWidth <= 0) return;
        
        const newScale = containerWidth / timelineWidth;
        this.setScale(newScale);
    }
    
    // 設置鍵盤快捷鍵
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // 只在時間軸獲得焦點時處理
            if (!this.container.matches(':focus-within')) return;
            
            // 根據按鍵執行不同操作
            switch (e.key) {
                case 'Delete':
                    this.deleteSelectedItem();
                    break;
                case 'c':
                    if (e.ctrlKey || e.metaKey) {
                        this.copySelectedItem();
                    }
                    break;
                case 'v':
                    if (e.ctrlKey || e.metaKey) {
                        this.pasteItem();
                    }
                    break;
                case 'z':
                    if (e.ctrlKey || e.metaKey) {
                        this.undo();
                    }
                    break;
                case 'y':
                    if (e.ctrlKey || e.metaKey) {
                        this.redo();
                    }
                    break;
                case ' ': // 空格
                    if (this.isPlaying) {
                        this.pause();
                    } else {
                        this.play();
                    }
                    e.preventDefault(); // 防止頁面滾動
                    break;
                case 'ArrowLeft':
                    this.seekBackward(e.shiftKey ? 5 : 1);
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    this.seekForward(e.shiftKey ? 5 : 1);
                    e.preventDefault();
                    break;
                case '+':
                case '=':
                    if (e.ctrlKey || e.metaKey) {
                        this.zoomIn();
                        e.preventDefault();
                    }
                    break;
                case '-':
                    if (e.ctrlKey || e.metaKey) {
                        this.zoomOut();
                        e.preventDefault();
                    }
                    break;
                case '0':
                    if (e.ctrlKey || e.metaKey) {
                        this.fitToView();
                        e.preventDefault();
                    }
                    break;
            }
        });
    }

    // 右鍵菜單
    setupContextMenu() {
        // 為項目添加右鍵菜單
        this.container.addEventListener('contextmenu', (e) => {
            // 檢查是否點擊在項目上
            const itemElement = e.target.closest('.track-item');
            if (!itemElement) return;
            
            e.preventDefault();
            
            // 獲取項目ID
            const itemId = itemElement.dataset.id;
            const trackId = itemElement.closest('.timeline-track').dataset.id;
            
            // 查找項目對象
            const track = this.tracks.find(t => t.id === trackId);
            if (!track) return;
            
            const item = track.items.find(i => i.id === itemId);
            if (!item) return;
            
            // 選擇項目
            this.selectItem(item);
            
            // 創建菜單
            const menuElement = document.createElement('div');
            menuElement.className = 'timeline-context-menu';
            menuElement.style.position = 'absolute';
            menuElement.style.left = `${e.pageX}px`;
            menuElement.style.top = `${e.pageY}px`;
            menuElement.style.zIndex = '1000';
            
            // 菜單項目
            menuElement.innerHTML = `
                <div class="list-group">
                    <button class="list-group-item list-group-item-action" data-action="cut">
                        <i class="bi bi-scissors me-2"></i>分割
                    </button>
                    <button class="list-group-item list-group-item-action" data-action="copy">
                        <i class="bi bi-files me-2"></i>複製
                    </button>
                    <button class="list-group-item list-group-item-action" data-action="delete">
                        <i class="bi bi-trash me-2"></i>刪除
                    </button>
                    <button class="list-group-item list-group-item-action" data-action="properties">
                        <i class="bi bi-gear me-2"></i>屬性
                    </button>
                </div>
            `;
            
            // 添加到文檔
            document.body.appendChild(menuElement);
            
            // 綁定菜單項目事件
            menuElement.querySelectorAll('button').forEach(button => {
                button.addEventListener('click', () => {
                    const action = button.dataset.action;
                    
                    switch (action) {
                        case 'cut':
                            this.cutSelectedItem();
                            break;
                        case 'copy':
                            this.copySelectedItem();
                            break;
                        case 'delete':
                            this.deleteSelectedItem();
                            break;
                        case 'properties':
                            this.showItemProperties(item);
                            break;
                    }
                    
                    // 移除菜單
                    menuElement.remove();
                });
            });
            
            // 點擊其他地方關閉菜單
            const closeMenu = () => {
                menuElement.remove();
                document.removeEventListener('click', closeMenu);
            };
            
            // 延遲添加事件，避免立即觸發
            setTimeout(() => {
                document.addEventListener('click', closeMenu);
            }, 10);
        });
    }

    showItemProperties(item) {
        // 創建或獲取屬性對話框
        let propertiesModal = document.getElementById('itemPropertiesModal');
        
        if (!propertiesModal) {
            propertiesModal = document.createElement('div');
            propertiesModal.className = 'modal fade';
            propertiesModal.id = 'itemPropertiesModal';
            propertiesModal.setAttribute('tabindex', '-1');
            
            propertiesModal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">項目屬性</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="itemPropertiesForm">
                                <div class="mb-3">
                                    <label for="itemName" class="form-label">名稱</label>
                                    <input type="text" class="form-control" id="itemName">
                                </div>
                                <div class="mb-3">
                                    <label for="itemStartTime" class="form-label">開始時間 (秒)</label>
                                    <input type="number" class="form-control" id="itemStartTime" step="0.1" min="0">
                                </div>
                                <div class="mb-3">
                                    <label for="itemDuration" class="form-label">持續時間 (秒)</label>
                                    <input type="number" class="form-control" id="itemDuration" step="0.1" min="0.1">
                                </div>
                                <div class="mb-3">
                                    <label for="itemColor" class="form-label">顏色</label>
                                    <input type="color" class="form-control" id="itemColor">
                                </div>
                                <div id="itemSpecificSettings">
                                    <!-- 根據項目類型動態添加 -->
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="saveItemProperties">套用</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(propertiesModal);
        }
        
        // 填充表單數據
        document.getElementById('itemName').value = item.name || '';
        document.getElementById('itemStartTime').value = item.startTime;
        document.getElementById('itemDuration').value = item.duration;
        document.getElementById('itemColor').value = item.color || '#007bff';
        
        // 根據項目類型添加特定設置
        const specificSettings = document.getElementById('itemSpecificSettings');
        specificSettings.innerHTML = '';
        
        const trackType = item.trackId.replace('Track', '');
        
        if (trackType === 'video') {
            specificSettings.innerHTML = `
                <div class="mb-3">
                    <label for="itemVolume" class="form-label">音量</label>
                    <input type="range" class="form-range" id="itemVolume" min="0" max="1" step="0.1" value="${item.volume || 1}">
                </div>
                <div class="mb-3">
                    <label for="itemSpeed" class="form-label">播放速度</label>
                    <select class="form-select" id="itemSpeed">
                        <option value="0.5" ${item.speed === 0.5 ? 'selected' : ''}>0.5x (慢動作)</option>
                        <option value="0.75" ${item.speed === 0.75 ? 'selected' : ''}>0.75x (較慢)</option>
                        <option value="1" ${!item.speed || item.speed === 1 ? 'selected' : ''}>1x (正常)</option>
                        <option value="1.5" ${item.speed === 1.5 ? 'selected' : ''}>1.5x (較快)</option>
                        <option value="2" ${item.speed === 2 ? 'selected' : ''}>2x (快速)</option>
                    </select>
                </div>
            `;
        } else if (trackType === 'audio') {
            specificSettings.innerHTML = `
                <div class="mb-3">
                    <label for="itemVolume" class="form-label">音量</label>
                    <input type="range" class="form-range" id="itemVolume" min="0" max="1" step="0.1" value="${item.volume || 1}">
                </div>
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="itemFadeIn" ${item.fadeIn ? 'checked' : ''}>
                        <label class="form-check-label" for="itemFadeIn">淡入</label>
                    </div>
                </div>
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="itemFadeOut" ${item.fadeOut ? 'checked' : ''}>
                        <label class="form-check-label" for="itemFadeOut">淡出</label>
                    </div>
                </div>
            `;
        } else if (trackType === 'subtitle') {
            specificSettings.innerHTML = `
                <div class="mb-3">
                    <label for="itemText" class="form-label">文本</label>
                    <textarea class="form-control" id="itemText" rows="3">${item.text || ''}</textarea>
                </div>
                <div class="mb-3">
                    <label for="itemFont" class="form-label">字體</label>
                    <select class="form-select" id="itemFont">
                        <option value="default" ${!item.font || item.font === 'default' ? 'selected' : ''}>預設</option>
                        <option value="sans-serif" ${item.font === 'sans-serif' ? 'selected' : ''}>無襯線體</option>
                        <option value="serif" ${item.font === 'serif' ? 'selected' : ''}>襯線體</option>
                        <option value="monospace" ${item.font === 'monospace' ? 'selected' : ''}>等寬字體</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label for="itemFontSize" class="form-label">字體大小</label>
                    <input type="range" class="form-range" id="itemFontSize" min="1" max="5" step="1" value="${item.fontSize || 3}">
                </div>
            `;
        }
        
        // 綁定保存按鈕
        const saveButton = document.getElementById('saveItemProperties');
        saveButton.onclick = () => {
            // 保存操作供撤銷
            this.saveHistoryState();
            
            // 更新項目屬性
            item.name = document.getElementById('itemName').value;
            item.startTime = parseFloat(document.getElementById('itemStartTime').value);
            item.duration = parseFloat(document.getElementById('itemDuration').value);
            item.color = document.getElementById('itemColor').value;
            
            // 根據項目類型獲取特定屬性
            if (trackType === 'video' || trackType === 'audio') {
                item.volume = parseFloat(document.getElementById('itemVolume').value);
            }
            
            if (trackType === 'video') {
                item.speed = parseFloat(document.getElementById('itemSpeed').value);
            }
            
            if (trackType === 'audio') {
                item.fadeIn = document.getElementById('itemFadeIn').checked;
                item.fadeOut = document.getElementById('itemFadeOut').checked;
            }
            
            if (trackType === 'subtitle') {
                item.text = document.getElementById('itemText').value;
                item.font = document.getElementById('itemFont').value;
                item.fontSize = parseInt(document.getElementById('itemFontSize').value);
            }
            
            // 重繪軌道
            this.drawTracks();
            
            // 關閉模態框
            const modal = bootstrap.Modal.getInstance(propertiesModal);
            modal.hide();
        };
        
        // 顯示模態框
        const modal = new bootstrap.Modal(propertiesModal);
        modal.show();
    }
    
    // 重寫項目移動方法，加入吸附功能
    moveItem(item, newTime) {
        // 保存操作供撤銷
        this.saveHistoryState();
        
        if (this.snapToGrid && newTime !== undefined) {
            // 吸附到網格
            newTime = Math.round(newTime / this.gridSize) * this.gridSize;
        }
        
        // 調用原方法
        super.moveItem(item, newTime);
    }
    
    // 重寫項目調整大小方法，加入吸附功能
    resizeItem(item, newDuration) {
        // 保存操作供撤銷
        this.saveHistoryState();
        
        if (this.snapToGrid && newDuration !== undefined) {
            // 吸附到網格
            newDuration = Math.round(newDuration / this.gridSize) * this.gridSize;
            if (newDuration < this.gridSize) newDuration = this.gridSize;
        }
        
        // 調用原方法
        super.resizeItem(item, newDuration);
    }
    
    // 向後跳轉
    seekBackward(seconds = 1) {
        const newTime = Math.max(0, this.currentTime - seconds);
        this.setCurrentTime(newTime);
    }
    
    // 向前跳轉
    seekForward(seconds = 1) {
        const newTime = Math.min(this.duration, this.currentTime + seconds);
        this.setCurrentTime(newTime);
    }
}