// subtitle.js - 字幕編輯器功能實現

class SubtitleEditor {
    constructor(options) {
        this.container = options.container;
        this.subtitles = [];
        this.currentIndex = -1;
        this.callbacks = {};
        
        // 初始化編輯器
        this.init();
    }
    
    init() {
        // 創建基本DOM結構
        this.editorEl = document.createElement('div');
        this.editorEl.className = 'subtitle-editor';
        this.container.appendChild(this.editorEl);
        
        // 創建字幕列表
        this.listEl = document.createElement('div');
        this.listEl.className = 'subtitle-list';
        this.editorEl.appendChild(this.listEl);
        
        // 創建編輯面板
        this.editPanelEl = document.createElement('div');
        this.editPanelEl.className = 'subtitle-edit-panel';
        this.editorEl.appendChild(this.editPanelEl);
        
        // 構建編輯面板
        this.buildEditPanel();
        
        // 綁定事件
        this.bindEvents();
    }
    
    // 構建編輯面板
    buildEditPanel() {
        // 文本輸入區
        const textLabel = document.createElement('label');
        textLabel.textContent = '字幕文本';
        this.editPanelEl.appendChild(textLabel);
        
        this.textArea = document.createElement('textarea');
        this.textArea.className = 'subtitle-text';
        this.textArea.rows = 4;
        this.editPanelEl.appendChild(this.textArea);
        
        // 開始時間
        const startTimeLabel = document.createElement('label');
        startTimeLabel.textContent = '開始時間 (秒)';
        this.editPanelEl.appendChild(startTimeLabel);
        
        this.startTimeInput = document.createElement('input');
        this.startTimeInput.type = 'number';
        this.startTimeInput.step = '0.1';
        this.startTimeInput.min = '0';
        this.startTimeInput.className = 'subtitle-start-time';
        this.editPanelEl.appendChild(this.startTimeInput);
        
        // 持續時間
        const durationLabel = document.createElement('label');
        durationLabel.textContent = '持續時間 (秒)';
        this.editPanelEl.appendChild(durationLabel);
        
        this.durationInput = document.createElement('input');
        this.durationInput.type = 'number';
        this.durationInput.step = '0.1';
        this.durationInput.min = '0.5';
        this.durationInput.className = 'subtitle-duration';
        this.editPanelEl.appendChild(this.durationInput);
        
        // 按鈕區
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'button-group';
        
        this.applyButton = document.createElement('button');
        this.applyButton.textContent = '應用';
        this.applyButton.className = 'btn btn-primary btn-sm';
        this.applyButton.disabled = true;
        buttonGroup.appendChild(this.applyButton);
        
        this.previewButton = document.createElement('button');
        this.previewButton.textContent = '預覽';
        this.previewButton.className = 'btn btn-outline-secondary btn-sm';
        this.previewButton.disabled = true;
        buttonGroup.appendChild(this.previewButton);
        
        this.editPanelEl.appendChild(buttonGroup);
    }
    
    // 綁定事件
    bindEvents() {
        // 應用按鈕
        this.applyButton.addEventListener('click', () => {
            if (this.currentIndex < 0) return;
            
            const subtitle = this.subtitles[this.currentIndex];
            subtitle.text = this.textArea.value;
            subtitle.startTime = parseFloat(this.startTimeInput.value) || 0;
            subtitle.duration = parseFloat(this.durationInput.value) || 2;
            subtitle.endTime = subtitle.startTime + subtitle.duration;
            
            // 更新列表項
            this.updateSubtitleItem(this.currentIndex);
            
            // 觸發字幕更新事件
            this.trigger('subtitleChange', subtitle);
        });
        
        // 預覽按鈕
        this.previewButton.addEventListener('click', () => {
            if (this.currentIndex < 0) return;
            
            const subtitle = this.subtitles[this.currentIndex];
            this.trigger('subtitlePreview', subtitle);
        });
        
        // 文本/時間變更時啟用應用按鈕
        this.textArea.addEventListener('input', () => {
            this.applyButton.disabled = this.currentIndex < 0;
        });
        
        this.startTimeInput.addEventListener('input', () => {
            this.applyButton.disabled = this.currentIndex < 0;
        });
        
        this.durationInput.addEventListener('input', () => {
            this.applyButton.disabled = this.currentIndex < 0;
        });
    }
    
