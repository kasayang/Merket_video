// 應用轉場按鈕
document.getElementById('applyTransitionBtn').addEventListener('click', () => {
    applyTransitionToSelectedItem();
});

// 文字大小滑塊值顯示
document.getElementById('textSize').addEventListener('input', (e) => {
    document.getElementById('textSizeValue').textContent = e.target.value;
});

// 轉場持續時間滑塊值顯示
document.getElementById('transitionDuration').addEventListener('input', (e) => {
    document.getElementById('transitionDurationValue').textContent = e.target.value;
});

// 綁定選擇片段屬性更新事件
document.getElementById('clipName').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipStartTime').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipDuration').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipVolume').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipSpeed').addEventListener('change', updateSelectedItemProperty);

// 綁定效果項目點擊事件
document.querySelectorAll('.effect-item').forEach(item => {
    item.addEventListener('click', () => {
        applyEffectToSelectedItem(item.dataset.effect);
    });
});

// 綁定轉場項目點擊事件
document.querySelectorAll('.transition-item').forEach(item => {
    item.addEventListener('click', () => {
        selectTransition(item.dataset.transition);
    });
});
}

// 匯入媒體文件
function importMediaFiles(files) {
// 顯示進度條
const progressBar = document.querySelector('#importMediaModal .progress');
const progressBarInner = progressBar.querySelector('.progress-bar');
progressBar.style.display = 'block';
progressBarInner.style.width = '0%';

// 處理每個文件
const totalFiles = files.length;
let processedFiles = 0;

Array.from(files).forEach(file => {
    // 創建媒體預覽
    const reader = new FileReader();
    reader.onload = function(e) {
        // 確定媒體類型
        let mediaType = '';
        if (file.type.startsWith('video/')) {
            mediaType = 'video';
        } else if (file.type.startsWith('audio/')) {
            mediaType = 'audio';
        } else if (file.type.startsWith('image/')) {
            mediaType = 'image';
        } else {
            console.warn('不支援的媒體類型:', file.type);
            updateImportProgress();
            return;
        }
        
        // 創建媒體對象
        const mediaItem = {
            id: 'media_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
            name: file.name,
            type: mediaType,
            url: e.target.result,
            duration: 0 // 會在加載後更新
        };
        
        // 對於視頻和音頻，獲取持續時間
        if (mediaType === 'video' || mediaType === 'audio') {
            const tempMedia = mediaType === 'video' ? document.createElement('video') : document.createElement('audio');
            tempMedia.preload = 'metadata';
            
            tempMedia.onloadedmetadata = function() {
                mediaItem.duration = tempMedia.duration;
                mediaLibrary.push(mediaItem);
                updateMediaLibraryUI();
                updateImportProgress();
            };
            
            tempMedia.onerror = function() {
                console.error('加載媒體元數據時出錯:', file.name);
                updateImportProgress();
            };
            
            tempMedia.src = e.target.result;
        } else {
            // 圖片，假設為標準持續時間（5秒）
            mediaItem.duration = 5.0;
            mediaLibrary.push(mediaItem);
            updateMediaLibraryUI();
            updateImportProgress();
        }
    };
    
    reader.onerror = function() {
        console.error('讀取文件時出錯:', file.name);
        updateImportProgress();
    };
    
    // 以數據 URL 形式讀取文件
    reader.readAsDataURL(file);
});

// 更新進度條並在完成時關閉模態框
function updateImportProgress() {
    processedFiles++;
    const percentage = Math.floor((processedFiles / totalFiles) * 100);
    progressBarInner.style.width = percentage + '%';
    progressBarInner.setAttribute('aria-valuenow', percentage);
    
    if (processedFiles >= totalFiles) {
        // 所有文件處理完畢
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('importMediaModal'));
            modal.hide();
            
            // 重置文件輸入和進度條
            document.getElementById('mediaFileInput').value = '';
            progressBar.style.display = 'none';
        }, 500);
    }
}
}

// 更新媒體庫 UI
function updateMediaLibraryUI() {
// 所有媒體容器
const allContainer = document.getElementById('allMediaContainer');
// 視頻媒體容器
const videoContainer = document.getElementById('videoMediaContainer');
// 音頻媒體容器
const audioContainer = document.getElementById('audioMediaContainer');
// 圖片媒體容器
const imageContainer = document.getElementById('imageMediaContainer');

// 清空所有容器
allContainer.innerHTML = '';
videoContainer.innerHTML = '';
audioContainer.innerHTML = '';
imageContainer.innerHTML = '';

// 填充媒體庫項目
mediaLibrary.forEach(media => {
    const mediaElement = createMediaElement(media);
    
    // 加到所有媒體標籤頁
    allContainer.appendChild(mediaElement.cloneNode(true));
    
    // 根據類型加到相應標籤頁
    if (media.type === 'video') {
        videoContainer.appendChild(mediaElement.cloneNode(true));
    } else if (media.type === 'audio') {
        audioContainer.appendChild(mediaElement.cloneNode(true));
    } else if (media.type === 'image') {
        imageContainer.appendChild(mediaElement.cloneNode(true));
    }
});

// 綁定拖放事件
bindMediaItemDragEvents();
}

