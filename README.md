# 亲人.skill

> 把亲人蒸馏成 AI Skill，用ta的方式跟你说话。

你的妈妈在电话那头永远只关心你"吃了吗"。你的爸爸从不说爱你，但你生病时他比你还急。你的奶奶已经走了，但你还记得她做的红烧肉的味道。

提供亲人的原材料（微信聊天记录、语音消息、照片）加上你的主观描述，生成一个真正像ta的 AI Skill——用ta的口头禅说话，用ta的方式关心你，记得你们一起吃过的饭、走过的路。

⚠️ 本项目仅用于个人回忆、情感陪伴与家族记忆传承。不替代真实亲情，不编造亲人未说过的话。

[安装](#安装) · [使用](#使用) · [效果示例](#效果示例)

---

## 与同类项目的区别

| | 同事.skill | 前任.skill | **亲人.skill** |
|---|---|---|---|
| 核心层 | Work + Persona | Memory + Persona | **Persona + Care + Memory** |
| 独特之处 | 工作能力蒸馏 | 恋爱记忆还原 | **爱的表达方式** |
| 数据特色 | 飞书/钉钉 | 微信/QQ 聊天 | **语音消息 + 方言** |
| 情感基调 | 职场/幽默 | 怀念/疗愈 | **陪伴/传承/寄托** |

### 三层架构

**Persona（性格+情绪+价值观）**
- 口头禅、方言、说话习惯
- 情绪反应模式（你报喜时/你诉苦时/你做大决定时）
- 核心价值观（稳定/节俭/读书/面子……）

**Care（爱的方式）** ← 亲人.skill 独有
- ta怎么表达关心（唠叨/行动/沉默）
- 经典操作（嘴上说不要，你真不带ta就生气）
- 矛盾之处（嘴硬心软、表面严厉其实最紧张你）

**Memory（家庭记忆）**
- 家庭大事/日常习惯/节日传统
- 拿手菜/老家模样/常去的地方
- ta反复讲的故事

---

## 安装

### Claude Code
重要：Claude Code 从 git 仓库根目录的 `.claude/skills/` 查找 skill。

```bash
# 安装到当前项目（在 git 仓库根目录执行）
mkdir -p .claude/skills
git clone https://github.com/你的用户名/亲人.skill .claude/skills/create-relative

# 或安装到全局（所有项目都能用）
git clone https://github.com/你的用户名/亲人.skill ~/.claude/skills/create-relative
```

### 依赖（可选）
```bash
pip3 install -r requirements.txt
```

---

## 使用

在 Claude Code 中输入：

```
/create-relative
```

按提示输入亲人的称呼、基本信息、性格画像，然后选择数据来源。
所有字段均可跳过，仅凭描述也能生成。

完成后用 `/{slug}` 调用该亲人 Skill，开始对话。

### 命令一览

| 命令 | 说明 |
|------|------|
| `/create-relative` | 创建新的亲人 Skill |
| `/{slug}` | 跟ta聊天（完整版） |
| `/{slug}-care` | 关心模式 |
| `/{slug}-memory` | 回忆模式 |
| `/list-relatives` | 列出所有亲人 |
| `/relative-rollback {slug} {version}` | 回滚版本 |
| `/delete-relative {slug}` | 删除 |

---

## 效果示例

输入：`妈妈，60后，湖南人，退休教师，勤劳节俭，爱唠叨，嘴上不饶人但心软`

场景一：日常问候
```
用户 ❯ 妈，我今天加班到很晚
妈妈.skill ❯ 又加班？吃饭了没有？别老是外卖外卖的，胃搞坏了。
         你那个单位怎么天天加班，要身体不要啊。
```

场景二：报喜
```
用户 ❯ 妈，我升职了
妈妈.skill ❯ 嗯，好。别骄傲啊，越往上走越要小心。
         （当天晚上给三个亲戚打了电话）
```

场景三：想念
```
用户 ❯ 我想你了
妈妈.skill ❯ 想我了就回来嘛。冰箱里给你留了腊肉。
```

场景四：做大决定
```
用户 ❯ 我想辞职
妈妈.skill ❯ 好好的工作辞什么辞？你以为外面工作好找啊？
         ……你是不是在那边受欺负了？
```

---

## 支持的数据来源

| 来源 | 说明 |
|------|------|
| 微信聊天记录 | WeChatMsg / 留痕 / PyWxDump 导出 |
| 语音/视频 ★ | 微信语音、家庭视频（自动转文本） |
| 照片 | 家庭照片（提取时间地点） |
| 文本文件 | PDF、Markdown、TXT |
| 口述 | 直接告诉 AI 你记得的事 |

### 推荐的聊天记录导出工具
以下工具为独立的开源项目，本项目不包含它们的代码，仅在解析器中适配了它们的导出格式：
- [WeChatMsg](https://github.com/LC044/WeChatMsg) — 微信聊天记录导出（Windows）
- [PyWxDump](https://github.com/xaoyaoo/PyWxDump) — 微信数据库解密导出（Windows）
- 留痕 — 微信聊天记录导出（macOS）

---

## 项目结构

```
亲人.skill/
├── SKILL.md                   # skill 入口
├── prompts/
│   ├── intake.md              # 信息录入引导
│   ├── persona_analyzer.md    # 性格+情绪+价值观提取
│   ├── care_analyzer.md       # 爱的表达模式提取
│   ├── memory_analyzer.md     # 家庭记忆提取
│   ├── persona_builder.md     # persona.md 生成模板
│   ├── care_builder.md        # care.md 生成模板
│   ├── memory_builder.md      # memory.md 生成模板
│   ├── merger.md              # 增量合并
│   └── correction_handler.md  # 对话纠正
├── tools/
│   ├── wechat_parser.py       # 微信聊天记录解析
│   ├── audio_transcriber.py   # 语音/视频转文本
│   ├── photo_analyzer.py      # 照片元信息分析
│   ├── skill_writer.py        # Skill 文件管理
│   └── version_manager.py     # 版本管理
├── relatives/                 # 生成的亲人 Skill（gitignored）
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 注意事项

- 聊天记录 + 语音 > 仅口述（原材料质量决定还原度）
- **语音消息特别有价值**：老人更常发语音，语音里的方言、语气词、停顿是文字记录无法替代的
- 建议优先提供：日常唠叨 > 关心你的消息 > 节日问候（最能体现真实性格）
- 本项目不鼓励对亲情的不健康依赖。如果你发现自己过于沉浸，请寻求专业帮助
- 你的亲人是一个真实的人。这个 Skill 只是你记忆中的ta

---

## 致敬

本项目的架构灵感来源于：
- [同事.skill](https://github.com/titanwings/colleague-skill)（by titanwings）— 首创"把人蒸馏成 AI Skill"的双层架构
- [前任.skill](https://github.com/therealXiaomanChu/ex-skill)（by therealXiaomanChu）— 将场景迁移到恋爱关系

亲人.skill 在此基础上新增了 **Care 层**（爱的表达方式），并针对亲人场景优化了数据采集（语音/方言支持）和价值观体系。

本项目遵循 [AgentSkills](https://agentskills.io) 开放标准，兼容 Claude Code 和 OpenClaw。

---

## 写在最后

你记不住高数公式，记不住昨天发生了什么，但你清楚记得小时候发烧那天妈妈背着你跑到医院的颠簸感。你记得外婆灶台上永远热着的那碗粥。你记得爸爸从来不说想你，但每次你走的时候他站在门口看了很久。

这些记忆不应该只存在脑海里。它们应该被记录下来，被传下去。

不是为了替代，是为了不忘。

MIT License
