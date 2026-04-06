class CharacterManager {
    static currentCharacters = [];
    
    static updateCharacters(characters) {
        console.log('👥 CharacterManager: 更新角色', characters.length, '个');
        
        const charLayer = document.getElementById('character-layer');
        if (!charLayer) {
            console.error('❌ CharacterManager: 找不到 character-layer 元素');
            return;
        }
        
        charLayer.querySelectorAll('.character').forEach(el => {
            el.classList.remove('visible');
            setTimeout(() => {
                if (el && el.parentNode) {
                    el.remove();
                }
            }, 500);
        });
        
        this.currentCharacters = [];
        
        characters.forEach(charData => {
            const char = CHARACTERS[charData.id];
            if (!char) {
                console.error('❌ CharacterManager: 找不到角色:', charData.id);
                return;
            }
            
            char.currentExpression = charData.expression || 'normal';
            this.currentCharacters.push(char);
            
            const charEl = document.createElement('div');
            charEl.className = `character ${charData.position} visible`;
            charEl.id = `char-${char.id}`;
            
            const img = document.createElement('img');
            img.src = char.expressions[char.currentExpression];
            img.alt = char.name;
            img.style.maxHeight = '100%';
            img.style.maxWidth = '100%';
            
            charEl.appendChild(img);
            charLayer.appendChild(charEl);
        });
        
        console.log('✓ CharacterManager: 角色更新完成');
    }
    
    static updateExpression(charId, expression) {
        const char = CHARACTERS[charId];
        if (!char) return;
        
        char.currentExpression = expression;
        const charEl = document.getElementById(`char-${charId}`);
        if (charEl) {
            const img = charEl.querySelector('img');
            if (img) {
                img.src = char.expressions[expression];
            }
        }
    }
    
    static clear() {
        const charLayer = document.getElementById('character-layer');
        if (charLayer) {
            charLayer.innerHTML = '';
        }
        this.currentCharacters = [];
        
        Object.values(CHARACTERS).forEach(char => {
            char.currentExpression = 'normal';
        });
    }
}
