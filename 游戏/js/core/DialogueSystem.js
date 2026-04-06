class DialogueSystem {
    static dialogueElement = null;
    static speakerElement = null;
    static currentText = '';
    static displayIndex = 0;
    static typingInterval = null;
    
    static init() {
        console.log('💬 DialogueSystem: 初始化');
        this.dialogueElement = document.getElementById('dialogue-text');
        this.speakerElement = document.getElementById('speaker-name');
        if (!this.dialogueElement) {
            console.error('❌ DialogueSystem: 找不到 dialogue-text 元素');
        }
        if (!this.speakerElement) {
            console.error('❌ DialogueSystem: 找不到 speaker-name 元素');
        }
    }
    
    static showDialogue(dialogue) {
        console.log('💬 DialogueSystem: 显示对话');
        
        if (!this.dialogueElement || !this.speakerElement) {
            this.init();
        }
        
        if (!this.dialogueElement || !this.speakerElement) {
            console.error('❌ DialogueSystem: 元素初始化失败');
            return;
        }
        
        if (game.isAutoMode) {
            game.stopAutoMode();
        }
        
        if (dialogue.speaker && CHARACTERS[dialogue.speaker]) {
            this.speakerElement.textContent = CHARACTERS[dialogue.speaker].name;
            this.speakerElement.style.display = 'block';
        } else {
            this.speakerElement.style.display = 'none';
        }
        
        this.currentText = dialogue.text;
        this.displayIndex = 0;
        this.dialogueElement.innerHTML = '';
        game.isTyping = true;
        
        if (game.isSkipMode) {
            this.skipTyping();
            return;
        }
        
        this.startTyping();
        console.log('✓ DialogueSystem: 对话开始显示');
    }
    
    static startTyping() {
        const speed = game.getTextSpeed();
        
        this.typingInterval = setInterval(() => {
            if (this.displayIndex < this.currentText.length) {
                const char = this.currentText[this.displayIndex];
                this.displayIndex++;
                
                let displayText = this.currentText.substring(0, this.displayIndex);
                displayText = displayText.replace(/\n/g, '<br>');
                
                if (this.dialogueElement) {
                    this.dialogueElement.innerHTML = displayText + '<span class="typing-cursor">▋</span>';
                }
            } else {
                this.finishTyping();
            }
        }, speed);
    }
    
    static skipTyping() {
        if (this.typingInterval) {
            clearInterval(this.typingInterval);
        }
        
        if (this.dialogueElement) {
            let displayText = this.currentText.replace(/\n/g, '<br>');
            this.dialogueElement.innerHTML = displayText;
        }
        this.displayIndex = this.currentText.length;
        this.finishTyping();
    }
    
    static finishTyping() {
        if (this.typingInterval) {
            clearInterval(this.typingInterval);
            this.typingInterval = null;
        }
        
        game.isTyping = false;
        console.log('✓ DialogueSystem: 对话显示完成');
        
        if (game.isAutoMode) {
            game.startAutoMode();
        }
    }
    
    static clear() {
        if (this.typingInterval) {
            clearInterval(this.typingInterval);
        }
        
        if (this.dialogueElement) {
            this.dialogueElement.innerHTML = '';
        }
        if (this.speakerElement) {
            this.speakerElement.textContent = '';
            this.speakerElement.style.display = 'none';
        }
        
        this.currentText = '';
        this.displayIndex = 0;
        game.isTyping = false;
    }
}
