// 文字編輯器模組（添加到新檔案 text-editor.js）
class TextEditor {
    constructor(options) {
        this.container = options.container;
        this.timeline = options.timeline;
        this.init();
    }
    
    init() {
        this.createFontControls();
        this.createAnimationControls();
        this.bindEvents();
    }
    
    // 創建字體控制項
    createFontControls() {
        // 字體、大小、顏色等控制項
    }
    
    // 創建動畫控制項
    createAnimationControls() {
        // 動畫效果選擇控制項
    }
    
    // 將文字添加到時間軸
    addTextToTimeline(textConfig) {
        this.timeline.addItem('textTrack', {
            id: `text_${Date.now()}`,
            name: textConfig.text.substring(0, 15) + '...',
            type: 'text',
            startTime: this.timeline.currentTime,
            duration: 5.0,
            text: textConfig.text,
            font: textConfig.font,
            fontSize: textConfig.fontSize,
            color: textConfig.color,
            animation: textConfig.animation
        });
    }
}