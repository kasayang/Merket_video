// 影音效果模組（添加到新檔案 media-effects.js）
class MediaEffects {
    constructor(options) {
        this.timeline = options.timeline;
        this.previewController = options.previewController;
        
        this.availableVideoFilters = [
            {id: 'grayscale', name: '灰階', preview: 'filter: grayscale(1)'},
            {id: 'sepia', name: '復古', preview: 'filter: sepia(1)'},
            {id: 'brightness', name: '亮度增強', preview: 'filter: brightness(1.5)'},
            // 更多濾鏡
        ];
        
        this.availableTransitions = [
            {id: 'fade', name: '淡入淡出'},
            {id: 'wipe', name: '擦除'},
            {id: 'slide', name: '滑動'},
            // 更多轉場
        ];
        
        this.init();
    }
    
    init() {
        this.createFilterGallery();
        this.createTransitionGallery();
        this.bindEvents();
    }
    
    // 應用濾鏡到所選項目
    applyFilter(itemId, filterId) {
        const item = this.timeline.getItemById(itemId);
        if (item && (item.type === 'video' || item.type === 'image')) {
            item.filter = filterId;
            this.timeline.updateItem(item);
            this.previewController.updatePreview();
        }
    }
    
    // 應用轉場效果
    applyTransition(itemId, transitionId) {
        const item = this.timeline.getItemById(itemId);
        if (item) {
            item.transition = transitionId;
            this.timeline.updateItem(item);
        }
    }
}