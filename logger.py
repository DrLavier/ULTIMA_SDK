"""logger.py — 纯日志 API（无 Qt widget 依赖）。

整合在一个文件内的三类东西：

- 全局可见性开关（DEBUG_FLAG / INFO_FLAG）+ set/get
- LogSignal：跨线程信号中枢
- log / log_info / log_debug / log_warning / log_error / log_success：顶层便捷函数
- LoguruHandler / install_loguru_bridge：可选 loguru 桥接

设计取舍：本文件只负责「往 LogSignal 上发信号」+「往 loguru 上写日志」两件事，
渲染层在 ui.CmdLogWidget 内完成。这样 logger.py 在 headless 测试 / CLI 下也能直接用。
"""

from __future__ import annotations

from pathlib import Path
import sys
import threading
from typing import Optional

from loguru import logger

from PyQt6.QtCore import QObject, pyqtSignal


# =============================================================================
# 终端输出（loguru sink）
# =============================================================================
# 默认 loguru 输出冗余（时间戳 + 模块:函数:行号）。这里改为 "LEVEL    | message"
# 简洁格式，并通过自定义 sink 让 wrap=False 的进度行用 \r 覆写而不刷屏。
_progress_active = False
_progress_lock = threading.Lock()


def _resolve_logs_dir() -> Path:
    from .sys import Paths
    return Paths.get_logs_dir()


def _terminal_sink(message):
    """自定义 loguru sink：根据 record.extra['progress'] 决定换行 vs 回车覆写。"""
    global _progress_active
    record = message.record
    is_progress = bool(record["extra"].get("progress", False))
    text = str(message).rstrip("\n")

    with _progress_lock:
        if is_progress:
            # 清整行 + 回车 + 写入（不换行），下一次再覆写
            sys.stderr.write("\033[2K\r" + text)
            sys.stderr.flush()
            _progress_active = True
        else:
            # 从进度行切回普通行：先补一个换行收尾
            if _progress_active:
                sys.stderr.write("\n")
                _progress_active = False
            sys.stderr.write(text + "\n")
            sys.stderr.flush()


def _install_log_sinks() -> None:
    """重置 loguru 默认 sink，并安装终端与文件 sink。幂等。"""
    logs_dir = _resolve_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        _terminal_sink,
        level="DEBUG",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    logger.add(
        logs_dir / "sdk_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        encoding="utf-8",
    )


_install_log_sinks()


# =============================================================================
# 全局可见性开关（GUI 控制）
# =============================================================================
DEBUG_FLAG: bool = False  # 默认关闭：debug 行平时不展示
INFO_FLAG: bool = True    # 默认打开：info 行平时展示


def set_debug_flag(value: bool) -> None:
    global DEBUG_FLAG
    DEBUG_FLAG = bool(value)


def get_debug_flag() -> bool:
    return DEBUG_FLAG


def set_info_flag(value: bool) -> None:
    global INFO_FLAG
    INFO_FLAG = bool(value)


def get_info_flag() -> bool:
    return INFO_FLAG


# =============================================================================
# LogSignal — 跨线程信号中枢（懒加载单例）
# =============================================================================
class LogSignal(QObject):
    """所有日志通过本类的 ``log_message`` 信号在线程间安全传递。"""

    log_message = pyqtSignal(str, str, bool, bool)  # (text, log_type, wrap, typer)

    _instance: Optional["LogSignal"] = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls) -> "LogSignal":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def emit_log(self, text: str, log_type: str = "info", wrap: bool = True, typer: bool = False):
        self.log_message.emit(text, log_type, wrap, typer)

    def debug(self, text, wrap=True, typer=False):
        self.emit_log(text, "debug", wrap, typer)

    def info(self, text, wrap=True, typer=False):
        self.emit_log(text, "info", wrap, typer)

    def warning(self, text, wrap=True, typer=False):
        self.emit_log(text, "warning", wrap, typer)

    def error(self, text, wrap=True, typer=False):
        self.emit_log(text, "error", wrap, typer)

    def success(self, text, wrap=True, typer=False):
        self.emit_log(text, "success", wrap, typer)


def get_log_signal() -> LogSignal:
    return LogSignal.instance()


# =============================================================================
# 顶层便捷函数（同时打到 loguru 系统输出 + 内置屏幕）
# =============================================================================
def log(text, log_type: str = "info", wrap: bool = True, typer: bool = False):
    get_log_signal().emit_log(str(text), log_type, wrap, typer)


def _bind(wrap: bool):
    """绑定 progress 标记给 sink；wrap=False 时让 sink 用 \\r 覆写。"""
    return logger.bind(progress=not wrap)


def log_info(text, wrap=True, typer=False):
    text = str(text)
    get_log_signal().info(text, wrap, typer)
    _bind(wrap).info(text)


def log_debug(text, wrap=True, typer=False):
    text = str(text)
    _bind(wrap).debug(text)  # 文件日志不受 DEBUG_FLAG 影响
    # 始终向 widget 发射；由 widget 按当前 DEBUG_FLAG 过滤渲染。
    # 这样切换开关时可重渲染历史，已显示的 debug 行也能动态隐藏/恢复。
    get_log_signal().debug(text, wrap, typer)


def log_warning(text, wrap=True, typer=False):
    text = str(text)
    get_log_signal().warning(text, wrap, typer)
    _bind(wrap).warning(text)


def log_error(text, wrap=True, typer=False):
    text = str(text)
    get_log_signal().error(text, wrap, typer)
    _bind(wrap).error(text)


def log_success(text, wrap=True, typer=False):
    text = str(text)
    get_log_signal().success(text, wrap, typer)
    _bind(wrap).success(text)


# =============================================================================
# LoguruHandler — 可选桥接
# =============================================================================
class LoguruHandler:
    """把任何 ``from loguru import logger`` 的输出镜像到内置 cmd 屏。"""

    def write(self, message):
        record = message.record
        level = record["level"].name.lower()
        text = record["message"]

        level_map = {
            "trace": "debug",
            "debug": "debug",
            "info": "info",
            "success": "success",
            "warning": "warning",
            "error": "error",
            "critical": "error",
        }
        log_type = level_map.get(level, "info")
        get_log_signal().emit_log(text, log_type, wrap=True, typer=False)


_loguru_installed = False


def install_loguru_bridge() -> None:
    """安装 LoguruHandler。

    幂等。注意：装上后 ``log_info`` 等会在内置屏渲染两次（直接 emit + 经 loguru 回灌），
    仅当你需要把第三方库里 ``logger.info(...)`` 也镜像到 widget 时才装。
    """
    global _loguru_installed
    if _loguru_installed:
        return
    logger.add(LoguruHandler(), level="DEBUG", format="{message}")
    _loguru_installed = True
