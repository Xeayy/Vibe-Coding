# 樱花之梦 ~ 故障排除指南

## 问题：点击"开始游戏"按钮后只显示"返回主菜单"

### 🔍 问题分析与解决方案

#### 1. 检查浏览器控制台（最重要！）

**步骤：**
1. 在浏览器中按 `F12` 打开开发者工具
2. 点击 "Console"（控制台）标签
3. 刷新页面（按 `F5`）
4. 查看是否有红色错误信息

**应该看到的日志：**
```
====================================
🌸 樱花之梦 ~ Sakura no Yume 🌸
====================================
开始初始化游戏...
1. 创建 Game 实例...
✓ Game 实例创建成功
2. 初始化 AudioSystem...
✓ AudioSystem 初始化成功
3. 初始化 UIManager...
UIManager 初始化中...
开始绑定事件...
✓ 已绑定事件: btn-start
✓ 已绑定事件: btn-load
...
UIManager 初始化完成
✓ UIManager 初始化成功
====================================
✅ 游戏加载完成！准备就绪！
====================================
```

#### 2. 使用调试页面

我已经创建了一个专门的调试页面来帮助诊断问题：

**访问：** `http://localhost:8080/debug.html`

**使用步骤：**
1. 打开调试页面
2. 点击 "测试文件加载" 按钮
3. 观察日志，确认所有文件都能正确加载
4. 点击 "检查数据" 按钮
5. 确认 CHARACTERS、SCENES、STORY 都已正确定义
6. 点击 "测试游戏启动" 按钮

#### 3. 我已修复的问题

**问题 1：重复的事件绑定**
- 原来的代码中，有些按钮 ID 被绑定了多次
- 已修复：使用 `safeAddEventListener` 方法，安全地绑定事件

**问题 2：缺少元素检查**
- 原来的代码直接访问元素，没有检查是否存在
- 已修复：添加了元素存在性检查，避免错误

**问题 3：缺少调试日志**
- 原来的代码没有足够的日志来诊断问题
- 已修复：添加了详细的 console.log 输出

**问题 4：缺少全局错误处理**
- 原来的代码没有全局错误捕获
- 已修复：添加了 window.onerror 和 unhandledrejection 处理

#### 4. 常见问题及解决方案

**问题 A：文件加载顺序错误**
- **症状**：控制台显示 "CHARACTERS is not defined"
- **原因**：JavaScript 文件加载顺序不对
- **解决**：确认 index.html 中的 script 标签顺序正确：
  ```html
  <script src="js/core/Game.js"></script>
  <script src="js/core/SceneManager.js"></script>
  <script src="js/core/DialogueSystem.js"></script>
  <script src="js/core/CharacterManager.js"></script>
  <script src="js/core/AffinitySystem.js"></script>
  <script src="js/core/SaveSystem.js"></script>
  <script src="js/core/AudioSystem.js"></script>
  <script src="js/core/UIManager.js"></script>
  <script src="js/data/Characters.js"></script>
  <script src="js/data/Scenes.js"></script>
  <script src="js/data/Story.js"></script>
  <script src="js/main.js"></script>
  ```

**问题 B：缓存问题**
- **症状**：修改代码后没有效果
- **解决**：
  1. 按 `Ctrl + Shift + R`（Windows）或 `Cmd + Shift + R`（Mac）强制刷新
  2. 或者在开发者工具中勾选 "Disable cache"

**问题 C：服务器问题**
- **症状**：页面无法加载
- **解决**：确认 Python HTTP 服务器正在运行
  - 检查终端是否显示：`Serving HTTP on :: port 8080`
  - 如果没有，重新运行：`python -m http.server 8080`

**问题 D：CSS 显示问题**
- **症状**：界面显示不正常
- **解决**：
  1. 确认 `css/style.css` 文件存在
  2. 检查 index.html 中的 link 标签：
     ```html
     <link rel="stylesheet" href="css/style.css">
     ```

#### 5. 测试游戏流程

1. **打开主页面**：`http://localhost:8080`
2. **打开控制台**：按 `F12`
3. **点击"开始游戏"按钮**
4. **观察控制台日志**，应该看到：
   ```
   点击了开始游戏按钮
   🎮 游戏开始!
   切换到游戏界面...
   开始执行故事...
   📖 nextStory 被调用, 当前节点: start
   ✅ 处理节点: start
   ➡️ 下一个节点: prologue_1
   ```
5. **观察游戏界面**：应该能看到樱花公园的背景，并且出现对话文本

#### 6. 如果问题仍然存在

请提供以下信息：
1. 浏览器控制台的完整截图
2. 你使用的浏览器（Chrome、Firefox、Edge 等）
3. 调试页面的测试结果

---

## 📋 已实现的功能清单

✅ 完整的视觉小说引擎
✅ 5名可攻略角色（樱井雪、美咲绫、冰室玲奈、星野唯、月影雫）
✅ 每个角色6种表情立绘
✅ 15个精美场景
✅ 剧情分支系统
✅ 好感度系统
✅ 存档/读档系统（9个存档位）
✅ 自动模式和跳过模式
✅ 文本速度调节
✅ 音量设置
✅ 全屏模式
✅ 键盘快捷键支持
✅ 详细的调试日志

---

## 🎯 下一步

游戏现在已经包含完整的调试功能！请：

1. 刷新游戏页面（按 `Ctrl + Shift + R`）
2. 打开浏览器控制台（按 `F12`）
3. 点击"开始游戏"按钮
4. 观察控制台日志，告诉我你看到了什么！