    // 載入字幕
    loadSubtitles(subtitles) {
        this.subtitles = subtitles || [];
        this.currentIndex = -1;
        
        // 渲染字幕列表
        this.renderSubtitleList();
        
        // 禁用編輯面板
        this.enableEditPanel(false);
        
        // 觸發載入事件
        this.trigger('subtitlesLoaded', this.subtitles);
    }
    
    // 渲染字幕列表
    renderSubtitleList() {
        this.listEl.innerHTML = '';
        
        if (this.subtitles.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = '尚未添加字幕';
            this.listEl.appendChild(emptyMessage);
            return;
        }
        
        // 創建字幕表格
        const table = document.createElement('table');
        table.className = 'subtitle-table';
        
        // 表頭
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        const headers = ['#', '開始時間', '結束時間', '持續時間', '文本', '操作'];
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // 表體
        const tbody = document.createElement('tbody');
        
        this.subtitles.forEach((subtitle, index) => {
            const row = this.createSubtitleRow(subtitle, index);
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        this.listEl.appendChild(table);
    }
    
    // 創建字幕行
    createSubtitleRow(subtitle, index) {
        const row = document.createElement('tr');
        row.dataset.index = index;
        
        // 序號列
        const indexCell = document.createElement('td');
        indexCell.textContent = index + 1;
        row.appendChild(indexCell);
        
        // 開始時間列
        const startTimeCell = document.createElement('td');
        startTimeCell.textContent = this.formatTime(subtitle.startTime);
        row.appendChild(startTimeCell);
        
        // 結束時間列
        const endTimeCell = document.createElement('td');
        endTimeCell.textContent = this.formatTime(subtitle.endTime);
        row.appendChild(endTimeCell);
        
        // 持續時間列
        const durationCell = document.createElement('td');
        durationCell.textContent = subtitle.duration.toFixed(1) + 's';
        row.appendChild(durationCell);
        
        // 文本列
        const textCell = document.createElement('td');
        textCell.className = 'subtitle-text-cell';
        textCell.textContent = subtitle.text.length > 30 
            ? subtitle.text.substring(0, 30) + '...' 
            : subtitle.text;
        textCell.title = subtitle.text;
        row.appendChild(textCell);
        
        // 操作列
        const actionCell = document.createElement('td');
        
        const editBtn = document.createElement('button');
        editBtn.className = 'btn btn-sm btn-outline-primary subtitle-edit-btn';
        editBtn.textContent = '編輯';
        editBtn.addEventListener('click', () => {
            this.editSubtitle(index);
        });
        actionCell.appendChild(editBtn);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger subtitle-delete-btn';
        deleteBtn.textContent = '刪除';
        deleteBtn.addEventListener('click', () => {
            this.deleteSubtitle(index);
        });
        actionCell.appendChild(deleteBtn);
        
        row.appendChild(actionCell);
        
        // 點擊行選擇字幕
        row.addEventListener('click', (e) => {
            if (!e.target.className.includes('btn')) {
                this.editSubtitle(index);
            }
        });
        
        return row;
    }
    
    // 更新字幕項
    updateSubtitleItem(index) {
        const rows = this.listEl.querySelectorAll('tbody tr');
        const subtitle = this.subtitles[index];
        
        if (rows[index]) {
            const cells = rows[index].querySelectorAll('td');
            
            cells[1].textContent = this.formatTime(subtitle.startTime);
            cells[2].textContent = this.formatTime(subtitle.endTime);
            cells[3].textContent = subtitle.duration.toFixed(1) + 's';
            
            cells[4].textContent = subtitle.text.length > 30 
                ? subtitle.text.substring(0, 30) + '...' 
                : subtitle.text;
            cells[4].title = subtitle.text;
        }
    }
    
    // 編輯字幕
    editSubtitle(index) {
        if (index < 0 || index >= this.subtitles.length) return;
        
        // 更新當前索引
        this.currentIndex = index;
        
        // 獲取字幕對象
        const subtitle = this.subtitles[index];
        
        // 填充編輯面板
        this.textArea.value = subtitle.text;
        this.startTimeInput.value = subtitle.startTime.toFixed(1);
        this.durationInput.value = subtitle.duration.toFixed(1);
        
        // 啟用編輯面板
        this.enableEditPanel(true);
        
        // 高亮選中行
        const rows = this.listEl.querySelectorAll('tbody tr');
        rows.forEach(row => row.classList.remove('selected'));
        
        if (rows[index]) {
            rows[index].classList.add('selected');
            rows[index].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        // 觸發選擇事件
        this.trigger('subtitleSelect', subtitle);
    }
    // 批量生成語音
    generateAudioForSubtitles() {
        if (!this.subtitles || this.subtitles.length === 0) {
            alert('沒有字幕，無法生成語音');
            return;
        }
        
        // 準備字幕資料
        const subtitlesData = this.subtitles.map(sub => {
            return {
                text: sub.text,
                startTime: sub.startTime
            };
        });
        
        // 發送到後端
        fetch('/api/batch_generate_speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subtitles: subtitlesData,
                engine: 'edge',
                voice: 'zh-TW-YunJheNeural',
                rate: 1.0
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('語音生成成功！共生成 ' + data.audio_files.length + ' 個音頻文件');
                
                // 更新字幕數據
                for (let i = 0; i < this.subtitles.length && i < data.audio_files.length; i++) {
                    this.subtitles[i].audio_file = data.audio_files[i];
                }
                
                // 觸發字幕更新
                this.trigger('subtitlesUpdated', this.subtitles);
                
                // 如果有時間軸，將音頻添加到時間軸
                if (window.timeline) {
                    // 清空之前的音頻軌道
                    const audioTrack = window.timeline.tracks.find(t => t.id === 'audioTrack');
                    if (audioTrack) {
                        audioTrack.items = [];
                    }
                    
                    // 添加新音頻
                    data.audio_files.forEach((file, index) => {
                        if (index < this.subtitles.length) {
                            window.timeline.addItem('audioTrack', {
                                id: `audio_${index+1}`,
                                name: `音頻 ${index+1}`,
                                startTime: this.subtitles[index].startTime,
                                duration: this.subtitles[index].duration,
                                file: file
                            });
                        }
                    });
                    
                    // 更新界面
                    if (typeof window.timeline.drawTracks === 'function') {
                        window.timeline.drawTracks();
                    }
                }
            } else {
                alert('語音生成失敗: ' + data.error);
            }
        })
        .catch(error => {
            alert('語音生成請求失敗: ' + error);
        });
    }    
    // 添加新字幕
    addSubtitle(subtitle) {
        const newSubtitle = {
            text: subtitle.text || '',
            startTime: subtitle.startTime || 0,
            duration: subtitle.duration || 2,
            endTime: (subtitle.startTime || 0) + (subtitle.duration || 2)
        };
        
        this.subtitles.push(newSubtitle);
        
        // 重新渲染列表
        this.renderSubtitleList();
        
        // 選擇新添加的字幕
        this.editSubtitle(this.subtitles.length - 1);
        
        // 觸發添加事件
        this.trigger('subtitleAdd', newSubtitle);
        
        return newSubtitle;
    }
    
    // 刪除字幕
    deleteSubtitle(index) {
        if (index < 0 || index >= this.subtitles.length) return;
        
        // 彈出確認對話框
        if (!confirm('確定要刪除這條字幕嗎？')) return;
        
        const subtitle = this.subtitles[index];
        
        // 從數組中移除
        this.subtitles.splice(index, 1);
        
        // 重新渲染列表
        this.renderSubtitleList();
        
        // 如果正在編輯的字幕被刪除，禁用編輯面板
        if (this.currentIndex === index) {
            this.currentIndex = -1;
            this.enableEditPanel(false);
        }
        // 如果刪除的是之前的字幕，更新當前索引
        else if (this.currentIndex > index) {
            this.currentIndex--;
        }
        
        // 觸發刪除事件
        this.trigger('subtitleDelete', subtitle);
    }
    
// 啟用/禁用編輯面板
enableEditPanel(enabled) {
    this.textArea.disabled = !enabled;
    this.startTimeInput.disabled = !enabled;
    this.durationInput.disabled = !enabled;
    this.applyButton.disabled = !enabled;
    this.previewButton.disabled = !enabled;
    
    if (!enabled) {
        this.textArea.value = '';
        this.startTimeInput.value = '';
        this.durationInput.value = '';
    }
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

// 格式化時間
formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
}

// 從文本批量生成字幕
generateFromText(text, options = {}) {
    // 默認選項
    const defaults = {
        startTime: 0,
        charactersPerSecond: 5,
        minDuration: 1.5,
        maxDuration: 5,
        splitByPunctuation: true
    };
    
    const settings = {...defaults, ...options};
    
    // 分割文本
    let segments = [];
    if (settings.splitByPunctuation) {
        // 按標點符號分割
        segments = text.split(/(?<=[。！？.!?])/);
    } else {
        // 按行分割
        segments = text.split('\n');
    }
    
    // 過濾空段落
    segments = segments.filter(segment => segment.trim().length > 0);
    
    // 清空現有字幕
    this.subtitles = [];
    
    // 計算字幕
    let currentTime = settings.startTime;
    
    segments.forEach(segment => {
        const text = segment.trim();
        if (!text) return;
        
        // 根據字符數計算持續時間
        let duration = text.length / settings.charactersPerSecond;
        
        // 限制在最小/最大時間範圍內
        duration = Math.max(settings.minDuration, Math.min(settings.maxDuration, duration));
        
        // 創建字幕
        const subtitle = {
            text: text,
            startTime: currentTime,
            duration: duration,
            endTime: currentTime + duration
        };
        
        this.subtitles.push(subtitle);
        
        // 更新下一個字幕的開始時間
        currentTime += duration;
    });
    
    // 渲染字幕列表
    this.renderSubtitleList();
    
    // 觸發生成事件
    this.trigger('subtitlesGenerated', this.subtitles);
    
    return this.subtitles;
}
// 在 SubtitleEditor 類別中添加或修改以下方法

// 增強 "生成字幕和語音" 功能，確保字幕和音頻同步添加到時間軸
generateSubtitlesFromText() {
    console.log('從文本生成字幕和語音');
    
    // 獲取文本內容
    const textArea = document.querySelector('#textForSubtitles');
    if (!textArea || !textArea.value.trim()) {
        alert('請先輸入文本');
        return;
    }
    
    // 獲取生成參數
    const charactersPerSecond = parseFloat(document.querySelector('#charactersPerSecond').value) || 5;
    const splitByPunctuation = document.querySelector('#splitByPunctuation').checked;
    
    // 顯示進度條
    const progressEl = document.getElementById('audioGenerationProgress');
    if (progressEl) {
        progressEl.classList.remove('d-none');
    }
    
    // 調用字幕編輯器的方法
    if (window.subtitleEditor) {
        // 生成字幕
        const subtitles = window.subtitleEditor.generateFromText(textArea.value, {
            charactersPerSecond: charactersPerSecond,
            splitByPunctuation: splitByPunctuation
        });
        
        console.log('字幕生成完成，共 ' + window.subtitleEditor.subtitles.length + ' 條字幕');
        
        // 添加字幕到時間軸
        this.addSubtitlesToTimeline(window.subtitleEditor.subtitles, true); // 添加參數確保添加到時間軸
        
        // 檢查是否需要生成語音
        const generateTTS = document.querySelector('#generateTTS');
        if (generateTTS && generateTTS.checked) {
            // 生成批量語音並強制添加到時間軸
            this.generateBatchAudioAndAddToTimeline(window.subtitleEditor.subtitles, true);
        }
    } else {
        console.error('字幕編輯器未初始化');
        alert('字幕編輯器未初始化');
    }
}

// 強化添加字幕到時間軸的方法，確保其正確顯示
addSubtitlesToTimeline(subtitles, forceUpdate = false) {
    if (!window.timeline) {
        console.error('時間軸未初始化');
        return;
    }
    
    // 清空字幕軌道
    const subtitleTrack = window.timeline.tracks.find(t => t.id === 'subtitleTrack');
    if (subtitleTrack) {
        subtitleTrack.items = [];
    }
    
    // 添加字幕到時間軸
    subtitles.forEach((subtitle, index) => {
        window.timeline.addItem('subtitleTrack', {
            id: `subtitle_${index+1}`,
            name: subtitle.text.length > 10 ? subtitle.text.substring(0, 10) + '...' : subtitle.text,
            startTime: subtitle.startTime,
            duration: subtitle.duration,
            text: subtitle.text,
            color: '#17a2b8'
        });
    });
    
    // 確保時間軸重繪
    if (typeof window.timeline.drawTracks === 'function') {
        window.timeline.drawTracks();
    }
    
    // 強制更新視圖
    if (forceUpdate && window.timeline.updateView) {
        window.timeline.updateView();
    }
    
    console.log('字幕已添加到時間軸，並強制更新視圖');
}

// 修改生成語音的方法，確保生成後自動添加到時間軸
generateBatchAudioAndAddToTimeline(subtitles, forceUpdate = false) {
    if (!subtitles || subtitles.length === 0) {
        showError('沒有字幕，無法生成語音');
        return;
    }
    
    // 禁用按鈕，防止重複點擊
    const generateBtn = document.getElementById('generateAudioForSubtitles');
    const generateSubBtn = document.getElementById('generateSubtitles');
    
    if (generateBtn) generateBtn.disabled = true;
    if (generateSubBtn) generateSubBtn.disabled = true;
    
    // 顯示進度提示
    const progressEl = document.getElementById('audioGenerationProgress');
    if (progressEl) {
        progressEl.classList.remove('d-none');
    }
    
    updateStatusBar('正在為所有字幕生成語音，這可能需要一些時間...');
    
    // 將字幕轉換為適合發送的格式
    const subtitlesData = subtitles.map(sub => {
        return {
            text: sub.text,
            startTime: sub.startTime
        };
    });
    
    // 添加防重複標識
    const requestId = Date.now().toString();
    
    // 發送請求到後端
    fetch('/api/batch_generate_speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Request-ID': requestId
        },
        body: JSON.stringify({
            subtitles: subtitlesData,
            engine: 'edge',
            voice: 'zh-TW-YunJheNeural',
            rate: 1.0,
            requestId: requestId
        })
    })
    .then(response => response.json())
    .then(data => {
        // 恢復按鈕狀態
        if (generateBtn) generateBtn.disabled = false;
        if (generateSubBtn) generateSubBtn.disabled = false;
        
        // 隱藏進度條
        if (progressEl) {
            progressEl.classList.add('d-none');
        }
        
        if (data.success) {
            updateStatusBar('語音生成完成！共生成 ' + data.audio_files.length + ' 個音頻文件');
            alert('語音生成成功！共生成 ' + data.audio_files.length + ' 個音頻文件');
            
            // 添加音頻到時間軸，並強制更新
            this.addAudioToTimeline(data.audio_files, subtitles, forceUpdate);
        } else {
            showError('語音生成失敗: ' + data.error);
        }
    })
    .catch(error => {
        // 恢復按鈕狀態和隱藏進度條
        if (generateBtn) generateBtn.disabled = false;
        if (generateSubBtn) generateSubBtn.disabled = false;
        if (progressEl) {
            progressEl.classList.add('d-none');
        }
        
        showError('語音生成請求失敗: ' + error);
    });
}