// 創建媒體元素
function createMediaElement(media) {
const mediaElement = document.createElement('div');
mediaElement.className = 'media-item';
mediaElement.dataset.id = media.id;
mediaElement.draggable = true;

// 縮略圖容器
const thumbnail = document.createElement('div');
thumbnail.className = 'media-thumbnail';

// 根據媒體類型創建不同預覽
if (media.type === 'video') {
    // 視頻縮略圖（使用 video 元素的第一幀）
    const videoElement = document.createElement('video');
    videoElement.src = media.url;
    videoElement.preload = 'metadata';
    videoElement.muted = true;
    videoElement.addEventListener('loadeddata', () => {
        // 用 canvas 捕獲第一幀
        const canvas = document.createElement('canvas');
        canvas.width = 160;
        canvas.height = 90;
        canvas.getContext('2d').drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        // 設置縮略圖背景
        thumbnail.style.backgroundImage = `url(${canvas.toDataURL()})`;
    });
    
    // 視頻圖標
    const icon = document.createElement('i');
    icon.className = 'bi bi-film media-icon';
    thumbnail.appendChild(icon);
} else if (media.type === 'audio') {
    // 音頻圖標（使用波形圖標）
    const icon = document.createElement('i');
    icon.className = 'bi bi-soundwave media-icon';
    thumbnail.appendChild(icon);
} else if (media.type === 'image') {
    // 圖片縮略圖
    thumbnail.style.backgroundImage = `url(${media.url})`;
}

// 媒體信息
const mediaInfo = document.createElement('div');
mediaInfo.className = 'media-info';

// 媒體名稱
const mediaName = document.createElement('div');
mediaName.className = 'media-name';
mediaName.textContent = media.name;

// 媒體時長（格式化為 MM:SS）
const mediaDuration = document.createElement('div');
mediaDuration.className = 'media-duration';

if (media.type === 'video' || media.type === 'audio') {
    const minutes = Math.floor(media.duration / 60);
    const seconds = Math.floor(media.duration % 60);
    mediaDuration.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
} else {
    mediaDuration.textContent = "00:05"; // 圖片默認 5 秒
}

// 組裝元素
mediaInfo.appendChild(mediaName);
mediaInfo.appendChild(mediaDuration);

mediaElement.appendChild(thumbnail);
mediaElement.appendChild(mediaInfo);

return mediaElement;
}

// 綁定媒體項目拖放事件
function bindMediaItemDragEvents() {
const mediaItems = document.querySelectorAll('.media-item');

mediaItems.forEach(item => {
    // 開始拖動
    item.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', item.dataset.id);
        e.dataTransfer.effectAllowed = 'copy';
    });
    
    // 雙擊預覽
    item.addEventListener('dblclick', () => {
        const mediaId = item.dataset.id;
        const media = mediaLibrary.find(m => m.id === mediaId);
        
        if (media) {
            previewMedia(media);
        }
    });
});

// 時間軸軌道接收拖放
const tracks = document.querySelectorAll('.timeline-track');

tracks.forEach(track => {
    // 允許放置
    track.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    });
    
    // 放置媒體
    track.addEventListener('drop', (e) => {
        e.preventDefault();
        
        const mediaId = e.dataTransfer.getData('text/plain');
        const media = mediaLibrary.find(m => m.id === mediaId);
        
        if (!media) return;
        
        // 獲取軌道 ID
        const trackId = track.dataset.id;
        const trackObj = activeProject.tracks.find(t => t.id === trackId);
        
        if (!trackObj) return;
        
        // 確保媒體類型與軌道匹配
        if ((media.type === 'video' && trackId === 'videoTrack') ||
            (media.type === 'audio' && trackId === 'audioTrack') ||
            (media.type === 'image' && trackId === 'videoTrack')) {
            
            // 計算放置時間點（基於鼠標放置位置）
            const trackRect = track.getBoundingClientRect();
            const trackContentRect = track.querySelector('.track-content').getBoundingClientRect();
            
            // 計算時間點（鼠標 X 位置相對於軌道內容）
            const relativeX = e.clientX - trackContentRect.left;
            const timePoint = relativeX / (trackContentRect.width / timeline.duration);
            
            // 創建時間軸項目
            addMediaToTimeline(media, trackId, timePoint);
        } else {
            alert('媒體類型與軌道不匹配');
        }
    });
});
}

