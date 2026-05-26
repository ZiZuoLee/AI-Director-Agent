# 📄 PRD：Storyboard Agent（完整版）

## 1. 项目概述
本项目构建一个“导演级 AI Agent”，实现从文本剧本到电影分镜图（Storyboard）的自动生成。

系统不仅生成图像，更强调：
- Agent决策能力
- 分镜语言建模（cinematography reasoning）
- 可解释AI（展示中间推理）

---

## 2. 系统整体Pipeline

```
User Input (Story)
        ↓
[1] Script Parser（语义解析）
        ↓
[2] Shot Planner（Agent核心）
        ↓
[3] Rule Engine（规则增强）
        ↓
[4] Prompt Generator
        ↓
[5] Image Generator（Diffusion）
        ↓
[6] Storyboard Composer
        ↓
Final Output（Storyboard）
```

---

## 3. 核心模块说明

### 3.1 Script Parser
- 输入：自然语言剧本
- 输出：结构化语义JSON
- 技术：Groq (Llama 3.3)

---

### 3.2 Shot Planner（核心创新）
- 拆分镜头（shot decomposition）
- 引入电影语言：
  - wide shot
  - close-up
  - tracking shot

---

### 3.3 Rule Engine（创新点）
- 非纯LLM推理
- 示例：
  - chase → tracking shot
  - emotion → close-up

---

### 3.4 Prompt Generator
- 将shot转为diffusion prompt
- 强化cinematic风格

---

### 3.5 Image Generator
- Stable Diffusion / ComfyUI
- 参数调优（CFG, Steps）

---

### 3.6 Storyboard Composer
- 拼接图片
- 添加文字描述

---

## 4. 创新点（评分关键）

### ⭐ 创新1：Agent化分镜规划
不仅生成图像，而是模拟导演决策

---

### ⭐ 创新2：规则+LLM混合推理
提升稳定性与可解释性

---

### ⭐ 创新3：中间表示可视化
展示JSON、shot list等

---

### ⭐ 创新4：cinematic prompt engineering
强化电影质感

---

## 5. MVP定义
- 输入一句话
- 输出3–5镜头
- 生成对应图像
- 拼接展示

---

## 6. 评估指标
- 连贯性（shots是否合理）
- 视觉质量
- 系统完整性
- 创新性

---

## 7. 风险与对策
| 风险 | 对策 |
|------|------|
| LLM不稳定 | JSON约束 |
| 图像不一致 | 固定seed |
| 时间不足 | 优先MVP |

---

## 8. 未来扩展
- 视频生成
- 角色一致性
- 多模态输入

