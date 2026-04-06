class UIManager {
    static isUIHidden = false;
    
    static init() {
        console.log('UIManager 初始化中...');
        this.bindEvents();
        console.log('UIManager 初始化完成');
    }
    
    static safeAddEventListener(id, event, callback) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, callback);
            console.log('✓ 已绑定事件: ' + id);
        } else {
            console.warn('⚠ 找不到元素: ' + id);
        }
    }
    
    static bindEvents() {
        console.log('开始绑定事件...');
        
        this.safeAddEventListener('btn-start', 'click', () => {
            console.log('点击了开始游戏按钮');
            AudioSystem.playSE('click');
            AffinitySystem.init();
            game.start();
        });
        
        this.safeAddEventListener('btn-load', 'click', () => {
            console.log('点击了读取存档按钮');
            AudioSystem.playSE('click');
            this.showSaveLoadScreen(false);
        });
        
        this.safeAddEventListener('btn-config', 'click', () => {
            console.log('点击了设置按钮');
            AudioSystem.playSE('click');
            this.showConfigScreen();
        });
        
        this.safeAddEventListener('btn-gallery', 'click', () => {
            console.log('点击了剧情回顾按钮');
            AudioSystem.playSE('click');
            this.showGalleryScreen();
        });
        
        this.safeAddEventListener('btn-save', 'click', () => {
            AudioSystem.playSE('click');
            this.showSaveLoadScreen(true);
        });
        
        this.safeAddEventListener('btn-skip', 'click', () => {
            AudioSystem.playSE('click');
            game.toggleSkipMode();
            const btn = document.getElementById('btn-skip');
            if (btn) btn.classList.toggle('active', game.isSkipMode);
        });
        
        this.safeAddEventListener('btn-auto', 'click', () => {
            AudioSystem.playSE('click');
            game.toggleAutoMode();
            const btn = document.getElementById('btn-auto');
            if (btn) btn.classList.toggle('active', game.isAutoMode);
        });
        
        this.safeAddEventListener('btn-hide', 'click', () => {
            AudioSystem.playSE('click');
            this.toggleUI();
        });
        
        this.safeAddEventListener('btn-menu', 'click', () => {
            AudioSystem.playSE('click');
            if (confirm('确定要返回主菜单吗？当前进度将丢失。')) {
                game.returnToMenu();
            }
        });
        
        this.safeAddEventListener('btn-close-save', 'click', () => {
            AudioSystem.playSE('click');
            this.hideModal('save-load-screen');
        });
        
        this.safeAddEventListener('btn-close-config', 'click', () => {
            AudioSystem.playSE('click');
            game.saveConfig();
            this.hideModal('config-screen');
        });
        
        this.safeAddEventListener('btn-close-gallery', 'click', () => {
            AudioSystem.playSE('click');
            this.hideModal('gallery-screen');
        });
        
        this.safeAddEventListener('btn-return-menu', 'click', () => {
            AudioSystem.playSE('click');
            game.returnToMenu();
        });
        
        this.safeAddEventListener('bgm-volume', 'input', (e) => {
            const value = e.target.value / 100;
            AudioSystem.setBGMVolume(value);
            const valEl = document.getElementById('bgm-value');
            if (valEl) valEl.textContent = e.target.value + '%';
        });
        
        this.safeAddEventListener('se-volume', 'input', (e) => {
            const value = e.target.value / 100;
            AudioSystem.setSEVolume(value);
            const valEl = document.getElementById('se-value');
            if (valEl) valEl.textContent = e.target.value + '%';
        });
        
        this.safeAddEventListener('voice-volume', 'input', (e) => {
            const value = e.target.value / 100;
            AudioSystem.setVoiceVolume(value);
            const valEl = document.getElementById('voice-value');
            if (valEl) valEl.textContent = e.target.value + '%';
        });
        
        this.safeAddEventListener('text-speed', 'input', (e) => {
            game.config.textSpeed = parseInt(e.target.value);
            const speeds = ['极慢', '慢', '中', '快', '极快'];
            const valEl = document.getElementById('text-speed-value');
            if (valEl) valEl.textContent = speeds[game.config.textSpeed - 1];
        });
        
        this.safeAddEventListener('auto-speed', 'input', (e) => {
            game.config.autoSpeed = parseInt(e.target.value);
            const speeds = ['极慢', '慢', '中', '快', '极快'];
            const valEl = document.getElementById('auto-speed-value');
            if (valEl) valEl.textContent = speeds[game.config.autoSpeed - 1];
        });
        
        this.safeAddEventListener('btn-fullscreen', 'click', () => {
            game.config.fullscreen = !game.config.fullscreen;
            if (game.config.fullscreen) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
            const btn = document.getElementById('btn-fullscreen');
            if (btn) {
                btn.classList.toggle('active', game.config.fullscreen);
                btn.textContent = game.config.fullscreen ? '开' : '关';
            }
        });
        
        this.safeAddEventListener('text-box', 'click', () => {
            if (game.state === 'playing') {
                game.continue();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });
    }
    
    static handleKeyDown(e) {
        if (game.state === 'playing') {
            switch (e.code) {
                case 'Space':
                case 'Enter':
                    e.preventDefault();
                    game.continue();
                    break;
                case 'Escape':
                    game.toggleAutoMode();
                    const btnAuto = document.getElementById('btn-auto');
                    if (btnAuto) {
                        if (game.isAutoMode) {
                            btnAuto.classList.add('active');
                        } else {
                            btnAuto.classList.remove('active');
                        }
                    }
                    break;
                case 'KeyS':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.showSaveLoadScreen(true);
                    }
                    break;
                case 'KeyL':
                    if (e.ctrlKey) {
                        e.preventDefault();
                        this.showSaveLoadScreen(false);
                    }
                    break;
            }
        }
    }
    
    static showChoices(choices) {
        const container = document.getElementById('choice-container');
        if (container) {
            container.innerHTML = '';
            
            choices.forEach((choice, index) => {
                const btn = document.createElement('button');
                btn.className = 'choice-btn';
                btn.textContent = choice.text;
                btn.addEventListener('click', () => {
                    AudioSystem.playSE('confirm');
                    game.makeChoice(choice);
                });
                container.appendChild(btn);
            });
        }
    }
    
    static hideChoices() {
        const container = document.getElementById('choice-container');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    static showSaveLoadScreen(isSave) {
        const container = document.getElementById('save-slots');
        if (!container) return;
        container.innerHTML = '';
        
        for (let i = 0; i < SaveSystem.MAX_SLOTS; i++) {
            const slot = document.createElement('div');
            slot.className = 'save-slot';
            
            const saveInfo = SaveSystem.getSaveInfo(i);
            
            if (saveInfo) {
                slot.innerHTML = `
                    <div class="slot-number">存档 ${i + 1}</div>
                    <div class="slot-date">${new Date(saveInfo.timestamp).toLocaleString('zh-CN')}</div>
                    <div class="slot-preview">${saveInfo.currentStoryNode || '游戏中'}</div>
                `;
            } else {
                slot.classList.add('empty');
                slot.innerHTML = `
                    <div class="slot-number">存档 ${i + 1}</div>
                    <div class="slot-date">空</div>
                `;
            }
            
            slot.addEventListener('click', () => {
                if (isSave) {
                    SaveSystem.save(i);
                    AudioSystem.playSE('confirm');
                    this.hideModal('save-load-screen');
                } else if (saveInfo) {
                    SaveSystem.load(i);
                    AudioSystem.playSE('confirm');
                    this.hideModal('save-load-screen');
                }
            });
            
            container.appendChild(slot);
        }
        
        const title = document.querySelector('#save-load-screen h2');
        if (title) {
            title.textContent = isSave ? '保存游戏' : '读取存档';
        }
        this.showModal('save-load-screen');
    }
    
    static showConfigScreen() {
        console.log('显示设置界面');
        this.updateConfigUI();
        this.showModal('config-screen');
    }
    
    static updateConfigUI() {
        const bgmVolume = document.getElementById('bgm-volume');
        const bgmValue = document.getElementById('bgm-value');
        if (bgmVolume) bgmVolume.value = game.config.bgmVolume * 100;
        if (bgmValue) bgmValue.textContent = Math.round(game.config.bgmVolume * 100) + '%';
        
        const seVolume = document.getElementById('se-volume');
        const seValue = document.getElementById('se-value');
        if (seVolume) seVolume.value = game.config.seVolume * 100;
        if (seValue) seValue.textContent = Math.round(game.config.seVolume * 100) + '%';
        
        const voiceVolume = document.getElementById('voice-volume');
        const voiceValue = document.getElementById('voice-value');
        if (voiceVolume) voiceVolume.value = game.config.voiceVolume * 100;
        if (voiceValue) voiceValue.textContent = Math.round(game.config.voiceVolume * 100) + '%';
        
        const textSpeed = document.getElementById('text-speed');
        const textSpeedValue = document.getElementById('text-speed-value');
        const textSpeeds = ['极慢', '慢', '中', '快', '极快'];
        if (textSpeed) textSpeed.value = game.config.textSpeed;
        if (textSpeedValue) textSpeedValue.textContent = textSpeeds[game.config.textSpeed - 1];
        
        const autoSpeed = document.getElementById('auto-speed');
        const autoSpeedValue = document.getElementById('auto-speed-value');
        if (autoSpeed) autoSpeed.value = game.config.autoSpeed;
        if (autoSpeedValue) autoSpeedValue.textContent = textSpeeds[game.config.autoSpeed - 1];
        
        const btnFullscreen = document.getElementById('btn-fullscreen');
        if (btnFullscreen) {
            btnFullscreen.classList.toggle('active', game.config.fullscreen);
            btnFullscreen.textContent = game.config.fullscreen ? '开' : '关';
        }
    }
    
    static showGalleryScreen() {
        const container = document.getElementById('gallery-content');
        if (container) {
            container.innerHTML = '';
            
            const cgs = [];
            cgs.forEach((cg, index) => {
                const item = document.createElement('div');
                item.className = 'gallery-item' + (cg.unlocked ? ' unlocked' : '');
                if (cg.unlocked && cg.image) {
                    item.style.backgroundImage = `url('${cg.image}')`;
                } else {
                    item.textContent = '???';
                }
                container.appendChild(item);
            });
            
            if (cgs.length === 0) {
                container.innerHTML = '<p style="color: rgba(255,255,255,0.5); text-align: center; grid-column: 1/-1;">暂无可解锁内容</p>';
            }
        }
        
        this.showModal('gallery-screen');
    }
    
    static showModal(screenId) {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.add('active');
        }
    }
    
    static hideModal(screenId) {
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.remove('active');
        }
    }
    
    static toggleUI() {
        this.isUIHidden = !this.isUIHidden;
        const uiLayer = document.getElementById('ui-layer');
        if (uiLayer) {
            if (this.isUIHidden) {
                uiLayer.style.opacity = '0';
                uiLayer.style.pointerEvents = 'none';
            } else {
                uiLayer.style.opacity = '1';
                uiLayer.style.pointerEvents = 'auto';
            }
        }
    }
}