// 將媒體添加到時間軸
function addMediaToTimeline(media, trackId, startTime = 0) {
// 尋找對應軌道
const track = activeProject.tracks.find(t => t.id === trackId);
if (!track) return;

// 創建時間軸項目
const timelineItem = {
    id: `item_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    name: media.name,
    type: media.type,
    trackId: trackId,
    startTime: startTime,
    duration: media.duration,
    mediaId: media.id,
    mediaUrl: media.url,
    color: getRandomColor(),
    volume: 1.0,
    speed: 1.0
};

// 添加到軌道
track.items.push(timelineItem);

// 更新時間軸
timeline.updateTracks(activeProject.tracks);

// 選擇新添加的項目
timeline.selectItem(timelineItem);
}

// 獲取隨機顏色
function getRandomColor() {
const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#7f8c8d', '#d35400'
];

return colors[Math.floor(Math.random() * colors.length)];
}

// 顯示所選項目的屬性
function displaySelectedItemProperties(item) {
if (!item) {
    // 未選擇項目，顯示提示
    document.getElementById('noClipSelected').style.display = 'block';
    document.getElementById('clipPropertiesForm').style.display = 'none';
    return;
}

// 隱藏提示，顯示表單
document.getElementById('noClipSelected').style.display = 'none';
document.getElementById('clipPropertiesForm').style.display = 'block';

// 填充表單
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

// 更新所選項目屬性
function updateSelectedItemProperty(e) {
const item = timeline.selectedItem;
if (!item) return;

// 保存操作歷史
timeline.saveHistoryState();

const property = e.target.id.replace('clip', '').toLowerCase();

switch (property) {
    case 'name':
        item.name = e.target.value;
        break;
    case 'starttime':
        item.startTime = parseFloat(e.target.value);
        break;
    case 'duration':
        item.duration = parseFloat(e.target.value);
        break;
    case 'volume':
        item.volume = parseFloat(e.target.value);
        break;
    case 'speed':
        item.speed = parseFloat(e.target.value);
        break;
}

// 更新時間軸
timeline.drawTracks();
}

// 預覽媒體
function previewMedia(media) {
const player = document.getElementById('previewPlayer');

// 清除之前的源
while (player.firstChild) {
    player.removeChild(player.firstChild);
}

if (media.type === 'video') {
    // 視頻預覽
    player.src = media.url;
    player.controls = true;
    player.play();
} else if (media.type === 'audio') {
    // 音頻預覽
    player.src = media.url;
    player.controls = true;
    player.play();
} else if (media.type === 'image') {
    // 圖片預覽
    player.style.display = 'none';
    
    // 創建臨時圖片預覽
    const imgPreview = document.createElement('img');
    imgPreview.id = 'imagePreview';
    imgPreview.src = media.url;
    imgPreview.style.maxWidth = '100%';
    imgPreview.style.maxHeight = '100%';
    
    const previewWindow = document.getElementById('previewWindow');
    previewWindow.appendChild(imgPreview);
}
}

// 添加文字到時間軸
function addTextToTimeline() {
const textContent = document.getElementById('textContent').value;
if (!textContent) {
    alert('請輸入文字內容');
    return;
}

// 獲取字幕軌道
const subtitleTrack = activeProject.tracks.find(t => t.id === 'subtitleTrack');
if (!subtitleTrack) return;

// 獲取文字設置
const font = document.getElementById('textFont').value;
const fontSize = document.getElementById('textSize').value;
const textColor = document.getElementById('textColor').value;
const textAlign = document.querySelector('input[name="textAlign"]:checked').value;

// 創建文字項目
const textItem = {
    id: `text_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    name: textContent.substring(0, 20) + (textContent.length > 20 ? '...' : ''),
    type: 'subtitle',
    trackId: 'subtitleTrack',
    startTime: timeline.currentTime,
    duration: 5.0, // 默認 5 秒
    text: textContent,
    font: font,
    fontSize: parseInt(fontSize),
    color: textColor,
    textAlign: textAlign,
    color: textColor // 項目顏色使用文字顏色
};

// 添加到軌道
subtitleTrack.items.push(textItem);

// 更新時間軸
timeline.updateTracks(activeProject.tracks);

// 選擇新添加的項目
timeline.selectItem(textItem);
}

// 應用效果到選中項目
function applyEffectToSelectedItem(effect) {
const item = timeline.selectedItem;
if (!item) {
    alert('請選擇一個項目');
    return;
}

if (item.type !== 'video' && item.type !== 'image') {
    alert('效果只能應用於視頻或圖片');
    return;
}

// 保存操作歷史
timeline.saveHistoryState();

// 設置效果
item.effect = effect;

// 根據效果類型設置參數
if (effect === 'none') {
    delete item.effectParams;
} else if (effect === 'grayscale' || effect === 'sepia' || effect === 'saturate') {
    item.effectParams = { intensity: 1.0 };
}

// 更新時間軸
timeline.drawTracks();
}

