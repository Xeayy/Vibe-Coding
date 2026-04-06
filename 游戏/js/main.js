window.onerror = function(message, source, lineno, colno, error) {
    console.error('❌ 全局错误:', message, '在', source, '行', lineno);
    if (error) {
        console.error('错误堆栈:', error.stack);
    }
    return false;
};

window.addEventListener('unhandledrejection', function(event) {
    console.error('❌ 未处理的 Promise 拒绝:', event.reason);
});

document.addEventListener('DOMContentLoaded', () => {
    console.log('====================================');
    console.log('🌸 樱花之梦 ~ Sakura no Yume 🌸');
    console.log('====================================');
    console.log('开始初始化游戏...');
    
    try {
        console.log('1. 创建 Game 实例...');
        game = new Game();
        console.log('✓ Game 实例创建成功');
        
        console.log('2. 初始化 AudioSystem...');
        AudioSystem.init();
        console.log('✓ AudioSystem 初始化成功');
        
        console.log('3. 初始化 UIManager...');
        UIManager.init();
        console.log('✓ UIManager 初始化成功');
        
        console.log('====================================');
        console.log('✅ 游戏加载完成！准备就绪！');
        console.log('====================================');
    } catch (e) {
        console.error('❌ 初始化失败:', e);
        console.error('堆栈:', e.stack);
        alert('游戏初始化失败，请查看控制台了解详情。');
    }
});
