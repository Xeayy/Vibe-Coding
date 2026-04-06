const STORAGE_KEY = "lingjing_chat_state_v2";
const OPENING_TEXT = "喵～ 我是灵境占卜师。说出你的困惑（学业、生活、情感），我会用学科思维为你占卜。";

const subjects = [
  {
    id: "math",
    name: "数学",
    intro: "用抽象与逻辑把复杂问题转成可求解结构。",
    keywords: ["优化", "概率", "递归", "建模", "博弈"],
    replies: [
      "从数学看，生活中的很多问题可以用优化思想解决。拖延像目标函数未收敛，建议把任务拆成最小步骤，每步只追求局部最优，晚间复盘误差并持续迭代。",
      "概率论提醒我们，坏运气不是常量而是随机波动。建议做一张情绪样本表，每天记录三件小确幸，两周后回看，你会看到正向事件逐步抬升。",
      "递归思想适合处理复杂任务。先定义最小可执行单元，比如先做一道题或先读一页，再递归推进下一层，焦虑会因为路径清晰而明显下降。",
      "鸽巢原理说明当任务数超过可用时间段，拥堵必然发生。建议先做高价值且临近截止项，把低价值任务延后或删除，给日程留缓冲区。",
      "线性代数中的特征向量代表变换下不变方向。学习也有高效方向，建议连续一周记录状态峰值时段，把最难内容固定在该时段完成。",
      "数学建模强调先抽象后求解。迷茫时把问题写成变量、约束和目标，再列出可控行动，模型清晰后决策会比情绪驱动更稳定。",
      "博弈论里的纳什均衡提示，僵局常来自双方都只做局部最优。人际冲突时先提出共同目标，再谈分歧，能把对抗转换为协同。",
      "无穷级数告诉我们微小增量在长期会累积成显著变化。每天进步1%看似不明显，但一学期后差距很大，建议坚持微习惯打卡。",
      "考试压力可看作约束优化：时间、体力、分值权重都有限。建议先做高频高分模块，再做难题突破，用模拟卷检验边际收益。",
      "注意力分散像噪声项过大，主信号被淹没。建议采用25分钟专注块，并把手机放到不可触达处，降低外部干扰方差。",
      "未来迷茫时可用坐标系方法，把兴趣、能力、机会当三轴。每周给一个小项目打分，三周后你会看到方向聚类，而不是原地犹豫。",
      "自律不是情绪问题，而是约束条件设计。建议提前设置默认路径，比如到座位先写三行计划，让行为由流程触发而非意志硬扛。",
      "人际关系里的误解常来自信息不对称。可借鉴方程求解，先确认已知事实再讨论结论，减少凭感觉推导带来的冲突。",
      "刷题效率低时，可用函数单调性思维检查方法是否有效。若投入增加但得分不升，说明策略失效，应立即换题型或换讲解资源。",
      "社交恐惧可做渐进逼近：从一句问候到一分钟交流。像数值迭代一样，每次只加一点步长，稳定收敛比一次性跨越更可靠。"
    ]
  },
  {
    id: "physics",
    name: "物理",
    intro: "用能量、运动与系统规律解释现实变化。",
    keywords: ["熵增", "惯性", "能量守恒", "共振", "杠杆"],
    replies: [
      "熵增定律说明系统若不输入能量会自然走向混乱。房间和日程变乱很正常，建议每天固定5分钟整理桌面和任务清单，持续做功对抗熵增。",
      "惯性定律解释了为何学习启动最难。建议用两分钟启动法，只要求自己先翻开资料并做第一小步，突破静摩擦后持续投入会更容易。",
      "能量守恒提醒精力不会消失，只会转化。焦虑是能量滞留，建议把它转成动作，如快走二十分钟或完成一页任务，心理负担会下降。",
      "热力学第二定律告诉你，陌生知识变熟悉需要外界做功。建议三轮学习：先粗读，再练题，再回读，理解温度会逐步上升。",
      "不确定性原理提示你无法同时追求绝对速度和绝对精度。先完成主干再精修细节，比一开始追求完美更能稳定输出。",
      "共振现象说明当外部频率匹配系统固有频率时效率最高。尝试不同环境和时段，找到你的学习共振点并固定执行。",
      "光速不变象征某些底层原则应保持恒定。节奏可调整，但诚实复盘和按时开始尽量不变，长期表现会更可靠。",
      "杠杆原理强调小力配合好支点可撬动大改变。建议建立一个高杠杆习惯，如睡前十分钟预习，投入小却能降低次日理解成本。",
      "考试前崩溃常因系统接近临界。建议像控制实验一样先稳睡眠和饮食，再按模块复习，先稳态后冲刺，避免状态瞬间塌陷。",
      "社交紧张像过强外场引起系统抖动。进入新场合前先做三次缓慢呼吸，降低生理激活水平，再开始交流会更顺。",
      "注意力像激光束，发散时能量密度下降。建议一次只开一个任务窗口，关掉多余通知，让能量集中在单一目标上。",
      "人际冲突可看作作用力与反作用力。你越强硬，对方越反弹；先降低冲量、改用低强度表达，系统更容易回到平衡。",
      "长期自律依赖动量积累。连续三天坚持一个小习惯后，行为惯性会帮助你继续前进，所以关键是先拿到最初动量。",
      "未来迷茫并非没有方向，而是参照系不清。建议设定三个月观察窗口，用可测指标记录成长，再判断下一步路线。",
      "复习效率低时别盲目加时长，先查能量损耗点。像能量审计那样记录一天精力峰谷，把高难任务放在峰值时段。"
    ]
  },
  {
    id: "cs",
    name: "计算机",
    intro: "用算法、结构与调试思维提升解决问题效率。",
    keywords: ["缓存", "分治", "调试", "对象", "复杂度"],
    replies: [
      "缓存机制说明短期记忆容量有限，信息塞太多会频繁失效。建议用间隔重复在1天、3天、7天回顾重点，把内容写入长期记忆。",
      "递归思维适合拆解大目标。先定义最小动作，例如每天一题，然后逐层调用下一步，复杂任务会从不可控变为可执行序列。",
      "死锁是双方互等导致停滞，人际关系也会出现。若都等对方先让步，系统无法前进；你先释放一个锁，往往就能恢复沟通。",
      "版本控制中的commit意味着可追踪改进。建议每周写一次生活提交日志：做对了什么、下周改什么，让成长可回放可迭代。",
      "分治法把大问题拆成小问题并行解决。复习可先按章节切块，再按题型切块，最后用整卷做合并测试，效率更高。",
      "调试核心是复现与定位。状态低迷时先记录触发条件和复现步骤，再一次只改一个变量，问题会更快被修复。",
      "面向对象强调属性与方法分离。你可以定义自己的行为接口：学习、休息、运动，各自设触发条件，生活系统会更稳定。",
      "时间复杂度告诉我们，不是所有问题都能快速解决。接受某些成长需要更长周期，先求稳定迭代，不要苛求即时突破。",
      "考试复习像任务调度，优先级错误会造成延迟爆炸。建议先处理高权重且未掌握模块，再安排低风险任务填充碎片时间。",
      "社交恐惧可按A/B测试做优化。尝试不同开场方式并记录反馈，保留有效脚本，逐步形成适合你的沟通模板。",
      "注意力分散常是上下文切换成本过高。建议同类任务批处理，例如统一回复消息、统一做题，减少线程频繁切换。",
      "未来迷茫时先做最小可行探索。给自己两周做一个小项目，不追求完美，只验证兴趣与耐受度，再决定是否深入。",
      "自律失败常是环境配置错误，不是人格问题。把学习资料放在触手可及处，把干扰应用移出首页，相当于优化默认配置。",
      "人际矛盾升级时像异常未捕获。建议先捕获情绪异常，再输出事实与需求，避免让冲突直接崩溃主流程。",
      "临考焦虑可做回滚策略：先回到最熟题型找稳定感，再逐步切回难点，相当于恢复到上一个可运行版本。"
    ]
  },
  {
    id: "design",
    name: "设计",
    intro: "用视觉与体验原则降低认知负担并提升行动意愿。",
    keywords: ["留白", "对比", "层次", "对齐", "用户中心"],
    replies: [
      "留白不是空白，而是给信息呼吸空间。若你感到压迫，可能是任务界面过满；建议只保留今日最关键三项，降低认知负荷。",
      "色彩心理学显示冷色有助镇定、暖色提升唤醒。复习焦虑时可用低饱和蓝灰背景，再用亮色标重点，注意力会更稳。",
      "对比原则用于突出重点。做决策时把选项按收益、成本、风险做对照表，视觉差异会帮助你快速识别优先级。",
      "重复原则建立秩序感。把每日启动动作固定，比如到座位先写三行计划，重复会形成稳定节奏并降低启动阻力。",
      "对齐原则强调元素关系清晰。整理学习区时按功能分区并对齐摆放，环境结构清楚后，大脑无效扫描会减少。",
      "视觉层次要求重要信息先被看见。把最关键任务放在日程最上方并使用醒目标记，执行概率会明显提高。",
      "用户中心设计强调先理解对象。沟通冲突时先复述对方需求再表达自己，会比直接反驳更容易达成协作。",
      "情感化设计说明美感会影响行为意愿。布置一个舒适学习角落，即便只是稳定光源和整洁桌面，也能提升坚持度。",
      "考试前资料混乱会让你持续焦躁。建议做信息架构：按科目、题型、难度分层归档，检索时间下降后心态也更稳。",
      "社交恐惧可借助界面设计思路。先准备两句通用开场和一个结束语，像按钮一样降低互动门槛。",
      "注意力不集中时，先删减视觉噪声。桌面只留当前任务相关物品，其余收纳，认知通道会从拥挤恢复清晰。",
      "未来迷茫时可做人生原型图：目标、路径、资源、风险各写三条。像产品草图一样先看全局，再做小步实验。",
      "自律靠流程设计而非硬抗。把学习开始动作设计成可见提示，如贴纸或闹钟文案，让行为由线索触发。",
      "人际误会常是信息层级错位。表达时先说结论再说依据，最后给建议，结构清晰会显著减少沟通摩擦。",
      "当压力过高时，给日程做留白。每天预留20分钟机动区处理突发，能防止计划被一点意外全部打乱。"
    ]
  },
  {
    id: "language",
    name: "语言学",
    intro: "理解语言如何影响认知、关系与行动。",
    keywords: ["语境", "词源", "隐喻", "语用", "礼貌"],
    replies: [
      "语言相对论提示表达会反过来塑造思维。把“我做不到”改成“我暂时还不会”，能把大脑从终局判断切换到成长路径。",
      "词源学能提升记忆粘性。背词时顺带查词根词缀和来源故事，语义网络更完整，回忆时会多一条检索通道。",
      "隐喻让抽象问题变可执行。把备考看作长跑而非冲刺，你会自然关注配速、补给和恢复，减少短期挫败感。",
      "语用学告诉我们同一句话在不同场景意义不同。沟通前先确认对象与目的，再选择措辞，误会会显著减少。",
      "语音象征说明某些发音会带来直觉联想。学外语时把发音模式和语义绑定，抽象词汇会更容易长期记住。",
      "关键期理论不等于成年人学不好语言。每天15分钟听读复述，比偶尔突击更能形成稳定进步。",
      "礼貌原则强调表达方式影响合作意愿。把命令句改为协商句，通常更容易得到积极响应并降低冲突。",
      "会话含义研究弦外之音。交流结束前加一句“我的理解是这样，对吗”，能及时对齐语义，减少后续误解。",
      "考试口语紧张时可用脚本化表达。提前准备开场句、转折句、收尾句，临场就像调用模板，稳定性更高。",
      "人际冲突中常见标签化语言。把“你总是”改为“这次我感受到”，能减少防御反应，提升问题解决概率。",
      "注意力漂移时，可用自我指令语。轻声说“先做这一页”，语言会像导航锚点，把思维拉回当前任务。",
      "未来迷茫时多用过程型词汇，如“探索”“试验”。词汇框架改变后，你更容易接受不确定阶段的正常性。",
      "社交恐惧可先练提问句。准备三个开放问题，如“你最近在忙什么”，比硬找话题更自然。",
      "自律失败后避免全盘否定。把“我又废了”改成“今天偏航了，明天回线”，语言重构能保护行动连续性。",
      "复盘时用具体描述替代模糊评价。说“今天完成了两章整理”比“还行”更有反馈价值，也更利于下次改进。"
    ]
  },
  {
    id: "psychology",
    name: "心理学",
    intro: "理解情绪、认知和行为背后的可调节机制。",
    keywords: ["认知失调", "心流", "锚定", "成长型思维", "多巴胺"],
    replies: [
      "认知失调指行为与信念冲突时，大脑会自动找理由自洽。若你总说要早睡却熬夜，建议记录触发场景并提前设置替代动作。",
      "习得性无助来自连续失败后的无力感。先完成一个十分钟内能做完的小任务，重新建立“我能做到”的证据链。",
      "锚定效应说明第一信息会影响后续判断。迎接挑战前先回顾三次成功经历，给自己设置积极锚点，行动意愿会提升。",
      "多巴胺机制表明预期奖励能推动启动。把大目标拆成小里程碑，每完成一步给小奖励，持续性通常会更好。",
      "成长型思维强调能力可发展。受挫时把“我不行”改成“方法还没对”，再做一次小实验，比自责更有效。",
      "心流出现在挑战与能力匹配时。任务过难会焦虑，过易会无聊；把难度调到略高于当前水平，专注会更稳定。",
      "破窗效应指出小混乱会诱发更大失序。学习结束前用两分钟复位环境，下次启动成本会大幅下降。",
      "曝光效应说明反复接触会增加好感。若你排斥某门课，先每天接触十分钟有趣内容，再过渡教材，抗拒会减弱。",
      "考试前心慌是正常应激，不代表能力下降。先做三分钟呼吸和肌肉放松，再进入熟悉题型，能快速恢复掌控感。",
      "社交恐惧时，大脑会高估被评判概率。建议把注意力从“我表现怎样”转向“我能帮对方什么”，焦虑会下降。",
      "注意力涣散常与奖励延迟有关。先给任务设置可见进度条，每完成一段就打勾，让大脑及时得到反馈。",
      "未来迷茫时不要逼自己一次定终局。设一个30天探索计划，每周体验一个方向，用实际感受替代空想焦虑。",
      "自律本质是习惯链设计。给新习惯绑定旧习惯，如“刷牙后背5个词”，触发线索稳定后执行更轻松。",
      "人际冲突升级时先做情绪命名。把“我很烦”细化成“我感到被忽视”，情绪被命名后冲动会减弱。",
      "低谷期先保底，不必追求满分表现。把每日目标降到可完成阈值，守住连续性比短期爆发更关键。"
    ]
  },
  {
    id: "biology",
    name: "生物学",
    intro: "从生命系统角度理解学习、情绪与行为状态。",
    keywords: ["生物钟", "神经可塑性", "稳态", "菌群", "镜像神经元"],
    replies: [
      "昼夜节律调控睡眠与清醒窗口。若白天困晚上清醒，多半是节律漂移；固定起床并晨间见光十分钟可帮助重置。",
      "神经可塑性说明大脑会随训练重塑。学新技能卡顿很正常，持续短时高频练习能强化突触连接。",
      "稳态机制让身体持续调平内环境。压力来时先补水、慢呼吸、短步行，能帮助神经系统更快回归平衡。",
      "进化心理学提醒许多冲动源于远古适应机制。意识到对高糖食物的偏好后，提前准备替代品更易控制。",
      "肠道菌群与情绪存在双向联系。规律摄入发酵食物和膳食纤维，通常会改善精神状态与专注表现。",
      "细胞自噬在休息期清除受损成分。长期熬夜会影响修复效率，建议尽量保证7到8小时睡眠。",
      "镜像神经元使情绪在群体中传播。沟通时先放慢语速并匹配对方节奏，更容易建立共情。",
      "用进废退是神经系统常态。想维持技能，每天五分钟也比间歇突击有效，稳定刺激能防止快速退化。",
      "考试周身体紧绷常是应激激素升高。建议把咖啡因控制在白天，晚间做轻运动，帮助夜间恢复系统启动。",
      "注意力低下可能来自血糖波动。长时间学习可用低糖零食和水分补给，避免能量骤降导致效率断崖。",
      "社交恐惧时心跳加速是交感神经激活，不等于危险。先接受这是一种生理反应，再做慢呼吸，身体会逐步降档。",
      "未来迷茫常伴随慢性压力。规律作息与轻有氧能提高前额叶功能，让你更容易做理性决策。",
      "自律要尊重生物节律。把高认知任务安排在清醒峰值时段，比硬熬夜更能产出高质量结果。",
      "人际关系中的共情可训练。观察对方表情与姿态并做轻度镜像，能提升理解准确率并减少误会。",
      "长期焦虑时优先修复基础生理：睡眠、光照、运动、饮食。底层参数稳定后，情绪和学习表现通常同步改善。"
    ]
  }
];