// 選擇轉場
let selectedTransition = 'none';
let transitionDuration = 1.0;

function selectTransition(transition) {
selectedTransition = transition;

// 高亮選中的轉場
document.querySelectorAll('.transition-item').forEach(item => {
    if (item.dataset.transition === transition) {
        item.classList.add('selected');
    } else {
        item.classList.remove('selected');
    }
});

// 更新轉場持續時間
transitionDuration = parseFloat(document.getElementById('transitionDuration').value);
}

// 應用轉場到選中項目
function applyTransitionToSelectedItem() {
const item = timeline.selectedItem;
if (!item) {
    alert('請選擇一個項目');
    return;
}

if (item.type !== 'video' && item.type !== 'image') {
    alert('轉場只能應用於視頻或圖片');
    return;
}

// 保存操作歷史
timeline.saveHistoryState();

// 設置轉場
item.transition = selectedTransition;
item.transitionDuration = transitionDuration;

// 更新時間軸
timeline.drawTracks();
}

// 時間軸變化處理
function handleTimelineChange() {
// 顯示當前選中項目的屬性
displaySelectedItemProperties(timeline.selectedItem);

// 更新預覽
updatePreview();
}

// 更新預覽
function updatePreview() {
// 獲取當前時間點的視頻項目
const currentTime = timeline.currentTime;
const videoTrack = activeProject.tracks.find(t => t.id === 'videoTrack');

if (!videoTrack) return;

// 查找當前時間點的項目
const activeItems = videoTrack.items.filter(item => 
    item.startTime <= currentTime && 
    item.startTime + item.duration > currentTime
);

// 如果找到視頻項目，更新預覽
if (activeItems.length > 0) {
    const activeItem = activeItems[0];
    const media = mediaLibrary.find(m => m.id === activeItem.mediaId);
    
    if (media) {
        // 設置視頻源
        const player = document.getElementById('previewPlayer');
        
        // 如果是不同的媒體或沒有源，設置新源
        if (!player.src || !player.src.includes(media.id)) {
            player.src = media.url;
            player.style.display = 'block';
            
            // 移除可能存在的圖片預覽
            const imgPreview = document.getElementById('imagePreview');
            if (imgPreview) imgPreview.remove();
        }
        
        // 計算視頻內部時間點
        const itemTime = currentTime - activeItem.startTime;
        
        // 設置播放位置
        if (Math.abs(player.currentTime - itemTime) > 0.1) {
            player.currentTime = itemTime;
        }
    }
}
}

// 創建新專案
function createNewProject() {
activeProject = {
    name: '未命名專案',
    tracks: [
        { id: 'videoTrack', name: '視頻軌', type: 'video', items: [] },
        { id: 'audioTrack', name: '音訊軌', type: 'audio', items: [] },
        { id: 'subtitleTrack', name: '字幕軌', type: 'subtitle', items: [] }
    ],
    duration: 60
};

// 更新時間軸
timeline.updateTracks(activeProject.tracks);
timeline.setDuration(activeProject.duration);
}

// 保存專案
function saveProject() {
// 創建專案數據
const projectData = {
    name: activeProject.name,
    tracks: activeProject.tracks,
    duration: activeProject.duration,
    mediaLibrary: mediaLibrary
};

// 轉換為 JSON
const jsonData = JSON.stringify(projectData);

// 創建 Blob
const blob = new Blob([jsonData], { type: 'application/json' });

// 創建下載連結
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = `${activeProject.name || '未命名專案'}.vedp`;

// 觸發下載
a.click();

// 清理
URL.revokeObjectURL(a.href);
}

// 打開專案
function openProject(file) {
const reader = new FileReader();

reader.onload = function(e) {
    try {
        // 解析專案文件
        const projectData = JSON.parse(e.target.result);
        
        // 設置專案數據
        activeProject = {
            name: projectData.name || '未命名專案',
            tracks: projectData.tracks || [],
            duration: projectData.duration || 60
        };
        
        // 設置媒體庫
        mediaLibrary = projectData.mediaLibrary || [];
        
        // 更新 UI
        updateMediaLibraryUI();
        
        // 更新時間軸
        timeline.updateTracks(activeProject.tracks);
        timeline.setDuration(activeProject.duration);
        
    } catch (error) {
        console.error('打開專案時出錯:', error);
        alert('無法打開專案文件，格式可能不正確。');
    }
};

reader.onerror = function() {
    alert('讀取文件時出錯，請重試。');
};

reader.readAsText(file);
}

// 匯出影片
function exportVideo() {
alert('影片匯出功能尚未實現。在實際應用中，這將需要服務器端處理或使用 WebCodecs API。');

// 隱藏模態框
const modal = bootstrap.Modal.getInstance(document.getElementById('exportVideoModal'));
modal.hide();
}
// 應用轉場按鈕
document.getElementById('applyTransitionBtn').addEventListener('click', () => {
    applyTransitionToSelectedItem();
});

