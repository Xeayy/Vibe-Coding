class AffinitySystem {
    static init() {
        Object.values(CHARACTERS).forEach(char => {
            char.affinity = 0;
        });
        this.updateDisplay();
    }
    
    static modifyAffinity(affinityData) {
        Object.keys(affinityData).forEach(charId => {
            const char = CHARACTERS[charId];
            if (char) {
                char.affinity = Math.max(0, Math.min(char.maxAffinity, char.affinity + affinityData[charId]));
                
                if (affinityData[charId] > 0) {
                    this.showAffinityChange(charId, '+' + affinityData[charId]);
                } else if (affinityData[charId] < 0) {
                    this.showAffinityChange(charId, affinityData[charId]);
                }
            }
        });
        this.updateDisplay();
    }
    
    static setAffinity(charId, value) {
        const char = CHARACTERS[charId];
        if (char) {
            char.affinity = Math.max(0, Math.min(char.maxAffinity, value));
            this.updateDisplay();
        }
    }
    
    static getAffinity(charId) {
        const char = CHARACTERS[charId];
        return char ? char.affinity : 0;
    }
    
    static updateDisplay() {
        const container = document.getElementById('affinity-display');
        if (!container) return;
        
        let html = '<h4>💖 好感度</h4>';
        
        Object.values(CHARACTERS).forEach(char => {
            if (char.affinity > 0 || char.affinity < 0) {
                const percentage = (char.affinity / char.maxAffinity) * 100;
                html += `
                    <div class="affinity-item">
                        <span class="affinity-name">${char.name}</span>
                        <div class="affinity-bar">
                            <div class="affinity-fill" style="width: ${percentage}%"></div>
                        </div>
                        <span class="affinity-value">${char.affinity}</span>
                    </div>
                `;
            }
        });
        
        container.innerHTML = html;
    }
    
    static showAffinityChange(charId, change) {
        const char = CHARACTERS[charId];
        if (!char) return;
        
        const container = document.getElementById('affinity-display');
        const popup = document.createElement('div');
        popup.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 183, 197, 0.9);
            color: #fff;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1.5rem;
            font-weight: bold;
            animation: affinityPopup 1.5s ease-out forwards;
            z-index: 1000;
        `;
        popup.textContent = `${char.name} ${change}`;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes affinityPopup {
                0% { opacity: 0; transform: translate(-50%, -30%); }
                20% { opacity: 1; transform: translate(-50%, -50%); }
                80% { opacity: 1; transform: translate(-50%, -50%); }
                100% { opacity: 0; transform: translate(-50%, -70%); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(popup);
        setTimeout(() => {
            popup.remove();
            style.remove();
        }, 1500);
    }
    
    static reset() {
        Object.values(CHARACTERS).forEach(char => {
            char.affinity = 0;
        });
        const container = document.getElementById('affinity-display');
        if (container) {
            container.innerHTML = '';
        }
    }
    
    static getAllAffinities() {
        const data = {};
        Object.values(CHARACTERS).forEach(char => {
            data[char.id] = char.affinity;
        });
        return data;
    }
    
    static loadAllAffinities(data) {
        Object.keys(data).forEach(charId => {
            const char = CHARACTERS[charId];
            if (char) {
                char.affinity = data[charId];
            }
        });
        this.updateDisplay();
    }
}
