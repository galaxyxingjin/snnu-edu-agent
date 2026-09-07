# 师小助 · 智能助学 Agent

> 面向高校「教学赋能」场景的一站式 AI 智能助教 —— 学科答疑、智能评测、讲义生成、知识点图解、虚拟物理实验，让教与学提质增效。

「师小助」是一个基于大模型（LLM）构建的对话式智能教育助手，围绕陕西师范大学「数字赋能教育」赛事方向，聚焦**课堂教学与自主学习**场景，用 AI 为师生提供备课、答疑、评测、实验演示等全链路支撑。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 📚 **学科答疑** | 数学、物理、英语、编程等学科讲解，「思路 → 步骤 → 答案 → 知识点」结构化输出，支持拍题识别 |
| 📝 **智能评测** | 按学科/知识点/难度自动出题、逐题批改、输出学情诊断报告，定位薄弱环节 |
| 📄 **文本讲义生成** | 按「教学目标 → 重难点 → 讲解 → 例题 → 小结 → 作业」结构自动生成课程讲义，一键导出 Word/PDF |
| 🖼️ **知识点图解** | 生成概念关系图、思维导图、函数图像、实验装置图、原子模型图等教学示意图片 |
| 🔬 **虚拟物理实验室** | 内置力学（斜面/自由落体/弹簧）、电学（串并联电路）、原子物理（原子模型展厅）三大实验场景，支持定量模拟 |
| 🎬 **教学 PPT 生成** | Markdown 一键生成可下载的教学课件（`.pptx`） |
| 🌐 **联网搜索** | 实时查询教育政策、考试安排、学术动态等时效性信息 |
| 🔐 **用户系统** | 介绍页 + 注册/登录（账号数据持久化到 PostgreSQL，密码加盐哈希存储） |

---

## 🏗️ 技术架构

- **Agent 框架**：LangChain / LangGraph（`create_agent` 多智能体编排）
- **大模型**：豆包 Doubao-Seed-2.0-Pro（多模态，支持文本/图片/视频输入）
- **短期记忆**：滑动窗口（默认保留最近 20 轮）+ PostgreSQL 持久化 Checkpointer
- **后端服务**：FastAPI（HTTP 服务，端口 5000）
- **数据存储**：PostgreSQL（用户数据 + 对话记忆）+ 对象存储（生成的文件/图片/PPT）
- **工具能力**：联网搜索、文档生成、图片生成、物理模拟计算

---

## 📁 目录结构

```
.
├── assets/web/                  # 前端页面
│   ├── index.html               # 介绍界面
│   ├── login.html               # 注册 / 登录页
│   └── chat.html                # 智能对话页（登录后进入）
├── config/
│   └── agent_llm_config.json    # 大模型配置与 System Prompt
├── scripts/                     # 启动脚本
├── src/
│   ├── agents/
│   │   └── agent.py             # Agent 主逻辑（build_agent）
│   ├── tools/                   # Agent 工具集
│   │   ├── diagram_generator.py # 知识点图解生成
│   │   ├── document_generator.py# 讲义/文档导出
│   │   ├── physics_lab.py       # 虚拟物理实验模拟
│   │   ├── pptx_tool.py         # 教学 PPT 生成
│   │   └── web_search_tool.py   # 联网搜索
│   ├── web/
│   │   └── auth.py              # 注册 / 登录鉴权
│   ├── storage/
│   │   ├── database/            # 数据库 + 用户模型
│   │   ├── memory/              # 短期记忆（Postgres Checkpointer）
│   │   └── s3/                  # 对象存储
│   └── main.py                  # 服务入口（FastAPI）
└── pyproject.toml               # 依赖管理（uv）
```

---

## 🚀 快速开始

### 本地运行（Agent 对话）

```bash
bash scripts/local_run.sh -m flow
```

### 启动 HTTP 服务（含前端页面）

```bash
bash scripts/http_run.sh -m http -p 5000
```

启动后访问：

- 介绍页：`http://localhost:5000/`
- 注册 / 登录页：`http://localhost:5000/login`
- 对话页：`http://localhost:5000/chat`（登录后自动跳转）

### 部署后如何访问

在平台点「部署 / 发布」触发一次部署，成功后平台会生成一个访问入口（URL），复制并打开即可：

1. 打开入口即是**介绍页**，浏览功能亮点；
2. 点击「登录 / 注册」进入登录页，可用游客账号 `youke` / `123456`（灰色提示）或注册新账号；
3. 登录后自动跳转到**对话页**，可点击顶部快捷入口（如「🔬 物理具象化实验室」）一键体验特色功能。

### 前端使用说明

- **游客账号**：用户名 `youke`，密码 `123456`（已在登录框以灰色提示显示）
- **注册新账号**：在登录页切换到「注册」标签，填写用户名与密码即可，账号数据持久化存储

---

## 🧰 技术栈

LangChain · LangGraph · FastAPI · SQLAlchemy · PostgreSQL · Coze Coding SDK · Doubao-Seed-2.0 · uv

---

## 📌 项目信息

- **赛事方向**：教学赋能（智能备课 / 学情诊断 / 个性化辅导 / 智能评测 / 学习规划）
- **关于反馈**：欢迎提交 [Issue](https://github.com/galaxyxingjin/snnu-edu-agent/issues) 交流建议