// 文字大小滑塊值顯示
document.getElementById('textSize').addEventListener('input', (e) => {
    document.getElementById('textSizeValue').textContent = e.target.value;
});

// 轉場持續時間滑塊值顯示
document.getElementById('transitionDuration').addEventListener('input', (e) => {
    document.getElementById('transitionDurationValue').textContent = e.target.value;
});

// 綁定選擇片段屬性更新事件
document.getElementById('clipName').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipStartTime').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipDuration').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipVolume').addEventListener('change', updateSelectedItemProperty);
document.getElementById('clipSpeed').addEventListener('change', updateSelectedItemProperty);

// 綁定效果項目點擊事件
document.querySelectorAll('.effect-item').forEach(item => {
    item.addEventListener('click', () => {
        applyEffectToSelectedItem(item.dataset.effect);
    });
});

// 綁定轉場項目點擊事件
document.querySelectorAll('.transition-item').forEach(item => {
    item.addEventListener('click', () => {
        selectTransition(item.dataset.transition);
    });
});
}

// 匯入媒體文件
function importMediaFiles(files) {
// 顯示進度條
const progressBar = document.querySelector('#importMediaModal .progress');
const progressBarInner = progressBar.querySelector('.progress-bar');
progressBar.style.display = 'block';
progressBarInner.style.width = '0%';

// 處理每個文件
const totalFiles = files.length;
let processedFiles = 0;

Array.from(files).forEach(file => {
    // 創建媒體預覽
    const reader = new FileReader();
    reader.onload = function(e) {
        // 確定媒體類型
        let mediaType = '';
        if (file.type.startsWith('video/')) {
            mediaType = 'video';
        } else if (file.type.startsWith('audio/')) {
            mediaType = 'audio';
        } else if (file.type.startsWith('image/')) {
            mediaType = 'image';
        } else {
            console.warn('不支援的媒體類型:', file.type);
            updateImportProgress();
            return;
        }
        
        // 創建媒體對象
        const mediaItem = {
            id: 'media_' + Date.now() + '_' + Math.floor(Math.random() * 1000),
            name: file.name,
            type: mediaType,
            url: e.target.result,
            duration: 0 // 會在加載後更新
        };
        
        // 對於視頻和音頻，獲取持續時間
        if (mediaType === 'video' || mediaType === 'audio') {
            const tempMedia = mediaType === 'video' ? document.createElement('video') : document.createElement('audio');
            tempMedia.preload = 'metadata';
            
            tempMedia.onloadedmetadata = function() {
                mediaItem.duration = tempMedia.duration;
                mediaLibrary.push(mediaItem);
                updateMediaLibraryUI();
                updateImportProgress();
            };
            
            tempMedia.onerror = function() {
                console.error('加載媒體元數據時出錯:', file.name);
                updateImportProgress();
            };
            
            tempMedia.src = e.target.result;
        } else {
            // 圖片，假設為標準持續時間（5秒）
            mediaItem.duration = 5.0;
            mediaLibrary.push(mediaItem);
            updateMediaLibraryUI();
            updateImportProgress();
        }
    };
    
    reader.onerror = function() {
        console.error('讀取文件時出錯:', file.name);
        updateImportProgress();
    };
    
    // 以數據 URL 形式讀取文件
    reader.readAsDataURL(file);
});

// 更新進度條並在完成時關閉模態框
function updateImportProgress() {
    processedFiles++;
    const percentage = Math.floor((processedFiles / totalFiles) * 100);
    progressBarInner.style.width = percentage + '%';
    progressBarInner.setAttribute('aria-valuenow', percentage);
    
    if (processedFiles >= totalFiles) {
        // 所有文件處理完畢
        setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('importMediaModal'));
            modal.hide();
            
            // 重置文件輸入和進度條
            document.getElementById('mediaFileInput').value = '';
            progressBar.style.display = 'none';
        }, 500);
    }
}
}

// 更新媒體庫 UI
function updateMediaLibraryUI() {
// 所有媒體容器
const allContainer = document.getElementById('allMediaContainer');
// 視頻媒體容器
const videoContainer = document.getElementById('videoMediaContainer');
// 音頻媒體容器
const audioContainer = document.getElementById('audioMediaContainer');
// 圖片媒體容器
const imageContainer = document.getElementById('imageMediaContainer');

// 清空所有容器
allContainer.innerHTML = '';
videoContainer.innerHTML = '';
audioContainer.innerHTML = '';
imageContainer.innerHTML = '';

// 填充媒體庫項目
mediaLibrary.forEach(media => {
    const mediaElement = createMediaElement(media);
    
    // 加到所有媒體標籤頁
    allContainer.appendChild(mediaElement.cloneNode(true));
    
    // 根據類型加到相應標籤頁
    if (media.type === 'video') {
        videoContainer.appendChild(mediaElement.cloneNode(true));
    } else if (media.type === 'audio') {
        audioContainer.appendChild(mediaElement.cloneNode(true));
    } else if (media.type === 'image') {
        imageContainer.appendChild(mediaElement.cloneNode(true));
    }
});

// 綁定拖放事件
bindMediaItemDragEvents();
}

