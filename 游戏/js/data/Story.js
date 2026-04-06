const STORY = {
    start: {
        id: 'start',
        next: 'prologue_1'
    },
    prologue_1: {
        id: 'prologue_1',
        scene: 'school_gate',
        dialogue: {
            speaker: null,
            text: '春天，是一个充满希望的季节。\n樱花纷飞的季节，也是新的故事开始的季节。',
            expression: null
        },
        next: 'prologue_2'
    },
    prologue_2: {
        id: 'prologue_2',
        dialogue: {
            speaker: null,
            text: '今天，是我转入这所学校的第一天。\n站在校门前，我深吸了一口气。',
            expression: null
        },
        next: 'prologue_3'
    },
    prologue_3: {
        id: 'prologue_3',
        characters: [
            { id: 'sakura', position: 'center', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '那个……你是新转来的同学吗？',
            expression: 'normal'
        },
        next: 'prologue_4'
    },
    prologue_4: {
        id: 'prologue_4',
        characters: [
            { id: 'sakura', position: 'center', expression: 'blushing' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '啊，抱歉，突然搭话很奇怪吧……\n我是樱井雪，是这个班的学生。',
            expression: 'blushing'
        },
        next: 'prologue_5'
    },
    prologue_5: {
        id: 'prologue_5',
        dialogue: {
            speaker: null,
            text: '眼前的少女有着粉色的头发，温柔的眼神中带着一丝害羞。\n她就是我在这所学校认识的第一个人。',
            expression: null
        },
        next: 'prologue_choice_1'
    },
    prologue_choice_1: {
        id: 'prologue_choice_1',
        choices: [
            {
                text: '「谢谢你，樱井同学。我是新来的……」',
                next: 'prologue_6a',
                affinity: { sakura: 5 }
            },
            {
                text: '「啊，是的。谢谢你特意过来。」',
                next: 'prologue_6b',
                affinity: { sakura: 3 }
            },
            {
                text: '「嗯，我是转学生。你好。」',
                next: 'prologue_6c',
                affinity: { sakura: 1 }
            }
        ]
    },
    prologue_6a: {
        id: 'prologue_6a',
        characters: [
            { id: 'sakura', position: 'center', expression: 'happy' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '不客气！如果有什么不知道的事情，随时可以问我哦。\n我带你去教室吧！',
            expression: 'happy'
        },
        next: 'prologue_7'
    },
    prologue_6b: {
        id: 'prologue_6b',
        characters: [
            { id: 'sakura', position: 'center', expression: 'happy' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '没关系的！作为班上的一员，帮助新同学是应该的。\n走吧，我们一起去教室！',
            expression: 'happy'
        },
        next: 'prologue_7'
    },
    prologue_6c: {
        id: 'prologue_6c',
        characters: [
            { id: 'sakura', position: 'center', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '嗯，你好……那，我带你去教室吧。',
            expression: 'normal'
        },
        next: 'prologue_7'
    },
    prologue_7: {
        id: 'prologue_7',
        scene: 'classroom',
        characters: [],
        dialogue: {
            speaker: null,
            text: '就这样，在樱井的带领下，我来到了新的教室。\n这里，将是我新生活开始的地方。',
            expression: null
        },
        next: 'chapter1_1'
    },
    chapter1_1: {
        id: 'chapter1_1',
        scene: 'classroom',
        dialogue: {
            speaker: null,
            text: '第一章：樱花树下的相遇',
            expression: null
        },
        next: 'chapter1_2'
    },
    chapter1_2: {
        id: 'chapter1_2',
        characters: [
            { id: 'misaki', position: 'right', expression: 'happy' }
        ],
        dialogue: {
            speaker: 'misaki',
            text: '哟！你就是新来的转学生？',
            expression: 'happy'
        },
        next: 'chapter1_3'
    },
    chapter1_3: {
        id: 'chapter1_3',
        characters: [
            { id: 'misaki', position: 'right', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'misaki',
            text: '我是美咲绫，是樱井雪的好朋友，也是网球部的王牌！\n以后大家就是同学了，请多指教！',
            expression: 'normal'
        },
        next: 'chapter1_4'
    },
    chapter1_4: {
        id: 'chapter1_4',
        characters: [
            { id: 'misaki', position: 'right', expression: 'normal' },
            { id: 'sakura', position: 'left', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '美咲，你不要吓着新同学了……',
            expression: 'normal'
        },
        next: 'chapter1_5'
    },
    chapter1_5: {
        id: 'chapter1_5',
        characters: [
            { id: 'misaki', position: 'right', expression: 'happy' },
            { id: 'sakura', position: 'left', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'misaki',
            text: '哈哈，抱歉抱歉！我只是太兴奋了！\n对了，午休的时候我们一起去食堂吧，我请你！',
            expression: 'happy'
        },
        next: 'chapter1_choice_1'
    },
    chapter1_choice_1: {
        id: 'chapter1_choice_1',
        choices: [
            {
                text: '「好啊，谢谢你！」',
                next: 'chapter1_6a',
                affinity: { misaki: 5 }
            },
            {
                text: '「不用了，我想自己熟悉一下学校。」',
                next: 'chapter1_6b',
                affinity: { misaki: -2, sakura: 1 }
            },
            {
                text: '「谢谢，不过我想先问樱井同学要不要一起。」',
                next: 'chapter1_6c',
                affinity: { sakura: 5, misaki: 2 }
            }
        ]
    },
    chapter1_6a: {
        id: 'chapter1_6a',
        characters: [
            { id: 'misaki', position: 'right', expression: 'happy' },
            { id: 'sakura', position: 'left', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'misaki',
            text: '太好了！那我们午休见！',
            expression: 'happy'
        },
        next: 'chapter1_7'
    },
    chapter1_6b: {
        id: 'chapter1_6b',
        characters: [
            { id: 'misaki', position: 'right', expression: 'normal' },
            { id: 'sakura', position: 'left', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'misaki',
            text: '这样啊……那好吧。如果改变主意了随时找我们！',
            expression: 'normal'
        },
        next: 'chapter1_7'
    },
    chapter1_6c: {
        id: 'chapter1_6c',
        characters: [
            { id: 'misaki', position: 'right', expression: 'happy' },
            { id: 'sakura', position: 'left', expression: 'blushing' }
        ],
        dialogue: {
            speaker: 'sakura',
            text: '哎？我……我当然没问题！',
            expression: 'blushing'
        },
        next: 'chapter1_7'
    },
    chapter1_7: {
        id: 'chapter1_7',
        characters: [
            { id: 'misaki', position: 'right', expression: 'normal' },
            { id: 'sakura', position: 'left', expression: 'normal' }
        ],
        dialogue: {
            speaker: null,
            text: '就这样，我在新班级的第一天开始了。\n但我没有想到，这只是一切的开始……',
            expression: null
        },
        next: 'chapter1_8'
    },
    chapter1_8: {
        id: 'chapter1_8',
        scene: 'cherry_blossom_park',
        characters: [],
        dialogue: {
            speaker: null,
            text: '放学后，我决定一个人到学校附近的樱花公园走走。\n粉色的花瓣随风飘舞，美不胜收。',
            expression: null
        },
        next: 'chapter1_9'
    },
    chapter1_9: {
        id: 'chapter1_9',
        characters: [
            { id: 'shizuku', position: 'center', expression: 'normal' }
        ],
        dialogue: {
            speaker: null,
            text: '在樱花树下，我看到了一个黑色长发的少女。\n她静静地站在那里，仿佛在凝视着什么。',
            expression: null
        },
        next: 'chapter1_10'
    },
    chapter1_10: {
        id: 'chapter1_10',
        characters: [
            { id: 'shizuku', position: 'center', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'shizuku',
            text: '……你来了。',
            expression: 'normal'
        },
        next: 'chapter1_11'
    },
    chapter1_11: {
        id: 'chapter1_11',
        characters: [
            { id: 'shizuku', position: 'center', expression: 'normal' }
        ],
        dialogue: {
            speaker: 'shizuku',
            text: '我一直在等你。\n月影雫……我的名字。',
            expression: 'normal'
        },
        next: 'chapter1_12'
    },
    chapter1_12: {
        id: 'chapter1_12',
        characters: [
            { id: 'shizuku', position: 'center', expression: 'happy' }
        ],
        dialogue: {
            speaker: 'shizuku',
            text: '我们的命运，从很久以前就已经联系在一起了。\n这一点，我很确信。',
            expression: 'happy'
        },
        next: 'chapter1_13'
    },
    chapter1_13: {
        id: 'chapter1_13',
        characters: [
            { id: 'shizuku', position: 'center', expression: 'normal' }
        ],
        dialogue: {
            speaker: null,
            text: '神秘的少女，谜一般的话语……\n这一切，究竟意味着什么？',
            expression: null
        },
        next: 'chapter1_end'
    },
    chapter1_end: {
        id: 'chapter1_end',
        dialogue: {
            speaker: null,
            text: '第一章 完\n\n感谢游玩《樱花之梦》演示版！\n\n这是一个完整的视觉小说游戏框架，包含了：\n• 完整的游戏引擎\n• 角色系统和好感度系统\n• 存档/读档功能\n• 剧情分支系统\n• 5名可攻略角色\n• 15个精美场景\n\n完整版本还将包含更多精彩内容！',
            expression: null
        },
        next: 'ending_demo'
    },
    ending_demo: {
        id: 'ending_demo',
        ending: {
            title: '序章结束',
            text: '感谢您体验《樱花之梦》序章！\n\n在这个樱花飞舞的季节，新的故事即将开始。\n五位少女的命运，将与你紧紧相连。\n\n期待在完整版本中与您再次相遇！'
        }
    }
};
