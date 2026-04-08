#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
离线桌面智能助手（单文件版）
说明：
1) 全核心功能本地运行，不调用在线 API，不上传数据。
2) 默认黑底白字极简风，支持托盘、悬浮监控、全局热键、离线语音、文件整理、任务提醒。
3) 配置、提醒、整理历史均本地持久化存储。
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import platform
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
import uuid
import webbrowser
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REQUIRED_RUNTIME_PACKAGES = [
    "PySide6",
    "psutil",
    "vosk",
    "sounddevice",
    "pynput",
    "simpleaudio",
    "pyinstaller",
]

PACKAGE_IMPORT_MAP = {
    "PySide6": "PySide6",
    "psutil": "psutil",
    "vosk": "vosk",
    "sounddevice": "sounddevice",
    "pynput": "pynput",
    "simpleaudio": "simpleaudio",
    "pyinstaller": "PyInstaller",
}


def detect_missing_packages() -> List[str]:
    missing: List[str] = []
    for pkg in REQUIRED_RUNTIME_PACKAGES:
        module_name = PACKAGE_IMPORT_MAP[pkg]
        if importlib.util.find_spec(module_name) is None:
            missing.append(pkg)
    return missing


def run_streaming_process(command: List[str], on_line: Callable[[str], None], cwd: Optional[Path] = None) -> int:
    try:
        on_line("执行命令: " + " ".join(command))
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd) if cwd else None,
        )
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            if line:
                on_line(line)
        return proc.wait()
    except Exception as exc:
        on_line(f"命令执行异常: {exc}")
        return 1


def install_packages_with_fallback(packages: List[str], on_line: Callable[[str], None]) -> bool:
    if not packages:
        return True
    code = run_streaming_process([sys.executable, "-m", "pip", "install", "-U", *packages], on_line)
    if code == 0:
        return True
    on_line("首次安装失败，正在自动执行修复后重试。")
    run_streaming_process([sys.executable, "-m", "pip", "install", "-U", "pip", "setuptools", "wheel"], on_line)
    code = run_streaming_process([sys.executable, "-m", "pip", "install", "-U", *packages], on_line)
    return code == 0


def bootstrap_when_pyside6_missing() -> None:
    """当 PySide6 缺失时，用 Tk 做极简可视化安装引导。"""
    if importlib.util.find_spec("PySide6") is not None:
        return
    try:
        import tkinter as tk
        from tkinter import messagebox, scrolledtext, ttk
    except Exception:
        print("缺少 PySide6，且无法启动图形引导。请先安装: python -m pip install -U PySide6")
        raise SystemExit(1)

    root = tk.Tk()
    root.title("离线桌面助手 - 初始化")
    root.geometry("760x520")
    root.configure(bg="#000000")
    root.protocol("WM_DELETE_WINDOW", lambda: root.destroy())

    ttk.Style().theme_use("clam")
    title = tk.Label(
        root,
        text="首次运行需要安装依赖，点击下方按钮自动完成",
        fg="#FFFFFF",
        bg="#000000",
        font=("Consolas", 13, "bold"),
    )
    title.pack(pady=10)
    progress = ttk.Progressbar(root, mode="indeterminate", length=700)
    progress.pack(pady=8)
    log_box = scrolledtext.ScrolledText(root, bg="#050505", fg="#FFFFFF", insertbackground="#FFFFFF", height=20)
    log_box.pack(fill="both", expand=True, padx=16, pady=8)
    btn_frame = tk.Frame(root, bg="#000000")
    btn_frame.pack(fill="x", padx=16, pady=10)

    state = {"done": False, "ok": False}

    def log_line(msg: str) -> None:
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        root.update_idletasks()

    def worker() -> None:
        missing = detect_missing_packages()
        ok = install_packages_with_fallback(missing, log_line)
        state["done"] = True
        state["ok"] = ok
        if ok:
            log_line("安装完成，正在重启程序。")
        else:
            log_line("自动安装失败，请检查网络后点击重试。")

    def poll() -> None:
        if not state["done"]:
            root.after(300, poll)
            return
        progress.stop()
        install_btn.config(state="normal")
        if state["ok"]:
            messagebox.showinfo("完成", "依赖已安装完成，程序将自动重启。")
            root.destroy()
            os.execv(sys.executable, [sys.executable, *sys.argv])
        else:
            messagebox.showerror("失败", "自动安装失败，请联网后重试。")

    def start_install() -> None:
        install_btn.config(state="disabled")
        state["done"] = False
        state["ok"] = False
        progress.start(10)
        threading.Thread(target=worker, daemon=True).start()
        poll()

    install_btn = tk.Button(
        btn_frame,
        text="一键安装全部运行依赖",
        command=start_install,
        bg="#101010",
        fg="#FFFFFF",
        font=("Consolas", 12, "bold"),
        padx=10,
        pady=10,
    )
    install_btn.pack(side="left")
    tip = tk.Label(
        btn_frame,
        text="全程自动安装，不需要打开命令行。",
        fg="#FFFFFF",
        bg="#000000",
        font=("Consolas", 11),
    )
    tip.pack(side="left", padx=12)
    root.mainloop()
    raise SystemExit(0)


bootstrap_when_pyside6_missing()

from PySide6.QtCore import QDateTime, QObject, Qt, QThread, QTimer, Signal, QUrl
from PySide6.QtGui import QAction, QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# ===== 可选第三方库（缺失时不会导致程序崩溃） =====
IMPORT_ERRORS: List[str] = []

try:
    import psutil  # type: ignore
except Exception as exc:
    psutil = None
    IMPORT_ERRORS.append(f"psutil 导入失败: {exc}")

try:
    import sounddevice as sd  # type: ignore
except Exception as exc:
    sd = None
    IMPORT_ERRORS.append(f"sounddevice 导入失败: {exc}")

try:
    from vosk import KaldiRecognizer, Model  # type: ignore
except Exception as exc:
    KaldiRecognizer = None
    Model = None
    IMPORT_ERRORS.append(f"vosk 导入失败: {exc}")

try:
    import simpleaudio as sa  # type: ignore
except Exception as exc:
    sa = None
    IMPORT_ERRORS.append(f"simpleaudio 导入失败: {exc}")

try:
    from pynput import keyboard  # type: ignore
except Exception as exc:
    keyboard = None
    IMPORT_ERRORS.append(f"pynput 导入失败: {exc}")


DEFAULT_RULES = [
    {"name": "图片", "folder": "图片", "exts": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"]},
    {"name": "文档", "folder": "文档", "exts": [".txt", ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".md"]},
    {"name": "视频", "folder": "视频", "exts": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]},
    {"name": "音频", "folder": "音频", "exts": [".mp3", ".wav", ".flac", ".aac", ".ogg"]},
    {"name": "安装包", "folder": "安装包", "exts": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".AppImage"]},
    {"name": "压缩包", "folder": "压缩包", "exts": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"]},
    {"name": "其他", "folder": "其他", "exts": []},
]


def get_data_dir() -> Path:
    """跨平台本地数据目录。"""
    home = Path.home()
    system = platform.system().lower()
    if system == "windows":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    elif system == "darwin":
        root = home / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    data_dir = root / "OfflineDesktopAssistant"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def candidate_monitor_paths() -> List[str]:
    """默认监控路径：桌面 + 下载。"""
    home = Path.home()
    candidates: List[Path] = [home / "Desktop", home / "Downloads"]
    if platform.system().lower() == "windows":
        user_profile = Path(os.environ.get("USERPROFILE", str(home)))
        one_drive = Path(os.environ.get("OneDrive", str(user_profile / "OneDrive")))
        candidates.extend(
            [
                user_profile / "Desktop",
                user_profile / "Downloads",
                one_drive / "Desktop",
                one_drive / "Downloads",
            ]
        )
    dedup: List[str] = []
    for p in candidates:
        if p.exists() and p.is_dir():
            s = str(p)
            if s not in dedup:
                dedup.append(s)
    return dedup


def deep_merge(default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(default)
    for key, value in custom.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_json(path: Path, fallback: Any) -> Any:
    try:
        if not path.exists():
            return fallback
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def default_config() -> Dict[str, Any]:
    data_dir = get_data_dir()
    default_model = data_dir / "vosk-model-small-cn"
    try:
        bundle_root = Path(getattr(sys, "_MEIPASS", ""))
        bundle_model = bundle_root / "vosk-model-small-cn"
        if str(bundle_root) and bundle_model.exists():
            default_model = bundle_model
    except Exception:
        pass
    return {
        "refresh_interval_sec": 1,
        "monitor_paths": candidate_monitor_paths(),
        "rules": DEFAULT_RULES,
        "organize_interval_min": 0,
        "floating": {"enabled": True, "opacity_percent": 85, "always_on_top": True},
        "voice": {
            "enabled": False,
            "model_path": str(default_model),
            "wake_word_enabled": False,
            "wake_word": "助手",
            "custom_commands": [],
        },
        "hotkeys": {
            "toggle_main": "<ctrl>+<alt>+h",
            "toggle_floating": "<ctrl>+<alt>+m",
            "organize_now": "<ctrl>+<alt>+o",
            "toggle_voice": "<ctrl>+<alt>+v",
        },
        "alert": {"sound_enabled": False, "sound_file": ""},
        "confirm_on_exit": True,
        "start_minimized_to_tray": False,
        "intro_completed": False,
        "packaging": {"include_model": False},
    }


def format_speed(bytes_per_sec: float) -> str:
    unit = ["B/s", "KB/s", "MB/s", "GB/s"]
    value = max(0.0, bytes_per_sec)
    idx = 0
    while value >= 1024 and idx < len(unit) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.2f} {unit[idx]}"