// 創建媒體元素
function createMediaElement(media) {
const mediaElement = document.createElement('div');
mediaElement.className = 'media-item';
mediaElement.dataset.id = media.id;
mediaElement.draggable = true;

// 縮略圖容器
const thumbnail = document.createElement('div');
thumbnail.className = 'media-thumbnail';

// 根據媒體類型創建不同預覽
if (media.type === 'video') {
    // 視頻縮略圖（使用 video 元素的第一幀）
    const videoElement = document.createElement('video');
    videoElement.src = media.url;
    videoElement.preload = 'metadata';
    videoElement.muted = true;
    videoElement.addEventListener('loadeddata', () => {
        // 用 canvas 捕獲第一幀
        const canvas = document.createElement('canvas');
        canvas.width = 160;
        canvas.height = 90;
        canvas.getContext('2d').drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        // 設置縮略圖背景
        thumbnail.style.backgroundImage = `url(${canvas.toDataURL()})`;
    });
    
    // 視頻圖標
    const icon = document.createElement('i');
    icon.className = 'bi bi-film media-icon';
    thumbnail.appendChild(icon);
} else if (media.type === 'audio') {
    // 音頻圖標（使用波形圖標）
    const icon = document.createElement('i');
    icon.className = 'bi bi-soundwave media-icon';
    thumbnail.appendChild(icon);
} else if (media.type === 'image') {
    // 圖片縮略圖
    thumbnail.style.backgroundImage = `url(${media.url})`;
}

// 媒體信息
const mediaInfo = document.createElement('div');
mediaInfo.className = 'media-info';

// 媒體名稱
const mediaName = document.createElement('div');
mediaName.className = 'media-name';
mediaName.textContent = media.name;

// 媒體時長（格式化為 MM:SS）
const mediaDuration = document.createElement('div');
mediaDuration.className = 'media-duration';

if (media.type === 'video' || media.type === 'audio') {
    const minutes = Math.floor(media.duration / 60);
    const seconds = Math.floor(media.duration % 60);
    mediaDuration.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
} else {
    mediaDuration.textContent = "00:05"; // 圖片默認 5 秒
}

// 組裝元素
mediaInfo.appendChild(mediaName);
mediaInfo.appendChild(mediaDuration);

mediaElement.appendChild(thumbnail);
mediaElement.appendChild(mediaInfo);

return mediaElement;
}

// 綁定媒體項目拖放事件
function bindMediaItemDragEvents() {
const mediaItems = document.querySelectorAll('.media-item');

mediaItems.forEach(item => {
    // 開始拖動
    item.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', item.dataset.id);
        e.dataTransfer.effectAllowed = 'copy';
    });
    
    // 雙擊預覽
    item.addEventListener('dblclick', () => {
        const mediaId = item.dataset.id;
        const media = mediaLibrary.find(m => m.id === mediaId);
        
        if (media) {
            previewMedia(media);
        }
    });
});

// 時間軸軌道接收拖放
const tracks = document.querySelectorAll('.timeline-track');

tracks.forEach(track => {
    // 允許放置
    track.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    });
    
    // 放置媒體
    track.addEventListener('drop', (e) => {
        e.preventDefault();
        
        const mediaId = e.dataTransfer.getData('text/plain');
        const media = mediaLibrary.find(m => m.id === mediaId);
        
        if (!media) return;
        
        // 獲取軌道 ID
        const trackId = track.dataset.id;
        const trackObj = activeProject.tracks.find(t => t.id === trackId);
        
        if (!trackObj) return;
        
        // 確保媒體類型與軌道匹配
        if ((media.type === 'video' && trackId === 'videoTrack') ||
            (media.type === 'audio' && trackId === 'audioTrack') ||
            (media.type === 'image' && trackId === 'videoTrack')) {
            
            // 計算放置時間點（基於鼠標放置位置）
            const trackRect = track.getBoundingClientRect();
            const trackContentRect = track.querySelector('.track-content').getBoundingClientRect();
            
            // 計算時間點（鼠標 X 位置相對於軌道內容）
            const relativeX = e.clientX - trackContentRect.left;
            const timePoint = relativeX / (trackContentRect.width / timeline.duration);
            
            // 創建時間軸項目
            addMediaToTimeline(media, trackId, timePoint);
        } else {
            alert('媒體類型與軌道不匹配');
        }
    });
});
}

