"""ULTIMA_SDK：从 ULTIMA 抽出的可复用基础设施。

仅 3 个内部模块，各自一类职责：

- :mod:`logger` — 日志 API（LogSignal / log_X / LoguruHandler）
- :mod:`ui`     — Qt 控件（TyperThread / SwitchButton / CmdLogWidget）
- :mod:`sys`    — 系统设施（Paths / Config / CrashHook / Task 系统）

最小用法：

    from ULTIMA_SDK import (
        log_info, install_crash_hook,
        get_tasks_manager, Task, CmdLogWidget,
    )

    install_crash_hook()
    log_info("应用启动")

    class DownloadTask(Task):
        def run(self):
            for i in range(100):
                self.progress_line(i / 100, f"下载 {i}/100")
                self.sleep(0.05)

    get_tasks_manager().submit(DownloadTask("下载"))
"""

# ---- logger -----------------------------------------------------------
from .logger import (
    LogSignal,
    LoguruHandler,
    install_loguru_bridge,
    set_debug_flag,
    get_debug_flag,
    set_info_flag,
    get_info_flag,
    log,
    log_info,
    log_success,
    log_warning,
    log_error,
    log_debug,
)

# ---- sys --------------------------------------------------------------
from .sys import (
    # 基础设施
    Paths,
    Config,
    CrashHook,
    install_crash_hook,
    uninstall_crash_hook,
    # 通用文件 I/O
    DataManager,
    load_data,
    read_data,
    up_data,
    save_data,
    get_data_value,
    # 资源查找
    Assets,
    # i18n
    I18n,
    tr,
    # 任务系统
    Task,
    TaskCancelledException,
    TaskStatus,
    TaskSignal,
    TaskWorker,
    TaskSlot,
    TasksManager,
    get_tasks_manager,
    get_task_signal,
    set_max_slots,
)

# ---- ui ---------------------------------------------------------------
from .ui import (
    TyperThread,
    SwitchButton,
    CmdLogWidget,
    I18nLabel,
    I18nButton,
    i18n_bind,
    LaviButton,
    setButton,
    LaviLabel,
    setText,
    LaviProgressBar,
    SettingConfirm,
    LaviComboBox,
    setComboBox,
    TitleGroupBox,
    setTitleGroupBox,
    WheelSelector,
    setWheelSelector,
    SliderSwitch,
    setSliderSwitch,
    TagInput,
    setTagInput,
    CheckboxItem,
    setCheckboxItem,
)

# 兼容别名：`from ULTIMA_SDK import config` 仍可用作 Config
config = Config

# 导入 SDK 时初始化 i18n（读 sdk.ini 的 [Localisation].lang，加载默认语种 + EN base）
I18n.init()


__version__ = "1.1.0"

__all__ = [
    # logger
    "LogSignal",
    "LoguruHandler",
    "install_loguru_bridge",
    "set_debug_flag",
    "get_debug_flag",
    "set_info_flag",
    "get_info_flag",
    "log",
    "log_info",
    "log_success",
    "log_warning",
    "log_error",
    "log_debug",
    # sys (infra)
    "Paths",
    "Config",
    "config",
    "CrashHook",
    "install_crash_hook",
    "uninstall_crash_hook",
    # sys (data I/O)
    "DataManager",
    "load_data",
    "read_data",
    "up_data",
    "save_data",
    "get_data_value",
    # sys (assets)
    "Assets",
    # sys (i18n)
    "I18n",
    "tr",
    # sys (tasks)
    "Task",
    "TaskCancelledException",
    "TaskStatus",
    "TaskSignal",
    "TaskWorker",
    "TaskSlot",
    "TasksManager",
    "get_tasks_manager",
    "get_task_signal",
    "set_max_slots",
    # ui
    "TyperThread",
    "SwitchButton",
    "CmdLogWidget",
    "I18nLabel",
    "I18nButton",
    "i18n_bind",
    "LaviButton",
    "setButton",
    "LaviLabel",
    "setText",
    "LaviProgressBar",
    "SettingConfirm",
    "LaviComboBox",
    "setComboBox",
    "TitleGroupBox",
    "setTitleGroupBox",
    "WheelSelector",
    "setWheelSelector",
    "SliderSwitch",
    "setSliderSwitch",
    "TagInput",
    "setTagInput",
    "CheckboxItem",
    "setCheckboxItem",
]