let chatHistoryEl;
let chatFormEl;
let chatInputEl;
let randomBtnEl;
let clearBtnEl;
let activeTimers = new Set();
let chatState = [];

document.addEventListener("DOMContentLoaded", () => {
  initCanvas();
  initBackgroundParallax();
  initChatSystem();
});

function initBackgroundParallax() {
  const root = document.body;
  if (!root) return;

  let targetX = 0;
  let targetY = 0;
  let rafId = 0;

  function apply() {
    rafId = 0;
    root.style.setProperty("--mx", `${targetX}px`);
    root.style.setProperty("--my", `${targetY}px`);
  }

  function queueApply() {
    if (rafId) return;
    rafId = requestAnimationFrame(apply);
  }

  window.addEventListener(
    "mousemove",
    (event) => {
      const nx = event.clientX / window.innerWidth - 0.5;
      const ny = event.clientY / window.innerHeight - 0.5;
      targetX = nx * 10;
      targetY = ny * 8;
      queueApply();
    },
    { passive: true }
  );

  window.addEventListener(
    "mouseleave",
    () => {
      targetX = 0;
      targetY = 0;
      queueApply();
    },
    { passive: true }
  );
}

function initCanvas() {
  const canvas = document.getElementById("starfield");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const particles = [];
  const maxParticles = 80;

  function createParticle(width, height) {
    return {
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 1.8 + 0.4,
      vx: (Math.random() - 0.5) * 0.08,
      vy: Math.random() * 0.18 + 0.03,
      a: Math.random() * 0.6 + 0.25
    };
  }

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const count = Math.min(maxParticles, Math.floor((canvas.width * canvas.height) / 16000));
    particles.length = 0;
    for (let i = 0; i < count; i += 1) particles.push(createParticle(canvas.width, canvas.height));
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.y > canvas.height + 2) p.y = -2;
      if (p.x > canvas.width + 2) p.x = -2;
      if (p.x < -2) p.x = canvas.width + 2;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${p.a})`;
      ctx.fill();
    }
    requestAnimationFrame(animate);
  }

  resize();
  animate();
  window.addEventListener("resize", resize);
}

function initChatSystem() {
  chatHistoryEl = document.getElementById("chatHistory");
  chatFormEl = document.getElementById("chatForm");
  chatInputEl = document.getElementById("chatInput");
  randomBtnEl = document.getElementById("randomBtn");
  clearBtnEl = document.getElementById("clearBtn");

  if (!chatHistoryEl || !chatFormEl || !chatInputEl) return;

  loadChatState();
  if (chatState.length > 0) {
    for (const item of chatState) renderMessageInstant(item);
  } else {
    addOpeningMessage();
  }

  chatFormEl.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = chatInputEl.value.trim();
    if (!text) return;
    const questionId = createQuestionId();

    addUserMessage(text, true);
    const subject = getRandomSubject();
    const reply = generateReply(subject, text);
    addTypingAgentMessage({
      text: reply,
      subjectId: subject.id,
      question: text,
      questionId,
      usedSubjects: [subject.id],
      allowSwitch: true,
      saveAfterDone: true
    });

    chatInputEl.value = "";
    chatInputEl.focus();
  });

  if (randomBtnEl) {
    randomBtnEl.addEventListener("click", () => {
      const questionId = createQuestionId();
      const question = "随机占卜";
      const subject = getRandomSubject();
      const reply = generateReply(subject, question);
      addTypingAgentMessage({
        text: reply,
        subjectId: subject.id,
        question,
        questionId,
        usedSubjects: [subject.id],
        allowSwitch: true,
        saveAfterDone: true
      });
    });
  }

  if (clearBtnEl) {
    clearBtnEl.addEventListener("click", () => {
      clearAllTimers();
      chatHistoryEl.innerHTML = "";
      chatState = [];
      localStorage.removeItem(STORAGE_KEY);
      addOpeningMessage();
    });
  }
}

function addOpeningMessage() {
  const opening = {
    role: "agent",
    text: OPENING_TEXT,
    subjectId: "",
    question: "",
    questionId: "",
    usedSubjects: [],
    allowSwitch: false
  };
  chatState.push(opening);
  saveChatState();
  renderMessageInstant(opening);
}

function createQuestionId() {
  return `q_${Date.now()}_${Math.floor(Math.random() * 100000)}`;
}

function getRandomSubject() {
  return subjects[Math.floor(Math.random() * subjects.length)];
}

function getSubjectById(id) {
  return subjects.find((item) => item.id === id);
}

function generateReply(subject, userQuestionText) {
  void userQuestionText;
  return subject.replies[Math.floor(Math.random() * subject.replies.length)];
}

function getRemainingCount(usedSubjects) {
  const unique = new Set(usedSubjects);
  return Math.max(0, subjects.length - unique.size);
}

function getSwitchButtonText(usedSubjects) {
  return `🔁 换一个学科（剩余${getRemainingCount(usedSubjects)}个）`;
}

function addUserMessage(text, saveState) {
  const data = { role: "user", text };
  renderMessageInstant(data);
  if (saveState) {
    chatState.push(data);
    saveChatState();
  }
}

function addTipMessage(text, saveState) {
  const data = {
    role: "agent",
    text,
    subjectId: "",
    question: "",
    questionId: "",
    usedSubjects: [],
    allowSwitch: false
  };
  renderMessageInstant(data);
  if (saveState) {
    chatState.push(data);
    saveChatState();
  }
}

function renderMessageInstant(data) {
  const msgEl = createMessageElement(data);
  if (data.role === "user") {
    const bubble = msgEl.querySelector(".bubble");
    bubble.textContent = data.text;
  } else {
    const bubble = msgEl.querySelector(".bubble");
    const content = msgEl.querySelector(".msg-content");
    content.textContent = data.text;
    if (data.subjectId) appendSignature(bubble, data.subjectId);
    const wrapper = msgEl.querySelector(".bubble-wrap");
    if (data.allowSwitch && data.subjectId && data.questionId) {
      wrapper.appendChild(createSwitchButton(data, msgEl));
    }
  }
  chatHistoryEl.appendChild(msgEl);
  scrollToBottom();
}

function addTypingAgentMessage(data) {
  const msgEl = createMessageElement({ ...data, role: "agent" });
  const contentEl = msgEl.querySelector(".msg-content");
  const bubble = msgEl.querySelector(".bubble");
  const wrapper = msgEl.querySelector(".bubble-wrap");

  chatHistoryEl.appendChild(msgEl);
  scrollToBottom();

  let index = 0;
  const timer = setInterval(() => {
    contentEl.textContent += data.text.charAt(index);
    index += 1;
    scrollToBottom();
    if (index >= data.text.length) {
      clearInterval(timer);
      activeTimers.delete(timer);

      if (data.subjectId) appendSignature(bubble, data.subjectId);
      if (data.allowSwitch && data.subjectId && data.questionId) {
        wrapper.appendChild(createSwitchButton(data, msgEl));
      }

      if (data.saveAfterDone) {
        chatState.push({
          role: "agent",
          text: data.text,
          subjectId: data.subjectId,
          question: data.question,
          questionId: data.questionId,
          usedSubjects: data.usedSubjects,
          allowSwitch: data.allowSwitch
        });
        saveChatState();
      }
    }
  }, 50);

  activeTimers.add(timer);
}

function createMessageElement(data) {
  const article = document.createElement("article");
  article.className = `message ${data.role}`;

  if (data.role === "agent") {
    article.dataset.subject = data.subjectId || "";
    article.dataset.question = data.question || "";
    article.dataset.questionId = data.questionId || "";
    article.dataset.usedSubjects = JSON.stringify(data.usedSubjects || []);

    const avatar = document.createElement("div");
    avatar.className = "mini-avatar";
    avatar.textContent = "🐱";
    article.appendChild(avatar);
  }

  const wrap = document.createElement("div");
  wrap.className = "bubble-wrap";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (data.role === "agent") {
    const content = document.createElement("span");
    content.className = "msg-content";
    bubble.appendChild(content);
  }

  wrap.appendChild(bubble);
  article.appendChild(wrap);
  return article;
}

function appendSignature(bubble, subjectId) {
  const subject = getSubjectById(subjectId);
  if (!subject) return;

  const signature = document.createElement("div");
  signature.className = "subject-signature";
  signature.append("—— 🎲 ");

  const tag = document.createElement("span");
  tag.className = "subject-tag";
  tag.title = subject.intro;
  tag.textContent = `${subject.name}视角`;
  signature.appendChild(tag);

  bubble.appendChild(signature);
}

function createSwitchButton(data, msgEl) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "switch-btn";
  btn.textContent = getSwitchButtonText(data.usedSubjects || []);
  btn.addEventListener("click", () => onSwitchSubject(msgEl));
  return btn;
}

function onSwitchSubject(messageEl) {
  const question = messageEl.dataset.question || "";
  const questionId = messageEl.dataset.questionId || createQuestionId();
  const usedSubjects = JSON.parse(messageEl.dataset.usedSubjects || "[]");

  let available = subjects.filter((s) => !usedSubjects.includes(s.id));
  let nextUsedBase = [...usedSubjects];

  if (available.length === 0) {
    addTipMessage("所有视角都看过了，再来一轮？", true);
    available = [...subjects];
    nextUsedBase = [];
  }

  const subject = available[Math.floor(Math.random() * available.length)];
  const nextUsed = [...new Set([...nextUsedBase, subject.id])];
  const reply = generateReply(subject, question);

  addTypingAgentMessage({
    text: reply,
    subjectId: subject.id,
    question,
    questionId,
    usedSubjects: nextUsed,
    allowSwitch: true,
    saveAfterDone: true
  });
}

function clearAllTimers() {
  for (const timer of activeTimers) clearInterval(timer);
  activeTimers.clear();
}

function saveChatState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(chatState));
}

function loadChatState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      chatState = [];
      return;
    }
    const parsed = JSON.parse(raw);
    chatState = Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    chatState = [];
  }
}

function scrollToBottom() {
  chatHistoryEl.scrollTop = chatHistoryEl.scrollHeight;
}
