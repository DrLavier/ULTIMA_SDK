"""ULTIMA_SDK 端到端演示 / End-to-end demo for ULTIMA_SDK.

运行 / Run:
    python -m ULTIMA_SDK.demo

验证点 / Things this demo verifies:
    - cmd 屏与系统终端日志同步
      The in-app cmd screen mirrors the system terminal log.
    - cmd 屏单行进度条：单一所有者，多任务并发时只一个 task 占 cmd 屏
      Single-line progress bar in the cmd screen has a single owner —
      only one task at a time is allowed to drive that line.
    - 图形进度条：每个 slot 一根，所有任务的进度都准确显示
      Graphical progress bars: one per slot, each showing its own task's
      progress accurately even with multiple concurrent tasks.
    - 5 级分类颜色
      Five log severity levels rendered with distinct colors.
    - DEBUG 切换：开关 OFF 时已显示的 debug 行立即被隐藏
      DEBUG toggle: turning the switch OFF immediately hides debug lines
      that are already on screen (and turning it back ON restores them).
    - sys.excepthook 捕获子线程异常
      sys.excepthook catches exceptions raised on worker threads.
    - max_slots=2 时 5 个任务按 FIFO 排队
      With max_slots=2, the 5 submitted tasks queue up in FIFO order.
"""

from __future__ import annotations

import os
import sys

# 让 demo.py 既能 ``python -m ULTIMA_SDK.demo`` 运行（推荐），也能直接
# ``python demo.py`` 双击运行：后者下 __package__ 为空，下面的相对导入会失败，
# 所以补上父目录到 sys.path 并把 __package__ 改写成包名再继续。
# Allow demo.py to be launched both as ``python -m ULTIMA_SDK.demo``
# (preferred) and as a bare ``python demo.py`` script. In the latter
# case __package__ is empty and the relative import below would fail,
# so we put the SDK's parent dir on sys.path and pin __package__ to
# the package name before the import block runs.
if __package__ in (None, ""):
    _sdk_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(_sdk_dir))
    __package__ = os.path.basename(_sdk_dir)

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import (
#---- Logger ----#
    log_debug,
    log_error,
    log_info,
    log_success,
    log_warning,
#---- Sys Func ----#
    I18n,
    tr,
    install_crash_hook,
    Task,
    get_task_signal,
    get_tasks_manager,
    i18n_bind,
    I18nButton,
    set_max_slots,
#---- UI ----#
    CmdLogWidget,
    LaviButton,
    LaviProgressBar,
    setButton,
    setCheckboxItem,
    setComboBox,
    setSliderSwitch,
    setTagInput,
    setText,
    setTitleGroupBox,
    setWheelSelector,
)


# ---------------------------------------------------------------------------
# 演示任务 / Demo tasks
# ---------------------------------------------------------------------------
class ProgressTask(Task):
    """长进度任务，用于验证 cmd 单行覆写 + 多任务图形进度条。

    Long-running progress task used to verify single-line cmd-screen
    overwrite behaviour together with multi-task graphical progress bars.
    """

    def __init__(self, name="Progress", steps: int = 60, interval: float = 0.05):
        super().__init__(name)
        self._steps = steps
        self._interval = interval

    def run(self):
        self.log_info("started")
        for i in range(self._steps + 1):
            # Cooperative cancellation point — raises if the task was cancelled.
            self.check_cancelled()
            self.progress_line(i / self._steps, f"step {i}/{self._steps}")
            self.sleep(self._interval)
        self.log_success("done")
        return "ok"


class CategoryTask(Task):
    """5 级分类日志颜色测试。

    Exercises all five log severity levels so their colors can be
    inspected on the cmd screen.
    """

    def run(self):
        # Each line is prefixed with its severity name so the colour
        # mapping is obvious at a glance.
        log_info("info line — generic information")
        log_success("success line — operation succeeded")
        log_warning("warning line — heads-up")
        log_error("error line — does NOT exit the app")
        log_debug("debug line #1 — only visible while the DEBUG switch is ON")
        log_debug("debug line #2 — must hide/restore in sync when the switch is toggled")
        return "categories shown"