// 強化添加音頻到時間軸的方法
addAudioToTimeline(audioFiles, subtitles, forceUpdate = false) {
    if (!window.timeline) {
        console.error('時間軸未初始化');
        return;
    }
    
    // 清空音頻軌道
    const audioTrack = window.timeline.tracks.find(t => t.id === 'audioTrack');
    if (audioTrack) {
        audioTrack.items = [];
    }
    
    // 添加音頻到時間軸
    audioFiles.forEach((audioFile, index) => {
        if (index < subtitles.length) {
            window.timeline.addItem('audioTrack', {
                id: `audio_${index+1}`,
                name: `音頻 ${index+1}`,
                startTime: subtitles[index].startTime,
                duration: subtitles[index].duration,
                file: audioFile,
                color: '#ffc107'
            });
            
            // 更新字幕對象，添加對應的音頻文件
            subtitles[index].audio_file = audioFile;
        }
    });
    
    // 重繪時間軸
    if (typeof window.timeline.drawTracks === 'function') {
        window.timeline.drawTracks();
    }
    
    // 強制更新視圖
    if (forceUpdate && window.timeline.updateView) {
        window.timeline.updateView();
    }
    
    // 觸發時間軸更新事件
    if (window.timeline.trigger) {
        window.timeline.trigger('tracksUpdated', {
            audioFiles: audioFiles,
            subtitles: subtitles
        });
    }
    
    console.log('音頻已添加到時間軸，並強制更新視圖');
}
// 導出字幕
exportSubtitles(format = 'srt') {
    if (this.subtitles.length === 0) {
        return '';
    }
    
    if (format === 'srt') {
        return this.exportToSRT();
    } else if (format === 'vtt') {
        return this.exportToVTT();
    }
    
    return '';
}