// 將媒體添加到時間軸
function addMediaToTimeline(media, trackId, startTime = 0) {
// 尋找對應軌道
const track = activeProject.tracks.find(t => t.id === trackId);
if (!track) return;

// 創建時間軸項目
const timelineItem = {
    id: `item_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    name: media.name,
    type: media.type,
    trackId: trackId,
    startTime: startTime,
    duration: media.duration,
    mediaId: media.id,
    mediaUrl: media.url,
    color: getRandomColor(),
    volume: 1.0,
    speed: 1.0
};

// 添加到軌道
track.items.push(timelineItem);

// 更新時間軸
timeline.updateTracks(activeProject.tracks);

// 選擇新添加的項目
timeline.selectItem(timelineItem);
}

// 獲取隨機顏色
function getRandomColor() {
const colors = [
    '#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#7f8c8d', '#d35400'
];

return colors[Math.floor(Math.random() * colors.length)];
}

// 顯示所選項目的屬性
function displaySelectedItemProperties(item) {
if (!item) {
    // 未選擇項目，顯示提示
    document.getElementById('noClipSelected').style.display = 'block';
    document.getElementById('clipPropertiesForm').style.display = 'none';
    return;
}

// 隱藏提示，顯示表單
document.getElementById('noClipSelected').style.display = 'none';
document.getElementById('clipPropertiesForm').style.display = 'block';

// 填充表單
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

// 更新所選項目屬性
function updateSelectedItemProperty(e) {
const item = timeline.selectedItem;
if (!item) return;

// 保存操作歷史
timeline.saveHistoryState();

const property = e.target.id.replace('clip', '').toLowerCase();

switch (property) {
    case 'name':
        item.name = e.target.value;
        break;
    case 'starttime':
        item.startTime = parseFloat(e.target.value);
        break;
    case 'duration':
        item.duration = parseFloat(e.target.value);
        break;
    case 'volume':
        item.volume = parseFloat(e.target.value);
        break;
    case 'speed':
        item.speed = parseFloat(e.target.value);
        break;
}

// 更新時間軸
timeline.drawTracks();
}

// 預覽媒體
function previewMedia(media) {
const player = document.getElementById('previewPlayer');

// 清除之前的源
while (player.firstChild) {
    player.removeChild(player.firstChild);
}

if (media.type === 'video') {
    // 視頻預覽
    player.src = media.url;
    player.controls = true;
    player.play();
} else if (media.type === 'audio') {
    // 音頻預覽
    player.src = media.url;
    player.controls = true;
    player.play();
} else if (media.type === 'image') {
    // 圖片預覽
    player.style.display = 'none';
    
    // 創建臨時圖片預覽
    const imgPreview = document.createElement('img');
    imgPreview.id = 'imagePreview';
    imgPreview.src = media.url;
    imgPreview.style.maxWidth = '100%';
    imgPreview.style.maxHeight = '100%';
    
    const previewWindow = document.getElementById('previewWindow');
    previewWindow.appendChild(imgPreview);
}
}

// 添加文字到時間軸
function addTextToTimeline() {
const textContent = document.getElementById('textContent').value;
if (!textContent) {
    alert('請輸入文字內容');
    return;
}

// 獲取字幕軌道
const subtitleTrack = activeProject.tracks.find(t => t.id === 'subtitleTrack');
if (!subtitleTrack) return;

// 獲取文字設置
const font = document.getElementById('textFont').value;
const fontSize = document.getElementById('textSize').value;
const textColor = document.getElementById('textColor').value;
const textAlign = document.querySelector('input[name="textAlign"]:checked').value;

// 創建文字項目
const textItem = {
    id: `text_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
    name: textContent.substring(0, 20) + (textContent.length > 20 ? '...' : ''),
    type: 'subtitle',
    trackId: 'subtitleTrack',
    startTime: timeline.currentTime,
    duration: 5.0, // 默認 5 秒
    text: textContent,
    font: font,
    fontSize: parseInt(fontSize),
    color: textColor,
    textAlign: textAlign,
    color: textColor // 項目顏色使用文字顏色
};

// 添加到軌道
subtitleTrack.items.push(textItem);

// 更新時間軸
timeline.updateTracks(activeProject.tracks);

// 選擇新添加的項目
timeline.selectItem(textItem);
}

// 應用效果到選中項目
function applyEffectToSelectedItem(effect) {
const item = timeline.selectedItem;
if (!item) {
    alert('請選擇一個項目');
    return;
}

if (item.type !== 'video' && item.type !== 'image') {
    alert('效果只能應用於視頻或圖片');
    return;
}

// 保存操作歷史
timeline.saveHistoryState();

// 設置效果
item.effect = effect;

// 根據效果類型設置參數
if (effect === 'none') {
    delete item.effectParams;
} else if (effect === 'grayscale' || effect === 'sepia' || effect === 'saturate') {
    item.effectParams = { intensity: 1.0 };
}

// 更新時間軸
timeline.drawTracks();
}

