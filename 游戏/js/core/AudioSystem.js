class AudioSystem {
    static bgmAudio = null;
    static currentBGM = null;
    static audioCache = {};
    
    static BGM_LIST = {
        title: { name: '标题音乐', loop: true },
        school_days: { name: '校园日常', loop: true },
        peaceful_days: { name: '和平的一天', loop: true },
        cherry_blossom: { name: '樱花', loop: true },
        quiet_moment: { name: '宁静的时刻', loop: true },
        music_room: { name: '音乐教室', loop: true },
        sports_day: { name: '运动日', loop: true },
        lunch_time: { name: '午餐时间', loop: true },
        everyday_life: { name: '日常生活', loop: true },
        sunset: { name: '夕阳', loop: true },
        night_time: { name: '夜晚', loop: true },
        shrine: { name: '神社', loop: true },
        summer_vacation: { name: '暑假', loop: true },
        festival: { name: '祭典', loop: true },
        mystery: { name: '神秘', loop: true },
        tension: { name: '紧张', loop: true },
        emotional: { name: '感伤', loop: true },
        happy: { name: '快乐', loop: true },
        romantic: { name: '浪漫', loop: true },
        sad: { name: '悲伤', loop: true }
    };
    
    static SE_LIST = {
        click: '点击',
        confirm: '确认',
        cancel: '取消',
        page: '翻页',
        affinity_up: '好感度上升',
        affinity_down: '好感度下降'
    };
    
    static init() {
        this.bgmAudio = new Audio();
        this.bgmAudio.loop = true;
    }
    
    static playBGM(bgmId) {
        if (this.currentBGM === bgmId) return;
        
        this.currentBGM = bgmId;
        
        this.bgmAudio.volume = game.config.bgmVolume;
        this.bgmAudio.play().catch(e => {
            console.log('音频播放需要用户交互');
        });
    }
    
    static stopBGM() {
        if (this.bgmAudio) {
            this.bgmAudio.pause();
            this.bgmAudio.currentTime = 0;
        }
        this.currentBGM = null;
    }
    
    static setBGMVolume(volume) {
        game.config.bgmVolume = volume;
        if (this.bgmAudio) {
            this.bgmAudio.volume = volume;
        }
    }
    
    static playSE(seId) {
        console.log('播放音效:', seId);
    }
    
    static setSEVolume(volume) {
        game.config.seVolume = volume;
    }
    
    static playVoice(voiceId) {
        console.log('播放语音:', voiceId);
    }
    
    static setVoiceVolume(volume) {
        game.config.voiceVolume = volume;
    }
}