// 導出為SRT格式
exportToSRT() {
    let output = '';
    
    this.subtitles.forEach((subtitle, index) => {
        // 序號
        output += (index + 1) + '\n';
        
        // 時間範圍
        output += this.formatSRTTime(subtitle.startTime) + ' --> ' + this.formatSRTTime(subtitle.endTime) + '\n';
        
        // 文本
        output += subtitle.text + '\n\n';
    });
    
    return output;
}

// 導出為VTT格式
exportToVTT() {
    let output = 'WEBVTT\n\n';
    
    this.subtitles.forEach((subtitle, index) => {
        // 序號 (可選)
        output += (index + 1) + '\n';
        
        // 時間範圍
        output += this.formatVTTTime(subtitle.startTime) + ' --> ' + this.formatVTTTime(subtitle.endTime) + '\n';
        
        // 文本
        output += subtitle.text + '\n\n';
    });
    
    return output;
}

// 格式化SRT時間
formatSRTTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
}

// 格式化VTT時間
formatVTTTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
}
}

// 在文檔加載完成後初始化字幕編輯器
document.addEventListener('DOMContentLoaded', () => {
// 查找字幕編輯器容器
const container = document.querySelector('#subtitleEdit');
if (!container) return;

// 創建字幕編輯器實例
window.subtitleEditor = new SubtitleEditor({
    container: container
});

// 從文本生成按鈕
const generateButton = document.querySelector('#generateSubtitles');
if (generateButton) {
    generateButton.addEventListener('click', () => {
        const textArea = document.querySelector('#textForSubtitles');
        if (!textArea) return;
        
        // 獲取生成參數
        const charactersPerSecond = parseFloat(document.querySelector('#charactersPerSecond').value) || 5;
        const splitByPunctuation = document.querySelector('#splitByPunctuation').checked;
        
        // 生成字幕
        window.subtitleEditor.generateFromText(textArea.value, {
            charactersPerSecond: charactersPerSecond,
            splitByPunctuation: splitByPunctuation
        });
    });
}

// 導出按鈕
const exportButton = document.querySelector('#exportSubtitles');
if (exportButton) {
    exportButton.addEventListener('click', () => {
        const format = document.querySelector('#exportFormat').value || 'srt';
        
        // 導出字幕
        const content = window.subtitleEditor.exportSubtitles(format);
        
        // 創建下載鏈接
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `subtitles.${format}`;
        a.click();
        
        // 釋放URL
        URL.revokeObjectURL(url);
    });
}
});