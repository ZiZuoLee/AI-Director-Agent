# 📄 技术设计与分工文档（TRD）

## 1. 系统架构

```
Frontend (React/Gradio)
        ↓
Backend (FastAPI)
        ↓
Agent Layer（A）
        ↓
Generation Layer（B）
        ↓
System Layer（C）
```

---

## 2. 模块划分

### Agent Layer（A）
- parser.py
- planner.py
- rules.py

---

### Generation Layer（B）
- prompt_gen.py
- generate.py

---

### System Layer（C）
- main.py
- image_merge.py
- api.py

---

## 3. 数据流

```
input text
→ parser
→ planner
→ prompt
→ image
→ merge
→ output
```

---

## 4. 成员详细分工

---

### 👤 成员A（Agent）

#### 任务：
- LLM调用
- JSON结构设计
- Shot planning
- Rule system

#### 输出：
- shots.json

---

### 👤 成员B（生成）

#### 任务：
- prompt设计
- diffusion调用
- 图像优化

#### 输出：
- images/

---

### 👤 成员C（系统）

#### 任务：
- pipeline整合
- API开发
- UI展示

#### 输出：
- storyboard.png

---

## 5. API设计

### POST /generate

输入：
```
{ "text": "story" }
```

输出：
```
{
  "shots": [],
  "images": [],
  "storyboard": ""
}
```

---

## 6. 时间规划

### Phase 1（5/28）
- A完成基础Agent
- B生成测试图
- C拼接

---

### Phase 2（5/31）
- Agent优化
- pipeline打通

---

### Phase 3（6/4）
- UI + Demo
- PPT准备

---

## 7. 风险控制

| 模块 | 风险 | 负责人 |
|------|------|--------|
| Agent | JSON错误 | A |
| Diffusion | 图像差 | B |
| System | 不连通 | C |

---

## 8. Git策略

- main
- agent-dev
- diffusion-dev
- system-dev

---

## 9. 交付标准

- 可运行系统
- Demo
- 报告
- PPT