def next_time(base_time: dt.datetime, recurrence: str) -> dt.datetime:
    if recurrence == "daily":
        return base_time + dt.timedelta(days=1)
    if recurrence == "weekly":
        return base_time + dt.timedelta(days=7)
    if recurrence == "monthly":
        year = base_time.year + (1 if base_time.month == 12 else 0)
        month = 1 if base_time.month == 12 else base_time.month + 1
        day = min(base_time.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return base_time.replace(year=year, month=month, day=day)
    return base_time


def unique_target_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


class RuleEditDialog(QDialog):
    def __init__(self, rule: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("分类规则编辑")
        self.setModal(True)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(rule.get("name", "") if rule else "")
        self.folder_edit = QLineEdit(rule.get("folder", "") if rule else "")
        exts = ", ".join(rule.get("exts", [])) if rule else ""
        self.exts_edit = QLineEdit(exts)
        layout.addRow("分类名称", self.name_edit)
        layout.addRow("目标文件夹", self.folder_edit)
        layout.addRow("后缀列表（逗号分隔）", self.exts_edit)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_rule(self) -> Dict[str, Any]:
        exts = [e.strip().lower() for e in self.exts_edit.text().split(",") if e.strip()]
        normalized = [e if e.startswith(".") else f".{e}" for e in exts]
        return {
            "name": self.name_edit.text().strip() or "未命名分类",
            "folder": self.folder_edit.text().strip() or "未命名文件夹",
            "exts": normalized,
        }


class VoiceCommandDialog(QDialog):
    def __init__(self, cmd: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("语音指令编辑")
        self.setModal(True)
        layout = QFormLayout(self)
        self.phrase_edit = QLineEdit(cmd.get("phrase", "") if cmd else "")
        self.action_combo = QComboBox()
        self.action_combo.addItems(
            [
                "open_app",
                "close_window",
                "organize_now",
                "show_floating",
                "hide_floating",
                "toggle_floating",
                "create_reminder",
                "exit_app",
                "run_shell",
            ]
        )
        if cmd and cmd.get("action"):
            idx = self.action_combo.findText(cmd["action"])
            if idx >= 0:
                self.action_combo.setCurrentIndex(idx)
        self.payload_edit = QLineEdit(cmd.get("payload", "") if cmd else "")
        layout.addRow("触发短语", self.phrase_edit)
        layout.addRow("动作", self.action_combo)
        layout.addRow("动作参数", self.payload_edit)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self) -> Dict[str, str]:
        return {
            "phrase": self.phrase_edit.text().strip(),
            "action": self.action_combo.currentText(),
            "payload": self.payload_edit.text().strip(),
        }


class ReminderEditDialog(QDialog):
    def __init__(self, reminder: Optional[Dict[str, Any]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("提醒编辑")
        self.setModal(True)
        layout = QFormLayout(self)
        self.content_edit = QLineEdit(reminder.get("content", "") if reminder else "")
        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dt_edit.setCalendarPopup(True)
        self.dt_edit.setDateTime(QDateTime.currentDateTime().addSecs(60))
        if reminder and reminder.get("next_time"):
            try:
                parsed = dt.datetime.fromisoformat(reminder["next_time"])
                self.dt_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(parsed.timestamp())))
            except Exception:
                pass
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems(["once", "daily", "weekly", "monthly"])
        if reminder and reminder.get("recurrence"):
            idx = self.recurrence_combo.findText(reminder["recurrence"])
            if idx >= 0:
                self.recurrence_combo.setCurrentIndex(idx)
        layout.addRow("提醒内容", self.content_edit)
        layout.addRow("提醒时间", self.dt_edit)
        layout.addRow("重复周期", self.recurrence_combo)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self) -> Dict[str, Any]:
        qdt = self.dt_edit.dateTime().toPython()
        return {
            "content": self.content_edit.text().strip() or "未命名提醒",
            "next_time": qdt.isoformat(timespec="seconds"),
            "recurrence": self.recurrence_combo.currentText(),
        }


class FloatingMonitorWindow(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("监控悬浮窗")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.resize(280, 180)
        layout = QVBoxLayout(self)
        self.cpu_label = QLabel("CPU: 0.0%")
        self.mem_label = QLabel("MEM: 0.0%")
        self.disk_label = QLabel("DISK: 0.0%")
        self.net_label = QLabel("NET: ↑0 B/s ↓0 B/s")
        self.cpu_bar = QProgressBar()
        self.mem_bar = QProgressBar()
        self.disk_bar = QProgressBar()
        for bar in [self.cpu_bar, self.mem_bar, self.disk_bar]:
            bar.setRange(0, 100)
            bar.setTextVisible(True)
        for w in [self.cpu_label, self.cpu_bar, self.mem_label, self.mem_bar, self.disk_label, self.disk_bar, self.net_label]:
            layout.addWidget(w)

    def update_metrics(self, cpu: float, mem: float, disk: float, up: str, down: str) -> None:
        self.cpu_label.setText(f"CPU: {cpu:.1f}%")
        self.mem_label.setText(f"MEM: {mem:.1f}%")
        self.disk_label.setText(f"DISK: {disk:.1f}%")
        self.net_label.setText(f"NET: ↑{up} ↓{down}")
        self.cpu_bar.setValue(int(cpu))
        self.mem_bar.setValue(int(mem))
        self.disk_bar.setValue(int(disk))


class VoiceWorker(QObject):
    recognized = Signal(str)
    status = Signal(str)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, model_path: str, wake_word_enabled: bool, wake_word: str) -> None:
        super().__init__()
        self.model_path = model_path
        self.wake_word_enabled = wake_word_enabled
        self.wake_word = wake_word.strip().lower()
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        if Model is None or KaldiRecognizer is None:
            self.status.emit("离线语音不可用：未安装 vosk。")
            self.finished.emit()
            return
        if sd is None:
            self.status.emit("离线语音不可用：未安装 sounddevice。")
            self.finished.emit()
            return
        model_dir = Path(self.model_path)
        if not model_dir.exists():
            self.status.emit(f"语音模型不存在: {model_dir}")
            self.finished.emit()
            return
        audio_q: "queue.Queue[bytes]" = queue.Queue()
        activated = not self.wake_word_enabled
        activated_until = 0.0

        try:
            model = Model(str(model_dir))
            recognizer = KaldiRecognizer(model, 16000)

            def callback(indata: bytes, frames: int, t: Any, status: Any) -> None:
                if status:
                    pass
                if not self._stop.is_set():
                    audio_q.put(bytes(indata))

            with sd.RawInputStream(
                samplerate=16000,
                blocksize=8000,
                dtype="int16",
                channels=1,
                callback=callback,
            ):
                self.status.emit("离线语音识别已启动。")
                while not self._stop.is_set():
                    try:
                        data = audio_q.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    if recognizer.AcceptWaveform(data):
                        raw = recognizer.Result()
                        try:
                            obj = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        text = (obj.get("text") or "").strip()
                        if not text:
                            continue
                        lowered = text.lower()
                        if self.wake_word_enabled:
                            if self.wake_word and self.wake_word in lowered:
                                activated = True
                                activated_until = time.time() + 8.0
                                self.status.emit("唤醒词已触发，请在 8 秒内说指令。")
                                continue
                            if not activated or time.time() > activated_until:
                                activated = False
                                continue
                        self.recognized.emit(text)
        except Exception:
            self.failed.emit(traceback.format_exc())
        finally:
            self.finished.emit()


class HotkeyManager(QObject):
    def __init__(self, logger: Callable[[str], None]) -> None:
        super().__init__()
        self.listener = None
        self.log = logger

    def stop(self) -> None:
        try:
            if self.listener is not None:
                self.listener.stop()
                self.listener = None
        except Exception:
            pass

    def register(self, hotkey_mapping: Dict[str, Callable[[], None]]) -> bool:
        self.stop()
        if keyboard is None:
            self.log("全局热键不可用：pynput 未安装或初始化失败。")
            return False
        try:
            wrapped: Dict[str, Callable[[], None]] = {}
            for combo, callback in hotkey_mapping.items():
                combo = combo.strip()
                if not combo:
                    continue
                wrapped[combo] = lambda cb=callback: QTimer.singleShot(0, cb)
            if not wrapped:
                self.log("未设置有效全局热键。")
                return False
            self.listener = keyboard.GlobalHotKeys(wrapped)
            self.listener.start()
            self.log("全局热键已生效。")
            return True
        except Exception as exc:
            self.log(f"全局热键注册失败: {exc}")
            return False


def open_path_in_file_manager(path: Path) -> None:
    try:
        if platform.system().lower() == "windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif platform.system().lower() == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass


class DependencyInstallWorker(QObject):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)

    def run(self) -> None:
        try:
            self.progress.emit(5)
            missing = detect_missing_packages()
            if not missing:
                self.progress.emit(100)
                self.finished.emit(True, "当前环境已具备全部依赖，无需安装。")
                return
            self.log.emit("检测到缺失依赖: " + ", ".join(missing))
            self.progress.emit(20)
            ok = install_packages_with_fallback(missing, self.log.emit)
            self.progress.emit(100)
            if ok:
                self.finished.emit(True, "依赖安装完成。建议重启程序以加载新组件。")
            else:
                self.finished.emit(False, "自动安装失败，请联网后再次点击安装。")
        except Exception as exc:
            self.finished.emit(False, f"依赖安装异常: {exc}")


class ModelDownloadWorker(QObject):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str, str)

    def __init__(self, data_dir: Path) -> None:
        super().__init__()
        self.data_dir = data_dir
        self.model_url = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"

    def run(self) -> None:
        zip_path = self.data_dir / "vosk-model-small-cn-0.22.zip"
        extract_root = self.data_dir / "_model_extract"
        target_model = self.data_dir / "vosk-model-small-cn"
        try:
            self.progress.emit(5)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.log.emit("开始下载中文离线语音模型。")
            with urllib.request.urlopen(self.model_url, timeout=90) as resp:
                total = int(resp.headers.get("Content-Length", "0") or "0")
                read = 0
                with zip_path.open("wb") as fp:
                    while True:
                        chunk = resp.read(1024 * 128)
                        if not chunk:
                            break
                        fp.write(chunk)
                        read += len(chunk)
                        if total > 0:
                            pct = min(70, int(read * 70 / total))
                            self.progress.emit(max(5, pct))
            self.log.emit("下载完成，正在解压模型。")
            self.progress.emit(75)
            if extract_root.exists():
                shutil.rmtree(extract_root, ignore_errors=True)
            extract_root.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_root)
            candidates = [p for p in extract_root.iterdir() if p.is_dir() and p.name.startswith("vosk-model-small-cn")]
            if not candidates:
                raise RuntimeError("未找到有效模型目录。")
            model_real = candidates[0]
            if target_model.exists():
                shutil.rmtree(target_model, ignore_errors=True)
            shutil.move(str(model_real), str(target_model))
            shutil.rmtree(extract_root, ignore_errors=True)
            self.progress.emit(100)
            self.finished.emit(True, "中文离线语音模型已自动配置完成。", str(target_model))
        except Exception as exc:
            self.finished.emit(False, f"模型下载失败: {exc}", "")


class PackageBuildWorker(QObject):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str, str)

    def __init__(self, script_path: Path, include_model: bool, model_path: str) -> None:
        super().__init__()
        self.script_path = script_path
        self.include_model = include_model
        self.model_path = model_path

    def run(self) -> None:
        try:
            self.progress.emit(10)
            cwd = self.script_path.parent
            dist_dir = cwd / "dist"
            work_dir = cwd / "build"
            spec_dir = cwd
            cmd = [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--windowed",
                "--onefile",
                "--name",
                "OfflineDesktopAssistant",
                "--collect-all",
                "PySide6",
                "--collect-all",
                "vosk",
                "--hidden-import=sounddevice",
                "--hidden-import=pynput",
                "--hidden-import=simpleaudio",
                "--distpath",
                str(dist_dir),
                "--workpath",
                str(work_dir),
                "--specpath",
                str(spec_dir),
            ]
            if self.include_model and self.model_path and Path(self.model_path).exists():
                sep = ";" if platform.system().lower() == "windows" else ":"
                cmd += ["--add-data", f"{self.model_path}{sep}vosk-model-small-cn"]
                self.log.emit("当前模式：带语音模型打包。")
            else:
                self.log.emit("当前模式：不带语音模型打包。")
            cmd.append(str(self.script_path))
            self.progress.emit(25)
            code = run_streaming_process(cmd, self.log.emit, cwd=cwd)
            self.progress.emit(100)
            if code == 0:
                self.finished.emit(True, "打包完成。", str(dist_dir))
            else:
                self.finished.emit(False, "打包失败，请查看日志后重试。", str(dist_dir))
        except Exception as exc:
            self.finished.emit(False, f"打包异常: {exc}", "")


class AssistantMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("离线桌面智能助手")
        self.resize(1100, 760)

        self.data_dir = get_data_dir()
        self.config_path = self.data_dir / "config.json"
        self.reminders_path = self.data_dir / "reminders.json"
        self.undo_path = self.data_dir / "last_organize.json"

        cfg = load_json(self.config_path, {})
        self.config = deep_merge(default_config(), cfg if isinstance(cfg, dict) else {})
        self.reminders = load_json(self.reminders_path, [])
        if not isinstance(self.reminders, list):
            self.reminders = []
        self.last_organize_ops = load_json(self.undo_path, [])
        if not isinstance(self.last_organize_ops, list):
            self.last_organize_ops = []

        self.voice_thread: Optional[QThread] = None
        self.voice_worker: Optional[VoiceWorker] = None
        self.is_quitting = False
        self.prev_net = None
        self.prev_net_time = time.time()
        self.flash_count = 0
        self.flash_default_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.flash_alt_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.active_task_thread: Optional[QThread] = None
        self.active_worker: Optional[QObject] = None
        self.monitor_missing_prompted = False

        self.action_handlers: Dict[str, Callable[[str], None]] = {}
        self.hotkey_manager = HotkeyManager(self.log)
        self.floating_window = FloatingMonitorWindow(self)

        self._build_ui()
        self._init_tray()
        self._init_timers()
        self._register_actions()
        self.load_config_to_ui()
        self.apply_hotkeys()
        self.update_monitor_metrics()
        self.refresh_rule_table()
        self.refresh_paths()
        self.refresh_custom_command_table()
        self.refresh_reminder_table()

        self.log(f"本地数据目录: {self.data_dir}")
        if IMPORT_ERRORS:
            for err in IMPORT_ERRORS:
                self.log(err)
        self.refresh_dependency_status()
        self.refresh_model_status()
        QTimer.singleShot(300, self.post_startup_tasks)

    def post_startup_tasks(self) -> None:
        """启动后执行的新手友好流程。"""
        try:
            if not self.config.get("intro_completed", False):
                self.show_beginner_guide()
                self.config["intro_completed"] = True
                save_json(self.config_path, self.config)
            if self.config.get("start_minimized_to_tray", False) and self.tray is not None:
                self.hide()
            missing = detect_missing_packages()
            if missing:
                if "psutil" in missing:
                    self.monitor_missing_prompted = True
                self.show_friendly_error(
                    "运行环境提示",
                    "检测到当前电脑缺少部分组件。点击“一键修复”后系统会自动安装，不需要输入命令。",
                    fix_label="一键修复",
                    fix_callback=self.start_dependency_install,
                )
            if not self.is_model_ready():
                self.show_friendly_error(
                    "语音功能提示",
                    "还没有检测到中文离线语音模型。点击“一键修复”可自动下载并完成配置。",
                    fix_label="一键修复",
                    fix_callback=self.start_model_download,
                )
        except Exception:
            self.log("启动后流程异常: " + traceback.format_exc())

    # ========================= 基础 UI =========================
    def _build_ui(self) -> None:
        root = QWidget()
        main_layout = QVBoxLayout(root)

        quick_group = QGroupBox("新手一键区")
        quick_layout = QVBoxLayout(quick_group)
        status_row = QHBoxLayout()
        self.dependency_status_label = QLabel("依赖检测中...")
        self.model_status_label = QLabel("语音模型检测中...")
        status_row.addWidget(self.dependency_status_label)
        status_row.addWidget(self.model_status_label)
        status_row.addStretch(1)
        quick_layout.addLayout(status_row)

        action_row_1 = QHBoxLayout()
        self.install_deps_btn = QPushButton("一键安装全部运行依赖")
        self.install_deps_btn.clicked.connect(self.start_dependency_install)
        self.download_model_btn = QPushButton("一键下载并配置中文语音模型")
        self.download_model_btn.clicked.connect(self.start_model_download)
        self.quick_organize_btn = QPushButton("一键整理桌面&下载文件夹")
        self.quick_organize_btn.clicked.connect(lambda: self.organize_now(confirm=True))
        for btn in [self.install_deps_btn, self.download_model_btn, self.quick_organize_btn]:
            btn.setMinimumHeight(42)
            btn.setProperty("primary", True)
        action_row_1.addWidget(self.install_deps_btn)
        action_row_1.addWidget(self.download_model_btn)
        action_row_1.addWidget(self.quick_organize_btn)
        quick_layout.addLayout(action_row_1)

        action_row_2 = QHBoxLayout()
        self.quick_floating_btn = QPushButton("一键显示/隐藏监控悬浮窗")
        self.quick_floating_btn.clicked.connect(self.toggle_floating_window)
        self.quick_topmost_btn = QPushButton("一键切换悬浮窗置顶")
        self.quick_topmost_btn.clicked.connect(self.toggle_floating_topmost)
        self.quick_reminder_btn = QPushButton("一键新建提醒")
        self.quick_reminder_btn.clicked.connect(self.quick_add_reminder)
        self.package_btn = QPushButton("一键打包成桌面可执行程序")
        self.package_btn.clicked.connect(self.start_packaging)
        for btn in [self.quick_floating_btn, self.quick_topmost_btn, self.quick_reminder_btn, self.package_btn]:
            btn.setMinimumHeight(38)
            btn.setProperty("secondary", True)
        action_row_2.addWidget(self.quick_floating_btn)
        action_row_2.addWidget(self.quick_topmost_btn)
        action_row_2.addWidget(self.quick_reminder_btn)
        action_row_2.addWidget(self.package_btn)
        quick_layout.addLayout(action_row_2)

        action_row_3 = QHBoxLayout()
        self.package_with_model_check = QCheckBox("打包时附带语音模型")
        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setRange(0, 100)
        self.task_progress_bar.setValue(0)
        self.task_status_label = QLabel("就绪")
        action_row_3.addWidget(self.package_with_model_check)
        action_row_3.addWidget(self.task_progress_bar, 1)
        action_row_3.addWidget(self.task_status_label)
        quick_layout.addLayout(action_row_3)
        main_layout.addWidget(quick_group)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_monitor_tab(), "系统监控")
        self.tabs.addTab(self._build_voice_tab(), "离线语音")
        self.tabs.addTab(self._build_organizer_tab(), "文件整理")
        self.tabs.addTab(self._build_reminder_tab(), "任务提醒")
        self.tabs.addTab(self._build_settings_tab(), "配置中心")
        main_layout.addWidget(self.tabs)

        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group, 1)
        self.setCentralWidget(root)

    def _build_monitor_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        grid = QGridLayout()
        self.cpu_label = QLabel("CPU: 0.0%")
        self.mem_label = QLabel("内存: 0.0%")
        self.disk_label = QLabel("磁盘: 0.0%")
        self.net_up_label = QLabel("上传: 0 B/s")
        self.net_down_label = QLabel("下载: 0 B/s")

        self.cpu_bar = QProgressBar()
        self.mem_bar = QProgressBar()
        self.disk_bar = QProgressBar()
        for bar in (self.cpu_bar, self.mem_bar, self.disk_bar):
            bar.setRange(0, 100)
            bar.setTextVisible(True)

        grid.addWidget(self.cpu_label, 0, 0)
        grid.addWidget(self.cpu_bar, 0, 1)
        grid.addWidget(self.mem_label, 1, 0)
        grid.addWidget(self.mem_bar, 1, 1)
        grid.addWidget(self.disk_label, 2, 0)
        grid.addWidget(self.disk_bar, 2, 1)
        grid.addWidget(self.net_up_label, 3, 0)
        grid.addWidget(self.net_down_label, 3, 1)
        layout.addLayout(grid)

        basic_ctrl = QHBoxLayout()
        self.floating_toggle_btn = QPushButton("显示/隐藏悬浮窗")
        self.floating_toggle_btn.clicked.connect(self.toggle_floating_window)
        basic_ctrl.addWidget(self.floating_toggle_btn)
        basic_ctrl.addStretch(1)
        layout.addLayout(basic_ctrl)

        advanced_group = QGroupBox("高级设置（监控参数）")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QHBoxLayout(advanced_group)
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(1, 60)
        self.refresh_spin.setValue(1)
        self.refresh_apply_btn = QPushButton("应用刷新频率")
        self.refresh_apply_btn.clicked.connect(self.apply_refresh_interval)
        advanced_layout.addWidget(QLabel("刷新频率(秒)"))
        advanced_layout.addWidget(self.refresh_spin)
        advanced_layout.addWidget(self.refresh_apply_btn)
        advanced_layout.addStretch(1)
        advanced_group.toggled.connect(lambda checked: advanced_group.setFlat(not checked))
        layout.addWidget(advanced_group)
        return tab

    def _build_voice_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        status_group = QGroupBox("语音状态")
        status_layout = QFormLayout(status_group)
        self.voice_status_label = QLabel("未启动")
        self.voice_start_btn = QPushButton("启动离线语音识别")
        self.voice_start_btn.clicked.connect(self.toggle_voice_recognition)
        self.wake_word_check = QCheckBox("启用语音唤醒")
        self.wake_word_edit = QLineEdit("助手")
        status_layout.addRow("当前状态", self.voice_status_label)
        status_layout.addRow("唤醒词", self.wake_word_edit)
        status_layout.addRow("", self.wake_word_check)
        status_layout.addRow("", self.voice_start_btn)
        layout.addWidget(status_group)

        model_group = QGroupBox("高级设置（手动模型配置）")
        model_group.setCheckable(True)
        model_group.setChecked(False)
        model_layout = QFormLayout(model_group)
        self.model_path_edit = QLineEdit()
        self.model_path_edit.textChanged.connect(lambda _: self.refresh_model_status())
        model_btn_row = QHBoxLayout()
        browse_btn = QPushButton("选择模型目录")
        browse_btn.clicked.connect(self.select_model_dir)
        guide_btn = QPushButton("生成模型下载脚本")
        guide_btn.clicked.connect(self.generate_model_download_script)
        model_btn_row.addWidget(browse_btn)
        model_btn_row.addWidget(guide_btn)
        model_layout.addRow("模型目录", self.model_path_edit)
        model_layout.addRow("", model_btn_row)
        layout.addWidget(model_group)
        self.model_path_edit.setVisible(False)
        browse_btn.setVisible(False)
        guide_btn.setVisible(False)
        model_group.toggled.connect(lambda checked: self.model_path_edit.setVisible(checked))
        model_group.toggled.connect(lambda checked: browse_btn.setVisible(checked))
        model_group.toggled.connect(lambda checked: guide_btn.setVisible(checked))

        built_in = QGroupBox("内置离线语音指令")
        built_layout = QVBoxLayout(built_in)
        built_layout.addWidget(QLabel("打开系统软件 / 关闭当前窗口 / 一键整理文件 / 显示监控 / 隐藏监控 / 新建任务提醒 / 退出程序"))
        layout.addWidget(built_in)

        custom_group = QGroupBox("高级设置（自定义语音指令）")
        custom_group.setCheckable(True)
        custom_group.setChecked(False)
        custom_layout = QVBoxLayout(custom_group)
        self.custom_cmd_table = QTableWidget(0, 3)
        self.custom_cmd_table.setHorizontalHeaderLabels(["触发短语", "动作", "参数"])
        self.custom_cmd_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.custom_cmd_table.setAlternatingRowColors(True)
        custom_layout.addWidget(self.custom_cmd_table)
        custom_btns = QHBoxLayout()
        add_btn = QPushButton("新增指令")
        edit_btn = QPushButton("编辑指令")
        del_btn = QPushButton("删除指令")
        add_btn.clicked.connect(self.add_custom_command)
        edit_btn.clicked.connect(self.edit_custom_command)
        del_btn.clicked.connect(self.delete_custom_command)
        custom_btns.addWidget(add_btn)
        custom_btns.addWidget(edit_btn)
        custom_btns.addWidget(del_btn)
        custom_btns.addStretch(1)
        custom_layout.addLayout(custom_btns)
        layout.addWidget(custom_group)
        custom_group.toggled.connect(lambda checked: self.custom_cmd_table.setVisible(checked))
        self.custom_cmd_table.setVisible(False)
        add_btn.setVisible(False)
        edit_btn.setVisible(False)
        del_btn.setVisible(False)
        custom_group.toggled.connect(lambda checked: add_btn.setVisible(checked))
        custom_group.toggled.connect(lambda checked: edit_btn.setVisible(checked))
        custom_group.toggled.connect(lambda checked: del_btn.setVisible(checked))
        layout.addStretch(1)
        return tab

    def _build_organizer_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        actions = QHBoxLayout()
        self.organize_now_btn = QPushButton("一键整理桌面和下载文件夹")
        self.organize_now_btn.clicked.connect(lambda: self.organize_now(confirm=True))
        self.undo_btn = QPushButton("撤销上一次整理")
        self.undo_btn.clicked.connect(self.undo_last_organize)
        self.quick_reset_paths_btn = QPushButton("恢复默认路径")
        self.quick_reset_paths_btn.clicked.connect(self.reset_default_monitor_paths)
        self.organize_interval_spin = QSpinBox()
        self.organize_interval_spin.setRange(0, 1440)
        self.organize_interval_apply = QPushButton("应用定时整理")
        self.organize_interval_apply.clicked.connect(self.apply_organize_interval)
        actions.addWidget(self.organize_now_btn)
        actions.addWidget(self.undo_btn)
        actions.addWidget(self.quick_reset_paths_btn)
        actions.addWidget(QLabel("定时(分钟,0=关闭)"))
        actions.addWidget(self.organize_interval_spin)
        actions.addWidget(self.organize_interval_apply)
        actions.addStretch(1)
        layout.addLayout(actions)

        advanced_group = QGroupBox("高级设置（路径与分类规则）")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(advanced_group)

        paths_group = QGroupBox("监控路径")
        paths_layout = QVBoxLayout(paths_group)
        self.paths_list = QListWidget()
        paths_layout.addWidget(self.paths_list)
        path_btns = QHBoxLayout()
        add_path = QPushButton("添加路径")
        rm_path = QPushButton("移除路径")
        add_path.clicked.connect(self.add_monitor_path)
        rm_path.clicked.connect(self.remove_monitor_path)
        path_btns.addWidget(add_path)
        path_btns.addWidget(rm_path)
        path_btns.addStretch(1)
        paths_layout.addLayout(path_btns)
        advanced_layout.addWidget(paths_group)

        rules_group = QGroupBox("分类规则")
        rules_layout = QVBoxLayout(rules_group)
        self.rules_table = QTableWidget(0, 3)
        self.rules_table.setHorizontalHeaderLabels(["分类名称", "目标文件夹", "后缀列表"])
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rules_table.setAlternatingRowColors(True)
        rules_layout.addWidget(self.rules_table)
        rule_btns = QHBoxLayout()
        add_rule = QPushButton("新增规则")
        edit_rule = QPushButton("编辑规则")
        del_rule = QPushButton("删除规则")
        add_rule.clicked.connect(self.add_rule)
        edit_rule.clicked.connect(self.edit_rule)
        del_rule.clicked.connect(self.delete_rule)
        rule_btns.addWidget(add_rule)
        rule_btns.addWidget(edit_rule)
        rule_btns.addWidget(del_rule)
        rule_btns.addStretch(1)
        rules_layout.addLayout(rule_btns)
        advanced_layout.addWidget(rules_group)

        layout.addWidget(advanced_group)
        advanced_group.toggled.connect(lambda checked: paths_group.setVisible(checked))
        advanced_group.toggled.connect(lambda checked: rules_group.setVisible(checked))
        paths_group.setVisible(False)
        rules_group.setVisible(False)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("整理记录默认支持撤销，已启用防误触确认。"))
        footer.addStretch(1)
        layout.addLayout(footer)
        return tab

    def _build_reminder_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.reminder_table = QTableWidget(0, 5)
        self.reminder_table.setHorizontalHeaderLabels(["ID", "内容", "下次提醒时间", "周期", "状态"])
        self.reminder_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.reminder_table.setColumnHidden(0, True)
        self.reminder_table.setAlternatingRowColors(True)
        layout.addWidget(self.reminder_table)

        btns = QHBoxLayout()
        add_btn = QPushButton("新增提醒")
        edit_btn = QPushButton("编辑提醒")
        del_btn = QPushButton("删除提醒")
        done_btn = QPushButton("标记完成")
        add_btn.clicked.connect(self.add_reminder)
        edit_btn.clicked.connect(self.edit_reminder)
        del_btn.clicked.connect(self.delete_reminder)
        done_btn.clicked.connect(self.complete_reminder)
        btns.addWidget(add_btn)
        btns.addWidget(edit_btn)
        btns.addWidget(del_btn)
        btns.addWidget(done_btn)
        btns.addStretch(1)
        layout.addLayout(btns)

        alert_group = QGroupBox("提醒方式")
        alert_layout = QFormLayout(alert_group)
        self.sound_enable_check = QCheckBox("启用本地音频提醒")
        self.sound_file_edit = QLineEdit()
        pick_sound_btn = QPushButton("选择音频文件")
        pick_sound_btn.clicked.connect(self.select_sound_file)
        alert_layout.addRow("", self.sound_enable_check)
        alert_layout.addRow("音频文件", self.sound_file_edit)
        alert_layout.addRow("", pick_sound_btn)
        layout.addWidget(alert_group)
        return tab

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        basic_group = QGroupBox("基础设置")
        basic_layout = QFormLayout(basic_group)
        self.start_minimized_check = QCheckBox("启动后自动最小化到系统托盘")
        self.confirm_exit_check = QCheckBox("关闭窗口时显示退出确认")
        basic_layout.addRow("", self.start_minimized_check)
        basic_layout.addRow("", self.confirm_exit_check)
        layout.addWidget(basic_group)

        advanced_group = QGroupBox("高级设置（快捷键与悬浮窗）")
        advanced_group.setCheckable(True)
        advanced_group.setChecked(False)
        advanced_layout = QVBoxLayout(advanced_group)

        hotkey_group = QGroupBox("全局快捷键")
        hotkey_layout = QFormLayout(hotkey_group)
        self.hk_main = QLineEdit()
        self.hk_floating = QLineEdit()
        self.hk_organize = QLineEdit()
        self.hk_voice = QLineEdit()
        hotkey_layout.addRow("显示/隐藏主界面", self.hk_main)
        hotkey_layout.addRow("显示/隐藏悬浮窗", self.hk_floating)
        hotkey_layout.addRow("一键整理文件", self.hk_organize)
        hotkey_layout.addRow("启动/停止语音识别", self.hk_voice)
        hk_apply = QPushButton("应用快捷键")
        hk_apply.clicked.connect(self.apply_hotkeys)
        hotkey_layout.addRow("", hk_apply)
        advanced_layout.addWidget(hotkey_group)

        floating_group = QGroupBox("悬浮窗设置")
        floating_layout = QFormLayout(floating_group)
        self.float_enabled_check = QCheckBox("启动时显示悬浮窗")
        self.float_topmost_check = QCheckBox("悬浮窗始终置顶")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_value_label.setText(f"{v}%"))
        self.opacity_value_label = QLabel("85%")
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.opacity_slider)
        opacity_row.addWidget(self.opacity_value_label)
        floating_layout.addRow("", self.float_enabled_check)
        floating_layout.addRow("", self.float_topmost_check)
        floating_layout.addRow("透明度", opacity_row)
        advanced_layout.addWidget(floating_group)
        layout.addWidget(advanced_group)
        advanced_group.toggled.connect(lambda checked: hotkey_group.setVisible(checked))
        advanced_group.toggled.connect(lambda checked: floating_group.setVisible(checked))
        hotkey_group.setVisible(False)
        floating_group.setVisible(False)

        save_btn = QPushButton("保存全部配置")
        save_btn.clicked.connect(self.save_all_settings)
        layout.addWidget(save_btn)
        layout.addWidget(QLabel("提示：所有设置会自动保存，你也可以手动点一次保存。"))
        layout.addStretch(1)
        return tab

    # ========================= 样式/托盘/计时器 =========================
    def _init_tray(self) -> None:
        self.tray: Optional[QSystemTrayIcon] = None
        self.tray_flash_timer = QTimer(self)
        self.tray_flash_timer.timeout.connect(self._on_tray_flash)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.log("系统托盘不可用。")
            return

        self.tray = QSystemTrayIcon(self.flash_default_icon, self)
        self.tray.setToolTip("离线桌面智能助手")
        menu = QMenu()
        show_action = QAction("显示主界面", self)
        hide_action = QAction("隐藏主界面", self)
        floating_action = QAction("显示/隐藏悬浮窗", self)
        topmost_action = QAction("切换悬浮窗置顶", self)
        organize_action = QAction("一键整理文件", self)
        reminder_action = QAction("一键新建提醒", self)
        deps_action = QAction("一键安装依赖", self)
        model_action = QAction("一键下载语音模型", self)
        package_action = QAction("一键打包程序", self)
        voice_action = QAction("启动/停止语音识别", self)
        quit_action = QAction("退出程序", self)
        show_action.triggered.connect(self.show_main_window)
        hide_action.triggered.connect(self.hide)
        floating_action.triggered.connect(self.toggle_floating_window)
        topmost_action.triggered.connect(self.toggle_floating_topmost)
        organize_action.triggered.connect(lambda: self.organize_now(confirm=True))
        reminder_action.triggered.connect(self.quick_add_reminder)
        deps_action.triggered.connect(self.start_dependency_install)
        model_action.triggered.connect(self.start_model_download)
        package_action.triggered.connect(self.start_packaging)
        voice_action.triggered.connect(self.toggle_voice_recognition)
        quit_action.triggered.connect(self.quit_app)
        for a in [show_action, hide_action, floating_action, topmost_action, organize_action, reminder_action, deps_action, model_action, package_action, voice_action]:
            menu.addAction(a)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _init_timers(self) -> None:
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.update_monitor_metrics)
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.organize_timer = QTimer(self)
        self.organize_timer.timeout.connect(lambda: self.organize_now(confirm=False))
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_all)
        self.auto_save_timer.start(5000)
        self.reminder_timer.start(10_000)

    def load_config_to_ui(self) -> None:
        if not self.config.get("monitor_paths"):
            self.config["monitor_paths"] = candidate_monitor_paths()
        self.refresh_spin.setValue(int(self.config.get("refresh_interval_sec", 1)))
        self.model_path_edit.setText(self.config.get("voice", {}).get("model_path", ""))
        self.wake_word_check.setChecked(bool(self.config.get("voice", {}).get("wake_word_enabled", False)))
        self.wake_word_edit.setText(self.config.get("voice", {}).get("wake_word", "助手"))
        self.organize_interval_spin.setValue(int(self.config.get("organize_interval_min", 0)))
        self.hk_main.setText(self.config.get("hotkeys", {}).get("toggle_main", ""))
        self.hk_floating.setText(self.config.get("hotkeys", {}).get("toggle_floating", ""))
        self.hk_organize.setText(self.config.get("hotkeys", {}).get("organize_now", ""))
        self.hk_voice.setText(self.config.get("hotkeys", {}).get("toggle_voice", ""))
        self.float_enabled_check.setChecked(bool(self.config.get("floating", {}).get("enabled", True)))
        self.float_topmost_check.setChecked(bool(self.config.get("floating", {}).get("always_on_top", True)))
        opacity = int(self.config.get("floating", {}).get("opacity_percent", 85))
        self.opacity_slider.setValue(opacity)
        self.opacity_value_label.setText(f"{opacity}%")
        self.confirm_exit_check.setChecked(bool(self.config.get("confirm_on_exit", True)))
        self.start_minimized_check.setChecked(bool(self.config.get("start_minimized_to_tray", False)))
        self.sound_enable_check.setChecked(bool(self.config.get("alert", {}).get("sound_enabled", False)))
        self.sound_file_edit.setText(self.config.get("alert", {}).get("sound_file", ""))
        self.package_with_model_check.setChecked(bool(self.config.get("packaging", {}).get("include_model", False)))
        self.apply_refresh_interval()
        self.apply_organize_interval()
        self.apply_floating_style()
        self.refresh_dependency_status()
        self.refresh_model_status()

    def save_all_settings(self) -> None:
        try:
            self.config["refresh_interval_sec"] = int(self.refresh_spin.value())
            self.config["organize_interval_min"] = int(self.organize_interval_spin.value())
            self.config["voice"]["model_path"] = self.model_path_edit.text().strip()
            self.config["voice"]["wake_word_enabled"] = bool(self.wake_word_check.isChecked())
            self.config["voice"]["wake_word"] = self.wake_word_edit.text().strip() or "助手"
            self.config["hotkeys"]["toggle_main"] = self.hk_main.text().strip()
            self.config["hotkeys"]["toggle_floating"] = self.hk_floating.text().strip()
            self.config["hotkeys"]["organize_now"] = self.hk_organize.text().strip()
            self.config["hotkeys"]["toggle_voice"] = self.hk_voice.text().strip()
            self.config["floating"]["enabled"] = bool(self.float_enabled_check.isChecked())
            self.config["floating"]["always_on_top"] = bool(self.float_topmost_check.isChecked())
            self.config["floating"]["opacity_percent"] = int(self.opacity_slider.value())
            self.config["confirm_on_exit"] = bool(self.confirm_exit_check.isChecked())
            self.config["start_minimized_to_tray"] = bool(self.start_minimized_check.isChecked())
            self.config["alert"]["sound_enabled"] = bool(self.sound_enable_check.isChecked())
            self.config["alert"]["sound_file"] = self.sound_file_edit.text().strip()
            self.config["packaging"]["include_model"] = bool(self.package_with_model_check.isChecked())
            save_json(self.config_path, self.config)
            self.apply_refresh_interval()
            self.apply_organize_interval()
            self.apply_hotkeys()
            self.apply_floating_style()
            self.refresh_dependency_status()
            self.refresh_model_status()
            self.log("配置已保存。")
        except Exception:
            self.log(traceback.format_exc())

    def auto_save_all(self) -> None:
        try:
            self.config["refresh_interval_sec"] = int(self.refresh_spin.value())
            self.config["organize_interval_min"] = int(self.organize_interval_spin.value())
            self.config["voice"]["model_path"] = self.model_path_edit.text().strip()
            self.config["voice"]["wake_word_enabled"] = bool(self.wake_word_check.isChecked())
            self.config["voice"]["wake_word"] = self.wake_word_edit.text().strip() or "助手"
            self.config["floating"]["enabled"] = bool(self.float_enabled_check.isChecked())
            self.config["floating"]["always_on_top"] = bool(self.float_topmost_check.isChecked())
            self.config["floating"]["opacity_percent"] = int(self.opacity_slider.value())
            self.config["confirm_on_exit"] = bool(self.confirm_exit_check.isChecked())
            self.config["start_minimized_to_tray"] = bool(self.start_minimized_check.isChecked())
            self.config["alert"]["sound_enabled"] = bool(self.sound_enable_check.isChecked())
            self.config["alert"]["sound_file"] = self.sound_file_edit.text().strip()
            self.config["packaging"]["include_model"] = bool(self.package_with_model_check.isChecked())
            save_json(self.config_path, self.config)
            save_json(self.reminders_path, self.reminders)
        except Exception:
            # 自动保存不能阻塞主流程，仅记录日志
            self.log("自动保存异常: " + traceback.format_exc())

    def show_friendly_error(
        self,
        title: str,
        message: str,
        fix_label: Optional[str] = None,
        fix_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        fix_btn = None
        if fix_label and fix_callback:
            fix_btn = msg.addButton(fix_label, QMessageBox.ButtonRole.AcceptRole)
        ok_btn = msg.addButton("确定", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if fix_btn is not None and msg.clickedButton() == fix_btn:
            try:
                fix_callback()
            except Exception:
                self.log("修复动作执行失败: " + traceback.format_exc())
        elif msg.clickedButton() == ok_btn:
            pass

    def refresh_dependency_status(self) -> None:
        missing = detect_missing_packages()
        if not missing:
            self.dependency_status_label.setText("依赖状态：已就绪")
            self.install_deps_btn.setEnabled(True)
            return
        self.dependency_status_label.setText(f"依赖状态：有 {len(missing)} 项待安装（点左侧一键安装）")
        self.log("检测到缺失依赖: " + ", ".join(missing))
        self.install_deps_btn.setEnabled(True)

    def is_model_ready(self) -> bool:
        model_path = self.model_path_edit.text().strip() or self.config.get("voice", {}).get("model_path", "")
        return bool(model_path and Path(model_path).exists())

    def refresh_model_status(self) -> None:
        if self.is_model_ready():
            self.model_status_label.setText("语音模型状态：已就绪")
            return
        self.model_status_label.setText("语音模型状态：未检测到，可一键下载")

    def set_task_progress(self, value: int, status: str) -> None:
        self.task_progress_bar.setValue(max(0, min(100, int(value))))
        self.task_status_label.setText(status)

    def _run_worker(self, worker: QObject, title: str, on_finished: Callable[..., None]) -> None:
        if self.active_task_thread is not None:
            self.show_friendly_error("任务进行中", "当前已有任务正在执行，请稍后再试。")
            return
        self.task_status_label.setText(title)
        self.task_progress_bar.setValue(0)
        self.active_task_thread = QThread(self)
        self.active_worker = worker
        worker.moveToThread(self.active_task_thread)
        self.active_task_thread.started.connect(worker.run)  # type: ignore[attr-defined]
        if hasattr(worker, "log"):
            worker.log.connect(self.log)  # type: ignore[attr-defined]
        if hasattr(worker, "progress"):
            worker.progress.connect(lambda v: self.set_task_progress(v, title))  # type: ignore[attr-defined]
        if hasattr(worker, "finished"):
            worker.finished.connect(on_finished)  # type: ignore[attr-defined]
            worker.finished.connect(self.active_task_thread.quit)  # type: ignore[attr-defined]
        self.active_task_thread.finished.connect(worker.deleteLater)  # type: ignore[attr-defined]
        self.active_task_thread.finished.connect(self._cleanup_worker_thread)
        self.active_task_thread.start()

    def _cleanup_worker_thread(self) -> None:
        try:
            if self.active_task_thread is not None:
                self.active_task_thread.deleteLater()
        except Exception:
            pass
        self.active_task_thread = None
        self.active_worker = None

    def start_dependency_install(self) -> None:
        worker = DependencyInstallWorker()
        self._run_worker(worker, "正在安装依赖...", self.on_dependency_install_finished)

    def on_dependency_install_finished(self, success: bool, msg: str) -> None:
        self.set_task_progress(100, "依赖安装完成" if success else "依赖安装失败")
        self.refresh_dependency_status()
        if success:
            QMessageBox.information(self, "完成", f"{msg}\n\n如果某些功能仍不可用，请重启程序。")
        else:
            self.show_friendly_error("安装失败", msg, "重试安装", self.start_dependency_install)

    def start_model_download(self) -> None:
        worker = ModelDownloadWorker(self.data_dir)
        self._run_worker(worker, "正在下载语音模型...", self.on_model_download_finished)

    def on_model_download_finished(self, success: bool, msg: str, model_path: str) -> None:
        self.set_task_progress(100, "语音模型处理完成" if success else "语音模型处理失败")
        if success and model_path:
            self.model_path_edit.setText(model_path)
            self.config["voice"]["model_path"] = model_path
            save_json(self.config_path, self.config)
            self.refresh_model_status()
            QMessageBox.information(self, "完成", msg)
        else:
            self.show_friendly_error("模型下载失败", msg, "重试下载", self.start_model_download)

    def start_packaging(self) -> None:
        if importlib.util.find_spec("PyInstaller") is None:
            self.show_friendly_error(
                "打包组件未安装",
                "当前电脑缺少打包组件，请先一键安装依赖。",
                fix_label="一键安装依赖",
                fix_callback=self.start_dependency_install,
            )
            return
        include_model = bool(self.package_with_model_check.isChecked())
        self.config["packaging"]["include_model"] = include_model
        save_json(self.config_path, self.config)
        worker = PackageBuildWorker(Path(__file__).resolve(), include_model, self.model_path_edit.text().strip())
        self._run_worker(worker, "正在打包可执行程序...", self.on_packaging_finished)

    def on_packaging_finished(self, success: bool, msg: str, dist_dir: str) -> None:
        self.set_task_progress(100, "打包完成" if success else "打包失败")
        if success:
            QMessageBox.information(self, "打包完成", msg + "\n程序将自动打开输出目录。")
            if dist_dir:
                open_path_in_file_manager(Path(dist_dir))
        else:
            self.show_friendly_error("打包失败", msg, "重试打包", self.start_packaging)

    def toggle_floating_topmost(self) -> None:
        self.float_topmost_check.setChecked(not self.float_topmost_check.isChecked())
        self.apply_floating_style()
        self.auto_save_all()
        self.log("悬浮窗置顶状态已切换。")

    def quick_add_reminder(self) -> None:
        reminder = {
            "id": str(uuid.uuid4()),
            "content": "新提醒（可在任务提醒页编辑）",
            "next_time": (dt.datetime.now() + dt.timedelta(minutes=30)).isoformat(timespec="seconds"),
            "recurrence": "once",
            "completed": False,
        }
        self.reminders.append(reminder)
        save_json(self.reminders_path, self.reminders)
        self.refresh_reminder_table()
        QMessageBox.information(self, "提醒已创建", "已创建一条 30 分钟后的提醒，可在任务提醒页修改内容和时间。")

    def reset_default_monitor_paths(self) -> None:
        self.config["monitor_paths"] = candidate_monitor_paths()
        save_json(self.config_path, self.config)
        self.refresh_paths()
        self.log("已恢复默认监控路径（桌面 + 下载）。")

    def show_beginner_guide(self) -> None:
        QMessageBox.information(
            self,
            "新手引导（3步）",
            "第1步：先看顶部状态，如果显示缺少依赖，点击“一键安装全部运行依赖”。\n"
            "第2步：若要用语音控制，点击“一键下载并配置中文语音模型”。\n"
            "第3步：常用功能都在顶部大按钮：整理文件、悬浮监控、提醒、打包。",
        )

    def open_microphone_settings(self) -> None:
        system = platform.system().lower()
        try:
            if system == "windows":
                subprocess.Popen(["start", "ms-settings:privacy-microphone"], shell=True)
            elif system == "darwin":
                QDesktopServices.openUrl(QUrl("x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"))
            else:
                # Linux 桌面环境差异较大，优先尝试 GNOME 设置
                subprocess.Popen(["gnome-control-center", "privacy"])
        except Exception:
            try:
                webbrowser.open("about:blank")
            except Exception:
                pass

    # ========================= 日志与通用 =========================
    def log(self, text: str) -> None:
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {text}"
        self.log_view.appendPlainText(line)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
        self.log(f"{title}: {message}")

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.toggle_main_window()

    def show_main_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def toggle_main_window(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show_main_window()

    # ========================= 系统监控 =========================
    def apply_refresh_interval(self) -> None:
        interval = int(self.refresh_spin.value())
        self.config["refresh_interval_sec"] = interval
        self.monitor_timer.start(max(1, interval) * 1000)
        self.log(f"系统监控刷新频率已设为 {interval} 秒。")
        save_json(self.config_path, self.config)

    def update_monitor_metrics(self) -> None:
        if psutil is None:
            self.cpu_label.setText("CPU: 依赖缺失")
            self.mem_label.setText("内存: 依赖缺失")
            self.disk_label.setText("磁盘: 依赖缺失")
            self.net_up_label.setText("上传: 依赖缺失")
            self.net_down_label.setText("下载: 依赖缺失")
            if not self.monitor_missing_prompted:
                self.monitor_missing_prompted = True
                self.show_friendly_error(
                    "监控功能未就绪",
                    "系统监控组件缺失，点击“一键修复”自动安装后即可正常显示。",
                    fix_label="一键修复",
                    fix_callback=self.start_dependency_install,
                )
            return
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            root = Path.home().anchor if Path.home().anchor else "/"
            disk = psutil.disk_usage(root).percent
            now = time.time()
            net = psutil.net_io_counters()
            if self.prev_net is None:
                up_speed = 0.0
                down_speed = 0.0
            else:
                dt_sec = max(1e-6, now - self.prev_net_time)
                up_speed = (net.bytes_sent - self.prev_net.bytes_sent) / dt_sec
                down_speed = (net.bytes_recv - self.prev_net.bytes_recv) / dt_sec
            self.prev_net = net
            self.prev_net_time = now
            up_txt = format_speed(up_speed)
            down_txt = format_speed(down_speed)

            self.cpu_label.setText(f"CPU: {cpu:.1f}%")
            self.mem_label.setText(f"内存: {mem:.1f}%")
            self.disk_label.setText(f"磁盘: {disk:.1f}%")
            self.net_up_label.setText(f"上传: {up_txt}")
            self.net_down_label.setText(f"下载: {down_txt}")
            self.cpu_bar.setValue(int(cpu))
            self.mem_bar.setValue(int(mem))
            self.disk_bar.setValue(int(disk))

            if self.floating_window.isVisible():
                self.floating_window.update_metrics(cpu, mem, disk, up_txt, down_txt)
        except Exception:
            self.log("监控更新失败: " + traceback.format_exc())

    def apply_floating_style(self) -> None:
        try:
            opacity = int(self.opacity_slider.value()) / 100.0
            topmost = bool(self.float_topmost_check.isChecked())
            enabled = bool(self.float_enabled_check.isChecked())
            self.floating_window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, topmost)
            self.floating_window.setWindowOpacity(opacity)
            self.floating_window.hide()
            if enabled:
                self.floating_window.show()
        except Exception:
            self.log("悬浮窗样式应用失败: " + traceback.format_exc())

    def toggle_floating_window(self) -> None:
        try:
            if self.floating_window.isVisible():
                self.floating_window.hide()
                self.log("悬浮窗已隐藏。")
            else:
                self.apply_floating_style()
                self.floating_window.show()
                self.log("悬浮窗已显示。")
        except Exception:
            self.log(traceback.format_exc())

    # ========================= 文件整理 =========================
    def refresh_paths(self) -> None:
        self.paths_list.clear()
        for p in self.config.get("monitor_paths", []):
            self.paths_list.addItem(str(p))

    def add_monitor_path(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择监控路径")
        if not path:
            return
        paths = self.config.get("monitor_paths", [])
        if path not in paths:
            paths.append(path)
            self.config["monitor_paths"] = paths
            save_json(self.config_path, self.config)
            self.refresh_paths()
            self.log(f"已添加监控路径: {path}")

    def remove_monitor_path(self) -> None:
        row = self.paths_list.currentRow()
        if row < 0:
            return
        paths = self.config.get("monitor_paths", [])
        if 0 <= row < len(paths):
            removed = paths.pop(row)
            self.config["monitor_paths"] = paths
            save_json(self.config_path, self.config)
            self.refresh_paths()
            self.log(f"已移除监控路径: {removed}")

    def refresh_rule_table(self) -> None:
        rules = self.config.get("rules", [])
        self.rules_table.setRowCount(len(rules))
        for i, rule in enumerate(rules):
            self.rules_table.setItem(i, 0, QTableWidgetItem(str(rule.get("name", ""))))
            self.rules_table.setItem(i, 1, QTableWidgetItem(str(rule.get("folder", ""))))
            self.rules_table.setItem(i, 2, QTableWidgetItem(", ".join(rule.get("exts", []))))

    def add_rule(self) -> None:
        dlg = RuleEditDialog(parent=self)
        if dlg.exec():
            rule = dlg.get_rule()
            self.config["rules"].append(rule)
            save_json(self.config_path, self.config)
            self.refresh_rule_table()
            self.log(f"已新增规则: {rule['name']}")

    def edit_rule(self) -> None:
        row = self.rules_table.currentRow()
        if row < 0:
            return
        rules = self.config.get("rules", [])
        if row >= len(rules):
            return
        dlg = RuleEditDialog(rules[row], self)
        if dlg.exec():
            rules[row] = dlg.get_rule()
            self.config["rules"] = rules
            save_json(self.config_path, self.config)
            self.refresh_rule_table()
            self.log(f"已更新规则: {rules[row]['name']}")

    def delete_rule(self) -> None:
        row = self.rules_table.currentRow()
        if row < 0:
            return
        rules = self.config.get("rules", [])
        if row >= len(rules):
            return
        name = rules[row].get("name", "未命名")
        rules.pop(row)
        self.config["rules"] = rules
        save_json(self.config_path, self.config)
        self.refresh_rule_table()
        self.log(f"已删除规则: {name}")

    def apply_organize_interval(self) -> None:
        minutes = int(self.organize_interval_spin.value())
        self.config["organize_interval_min"] = minutes
        save_json(self.config_path, self.config)
        if minutes <= 0:
            self.organize_timer.stop()
            self.log("定时整理已关闭。")
            return
        self.organize_timer.start(minutes * 60 * 1000)
        self.log(f"定时整理已开启：每 {minutes} 分钟执行一次。")

    def _build_ext_map(self) -> Tuple[Dict[str, str], str]:
        ext_map: Dict[str, str] = {}
        other_folder = "其他"
        for rule in self.config.get("rules", []):
            folder = str(rule.get("folder", "其他")).strip() or "其他"
            if str(rule.get("name", "")) == "其他":
                other_folder = folder
            for ext in rule.get("exts", []):
                normalized = str(ext).strip().lower()
                if not normalized:
                    continue
                if not normalized.startswith("."):
                    normalized = f".{normalized}"
                ext_map[normalized] = folder
        return ext_map, other_folder

    def organize_now(self, confirm: bool = True) -> None:
        paths = [Path(p) for p in self.config.get("monitor_paths", [])]
        if not paths:
            self.show_friendly_error(
                "未设置整理路径",
                "还没有可整理的路径。点击“一键修复”可自动恢复桌面和下载目录。",
                fix_label="一键修复",
                fix_callback=self.reset_default_monitor_paths,
            )
            return
        if confirm:
            ret = QMessageBox.question(
                self,
                "整理确认",
                "将按当前规则整理桌面和下载文件夹，操作可撤销。\n确定现在执行吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                self.log("已取消本次文件整理。")
                return
        ext_map, other_folder = self._build_ext_map()
        operations: List[Dict[str, str]] = []
        moved_count = 0
        try:
            for base in paths:
                if not base.exists() or not base.is_dir():
                    self.log(f"跳过无效路径: {base}")
                    continue
                for item in list(base.iterdir()):
                    if not item.is_file():
                        continue
                    ext = item.suffix.lower()
                    folder = ext_map.get(ext, other_folder)
                    target_dir = base / folder
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = unique_target_path(target_dir / item.name)
                    shutil.move(str(item), str(target))
                    operations.append({"src": str(item), "dst": str(target), "time": dt.datetime.now().isoformat(timespec="seconds")})
                    moved_count += 1
            self.last_organize_ops = operations
            save_json(self.undo_path, self.last_organize_ops)
            self.log(f"整理完成：共移动 {moved_count} 个文件。")
            if confirm:
                QMessageBox.information(self, "整理完成", f"已整理 {moved_count} 个文件，可使用“撤销上一次整理”恢复。")
        except Exception:
            self.log("文件整理失败: " + traceback.format_exc())
            self.show_error("整理失败", "文件整理过程中发生异常，请查看日志。")

    def undo_last_organize(self) -> None:
        ops = self.last_organize_ops or load_json(self.undo_path, [])
        if not ops:
            self.log("没有可撤销的整理记录。")
            return
        reverted = 0
        try:
            for op in reversed(ops):
                src = Path(op.get("src", ""))
                dst = Path(op.get("dst", ""))
                if not dst.exists():
                    continue
                src.parent.mkdir(parents=True, exist_ok=True)
                move_back_target = unique_target_path(src)
                shutil.move(str(dst), str(move_back_target))
                reverted += 1
            self.last_organize_ops = []
            save_json(self.undo_path, [])
            self.log(f"撤销完成：恢复 {reverted} 个文件。")
        except Exception:
            self.log("撤销失败: " + traceback.format_exc())
            self.show_error("撤销失败", "撤销过程中发生异常，请查看日志。")

    # ========================= 本地提醒 =========================
    def refresh_reminder_table(self) -> None:
        self.reminder_table.setRowCount(len(self.reminders))
        for i, rem in enumerate(self.reminders):
            rid = str(rem.get("id", ""))
            content = str(rem.get("content", ""))
            next_t = str(rem.get("next_time", ""))
            rec = str(rem.get("recurrence", "once"))
            status = "已完成" if rem.get("completed", False) else "进行中"
            self.reminder_table.setItem(i, 0, QTableWidgetItem(rid))
            self.reminder_table.setItem(i, 1, QTableWidgetItem(content))
            self.reminder_table.setItem(i, 2, QTableWidgetItem(next_t))
            self.reminder_table.setItem(i, 3, QTableWidgetItem(rec))
            self.reminder_table.setItem(i, 4, QTableWidgetItem(status))

    def _selected_reminder_index(self) -> int:
        row = self.reminder_table.currentRow()
        if row < 0 or row >= len(self.reminders):
            return -1
        return row

    def add_reminder(self) -> None:
        dlg = ReminderEditDialog(parent=self)
        if not dlg.exec():
            return
        data = dlg.get_data()
        reminder = {
            "id": str(uuid.uuid4()),
            "content": data["content"],
            "next_time": data["next_time"],
            "recurrence": data["recurrence"],
            "completed": False,
        }
        self.reminders.append(reminder)
        save_json(self.reminders_path, self.reminders)
        self.refresh_reminder_table()
        self.log(f"新增提醒: {reminder['content']} @ {reminder['next_time']}")

    def edit_reminder(self) -> None:
        idx = self._selected_reminder_index()
        if idx < 0:
            return
        dlg = ReminderEditDialog(self.reminders[idx], self)
        if not dlg.exec():
            return
        data = dlg.get_data()
        self.reminders[idx]["content"] = data["content"]
        self.reminders[idx]["next_time"] = data["next_time"]
        self.reminders[idx]["recurrence"] = data["recurrence"]
        self.reminders[idx]["completed"] = False
        save_json(self.reminders_path, self.reminders)
        self.refresh_reminder_table()
        self.log(f"已更新提醒: {data['content']}")

    def delete_reminder(self) -> None:
        idx = self._selected_reminder_index()
        if idx < 0:
            return
        rem = self.reminders.pop(idx)
        save_json(self.reminders_path, self.reminders)
        self.refresh_reminder_table()
        self.log(f"已删除提醒: {rem.get('content', '')}")

    def complete_reminder(self) -> None:
        idx = self._selected_reminder_index()
        if idx < 0:
            return
        self.reminders[idx]["completed"] = True
        save_json(self.reminders_path, self.reminders)
        self.refresh_reminder_table()
        self.log(f"提醒已标记完成: {self.reminders[idx].get('content', '')}")

    def check_reminders(self) -> None:
        now = dt.datetime.now()
        changed = False
        for rem in self.reminders:
            if rem.get("completed", False):
                continue
            try:
                due = dt.datetime.fromisoformat(str(rem.get("next_time", "")))
            except Exception:
                continue
            if now >= due:
                self.trigger_reminder(rem)
                recurrence = rem.get("recurrence", "once")
                if recurrence == "once":
                    rem["completed"] = True
                else:
                    rem["next_time"] = next_time(due, recurrence).isoformat(timespec="seconds")
                changed = True
        if changed:
            save_json(self.reminders_path, self.reminders)
            self.refresh_reminder_table()

    def trigger_reminder(self, rem: Dict[str, Any]) -> None:
        content = str(rem.get("content", "提醒"))
        self.log(f"触发提醒: {content}")
        if self.tray:
            self.tray.showMessage("任务提醒", content, QSystemTrayIcon.MessageIcon.Information, 8000)
        self.flash_count = 8
        self.tray_flash_timer.start(300)
        if self.sound_enable_check.isChecked():
            self.play_alert_sound()
        QMessageBox.information(self, "任务提醒", content)

    def play_alert_sound(self) -> None:
        file_path = self.sound_file_edit.text().strip()
        try:
            if file_path and sa is not None and Path(file_path).exists():
                wave_obj = sa.WaveObject.from_wave_file(file_path)
                wave_obj.play()
            else:
                QApplication.beep()
        except Exception:
            QApplication.beep()

    def _on_tray_flash(self) -> None:
        if not self.tray:
            self.tray_flash_timer.stop()
            return
        if self.flash_count <= 0:
            self.tray.setIcon(self.flash_default_icon)
            self.tray_flash_timer.stop()
            return
        current = self.tray.icon()
        if current.cacheKey() == self.flash_default_icon.cacheKey():
            self.tray.setIcon(self.flash_alt_icon)
        else:
            self.tray.setIcon(self.flash_default_icon)
        self.flash_count -= 1

    def select_sound_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "WAV Files (*.wav);;All Files (*)")
        if file_path:
            self.sound_file_edit.setText(file_path)

    # ========================= 离线语音 =========================
    def select_model_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择 Vosk 模型目录")
        if folder:
            self.model_path_edit.setText(folder)
            self.config["voice"]["model_path"] = folder
            save_json(self.config_path, self.config)
            self.refresh_model_status()

    def generate_model_download_script(self) -> None:
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
        target_zip = self.data_dir / "vosk-model-small-cn-0.22.zip"
        target_dir = self.data_dir / "vosk-model-small-cn"
        script_text = ""
        if platform.system().lower() == "windows":
            script_path = self.data_dir / "download_vosk_model.bat"
            script_text = (
                "@echo off\n"
                "setlocal\n"
                f"set URL={model_url}\n"
                f"set ZIP={target_zip}\n"
                f"set OUT={self.data_dir}\n"
                "powershell -Command \"Invoke-WebRequest -Uri %URL% -OutFile %ZIP%\"\n"
                "powershell -Command \"Expand-Archive -LiteralPath %ZIP% -DestinationPath %OUT% -Force\"\n"
                f"echo 下载完成后，请把模型目录设置为: {target_dir}\n"
                "pause\n"
            )
        else:
            script_path = self.data_dir / "download_vosk_model.sh"
            script_text = (
                "#!/usr/bin/env bash\n"
                "set -e\n"
                f"URL='{model_url}'\n"
                f"ZIP='{target_zip}'\n"
                f"OUT='{self.data_dir}'\n"
                "mkdir -p \"$OUT\"\n"
                "if command -v curl >/dev/null 2>&1; then curl -L \"$URL\" -o \"$ZIP\"; else wget -O \"$ZIP\" \"$URL\"; fi\n"
                "unzip -o \"$ZIP\" -d \"$OUT\"\n"
                f"echo '下载完成后，请把模型目录设置为: {target_dir}'\n"
            )
        try:
            script_path.write_text(script_text, encoding="utf-8")
            if platform.system().lower() != "windows":
                script_path.chmod(0o755)
            self.log(f"已生成模型下载脚本: {script_path}")
            QMessageBox.information(
                self,
                "下载脚本已生成",
                f"脚本路径:\n{script_path}\n\n无网环境下可先在其他设备下载后拷贝模型目录到本机。",
            )
        except Exception:
            self.log("生成下载脚本失败: " + traceback.format_exc())

    def toggle_voice_recognition(self) -> None:
        if self.voice_thread is not None:
            self.stop_voice_recognition()
            return
        self.start_voice_recognition()

    def start_voice_recognition(self) -> None:
        try:
            model_path = self.model_path_edit.text().strip()
            wake_enabled = self.wake_word_check.isChecked()
            wake_word = self.wake_word_edit.text().strip() or "助手"
            if not model_path or not Path(model_path).exists():
                self.show_friendly_error(
                    "语音模型未就绪",
                    "当前还没有可用的中文语音模型，请先点击“一键修复”自动下载。",
                    fix_label="一键修复",
                    fix_callback=self.start_model_download,
                )
                return
            if Model is None or KaldiRecognizer is None or sd is None:
                self.show_friendly_error(
                    "语音组件未就绪",
                    "语音组件缺失，请点击“一键修复”自动安装依赖。",
                    fix_label="一键修复",
                    fix_callback=self.start_dependency_install,
                )
                return
            self.config["voice"]["model_path"] = model_path
            self.config["voice"]["wake_word_enabled"] = wake_enabled
            self.config["voice"]["wake_word"] = wake_word
            save_json(self.config_path, self.config)

            self.voice_worker = VoiceWorker(model_path, wake_enabled, wake_word)
            self.voice_thread = QThread(self)
            self.voice_worker.moveToThread(self.voice_thread)
            self.voice_thread.started.connect(self.voice_worker.run)
            self.voice_worker.status.connect(self.on_voice_status)
            self.voice_worker.recognized.connect(self.on_voice_recognized)
            self.voice_worker.failed.connect(self.on_voice_failed)
            self.voice_worker.finished.connect(self.on_voice_finished)
            self.voice_worker.finished.connect(self.voice_thread.quit)
            self.voice_thread.finished.connect(self.voice_thread.deleteLater)
            self.voice_thread.start()
            self.voice_status_label.setText("启动中...")
            self.voice_start_btn.setText("停止离线语音识别")
            self.log("语音识别线程已启动。")
        except Exception:
            self.log("启动语音识别失败: " + traceback.format_exc())
            self.show_friendly_error(
                "语音识别启动失败",
                "请在系统设置里允许本程序访问麦克风，点击“一键修复”可直接打开系统设置。",
                fix_label="一键修复",
                fix_callback=self.open_microphone_settings,
            )

    def stop_voice_recognition(self) -> None:
        try:
            if self.voice_worker is not None:
                self.voice_worker.stop()
            if self.voice_thread is not None:
                self.voice_thread.quit()
                self.voice_thread.wait(3000)
            self.voice_worker = None
            self.voice_thread = None
            self.voice_status_label.setText("已停止")
            self.voice_start_btn.setText("启动离线语音识别")
            self.log("语音识别已停止。")
        except Exception:
            self.log("停止语音识别失败: " + traceback.format_exc())

    def on_voice_status(self, msg: str) -> None:
        self.voice_status_label.setText(msg)
        self.log(f"语音状态: {msg}")

    def on_voice_failed(self, detail: str) -> None:
        self.voice_status_label.setText("异常")
        self.log("语音识别异常: " + detail)
        self.show_friendly_error(
            "语音识别中断",
            "语音服务运行中断。请检查麦克风权限和模型状态后重试。",
            fix_label="打开麦克风设置",
            fix_callback=self.open_microphone_settings,
        )

    def on_voice_finished(self) -> None:
        self.voice_worker = None
        self.voice_thread = None
        self.voice_start_btn.setText("启动离线语音识别")
        self.voice_status_label.setText("已停止")

    def on_voice_recognized(self, text: str) -> None:
        self.log(f"识别结果: {text}")
        self.dispatch_voice_command(text)

    def refresh_custom_command_table(self) -> None:
        commands = self.config.get("voice", {}).get("custom_commands", [])
        self.custom_cmd_table.setRowCount(len(commands))
        for i, cmd in enumerate(commands):
            self.custom_cmd_table.setItem(i, 0, QTableWidgetItem(str(cmd.get("phrase", ""))))
            self.custom_cmd_table.setItem(i, 1, QTableWidgetItem(str(cmd.get("action", ""))))
            self.custom_cmd_table.setItem(i, 2, QTableWidgetItem(str(cmd.get("payload", ""))))

    def add_custom_command(self) -> None:
        dlg = VoiceCommandDialog(parent=self)
        if dlg.exec():
            cmd = dlg.get_data()
            if not cmd["phrase"]:
                self.show_error("输入错误", "触发短语不能为空。")
                return
            self.config["voice"]["custom_commands"].append(cmd)
            save_json(self.config_path, self.config)
            self.refresh_custom_command_table()
            self.log(f"新增自定义语音指令: {cmd['phrase']}")

    def edit_custom_command(self) -> None:
        row = self.custom_cmd_table.currentRow()
        commands = self.config.get("voice", {}).get("custom_commands", [])
        if row < 0 or row >= len(commands):
            return
        dlg = VoiceCommandDialog(commands[row], self)
        if dlg.exec():
            commands[row] = dlg.get_data()
            self.config["voice"]["custom_commands"] = commands
            save_json(self.config_path, self.config)
            self.refresh_custom_command_table()
            self.log(f"更新自定义语音指令: {commands[row].get('phrase', '')}")

    def delete_custom_command(self) -> None:
        row = self.custom_cmd_table.currentRow()
        commands = self.config.get("voice", {}).get("custom_commands", [])
        if row < 0 or row >= len(commands):
            return
        phrase = commands[row].get("phrase", "")
        commands.pop(row)
        self.config["voice"]["custom_commands"] = commands
        save_json(self.config_path, self.config)
        self.refresh_custom_command_table()
        self.log(f"已删除自定义语音指令: {phrase}")

    def dispatch_voice_command(self, text: str) -> None:
        lowered = text.strip().lower()
        if not lowered:
            return

        for cmd in self.config.get("voice", {}).get("custom_commands", []):
            phrase = str(cmd.get("phrase", "")).strip().lower()
            if phrase and phrase in lowered:
                action = str(cmd.get("action", "")).strip()
                payload = str(cmd.get("payload", "")).strip()
                self.execute_action(action, payload)
                return

        if "关闭当前窗口" in lowered:
            self.execute_action("close_window", "")
            return
        if lowered.startswith("打开"):
            app = text[2:].strip()
            self.execute_action("open_app", app)
            return
        if "整理" in lowered:
            self.execute_action("organize_now", "")
            return
        if "显示" in lowered and ("悬浮" in lowered or "监控" in lowered):
            self.execute_action("show_floating", "")
            return
        if "隐藏" in lowered and ("悬浮" in lowered or "监控" in lowered):
            self.execute_action("hide_floating", "")
            return
        if "新建任务提醒" in lowered or lowered.startswith("提醒"):
            content = text.replace("新建任务提醒", "").replace("提醒", "").strip() or "语音创建提醒"
            self.execute_action("create_reminder", content)
            return
        if "退出程序" in lowered or "退出助手" in lowered:
            self.execute_action("exit_app", "")
            return

        self.log(f"未匹配语音指令: {text}")

    # ========================= 动作注册与执行 =========================
    def _register_actions(self) -> None:
        self.register_action("open_app", self._action_open_app)
        self.register_action("close_window", self._action_close_window)
        self.register_action("organize_now", lambda _: self.organize_now())
        self.register_action("show_floating", lambda _: self._set_floating_visible(True))
        self.register_action("hide_floating", lambda _: self._set_floating_visible(False))
        self.register_action("toggle_floating", lambda _: self.toggle_floating_window())
        self.register_action("create_reminder", self._action_create_reminder)
        self.register_action("exit_app", lambda _: self.quit_app())
        self.register_action("run_shell", self._action_run_shell)

    def register_action(self, name: str, handler: Callable[[str], None]) -> None:
        self.action_handlers[name] = handler

    def execute_action(self, action: str, payload: str) -> None:
        handler = self.action_handlers.get(action)
        if handler is None:
            self.log(f"未知动作: {action}")
            return
        try:
            handler(payload)
            self.log(f"动作执行: {action} ({payload})")
        except Exception:
            self.log(f"动作执行失败({action}): {traceback.format_exc()}")

    def _action_open_app(self, app_name: str) -> None:
        name = app_name.strip()
        if not name:
            self.log("打开应用失败：未提供应用名称。")
            return
        try:
            p = Path(name)
            if p.exists():
                if platform.system().lower() == "windows":
                    os.startfile(str(p))  # type: ignore[attr-defined]
                elif platform.system().lower() == "darwin":
                    subprocess.Popen(["open", str(p)])
                else:
                    subprocess.Popen(["xdg-open", str(p)])
                return
        except Exception:
            pass

        system = platform.system().lower()
        win_alias = {"记事本": "notepad", "计算器": "calc", "画图": "mspaint", "资源管理器": "explorer"}
        mac_alias = {"终端": "Terminal", "访达": "Finder", "文本编辑": "TextEdit", "计算器": "Calculator"}
        linux_alias = {"终端": "x-terminal-emulator", "文件管理器": "xdg-open .", "计算器": "gnome-calculator"}
        if system == "windows":
            target = win_alias.get(name, name)
            subprocess.Popen(target, shell=True)
        elif system == "darwin":
            target = mac_alias.get(name, name)
            subprocess.Popen(["open", "-a", target])
        else:
            target = linux_alias.get(name, name)
            if " " in target:
                subprocess.Popen(target, shell=True)
            else:
                subprocess.Popen([target])

    def _action_close_window(self, _: str) -> None:
        if keyboard is None:
            self.log("关闭窗口失败：pynput 不可用。")
            return
        ctl = keyboard.Controller()
        system = platform.system().lower()
        if system == "darwin":
            with ctl.pressed(keyboard.Key.cmd):
                ctl.press("w")
                ctl.release("w")
        else:
            with ctl.pressed(keyboard.Key.alt):
                ctl.press(keyboard.Key.f4)
                ctl.release(keyboard.Key.f4)

    def _action_create_reminder(self, payload: str) -> None:
        content = payload.strip() or "语音提醒"
        remind_time = dt.datetime.now() + dt.timedelta(minutes=1)
        reminder = {
            "id": str(uuid.uuid4()),
            "content": content,
            "next_time": remind_time.isoformat(timespec="seconds"),
            "recurrence": "once",
            "completed": False,
        }
        self.reminders.append(reminder)
        save_json(self.reminders_path, self.reminders)
        self.refresh_reminder_table()
        self.log(f"已创建提醒: {content} @ {remind_time}")

    def _action_run_shell(self, payload: str) -> None:
        cmd = payload.strip()
        if not cmd:
            self.log("run_shell 未执行：命令为空。")
            return
        subprocess.Popen(cmd, shell=True)

    def _set_floating_visible(self, visible: bool) -> None:
        if visible:
            self.apply_floating_style()
            self.floating_window.show()
        else:
            self.floating_window.hide()

    # ========================= 全局热键 =========================
    def apply_hotkeys(self) -> None:
        self.config["hotkeys"]["toggle_main"] = self.hk_main.text().strip()
        self.config["hotkeys"]["toggle_floating"] = self.hk_floating.text().strip()
        self.config["hotkeys"]["organize_now"] = self.hk_organize.text().strip()
        self.config["hotkeys"]["toggle_voice"] = self.hk_voice.text().strip()
        save_json(self.config_path, self.config)

        mapping = {
            self.config["hotkeys"]["toggle_main"]: self.toggle_main_window,
            self.config["hotkeys"]["toggle_floating"]: self.toggle_floating_window,
            self.config["hotkeys"]["organize_now"]: self.organize_now,
            self.config["hotkeys"]["toggle_voice"]: self.toggle_voice_recognition,
        }
        self.hotkey_manager.register(mapping)

    # ========================= 退出控制 =========================
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.is_quitting:
            event.accept()
            return
        if not self.confirm_exit_check.isChecked():
            self.hide()
            event.ignore()
            return
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("退出确认")
        msg.setText("请选择操作：")
        to_tray = msg.addButton("最小化到托盘", QMessageBox.ButtonRole.AcceptRole)
        quit_btn = msg.addButton("退出程序", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = msg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == to_tray:
            self.hide()
            event.ignore()
            return
        if clicked == quit_btn:
            self.quit_app()
            event.accept()
            return
        if clicked == cancel_btn:
            event.ignore()
            return
        event.ignore()

    def quit_app(self) -> None:
        self.is_quitting = True
        try:
            self.stop_voice_recognition()
        except Exception:
            pass
        try:
            self.hotkey_manager.stop()
        except Exception:
            pass
        try:
            save_json(self.config_path, self.config)
            save_json(self.reminders_path, self.reminders)
        except Exception:
            pass
        QApplication.quit()


def apply_dark_mono_style(app: QApplication) -> None:
    app.setStyleSheet(
        """
        * {
            background: #000000;
            color: #FFFFFF;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12px;
        }
        QMainWindow, QWidget, QDialog, QMenu, QTabWidget::pane, QGroupBox {
            background: #000000;
            color: #FFFFFF;
            border: 1px solid #2E2E2E;
        }
        QGroupBox {
            margin-top: 12px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px 0 6px;
            color: #FFFFFF;
            background: #000000;
            font-weight: bold;
        }
        QLabel, QCheckBox, QRadioButton {
            color: #FFFFFF;
            background: transparent;
        }
        QLineEdit, QPlainTextEdit, QListWidget, QTableWidget, QDateTimeEdit, QComboBox, QSpinBox {
            background: #070707;
            color: #FFFFFF;
            border: 1px solid #2D2D2D;
            border-radius: 3px;
            selection-background-color: #FFFFFF;
            selection-color: #000000;
        }
        QTabWidget::pane {
            top: -1px;
        }
        QTabBar::tab {
            background: #080808;
            color: #FFFFFF;
            border: 1px solid #2F2F2F;
            padding: 8px 14px;
            min-width: 86px;
        }
        QTabBar::tab:selected {
            background: #111111;
            border-bottom: 2px solid #FFFFFF;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background: #121212;
        }
        QPushButton {
            background: #101010;
            color: #FFFFFF;
            border: 1px solid #454545;
            border-radius: 4px;
            padding: 6px 10px;
        }
        QPushButton:hover {
            background: #1A1A1A;
        }
        QPushButton:pressed {
            background: #262626;
        }
        QPushButton[primary="true"] {
            background: #FFFFFF;
            color: #000000;
            border: 1px solid #FFFFFF;
            font-size: 13px;
            font-weight: bold;
            padding: 8px 10px;
        }
        QPushButton[primary="true"]:hover {
            background: #EAEAEA;
        }
        QPushButton[secondary="true"] {
            background: #141414;
            border: 1px solid #5A5A5A;
            font-weight: bold;
        }
        QProgressBar {
            border: 1px solid #4A4A4A;
            border-radius: 3px;
            text-align: center;
            background: #0A0A0A;
        }
        QProgressBar::chunk {
            background-color: #FFFFFF;
        }
        QHeaderView::section {
            background: #0F0F0F;
            color: #FFFFFF;
            border: 1px solid #2F2F2F;
            padding: 4px;
        }
        QTableWidget {
            gridline-color: #1E1E1E;
            alternate-background-color: #090909;
        }
        QMenu::item:selected {
            background: #FFFFFF;
            color: #000000;
        }
        """
    )


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    apply_dark_mono_style(app)
    window = AssistantMainWindow()
    if window.config.get("start_minimized_to_tray", False) and window.tray is not None:
        window.hide()
    else:
        window.show()
    if window.config.get("floating", {}).get("enabled", True):
        window.apply_floating_style()
        window.floating_window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(traceback.format_exc())
        raise
