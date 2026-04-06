class SaveSystem {
    static SAVE_KEY = 'sakura_no_yume_save';
    static MAX_SLOTS = 9;
    
    static getAllSaves() {
        const saves = localStorage.getItem(this.SAVE_KEY);
        return saves ? JSON.parse(saves) : {};
    }
    
    static save(slotIndex) {
        const saves = this.getAllSaves();
        
        const saveData = {
            version: game.version,
            timestamp: Date.now(),
            currentStoryNode: game.currentStoryNode,
            affinities: AffinitySystem.getAllAffinities(),
            config: { ...game.config },
            currentScene: SceneManager.currentScene?.id,
            currentCharacters: CharacterManager.currentCharacters.map(c => ({
                id: c.id,
                expression: c.currentExpression
            }))
        };
        
        saves[slotIndex] = saveData;
        localStorage.setItem(this.SAVE_KEY, JSON.stringify(saves));
        
        return true;
    }
    
    static load(slotIndex) {
        const saves = this.getAllSaves();
        const saveData = saves[slotIndex];
        
        if (!saveData) {
            return false;
        }
        
        if (saveData.config) {
            game.config = { ...game.config, ...saveData.config };
        }
        
        if (saveData.affinities) {
            AffinitySystem.loadAllAffinities(saveData.affinities);
        }
        
        game.currentStoryNode = saveData.currentStoryNode;
        game.state = 'playing';
        
        game.showScreen('game-screen');
        game.nextStory();
        
        return true;
    }
    
    static hasSave(slotIndex) {
        const saves = this.getAllSaves();
        return !!saves[slotIndex];
    }
    
    static getSaveInfo(slotIndex) {
        const saves = this.getAllSaves();
        return saves[slotIndex] || null;
    }
    
    static deleteSave(slotIndex) {
        const saves = this.getAllSaves();
        delete saves[slotIndex];
        localStorage.setItem(this.SAVE_KEY, JSON.stringify(saves));
    }
    
    static quickSave() {
        return this.save(0);
    }
    
    static quickLoad() {
        return this.load(0);
    }
}
