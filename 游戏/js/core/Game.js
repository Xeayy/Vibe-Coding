class Game {
    constructor() {
        this.version = '1.0.0';
        this.state = 'menu';
        this.currentSceneId = null;
        this.currentStoryNode = null;
        this.isTyping = false;
        this.isAutoMode = false;
        this.isSkipMode = false;
        this.autoTimer = null;
        
        this.config = {
            bgmVolume: 0.7,
            seVolume: 0.8,
            voiceVolume: 1.0,
            textSpeed: 3,
            autoSpeed: 3,
            fullscreen: false
        };
        
        this.init();
    }
    
    init() {
        console.log('樱花之梦 ~ Sakura no Yume v' + this.version);
        console.log('游戏初始化中...');
        
        this.loadConfig();
        this.createSakuraParticles();
    }
    
    loadConfig() {
        const saved = localStorage.getItem('sakura_no_yume_config');
        if (saved) {
            try {
                this.config = { ...this.config, ...JSON.parse(saved) };
            } catch (e) {
                console.error('加载配置失败:', e);
            }
        }
    }
    
    saveConfig() {
        localStorage.setItem('sakura_no_yume_config', JSON.stringify(this.config));
    }
    
    createSakuraParticles() {
        const container = document.querySelector('.sakura-particles');
        if (!container) return;
        
        for (let i = 0; i < 20; i++) {
            setTimeout(() => {
                this.createParticle(container);
            }, i * 500);
        }
    }
    
    createParticle(container) {
        const particle = document.createElement('div');
        particle.className = 'sakura-particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = (5 + Math.random() * 5) + 's';
        particle.style.animationDelay = Math.random() * 2 + 's';
        container.appendChild(particle);
        
        setTimeout(() => {
            particle.remove();
            this.createParticle(container);
        }, 10000);
    }
    
    start() {
        console.log('========================================');
        console.log('🎮 游戏开始!');
        console.log('========================================');
        this.state = 'playing';
        this.currentStoryNode = 'start';
        this.isAutoMode = false;
        this.isSkipMode = false;
        
        console.log('切换到游戏界面...');
        this.showScreen('game-screen');
        
        console.log('等待 100ms 后开始执行故事...');
        setTimeout(() => {
            console.log('开始执行故事...');
            this.nextStory();
        }, 100);
    }
    
    nextStory() {
        console.log('========================================');
        console.log('📖 nextStory 被调用, 当前节点:', this.currentStoryNode);
        console.log('========================================');
        
        if (!this.currentStoryNode) {
            console.error('❌ 没有当前故事节点!');
            return;
        }
        
        const node = STORY[this.currentStoryNode];
        if (!node) {
            console.error('❌ 找不到故事节点:', this.currentStoryNode);
            return;
        }
        
        console.log('✅ 处理节点:', node.id);
        console.log('   - 有 scene?', !!node.scene);
        console.log('   - 有 characters?', !!node.characters);
        console.log('   - 有 choices?', !!node.choices);
        console.log('   - 有 dialogue?', !!node.dialogue);
        console.log('   - 有 next?', !!node.next);
        console.log('   - 有 ending?', !!node.ending);
        
        if (node.ending) {
            console.log('🎬 显示结局');
            this.showEnding(node.ending);
            return;
        }
        
        if (node.scene) {
            console.log('🖼️ 切换场景:', node.scene);
            SceneManager.changeScene(node.scene);
        }
        
        if (node.characters) {
            console.log('👥 更新角色:', node.characters.length, '个角色');
            CharacterManager.updateCharacters(node.characters);
        }
        
        if (node.choices) {
            console.log('🎯 显示选择:', node.choices.length, '个选项');
            UIManager.showChoices(node.choices);
            console.log('⏸️  停止在选择节点，等待用户选择');
            return;
        }
        
        if (node.dialogue) {
            console.log('💬 显示对话');
            DialogueSystem.showDialogue(node.dialogue);
            if (node.next) {
                console.log('⏳ 对话显示完成后将移动到:', node.next);
            }
            console.log('⏸️  停止在对话节点，等待用户点击继续');
            return;
        }
        
        if (node.next) {
            console.log('➡️ 移动到下一个节点:', node.next);
            this.currentStoryNode = node.next;
            console.log('🔄 递归调用 nextStory()');
            this.nextStory();
        } else {
            console.log('⚠️  此节点没有 next，停止');
        }
    }
    
    makeChoice(choice) {
        if (choice.affinity) {
            AffinitySystem.modifyAffinity(choice.affinity);
        }
        this.currentStoryNode = choice.next;
        UIManager.hideChoices();
        this.nextStory();
    }
    
    continue() {
        if (this.isTyping) {
            DialogueSystem.skipTyping();
            return;
        }
        
        if (this.currentStoryNode) {
            const currentNode = STORY[this.currentStoryNode];
            if (currentNode && currentNode.next) {
                console.log('🔄 从 continue() 移动到:', currentNode.next);
                this.currentStoryNode = currentNode.next;
                this.nextStory();
            }
        }
    }
    
    toggleAutoMode() {
        this.isAutoMode = !this.isAutoMode;
        if (this.isAutoMode) {
            this.startAutoMode();
        } else {
            this.stopAutoMode();
        }
    }
    
    startAutoMode() {
        const autoSpeeds = [5000, 4000, 3000, 2000, 1000];
        const delay = autoSpeeds[this.config.autoSpeed - 1];
        
        this.autoTimer = setTimeout(() => {
            if (this.isAutoMode && !this.isTyping && this.state === 'playing') {
                this.continue();
            }
        }, delay);
    }
    
    stopAutoMode() {
        if (this.autoTimer) {
            clearTimeout(this.autoTimer);
            this.autoTimer = null;
        }
    }
    
    toggleSkipMode() {
        this.isSkipMode = !this.isSkipMode;
    }
    
    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });
        document.getElementById(screenId).classList.add('active');
    }
    
    showEnding(ending) {
        this.state = 'ending';
        this.stopAutoMode();
        
        document.getElementById('ending-title').textContent = ending.title;
        document.getElementById('ending-text').textContent = ending.text;
        
        this.showScreen('ending-screen');
    }
    
    returnToMenu() {
        this.state = 'menu';
        this.currentStoryNode = null;
        this.stopAutoMode();
        this.isAutoMode = false;
        this.isSkipMode = false;
        
        SceneManager.clear();
        CharacterManager.clear();
        DialogueSystem.clear();
        AffinitySystem.reset();
        
        this.showScreen('main-menu');
    }
    
    getTextSpeed() {
        const speeds = [100, 70, 50, 30, 15];
        return speeds[this.config.textSpeed - 1];
    }
}

let game;