class CrashTask(Task):
    """故意触发未捕获异常，验证崩溃 hook + 任务自身 FAILED 状态。

    Deliberately raises an uncaught exception to verify both the global
    crash hook and that the task itself transitions to the FAILED state.
    """

    def run(self):
        self.log_info("about to raise ZeroDivisionError")
        self.sleep(0.3)
        return 1 / 0


# ---------------------------------------------------------------------------
# 主窗口 / Main window
# ---------------------------------------------------------------------------
class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 窗口标题走 i18n / Bind window title through i18n so it reflects
        # language switches at runtime.
        i18n_bind(self, "setWindowTitle", "demo.window_title", default="ULTIMA_SDK Demo")
        self.resize(1000, 1000)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)

        # ---- 语种切换栏 / Language switch row ---------------------------
        lang_row = QHBoxLayout()
        lang_row.addWidget(setText("demo.lang_label", default="Language:", kind="content"))
        # LaviComboBox：非 editable + hightlight + i18n。
        # 项 key 仍是裸语言代码（EN / FR / ZH_S），由 tr() 路由到
        # 各翻译文件 [default] 段下的 en / fr / zh_s 条目作为显示文本，
        # 因此当前语种下能看到 "简体中文" / "Français" / "English" 等本地化名称。
        # 关键：监听 currentIndexChanged 而不是 currentTextChanged——后者发的
        # 是显示文本（"简体中文"），不是稳定的代码；用 currentKey() 拿到的才是
        # 写回 sdk.ini 的真正语言代码。
        # Localised picker: items are bare language codes so tr() routes
        # each one through [default].<code> in every locale file, giving
        # localised display text ("简体中文" / "Français" / "English"). We
        # listen on currentIndexChanged — not currentTextChanged — because
        # the latter sends the *translated* label, while currentKey() is
        # the stable code we actually want to write back to sdk.ini.
        self._lang_combo = setComboBox([], height=28, hightlight=True)
        self._reload_languages()
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lang_row.addWidget(self._lang_combo)

        # Themed export button via LaviButton (border + notice spec for an
        # accented outline). LaviButton inherits I18nButton, so the label
        # still re-translates automatically on language switch.
        btn_export = LaviButton(
            "demo.export_btn",
            default="Export Translation Template",
            kind="border",
            spec="notice",
            height=28,
        )
        btn_export.clicked.connect(self._export_template)
        lang_row.addWidget(btn_export)

        # 第二个只读 LaviComboBox：演示 (key, default) 元组形式 + currentKey()
        # A second read-only combo box, demonstrating the (key, default)
        # tuple item format and currentKey() lookup.
        lang_row.addSpacing(20)
        lang_row.addWidget(setText(
            "demo.fruit_label", default="Fruit:", kind="content"
        ))
        self._fruit_combo = setComboBox(
            [
                ("demo.fruit.apple",      "Apple"),
                ("demo.fruit.banana",     "Banana"),
                ("demo.fruit.cherry",     "Cherry"),
                ("demo.fruit.dragon",     "Dragonfruit"),
                ("demo.fruit.elderberry", "Elderberry"),
                ("demo.fruit.fig",        "Fig"),
                ("demo.fruit.grape",      "Grape"),
            ],
            width=180, height=28,
        )
        self._fruit_combo.currentIndexChanged.connect(
            lambda _idx: log_info(
                f"fruit combo → key={self._fruit_combo.currentKey()} "
                f"text={self._fruit_combo.currentText()!r}"
            )
        )
        lang_row.addWidget(self._fruit_combo)

        lang_row.addStretch()
        root.addLayout(lang_row)

        # ---- 槽位图形进度条区 / Slot graphical progress bars ------------
        # One LaviProgressBar per slot. Each bar subscribes to TaskSignal
        # and renders the progress + status of whichever task is currently
        # occupying that slot.
        slots_group = setTitleGroupBox(
            "demo.slots_group",
            default="Slot status (LaviProgressBar — auto-renders concurrent task progress & state)",
        )
        slots_layout = QVBoxLayout(slots_group)
        slots_layout.setContentsMargins(10, 16, 10, 10)
        slots_layout.setSpacing(8)

        self._progress_bars: list[LaviProgressBar] = []

        mgr = get_tasks_manager()
        for i in range(mgr.max_slots):
            bar = LaviProgressBar(
                task_key="",
                default_name=f"Slot {i}",
                total=100,
                slot_idx=i,
            )
            slots_layout.addWidget(bar)
            self._progress_bars.append(bar)
        root.addWidget(slots_group)

        # ---- setButton 风格展示（3 kind × 4 spec = 12 按钮 + 3 状态按钮）
        # setButton style showcase: a 3-kind × 4-spec matrix of 12 buttons
        # plus extra state-variant buttons (disabled / checkable / icon).
        btn_group = setTitleGroupBox(
            "demo.btn_group",
            default="setButton factory showcase (kind × spec matrix)",
        )
        grid = QGridLayout(btn_group)
        grid.setContentsMargins(10, 16, 10, 10)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        kinds = ["normal", "border", "light"]
        specs = ["none", "notice", "save", "danger"]

        # 列头 / Column headers — one per spec
        for c, sp in enumerate(specs):
            grid.addWidget(setText("", default=sp, kind="title"), 0, c + 1, alignment=Qt.AlignmentFlag.AlignCenter)
        # 行头 + 矩阵 / Row headers + the kind × spec button matrix
        for r, kd in enumerate(kinds):
            grid.addWidget(setText("", default=kd, kind="title"), r + 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
            for c, sp in enumerate(specs):
                key = f"demo.btn.{kd}.{sp}"
                btn = setButton(
                    key, 110, 34,
                    kind=kd, spec=sp,
                    default=sp.upper(),
                    checkable=True,
                )
                btn.clicked.connect(
                    lambda c, k=key: log_info(f"clicked → {k} ({'ON' if c else 'OFF'})")
                )
                grid.addWidget(btn, r + 1, c + 1)

        # 额外状态行：disabled / checkable / icon override
        # Extra row: disabled / checkable / colour override / icon variants.
        extra_row = QHBoxLayout()
        extra_row.setSpacing(5)
        btn_dis = setButton("demo.btn.disabled", 110, 34,
                            kind="normal", spec="none",
                            default="DISABLED", disabled=True)
        btn_chk = setButton("demo.btn.checkable", 130, 34,
                            kind="border", spec="notice",
                            default="CHECKABLE", checkable=True)
        btn_chk.clicked.connect(
            lambda c: log_info(f"checkable → {'ON' if c else 'OFF'}"))
        btn_ov = setButton("demo.btn.override", 130, 34,
                           kind="normal", spec="none",
                           default="OVERRIDE",
                           bg_color="#E872E8", font_color="#000000")
        btn_ov.clicked.connect(lambda: log_info("override clicked"))
        # 演示内置 SVG 图标自动解析（仅传 stem，自动找 assets/icon/icon_play.svg）
        # Built-in SVG icon auto-resolution: pass only the stem and the
        # SDK looks up assets/icon/icon_play.svg automatically.
        btn_icon = setButton("demo.btn.icon", 130, 34,
                             kind="border", spec="save",
                             default="ICON",
                             icon="icon_play")
        btn_icon.clicked.connect(lambda: log_info("icon clicked"))
        # 纯图标按钮：方形尺寸 + icon_only=True 跳过 i18n 文本绑定
        # Icon-only button: square geometry plus icon_only=True skips i18n
        # text binding entirely.
        btn_icon_only_play = setButton("", 34, 34,
                                       kind="light", spec="save",
                                       icon="icon_play", icon_only=True)
        btn_icon_only_play.clicked.connect(lambda: log_info("icon-only play"))
        btn_icon_only_stop = setButton("", 34, 34,
                                       kind="light", spec="danger",
                                       icon="icon_stop", icon_only=True)
        btn_icon_only_stop.clicked.connect(lambda: log_info("icon-only stop"))
        btn_icon_only_set = setButton("", 34, 34,
                                      kind="border", spec="none",
                                      icon="icon_setting", icon_only=True)
        btn_icon_only_set.clicked.connect(lambda: log_info("icon-only setting"))
        extra_row.addWidget(btn_dis)
        extra_row.addWidget(btn_chk)
        extra_row.addWidget(btn_ov)
        extra_row.addWidget(btn_icon)
        extra_row.addWidget(btn_icon_only_play)
        extra_row.addWidget(btn_icon_only_stop)
        extra_row.addWidget(btn_icon_only_set)
        extra_row.addStretch()
        grid.addLayout(extra_row, len(kinds) + 1, 0, 1, len(specs) + 1)

        root.addWidget(btn_group)

        # ---- misc 组件展示 / Misc widget showcase ------------------------
        misc_group = setTitleGroupBox(
            "demo.misc_group",
            default="Misc widgets (WheelSelector / SliderSwitch / TagInput / CheckboxItem)",
        )
        misc_row = QHBoxLayout(misc_group)
        misc_row.setContentsMargins(10, 16, 10, 10)
        misc_row.setSpacing(12)

        wheel = setWheelSelector(
            [
                ("demo.wheel.apple",  "Apple"),
                ("demo.wheel.banana", "Banana"),
                ("demo.wheel.cherry", "Cherry"),
                ("demo.wheel.dragon", "Dragonfruit"),
                ("demo.wheel.elder",  "Elderberry"),
            ],
            visible_count=5, radius=70, i18n=True,
        )
        wheel.setFixedSize(180, 180)
        wheel.currentIndexChanged.connect(
            lambda idx, raw: log_info(f"wheel → idx={idx} key={raw}")
        )
        wheel.item_activated.connect(
            lambda idx, raw: log_success(f"wheel activated → {raw}")
        )
        misc_row.addWidget(wheel)

        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        slider = setSliderSwitch(
            [
                ("demo.size.s", "Small"),
                ("demo.size.m", "Medium"),
                ("demo.size.l", "Large00000000"),
            ],
            height=44,  # 演示 height 参数生效（默认 32）/ overrides default 32
        )
        slider.current_changed.connect(
            lambda idx, key: log_info(f"slider → idx={idx} key={key}")
        )
        right_col.addWidget(slider, alignment=Qt.AlignmentFlag.AlignLeft)

        tags = setTagInput(
            mode="input",
            placeholder_key="demo.tag.placeholder",
            placeholder="Press Enter to add a tag",
        )
        tags.changed.connect(lambda: log_info(f"tags → {tags.get_values()}"))
        right_col.addWidget(tags)

        chk_row = QHBoxLayout()
        chk_row.setSpacing(20)
        chk_notify = setCheckboxItem("demo.check.notify", default="Enable notifications", checked=True)
        chk_dark   = setCheckboxItem("demo.check.dark",   default="Dark mode")
        chk_notify.toggled.connect(lambda v: log_info(f"notify → {v}"))
        chk_dark.toggled.connect(lambda v: log_info(f"dark → {v}"))
        chk_row.addWidget(chk_notify)
        chk_row.addWidget(chk_dark)
        chk_row.addStretch()
        right_col.addLayout(chk_row)
        right_col.addStretch()

        misc_row.addLayout(right_col, stretch=1)
        root.addWidget(misc_group)

        # ---- 控制按钮 / Control buttons ----------------------------------
        btn_row = QHBoxLayout()
        btn_run = I18nButton("demo.btn_submit", default="Submit 5 tasks")
        btn_run.clicked.connect(self._submit_demo_batch)
        btn_row.addWidget(btn_run)

        btn_cancel = I18nButton("demo.btn_cancel", default="Cancel all running/queued tasks")
        btn_cancel.clicked.connect(self._cancel_all)
        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # ---- cmd 日志屏 / cmd-style log screen ---------------------------
        self.cmd = CmdLogWidget()
        root.addWidget(self.cmd, stretch=1)

        # ---- 信号绑定 / Signal wiring ------------------------------------
        # 进度/状态由各 LaviProgressBar 自身订阅 TaskSignal；
        # 这里只在 status=running 时把任务名喂给对应槽的进度条。
        # Each LaviProgressBar already subscribes to TaskSignal for its
        # own progress + status updates. The only thing we do here is push
        # the task's display name into the bar of the slot that just
        # transitioned to "running".
        get_task_signal().status_changed.connect(self._on_status_for_name)

        # 跟踪用户提交的任务 ID（用于一键取消）
        # Track IDs of tasks submitted by the user so the "cancel all"
        # button can target exactly that batch.
        self._submitted_ids: list[str] = []

    # ---- 信号槽 / Signal slots -----------------------------------------
    def _on_status_for_name(self, slot_index: int, task_id: str, status: str):
        if not (0 <= slot_index < len(self._progress_bars)):
            return
        if status == "running":
            task = get_tasks_manager().get_task(task_id)
            if task:
                self._progress_bars[slot_index].set_task_name("", default=task.name)

    # ---- 语种 / Language -----------------------------------------------
    def _reload_languages(self):
        """扫描 localisation/ 目录刷新下拉框选项；若当前语种不在列表里就追加。

        Rescan the localisation/ directory and refresh the language combo.
        If the currently active language is not in the discovered list it
        is appended so the user never ends up with an empty selection.
        """
        langs = I18n.available_languages()
        if not langs:
            langs = [I18n.get_language()]
        if I18n.get_language() not in langs:
            langs.append(I18n.get_language())
        self._lang_combo.blockSignals(True)
        self._lang_combo.setItems(langs)
        # 用 key（语言代码）而不是 setCurrentText：在非英语语种下显示文本是
        # 本地化名称（"简体中文"），用文本匹配会失败。
        # Use key (the language code) rather than setCurrentText: when the
        # current language is not English, the display text is the
        # localised name ("简体中文"), so a text match would not find it.
        self._lang_combo.setCurrentKey(I18n.get_language())
        self._lang_combo.blockSignals(False)

    def _on_lang_changed(self, idx: int):
        # 用 keyAt(idx) 而不是 currentKey()：QComboBox 内部的 popup 点击处理
        # 会先 emit currentIndexChanged，再让我们的 _on_view_clicked 调到
        # _commit 更新 _committed_index——所以在这个 slot 里 currentKey() 还是
        # 旧值，必须用信号自带的 idx 直接查模型。
        # Use keyAt(idx) instead of currentKey(): QComboBox emits
        # currentIndexChanged from its internal popup-click handler before
        # our _on_view_clicked gets a chance to call _commit, so
        # currentKey() still reflects the previous selection inside this
        # slot. Look up by the index Qt just gave us instead.
        lang = self._lang_combo.keyAt(idx)
        if lang and lang != I18n.get_language():
            I18n.set_language(lang)
            log_info(f"language switched → {lang}")

    def _export_template(self):
        path = I18n.export_template(I18n.get_language(), merge=True)
        log_success(f"translation template exported → {path}")
        self._reload_languages()

    # ---- 操作 / Actions ------------------------------------------------
    def _submit_demo_batch(self):
        log_info("=" * 60)
        log_info(f"submitting a batch of demo tasks (max_slots={get_tasks_manager().max_slots})")
        log_info("=" * 60)

        mgr = get_tasks_manager()
        self._submitted_ids = []
        # Two long progress tasks, one category-colour task, one crash
        # task, and a third progress task — five in total. With
        # max_slots=2 the last three queue up behind the first two.
        self._submitted_ids.append(mgr.submit(ProgressTask("Progress A", steps=80, interval=0.05)))
        self._submitted_ids.append(mgr.submit(ProgressTask("Progress B", steps=60, interval=0.07)))
        self._submitted_ids.append(mgr.submit(CategoryTask("Category colours")))
        self._submitted_ids.append(mgr.submit(CrashTask("Crash test")))
        self._submitted_ids.append(mgr.submit(ProgressTask("Progress C", steps=40, interval=0.06)))

    def _cancel_all(self):
        mgr = get_tasks_manager()
        cancelled = 0
        for tid in self._submitted_ids:
            if mgr.cancel(tid):
                cancelled += 1
        log_warning(f"cancelled {cancelled} task(s)")


def main():
    # Install the global crash hook first so any later import / startup
    # error is also routed through the SDK's logging pipeline.
    install_crash_hook()

    app = QApplication(sys.argv)

    # 槽位定为 2 以演示 FIFO 排队（5 个任务，2 个槽位）
    # Pin max_slots to 2 so the FIFO queueing behaviour is visible when
    # the demo submits 5 tasks against only 2 execution slots.
    set_max_slots(2)

    win = DemoWindow()
    win.show()

    # Startup banner shown in the cmd screen.
    log_info('ULTIMA_SDK Demo started — click "Submit 5 tasks" to begin')
    log_info("• the cmd screen only shows one task's progress bar (single owner)")
    log_info("• the graphical progress bars above show every concurrent task")
    log_info("• toggling the DEBUG switch (top-right) hides/restores debug lines live")

    # 自动 3 秒后跑
    # Auto-fire the demo batch after 3s 
    QTimer.singleShot(3000, win._submit_demo_batch)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