// 選擇轉場
let selectedTransition = 'none';
let transitionDuration = 1.0;

function selectTransition(transition) {
selectedTransition = transition;

// 高亮選中的轉場
document.querySelectorAll('.transition-item').forEach(item => {
    if (item.dataset.transition === transition) {
        item.classList.add('selected');
    } else {
        item.classList.remove('selected');
    }
});

// 更新轉場持續時間
transitionDuration = parseFloat(document.getElementById('transitionDuration').value);
}

// 應用轉場到選中項目
function applyTransitionToSelectedItem() {
const item = timeline.selectedItem;
if (!item) {
    alert('請選擇一個項目');
    return;
}

if (item.type !== 'video' && item.type !== 'image') {
    alert('轉場只能應用於視頻或圖片');
    return;
}

// 保存操作歷史
timeline.saveHistoryState();

// 設置轉場
item.transition = selectedTransition;
item.transitionDuration = transitionDuration;

// 更新時間軸
timeline.drawTracks();
}

// 時間軸變化處理
function handleTimelineChange() {
// 顯示當前選中項目的屬性
displaySelectedItemProperties(timeline.selectedItem);

// 更新預覽
updatePreview();
}

// 更新預覽
function updatePreview() {
// 獲取當前時間點的視頻項目
const currentTime = timeline.currentTime;
const videoTrack = activeProject.tracks.find(t => t.id === 'videoTrack');

if (!videoTrack) return;

// 查找當前時間點的項目
const activeItems = videoTrack.items.filter(item => 
    item.startTime <= currentTime && 
    item.startTime + item.duration > currentTime
);

// 如果找到視頻項目，更新預覽
if (activeItems.length > 0) {
    const activeItem = activeItems[0];
    const media = mediaLibrary.find(m => m.id === activeItem.mediaId);
    
    if (media) {
        // 設置視頻源
        const player = document.getElementById('previewPlayer');
        
        // 如果是不同的媒體或沒有源，設置新源
        if (!player.src || !player.src.includes(media.id)) {
            player.src = media.url;
            player.style.display = 'block';
            
            // 移除可能存在的圖片預覽
            const imgPreview = document.getElementById('imagePreview');
            if (imgPreview) imgPreview.remove();
        }
        
        // 計算視頻內部時間點
        const itemTime = currentTime - activeItem.startTime;
        
        // 設置播放位置
        if (Math.abs(player.currentTime - itemTime) > 0.1) {
            player.currentTime = itemTime;
        }
    }
}
}

// 創建新專案
function createNewProject() {
activeProject = {
    name: '未命名專案',
    tracks: [
        { id: 'videoTrack', name: '視頻軌', type: 'video', items: [] },
        { id: 'audioTrack', name: '音訊軌', type: 'audio', items: [] },
        { id: 'subtitleTrack', name: '字幕軌', type: 'subtitle', items: [] }
    ],
    duration: 60
};

// 更新時間軸
timeline.updateTracks(activeProject.tracks);
timeline.setDuration(activeProject.duration);
}

// 保存專案
function saveProject() {
// 創建專案數據
const projectData = {
    name: activeProject.name,
    tracks: activeProject.tracks,
    duration: activeProject.duration,
    mediaLibrary: mediaLibrary
};

// 轉換為 JSON
const jsonData = JSON.stringify(projectData);

// 創建 Blob
const blob = new Blob([jsonData], { type: 'application/json' });

// 創建下載連結
const a = document.createElement('a');
a.href = URL.createObjectURL(blob);
a.download = `${activeProject.name || '未命名專案'}.vedp`;

// 觸發下載
a.click();

// 清理
URL.revokeObjectURL(a.href);
}

// 打開專案
function openProject(file) {
const reader = new FileReader();

reader.onload = function(e) {
    try {
        // 解析專案文件
        const projectData = JSON.parse(e.target.result);
        
        // 設置專案數據
        activeProject = {
            name: projectData.name || '未命名專案',
            tracks: projectData.tracks || [],
            duration: projectData.duration || 60
        };
        
        // 設置媒體庫
        mediaLibrary = projectData.mediaLibrary || [];
        
        // 更新 UI
        updateMediaLibraryUI();
        
        // 更新時間軸
        timeline.updateTracks(activeProject.tracks);
        timeline.setDuration(activeProject.duration);
        
    } catch (error) {
        console.error('打開專案時出錯:', error);
        alert('無法打開專案文件，格式可能不正確。');
    }
};

reader.onerror = function() {
    alert('讀取文件時出錯，請重試。');
};

reader.readAsText(file);
}

// 匯出影片
function exportVideo() {
alert('影片匯出功能尚未實現。在實際應用中，這將需要服務器端處理或使用 WebCodecs API。');

// 隱藏模態框
const modal = bootstrap.Modal.getInstance(document.getElementById('exportVideoModal'));
modal.hide();
}