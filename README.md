# ULTIMA_SDK

A reusable PyQt6 application SDK / 一个可复用的 PyQt6 应用 SDK

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](requirements.txt)
[![PyQt](https://img.shields.io/badge/PyQt-6-green.svg)](requirements.txt)

---

## 简介 / Introduction

**中文**

ULTIMA_SDK 是我使用 Claude 从过往个人项目中沉淀、整理出的一份通用 SDK 框架，
目标是在不同的 Python 环境下被生产项目快速复用，做到「拷过去就能用」的前端 UI 部署体验。

核心特性：

- **快速前端 UI 部署**：开箱即用的主题化 Qt 控件族（按钮 / 标签 / 进度条 / 下拉框 / 滑动开关 / 滚轮选择器 / 标签输入 / 复选项 / 分组框）。
- **多槽位线程管理器**：内置 `TasksManager`，支持 N 路并发槽位、FIFO 队列、可中断 `sleep`、跨线程进度上报与统一取消。
- **二进制文件安全读写**：`DataManager` 统一封装 INI/JSON/YAML/TOML/pickle/parquet/xlsx/csv/text/bytes 的原子读写，避免半写文件损坏。
- **I18n 多语种支持**：三级回退（当前语种 → 英文 base → key 字面量），并支持 **导出 key 列表** 用于交付翻译。
- **崩溃钩子 / 日志中枢**：`install_crash_hook` 接管子线程异常；`LogSignal` 跨线程汇聚日志到 `CmdLogWidget`。

授权协议：**Apache License 2.0**。

**English**

ULTIMA_SDK is a general-purpose SDK framework that I distilled from my prior personal
projects with the help of Claude. The goal is fast reuse across different Python
environments — drop the package into any production project and get a working frontend
out of the box.

Highlights:

- **Fast frontend deployment** — a themed family of Qt widgets (button, label, progress
  bar, combo box, slider switch, wheel selector, tag input, checkbox item, group box).
- **Multi-slot thread manager** — `TasksManager` with N concurrent slots, FIFO queueing,
  interruptible `sleep`, cross-thread progress reporting, and unified cancellation.
- **Safe atomic file I/O** — `DataManager` wraps INI / JSON / YAML / TOML / pickle /
  parquet / xlsx / csv / text / bytes with atomic writes, so partial-write corruption
  cannot happen.
- **I18n with translation export** — three-tier fallback (current locale → English base
  → key literal); key tables can be **exported** for translators.
- **Crash hook & log hub** — `install_crash_hook` captures uncaught exceptions on worker
  threads; `LogSignal` funnels cross-thread logs into `CmdLogWidget`.

License: **Apache License 2.0**.

---

## Requirements

```
PyQt6
loguru
```

可选依赖（按需启用 `DataManager` 的特定格式 / optional, enable only when the matching
`DataManager` format is used）：

```
pyyaml          # YAML
pandas          # parquet / xlsx / csv (DataFrame I/O)
tomli           # TOML read on Python < 3.11
tomli_w         # TOML write
openpyxl        # xlsx engine for pandas
pyarrow         # parquet engine for pandas
```

详见 [`requirements.txt`](requirements.txt) / See [`requirements.txt`](requirements.txt) for details.

---

## 文件树 / File Tree

```
ULTIMA_SDK/
├── __init__.py              # 包入口；统一从这里 import / single import entry point
├── logger.py                # 日志 API：LogSignal / log_X / LoguruHandler
├── sys.py                   # 系统设施：Paths / Config / CrashHook / DataManager / I18n / Tasks
├── ui.py                    # Qt 控件家族：TyperThread / SwitchButton / CmdLogWidget / Lavi*
├── demo.py                  # 端到端调用示例（推荐入口） / end-to-end demo (recommended entry)
├── sdk.skill.yaml           # Agent 对接说明（可作为正式 Skill 化的基础） / agent-facing skill spec
├── requirements.txt
├── LICENSE                  # Apache 2.0
├── README.md
│
├── config/
│   └── sdk.ini              # 主题色 / 字号 / 控件参数 / 当前语种 / 外部路径覆盖
│
├── assets/                  # 内置资产 / bundled assets
│   ├── icon/                # SVG 图标（自绘） / hand-drawn SVG icons
│   │   ├── icon_close.svg
│   │   ├── icon_mini.svg
│   │   ├── icon_move.svg
│   │   ├── icon_no.svg / icon_yes.svg
│   │   ├── icon_pause.svg / icon_play.svg / icon_stop.svg
│   │   ├── icon_rename.svg / icon_reset.svg / icon_setting.svg
│   │   └── icon_zone_in.svg / icon_zone_out.svg
│   └── sound/               # 音效（可商用） / royalty-free SFX
│       ├── beep.wav
│       ├── notify.wav
│       ├── picked.wav
│       └── slip.wav
│
├── localisation/            # ★ 翻译表目录（可被 sdk.ini → [Localisation].dir 重定向到外部）
│   │                        # ★ Locale tables (can be redirected to an external dir
│   │                        #   via sdk.ini → [Localisation].dir)
│   ├── EN.txt               # 英文 base，缺失键回退到此 / English base, fallback target
│   ├── FR.txt
│   └── ZH_S.txt
│
└── logs/                    # 运行时生成 / runtime-generated
```

> ★ **可外置目录 / Externally-redirectable paths**
>
> - `localisation/` 可在 `config/sdk.ini` 的 `[Localisation].dir` 字段被指向项目外的翻译表目录。
>   Can be redirected via `[Localisation].dir` in `config/sdk.ini` to a translation
>   directory outside the package.
> - `assets/` 与 `logs/` 同样支持通过 `[Resources].assets_dir` / `[Resources].logs_dir`
>   覆盖为补充路径，实现「内置资产 + 项目自有资产」共存。
>   `assets/` and `logs/` accept `[Resources].assets_dir` / `[Resources].logs_dir`
>   overrides so that bundled assets coexist with project-supplied assets.

---

## 内置资产声明 / Bundled Assets Statement

**中文**

- **音效（`assets/sound/`）** — `beep.wav` / `notify.wav` / `picked.wav` / `slip.wav`
  均为**可商用**音效（royalty-free），可随本 SDK 一同分发与商用。
- **图标（`assets/icon/`）** — 全部 SVG 图标均由本人**自绘**，随 SDK 以 Apache 2.0 协议授权。

**English**

- **Sound effects (`assets/sound/`)** — `beep.wav`, `notify.wav`, `picked.wav`, `slip.wav`
  are **royalty-free** and may be redistributed and used commercially together with this SDK.
- **Icons (`assets/icon/`)** — all SVG icons are **hand-drawn by the author** and
  released under Apache 2.0 along with the SDK.

---

## sdk.skill.yaml — Agent 对接清单 / Agent-facing Skill Spec

`sdk.skill.yaml` 是为 **Agent 快速对接** 而准备的结构化说明：它声明了 SDK 的导入入口、
核心 API、调用规则与边界条件，可让 LLM/Agent 在零探索成本下正确调用本 SDK。该文件
也可作为后续将 SDK **正式 Skill 化** 的基础（直接演化为 Claude Skill / 其他 Agent
平台的 skill 描述文件）。

`sdk.skill.yaml` is a structured spec written for **agent onboarding**: it declares the
import entry point, core APIs, invocation rules, and boundary conditions so that an
LLM/agent can call this SDK correctly with zero exploration. It also serves as the
foundation for **promoting the SDK to a formal Skill** (e.g. directly evolving into a
Claude Skill or any other agent-platform skill manifest).

---

## demo.py — 调用示例 / Call-site Example

`demo.py` 是一份**端到端调用示例**，演示了 SDK 的全部核心能力如何协同工作 —— 包括
日志中枢、`Task` 子类、N 槽并发、单行进度条所有权、I18n 绑定、崩溃钩子，以及主题化
控件的组装方式。新接入项目时建议**直接对照 `demo.py` 抄写最小骨架**，再按需裁剪。

`demo.py` is an **end-to-end call-site example** that exercises every core capability
together — log hub, `Task` subclassing, N-slot concurrency, single-owner progress line,
I18n binding, crash hook, and themed widget composition. When wiring the SDK into a new
project, the recommended starting point is to **copy the minimal skeleton from `demo.py`**
and trim from there.

运行 / Run:

```bash
# 推荐 / preferred
python -m ULTIMA_SDK.demo

# 也可直接运行 / or run directly
python demo.py
```

---

## License

Released under the **Apache License 2.0** — see [`LICENSE`](LICENSE).
