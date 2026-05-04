# QuillPilot

[![License: MIT](https://img.shields.io/badge/License-MIT-00A1E0.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-032D60.svg)](pyproject.toml)
[![FastAPI](https://img.shields.io/badge/FastAPI-Local%20API-04844B.svg)](quillpilot/api.py)
[![Status](https://img.shields.io/badge/Status-v0.2%20development-FF9A3C.svg)](#roadmap)

**QuillPilot 是一个本地优先、编辑器无关的 AI 论文写作 Copilot。**

它不内置编辑器，而是通过本地 FastAPI 服务、Web 控制台、全局快捷键、剪贴板和后续插件机制，为 LaTeX、Markdown、Word、TeXstudio、VS Code 等任意写作环境提供从文献到成稿的智能辅助。

```text
PDF + BibTeX -> Repository -> Reading -> Writing -> Citation
```

## 目录

- [QuillPilot](#quillpilot)
  - [目录](#目录)
  - [核心定位](#核心定位)
  - [当前能力](#当前能力)
  - [界面结构](#界面结构)
  - [快速开始](#快速开始)
    - [1. 创建环境](#1-创建环境)
    - [2. 安装依赖](#2-安装依赖)
    - [3. 启动服务](#3-启动服务)
  - [配置模型](#配置模型)
  - [导入文献库](#导入文献库)
  - [本地 API](#本地-api)
  - [快捷键](#快捷键)
  - [项目结构](#项目结构)
  - [后续开发要求](#后续开发要求)
    - [产品要求](#产品要求)
    - [技术要求](#技术要求)
    - [体验要求](#体验要求)
    - [测试要求](#测试要求)
  - [Roadmap](#roadmap)
  - [开发与测试](#开发与测试)
  - [许可证](#许可证)

## 核心定位

QuillPilot 面向学术写作者，目标是让 AI 能够在用户已有编辑器中工作，而不是强迫用户迁移到新的编辑器。

| 原则 | 说明 |
| --- | --- |
| 本地优先 | 文献库、设置、检索索引默认保存在本机 |
| 编辑器无关 | 通过 API、快捷键、剪贴板和插件接入任意编辑器 |
| 引用可信 | LaTeX 引用只能来自已导入 BibTeX 的真实 key |
| 可替换模型 | 支持 OpenAI-compatible API 和本地 LLM endpoint |
| 低侵入工作流 | 用户复制选中文本，通过快捷键调用 Copilot，再将结果写回剪贴板 |

## 当前能力

| 模块 | 能力 |
| --- | --- |
| Repository | 导入 PDF 文件夹和 BibTeX 文件，解析论文文本并写入 SQLite，支持导入任务状态、真实库统计和文献去重 |
| Search | 优先使用 SQLite FTS5 检索标题、作者、BibTeX key、正文片段，未命中时退回关键词扫描 |
| Reading | 基于检索片段回答论文理解问题，并返回 source snippets |
| Writing | 支持润色、扩写、重写、摘要、提纲、反驳等写作辅助，并可附带检索来源 |
| Citation | 根据查询生成 `\cite{}`、`\citep{}`、`\citet{}`；多候选会按匹配可靠度排序，并可在控制台中选择真实 BibTeX key |
| Settings | 支持语言、字体、字号、API provider、本地 LLM、快捷键配置 |
| Hotkeys | Windows-first 全局快捷键与剪贴板工作流 |
| API | 暴露本地 HTTP API，便于后续插件或外部工具集成 |

可选能力：

- 安装 `.[vector]` 后自动启用 ChromaDB 向量索引。
- API provider 未配置 API key 时，读写接口仍会返回离线请求预览，便于调试。
- 本地 LLM provider 可调用不需要 API key 的 OpenAI-compatible endpoint，例如 Ollama 的 `/v1/chat/completions`。

## 界面结构

本地 Web 控制台地址：

```text
http://127.0.0.1:8765/
```

控制台分为四个互相独立的视图：

| 视图 | 路由 | 说明 |
| --- | --- | --- |
| Home | `#home` | 服务状态、数据库路径、导入指标 |
| Repository | `#repository` | PDF/BibTeX 导入、文献检索、结果表格 |
| Copilot | `#copilot` | 阅读问答、写作辅助、引用插入 |
| Settings | `#settings` | 通用设置、API 提供商、快捷键配置 |

语言切换会立即更新可见 UI/UX 文案，包括导航、标题、按钮、表单标签、placeholder、状态 chip、空状态和 toast。当前支持：

- 简体中文
- English
- Francais

## 快速开始

### 1. 创建环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
pip install -e .[dev,desktop]
```

可选向量检索后端：

```powershell
pip install -e .[vector]
```

### 3. 启动服务

```powershell
quillpilot-api
```

打开：

```text
http://127.0.0.1:8765/
```

## 配置模型

QuillPilot 默认使用 OpenAI-compatible Chat Completions API。

```powershell
$env:QUILLPILOT_API_KEY="your_api_key"
$env:QUILLPILOT_BASE_URL="https://api.openai.com/v1"
$env:QUILLPILOT_MODEL="gpt-4o-mini"
```

也可以在控制台中进入：

```text
Settings -> Providers
```

支持配置：

- OpenAI-compatible API
- 本地 LLM，例如 `http://127.0.0.1:11434/v1`
- 多 provider 管理
- 默认 provider 选择
- provider 启用和禁用

说明：

- `kind=api` 的 provider 需要 API key；未配置时会返回离线请求预览。
- `kind=local` 的 provider 不强制要求 API key，适合 Ollama、LM Studio 等本地 OpenAI-compatible endpoint。

## 导入文献库

通过控制台导入：

```text
Repository -> Knowledge Base
```

或通过 API 导入：

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8765/library/import `
  -ContentType "application/json" `
  -Body '{"pdf_dir":"F:\\papers","bib_file":"F:\\papers\\refs.bib"}'
```

v0.2 推荐使用任务式导入，便于前端或插件轮询状态：

```powershell
$task = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8765/library/import/tasks `
  -ContentType "application/json" `
  -Body '{"pdf_dir":"F:\\papers","bib_file":"F:\\papers\\refs.bib"}'

Invoke-RestMethod -Uri "http://127.0.0.1:8765/library/import/tasks/$($task.task_id)"
```

查看文献库统计：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8765/library/stats
```

当前限制：

- 只支持可抽取文本的 PDF。
- 扫描版 PDF OCR 暂未实现。
- 导入会按 PDF 路径、BibTeX key、DOI 和规范化标题复用已有论文记录，重复命中会返回 warning。
- 引用插入只使用已导入 BibTeX 中存在的 key。
- 查询命中多个引用候选时，控制台会按 BibTeX key、标题、作者、年份和关键词匹配可靠度排序，并要求选择其中一条，再生成并复制 LaTeX 引用命令。

## 本地 API

交互式 API 文档：

```text
http://127.0.0.1:8765/docs
```

| Method | Endpoint | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 查看服务状态、数据库路径、LLM 配置状态和文献库统计 |
| `GET` | `/settings` | 读取 UI、provider、快捷键设置 |
| `PUT` | `/settings` | 保存 UI、provider、快捷键设置 |
| `POST` | `/library/import` | 同步导入 PDF 目录和/或 BibTeX 文件，保留给脚本和兼容调用 |
| `POST` | `/library/import/tasks` | 创建异步导入任务 |
| `GET` | `/library/import/tasks/{task_id}` | 查询导入任务状态和结果 |
| `GET` | `/library/stats` | 查看论文数、BibTeX 条目数、chunk 数和最近导入任务状态 |
| `GET` | `/library/search?q=...` | 搜索本地文献库，优先使用 SQLite FTS5 |
| `POST` | `/read/ask` | 基于检索片段进行阅读问答 |
| `POST` | `/write/assist` | 执行润色、扩写、重写、摘要、提纲、反驳 |
| `POST` | `/cite/insert` | 根据真实 BibTeX key 生成 LaTeX 引用 |

## 快捷键

启动 API 后运行：

```powershell
quillpilot-hotkeys
```

默认快捷键：

| 快捷键 | 动作 |
| --- | --- |
| `Ctrl+Alt+R` | 读取剪贴板文本并执行阅读解释 |
| `Ctrl+Alt+W` | 对剪贴板文本进行学术润色 |
| `Ctrl+Alt+C` | 查找引用并复制 LaTeX 引用命令 |

快捷键可在控制台中修改：

```text
Settings -> Hotkeys
```

保存后需要重启 `quillpilot-hotkeys` 生效。

## 项目结构

```text
QuillPilot/
├─ quillpilot/
│  ├─ api.py              # FastAPI app and route wiring
│  ├─ bibtex.py           # BibTeX parsing
│  ├─ chunking.py         # Text chunking
│  ├─ config.py           # Environment and local data paths
│  ├─ db.py               # SQLite schema and connection helper
│  ├─ hotkeys.py          # Clipboard and global hotkey client
│  ├─ library.py          # Import, search, citation core
│  ├─ llm.py              # OpenAI-compatible LLM provider
│  ├─ models.py           # Pydantic request/response/settings models
│  ├─ pdf.py              # PDF text extraction
│  ├─ search.py           # Keyword search and optional Chroma adapter
│  ├─ user_settings.py    # Persisted app settings service
│  └─ static/             # Web console UI
├─ tests/                 # Unit and API tests
├─ DESIGN.md              # Cloud Tower UI design system
├─ LICENSE                # MIT License
├─ pyproject.toml         # Package metadata and dependencies
└─ README.md
```

## 后续开发要求

### 产品要求

- 保持“无内置编辑器”的定位，优先增强本地 API、快捷键、剪贴板和插件接入能力。
- 所有引用相关能力必须基于真实导入的 BibTeX key，不允许生成不存在的引用。
- 知识库导入和检索结果必须明确来源，阅读回答需要返回 source snippets。
- 设置项必须持久化，并且 UI 改动应尽可能即时生效。
- 多语言新增文案必须进入统一 i18n 字典，不允许硬编码散落在 HTML 或 JS 逻辑中。

### 技术要求

- Python 版本保持 `>=3.11`。
- 后端接口使用 Pydantic model 定义请求和响应结构。
- 本地持久化优先使用 SQLite；新增表结构必须兼容已有用户数据。
- ChromaDB 继续保持可选依赖，不能让基础安装依赖向量后端。
- OpenAI-compatible provider 抽象需要保持可替换，不应把供应商逻辑写死在业务层。
- 前端继续使用轻量静态资源托管，除非有明确理由，不引入 Node 构建链。
- UI 必须遵守 `DESIGN.md` 的 Cloud Tower 设计规范。

### 体验要求

- 四个主视图 Home、Repository、Copilot、Settings 必须保持互相独立。
- 页面上的文字、placeholder、按钮、状态、toast 都必须响应语言切换。
- 数据密集页面优先使用表格、紧凑输入和明确状态 chip。
- 快捷键相关变更需要说明是否需要重启 hotkey 客户端。
- 错误提示要说明用户能采取的下一步动作。

### 测试要求

- 新增 API 必须有 FastAPI TestClient 覆盖。
- 修改导入、检索、引用、设置持久化逻辑时必须增加回归测试。
- 修改前端静态资源时至少覆盖 UI 文件可服务、关键路由标记和 i18n 标记。
- 发布前必须运行：

```powershell
pytest
python -m pip install -e . --dry-run
```

## Roadmap

| 阶段 | 目标 |
| --- | --- |
| v0.1 | 本地 API、PDF/BibTeX 导入、检索、写作辅助、引用插入、设置界面 |
| v0.2 | 进行中：导入任务状态、真实库统计、FTS5 检索、本地 LLM provider 修正、source snippets 展示、引用候选选择与排序、文献去重；后续补 OCR |
| v0.3 | VS Code / Word / TeXstudio 插件适配 |
| v0.4 | 更完整的本地模型管理、embedding provider 管理 |
| v0.5 | 项目级写作上下文、章节级大纲、审稿意见工作流 |

## 开发与测试

运行测试：

```powershell
pytest
```

检查前端静态脚本语法：

```powershell
node --check quillpilot\static\app.js
```

手动启动 API：

```powershell
python -m uvicorn quillpilot.api:app --host 127.0.0.1 --port 8765
```

验证安装元数据：

```powershell
python -m pip install -e . --dry-run
```

## 许可证

QuillPilot 基于 [MIT License](LICENSE) 开源。
