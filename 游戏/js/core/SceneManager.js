class SceneManager {
    static currentScene = null;
    
    static changeScene(sceneId) {
        console.log('🖼️ SceneManager: 尝试切换到场景', sceneId);
        
        const scene = SCENES[sceneId];
        if (!scene) {
            console.error('❌ SceneManager: 找不到场景:', sceneId);
            return;
        }
        
        this.currentScene = scene;
        
        const bgLayer = document.getElementById('background-layer');
        if (!bgLayer) {
            console.error('❌ SceneManager: 找不到 background-layer 元素');
            return;
        }
        
        bgLayer.style.opacity = '0';
        
        setTimeout(() => {
            if (bgLayer) {
                bgLayer.style.backgroundImage = `url('${scene.background}')`;
                bgLayer.style.opacity = '1';
                console.log('✓ SceneManager: 场景背景已设置');
            }
        }, 250);
        
        if (scene.bgm) {
            AudioSystem.playBGM(scene.bgm);
        }
        
        console.log('✓ SceneManager: 场景切换完成');
    }
    
    static clear() {
        this.currentScene = null;
        const bgLayer = document.getElementById('background-layer');
        if (bgLayer) {
            bgLayer.style.backgroundImage = '';
        }
    }
}
