# -*- coding: utf-8 -*-
"""
Clipboard Plain Text Purifier for Windows 10/11
- Single-file app
- Tray background mode
- Smart / Extreme purification modes
- Global hotkeys via pynput
- Autostart via Startup folder
"""

import ctypes
import hashlib
import os
import sys
import time
import winreg
from ctypes import wintypes


# -----------------------------
# Win32 constants
# -----------------------------
WM_NULL = 0x0000
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010
WM_COMMAND = 0x0111
WM_SIZE = 0x0005
WM_APP = 0x8000
WM_TRAYICON = WM_APP + 1
WM_HOTKEY_ACTION = WM_APP + 2
WM_CLIPBOARDUPDATE = 0x031D
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203

SW_HIDE = 0
SW_SHOW = 5

WS_OVERLAPPEDWINDOW = 0x00CF0000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_VSCROLL = 0x00200000
ES_MULTILINE = 0x0004
ES_AUTOVSCROLL = 0x0040
ES_READONLY = 0x0800
ES_LEFT = 0x0000
WS_EX_CLIENTEDGE = 0x00000200

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MF_DISABLED = 0x00000002
TPM_RIGHTBUTTON = 0x0002

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010
NIIF_INFO = 0x00000001

IDI_APPLICATION = 32512
IDC_ARROW = 32512

CF_TEXT = 1
CF_UNICODETEXT = 13

GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040


# menu IDs
ID_MENU_STATUS = 1001
ID_MENU_MODE_STATUS = 1002
ID_MENU_TOGGLE_MODE = 1003
ID_MENU_TOGGLE_ENABLE = 1004
ID_MENU_CLEAR_CLIPBOARD = 1005
ID_MENU_TOGGLE_AUTOSTART = 1006
ID_MENU_TOGGLE_LOG_WINDOW = 1007
ID_MENU_EXIT = 1008

# hotkey action IDs
ACTION_TOGGLE_MODE = 2001
ACTION_TOGGLE_ENABLE = 2002
ACTION_CLEAR_CLIPBOARD = 2003

# modes
MODE_SMART = 0
MODE_EXTREME = 1


# -----------------------------
# Win32 setup
# -----------------------------
LRESULT = ctypes.c_ssize_t
WNDPROC_TYPE = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
HMODULE = wintypes.HANDLE
HINSTANCE = wintypes.HANDLE
HICON = wintypes.HANDLE
HCURSOR = wintypes.HANDLE
HBRUSH = wintypes.HANDLE
HMENU = wintypes.HANDLE
ATOM = wintypes.WORD


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", HICON),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC_TYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", wintypes.POINT),
        ("lPrivate", wintypes.DWORD),
    ]


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

# function prototypes that matter for 64-bit correctness
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = HMODULE

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = ATOM

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    HMENU,
    HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.LoadIconW.argtypes = [HINSTANCE, wintypes.LPCWSTR]
user32.LoadIconW.restype = HICON

user32.LoadCursorW.argtypes = [HINSTANCE, wintypes.LPCWSTR]
user32.LoadCursorW.restype = HCURSOR

user32.CreatePopupMenu.restype = HMENU

user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int

user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT

user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE

user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HANDLE

kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
kernel32.GlobalLock.restype = wintypes.LPVOID

kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
kernel32.GlobalUnlock.restype = wintypes.BOOL

kernel32.GlobalFree.argtypes = [wintypes.HANDLE]
kernel32.GlobalFree.restype = wintypes.HANDLE

shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL


APP_INSTANCE = None


def _make_int_resource(value):
    # MAKEINTRESOURCEW helper
    return ctypes.c_wchar_p(value)


def _wndproc_factory():
    @WNDPROC_TYPE
    def wndproc(hwnd, msg, wparam, lparam):
        global APP_INSTANCE
        if APP_INSTANCE is None:
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        return APP_INSTANCE.dispatch_wndproc(hwnd, msg, wparam, lparam)

    return wndproc


WNDPROC = _wndproc_factory()


class ClipboardPurifierApp:
    def __init__(self):
        self.hinstance = kernel32.GetModuleHandleW(None)
        self.main_class_name = "ClipboardPurifierMainWindow"
        self.log_class_name = "ClipboardPurifierLogWindow"

        self.main_hwnd = None
        self.log_hwnd = None
        self.log_edit_hwnd = None

        self.hicon = user32.LoadIconW(None, _make_int_resource(IDI_APPLICATION))
        self.tray_uid = 1

        self.enabled = True
        self.mode = MODE_SMART
        self.autostart = False

        self.running = True
        self.hotkey_listener = None

        self._fmt_rtf = user32.RegisterClipboardFormatW("Rich Text Format")
        self._fmt_html = user32.RegisterClipboardFormatW("HTML Format")

        self._ignore_clipboard_until = 0.0
        self._last_written_signature = ""
        self._last_seen_signature = ""
        self._last_seen_time = 0.0

        self._logs = []
        self._max_logs = 250

        self.settings_key = r"Software\ClipboardTextPurifier"
        self.startup_file_name = "ClipboardTextPurifier_Autostart.cmd"

        self._load_settings()
        self.autostart = self._is_autostart_enabled()

    # -----------------------------
    # text helpers
    # -----------------------------
    def mode_name(self):
        return "智能保留模式" if self.mode == MODE_SMART else "极致纯净模式"

    def status_name(self):
        return "开启" if self.enabled else "暂停"

    def _tray_tip(self):
        return f"剪贴板纯文本净化工具 | 状态:{self.status_name()} | 模式:{self.mode_name()}"

    # -----------------------------
    # logging and notifications
    # -----------------------------
    def log(self, message):
        line = f"[{time.strftime('%H:%M:%S')}] {message}"
        self._logs.append(line)
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs :]

        print(line)
        self._refresh_log_window()

    def _refresh_log_window(self):
        if not self.log_edit_hwnd:
            return
        user32.SetWindowTextW(self.log_edit_hwnd, "\r\n".join(self._logs))

    def show_balloon(self, title, message):
        if not self.main_hwnd:
            return
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.main_hwnd
        nid.uID = self.tray_uid
        nid.uFlags = NIF_INFO
        nid.szInfoTitle = (title or "提示")[:63]
        nid.szInfo = (message or "")[:255]
        nid.dwInfoFlags = NIIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def friendly_error(self, message):
        self.log(message)
        self.show_balloon("操作提醒", message)

    # -----------------------------
    # settings persistence
    # -----------------------------
    def _load_settings(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.settings_key, 0, winreg.KEY_READ)
            try:
                self.enabled = bool(winreg.QueryValueEx(key, "Enabled")[0])
            except FileNotFoundError:
                self.enabled = True
            try:
                self.mode = int(winreg.QueryValueEx(key, "Mode")[0])
            except FileNotFoundError:
                self.mode = MODE_SMART
            winreg.CloseKey(key)
        except OSError:
            self.enabled = True
            self.mode = MODE_SMART

        if self.mode not in (MODE_SMART, MODE_EXTREME):
            self.mode = MODE_SMART

    def _save_settings(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.settings_key)
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1 if self.enabled else 0)
            winreg.SetValueEx(key, "Mode", 0, winreg.REG_DWORD, int(self.mode))
            winreg.CloseKey(key)
        except OSError:
            self.log("本地设置保存失败，但不影响继续使用。")

    # -----------------------------
    # autostart by startup folder
    # -----------------------------
    def _startup_folder(self):
        appdata = os.environ.get("APPDATA", "")
        return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

    def _autostart_cmd_path(self):
        return os.path.join(self._startup_folder(), self.startup_file_name)

    def _build_launch_command(self):
        if getattr(sys, "frozen", False):
            exe_path = os.path.abspath(sys.executable)
            return f'start "" "{exe_path}"'

        py = os.path.abspath(sys.executable)
        pyw = os.path.join(os.path.dirname(py), "pythonw.exe")
        py_runner = pyw if os.path.exists(pyw) else py
        script = os.path.abspath(sys.argv[0])
        return f'start "" "{py_runner}" "{script}"'

    def _is_autostart_enabled(self):
        return os.path.exists(self._autostart_cmd_path())

    def _set_autostart(self, enable):
        path = self._autostart_cmd_path()
        try:
            if enable:
                content = "@echo off\r\n" + self._build_launch_command() + "\r\n"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.autostart = True
                self.log("开机自启：已开启")
                self.show_balloon("开机自启已开启", "下次开机后会自动后台运行。")
            else:
                if os.path.exists(path):
                    os.remove(path)
                self.autostart = False
                self.log("开机自启：已关闭")
                self.show_balloon("开机自启已关闭", "以后开机不会自动启动。")
        except Exception:
            self.friendly_error("开机自启设置失败，请稍后再试。")

    # -----------------------------
    # clipboard safe operations
    # -----------------------------
    def _open_clipboard_safe(self, retry=20, delay_ms=20):
        for _ in range(retry):
            if user32.OpenClipboard(None):
                return True
            kernel32.Sleep(delay_ms)
        return False

    def _read_clipboard_text_info(self):
        info = {"text": None, "has_rich": False}

        if not self._open_clipboard_safe():
            return info

        try:
            has_unicode = bool(user32.IsClipboardFormatAvailable(CF_UNICODETEXT))
            has_ansi = bool(user32.IsClipboardFormatAvailable(CF_TEXT))

            has_rtf = bool(self._fmt_rtf and user32.IsClipboardFormatAvailable(self._fmt_rtf))
            has_html = bool(self._fmt_html and user32.IsClipboardFormatAvailable(self._fmt_html))
            info["has_rich"] = has_rtf or has_html

            # only process text content; skip file/image/audio/video formats
            if not has_unicode and not has_ansi:
                return info

            if has_unicode:
                h = user32.GetClipboardData(CF_UNICODETEXT)
                if h:
                    p = kernel32.GlobalLock(h)
                    if p:
                        try:
                            info["text"] = ctypes.wstring_at(p)
                        finally:
                            kernel32.GlobalUnlock(h)
            else:
                h = user32.GetClipboardData(CF_TEXT)
                if h:
                    p = kernel32.GlobalLock(h)
                    if p:
                        try:
                            raw = ctypes.string_at(p)
                            try:
                                info["text"] = raw.decode("utf-8", errors="strict")
                            except UnicodeDecodeError:
                                info["text"] = raw.decode("gbk", errors="replace")
                        finally:
                            kernel32.GlobalUnlock(h)
        finally:
            user32.CloseClipboard()

        return info

    def _write_clipboard_text_plain(self, text):
        if text is None:
            return False

        if not self._open_clipboard_safe():
            return False

        h_mem = None
        try:
            if not user32.EmptyClipboard():
                return False

            data = (text + "\x00").encode("utf-16-le")
            h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE | GMEM_ZEROINIT, len(data))
            if not h_mem:
                return False

            p = kernel32.GlobalLock(h_mem)
            if not p:
                kernel32.GlobalFree(h_mem)
                return False

            try:
                ctypes.memmove(p, data, len(data))
            finally:
                kernel32.GlobalUnlock(h_mem)

            if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                kernel32.GlobalFree(h_mem)
                return False

            h_mem = None  # ownership passed to system
            return True
        finally:
            user32.CloseClipboard()
            if h_mem:
                kernel32.GlobalFree(h_mem)

    def clear_clipboard(self, show_tip=True):
        if not self._open_clipboard_safe():
            self.friendly_error("清空剪贴板失败，请稍后再试。")
            return

        try:
            user32.EmptyClipboard()
        finally:
            user32.CloseClipboard()

        self._ignore_clipboard_until = time.monotonic() + 0.35
        self._last_written_signature = ""
        self._last_seen_signature = ""
        self.log("已清空剪贴板")

        if show_tip:
            self.show_balloon("剪贴板已清空", "当前剪贴板内容已经清除。")

    # -----------------------------
    # purification
    # -----------------------------
    @staticmethod
    def sanitize_extreme(text):
        if text is None:
            return ""

        t = text.replace("\r\n", "\n").replace("\r", "\n")
        t = t.replace("\t", " ")

        lines = [line.strip() for line in t.split("\n")]
        out = []
        prev_blank = False
        for line in lines:
            blank = (line == "")
            if blank and prev_blank:
                continue
            out.append(line)
            prev_blank = blank

        return "\n".join(out).strip().replace("\n", "\r\n")

    def process_clipboard_update(self):
        try:
            if not self.enabled:
                return

            now = time.monotonic()
            if now < self._ignore_clipboard_until:
                return

            info = self._read_clipboard_text_info()
            text = info.get("text")
            has_rich = bool(info.get("has_rich"))

            if text is None:
                return

            source_sig = hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()
            if source_sig == self._last_seen_signature and (now - self._last_seen_time) < 0.2:
                return
            self._last_seen_signature = source_sig
            self._last_seen_time = now

            if self.mode == MODE_SMART:
                # smart mode: remove rich formatting only, keep content unchanged
                if not has_rich:
                    return
                purified = text
            else:
                purified = self.sanitize_extreme(text)
                if purified == text and not has_rich:
                    return

            write_sig = hashlib.sha256((purified + f"|{self.mode}").encode("utf-8", errors="surrogatepass")).hexdigest()
            if write_sig == self._last_written_signature:
                return

            if not self._write_clipboard_text_plain(purified):
                return

            self._last_written_signature = write_sig
            self._ignore_clipboard_until = time.monotonic() + 0.35

            if self.mode == MODE_SMART:
                self.log("已自动净化：仅清除富文本格式，文字内容保持不变")
            else:
                self.log("已自动净化：已输出极致纯净文本")
        except Exception:
            self.friendly_error("处理剪贴板时出现异常，本次内容已自动跳过。")

    # -----------------------------
    # tray
    # -----------------------------
    def _add_tray_icon(self):
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.main_hwnd
        nid.uID = self.tray_uid
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self.hicon
        nid.szTip = self._tray_tip()[:127]
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

    def _remove_tray_icon(self):
        if not self.main_hwnd:
            return
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.main_hwnd
        nid.uID = self.tray_uid
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))

    def _update_tray_tip(self):
        if not self.main_hwnd:
            return
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.main_hwnd
        nid.uID = self.tray_uid
        nid.uFlags = NIF_TIP
        nid.szTip = self._tray_tip()[:127]
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def _show_tray_menu(self):
        menu = user32.CreatePopupMenu()
        if not menu:
            return

        try:
            user32.AppendMenuW(menu, MF_STRING | MF_DISABLED, ID_MENU_STATUS, f"净化状态：{self.status_name()}")
            user32.AppendMenuW(menu, MF_STRING | MF_DISABLED, ID_MENU_MODE_STATUS, f"当前模式：{self.mode_name()}")
            user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)

            user32.AppendMenuW(menu, MF_STRING, ID_MENU_TOGGLE_MODE, "切换净化模式 (Ctrl+Alt+V)")
            user32.AppendMenuW(menu, MF_STRING, ID_MENU_TOGGLE_ENABLE, "开启/暂停净化 (Ctrl+Alt+B)")
            user32.AppendMenuW(menu, MF_STRING, ID_MENU_CLEAR_CLIPBOARD, "清空剪贴板 (Ctrl+Alt+X)")
            user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)

            autostart_label = "关闭开机自启" if self.autostart else "开启开机自启"
            user32.AppendMenuW(menu, MF_STRING, ID_MENU_TOGGLE_AUTOSTART, autostart_label)

            log_label = "隐藏控制台窗口" if (self.log_hwnd and user32.IsWindowVisible(self.log_hwnd)) else "显示控制台窗口"
            user32.AppendMenuW(menu, MF_STRING, ID_MENU_TOGGLE_LOG_WINDOW, log_label)

            user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            user32.AppendMenuW(menu, MF_STRING, ID_MENU_EXIT, "退出程序")

            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            user32.SetForegroundWindow(self.main_hwnd)
            user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON, pt.x, pt.y, 0, self.main_hwnd, None)
            user32.PostMessageW(self.main_hwnd, WM_NULL, 0, 0)
        finally:
            user32.DestroyMenu(menu)

    # -----------------------------
    # hotkeys (pynput)
    # -----------------------------
    def _start_hotkeys(self):
        try:
            from pynput import keyboard
        except Exception:
            self.hotkey_listener = None
            self.friendly_error("全局快捷键未启用：缺少依赖 pynput。")
            return

        def post_action(action_id):
            try:
                if self.main_hwnd:
                    user32.PostMessageW(self.main_hwnd, WM_HOTKEY_ACTION, action_id, 0)
            except Exception:
                self.friendly_error("快捷键触发失败，已自动忽略。")

        try:
            self.hotkey_listener = keyboard.GlobalHotKeys(
                {
                    "<ctrl>+<alt>+v": lambda: post_action(ACTION_TOGGLE_MODE),
                    "<ctrl>+<alt>+b": lambda: post_action(ACTION_TOGGLE_ENABLE),
                    "<ctrl>+<alt>+x": lambda: post_action(ACTION_CLEAR_CLIPBOARD),
                }
            )
            self.hotkey_listener.start()
            self.log("全局快捷键已启用：Ctrl+Alt+V / Ctrl+Alt+B / Ctrl+Alt+X")
        except Exception:
            self.hotkey_listener = None
            self.friendly_error("全局快捷键初始化失败，请重启后重试。")

    def _stop_hotkeys(self):
        try:
            if self.hotkey_listener:
                self.hotkey_listener.stop()
                self.hotkey_listener = None
        except Exception:
            pass

    # -----------------------------
    # mode/state toggles
    # -----------------------------
    def toggle_mode(self, show_tip=True):
        self.mode = MODE_EXTREME if self.mode == MODE_SMART else MODE_SMART
        self._save_settings()
        self._update_tray_tip()
        self.log(f"净化模式切换为：{self.mode_name()}")
        if show_tip:
            self.show_balloon("净化模式已切换", f"当前：{self.mode_name()}")

    def toggle_enabled(self, show_tip=True):
        self.enabled = not self.enabled
        self._save_settings()
        self._update_tray_tip()
        self.log(f"净化总开关：{self.status_name()}")
        if show_tip:
            msg = "已开启净化，复制文字会自动清格式。" if self.enabled else "已暂停净化，复制内容会保持原样。"
            self.show_balloon("净化开关已切换", msg)

    # -----------------------------
    # window creation
    # -----------------------------
    def _register_window_classes(self):
        wc_main = WNDCLASSW()
        wc_main.style = 0
        wc_main.lpfnWndProc = WNDPROC
        wc_main.cbClsExtra = 0
        wc_main.cbWndExtra = 0
        wc_main.hInstance = self.hinstance
        wc_main.hIcon = self.hicon
        wc_main.hCursor = user32.LoadCursorW(None, _make_int_resource(IDC_ARROW))
        wc_main.hbrBackground = 0
        wc_main.lpszMenuName = None
        wc_main.lpszClassName = self.main_class_name
        user32.RegisterClassW(ctypes.byref(wc_main))

        wc_log = WNDCLASSW()
        wc_log.style = 0
        wc_log.lpfnWndProc = WNDPROC
        wc_log.cbClsExtra = 0
        wc_log.cbWndExtra = 0
        wc_log.hInstance = self.hinstance
        wc_log.hIcon = self.hicon
        wc_log.hCursor = user32.LoadCursorW(None, _make_int_resource(IDC_ARROW))
        wc_log.hbrBackground = 0
        wc_log.lpszMenuName = None
        wc_log.lpszClassName = self.log_class_name
        user32.RegisterClassW(ctypes.byref(wc_log))

    def _create_main_window(self):
        self.main_hwnd = user32.CreateWindowExW(
            0,
            self.main_class_name,
            "ClipboardPurifierHiddenWindow",
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            self.hinstance,
            None,
        )
        if not self.main_hwnd:
            raise RuntimeError("Failed to create hidden main window.")

    def _create_log_window(self):
        width = 640
        height = 420
        self.log_hwnd = user32.CreateWindowExW(
            0,
            self.log_class_name,
            "剪贴板纯文本净化工具 - 控制台",
            WS_OVERLAPPEDWINDOW,
            160,
            120,
            width,
            height,
            None,
            None,
            self.hinstance,
            None,
        )

        if not self.log_hwnd:
            return

        self.log_edit_hwnd = user32.CreateWindowExW(
            WS_EX_CLIENTEDGE,
            "EDIT",
            "",
            WS_CHILD | WS_VISIBLE | WS_VSCROLL | ES_LEFT | ES_MULTILINE | ES_AUTOVSCROLL | ES_READONLY,
            10,
            10,
            width - 35,
            height - 70,
            self.log_hwnd,
            None,
            self.hinstance,
            None,
        )

        user32.ShowWindow(self.log_hwnd, SW_HIDE)

    def _toggle_log_window(self):
        if not self.log_hwnd:
            return
        if user32.IsWindowVisible(self.log_hwnd):
            user32.ShowWindow(self.log_hwnd, SW_HIDE)
        else:
            user32.ShowWindow(self.log_hwnd, SW_SHOW)
            user32.SetForegroundWindow(self.log_hwnd)

    # -----------------------------
    # message handlers
    # -----------------------------
    def _on_hotkey_action(self, action_id):
        if action_id == ACTION_TOGGLE_MODE:
            self.toggle_mode(show_tip=True)
        elif action_id == ACTION_TOGGLE_ENABLE:
            self.toggle_enabled(show_tip=True)
        elif action_id == ACTION_CLEAR_CLIPBOARD:
            self.clear_clipboard(show_tip=True)

    def _on_menu_command(self, cmd_id):
        if cmd_id == ID_MENU_TOGGLE_MODE:
            self.toggle_mode(show_tip=True)
        elif cmd_id == ID_MENU_TOGGLE_ENABLE:
            self.toggle_enabled(show_tip=True)
        elif cmd_id == ID_MENU_CLEAR_CLIPBOARD:
            self.clear_clipboard(show_tip=True)
        elif cmd_id == ID_MENU_TOGGLE_AUTOSTART:
            self._set_autostart(not self.autostart)
        elif cmd_id == ID_MENU_TOGGLE_LOG_WINDOW:
            self._toggle_log_window()
        elif cmd_id == ID_MENU_EXIT:
            user32.DestroyWindow(self.main_hwnd)

    def _log_wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_CLOSE:
            user32.ShowWindow(hwnd, SW_HIDE)
            return 0

        if msg == WM_SIZE and self.log_edit_hwnd:
            width = lparam & 0xFFFF
            height = (lparam >> 16) & 0xFFFF
            user32.MoveWindow(self.log_edit_hwnd, 10, 10, max(100, width - 20), max(100, height - 20), True)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _main_wndproc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            if lparam == WM_RBUTTONUP:
                self._show_tray_menu()
            elif lparam == WM_LBUTTONDBLCLK:
                self._toggle_log_window()
            return 0

        if msg == WM_COMMAND:
            self._on_menu_command(wparam & 0xFFFF)
            return 0

        if msg == WM_CLIPBOARDUPDATE:
            self.process_clipboard_update()
            return 0

        if msg == WM_HOTKEY_ACTION:
            self._on_hotkey_action(int(wparam))
            return 0

        if msg == WM_DESTROY:
            self.running = False
            try:
                user32.RemoveClipboardFormatListener(self.main_hwnd)
            except Exception:
                pass
            self._remove_tray_icon()
            self._stop_hotkeys()
            self._save_settings()
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def dispatch_wndproc(self, hwnd, msg, wparam, lparam):
        try:
            if hwnd == self.log_hwnd:
                return self._log_wndproc(hwnd, msg, wparam, lparam)
            if hwnd == self.main_hwnd:
                return self._main_wndproc(hwnd, msg, wparam, lparam)
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        except Exception:
            self.friendly_error("窗口事件处理异常，程序已自动恢复。")
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    # -----------------------------
    # run
    # -----------------------------
    def start(self):
        global APP_INSTANCE
        APP_INSTANCE = self

        self._register_window_classes()
        self._create_main_window()
        self._create_log_window()

        self._add_tray_icon()
        self._update_tray_tip()

        if not user32.AddClipboardFormatListener(self.main_hwnd):
            self.friendly_error("系统剪贴板监听初始化失败，稍后可重启程序再试。")

        self._start_hotkeys()

        self.log("程序已在后台运行（系统托盘）。")
        self.log(f"当前净化状态：{self.status_name()}")
        self.log(f"当前净化模式：{self.mode_name()}")
        self.log("快捷键：Ctrl+Alt+V 切换模式 | Ctrl+Alt+B 开关净化 | Ctrl+Alt+X 清空剪贴板")

        self.show_balloon(
            "剪贴板净化工具已启动",
            f"当前{self.status_name()}，模式为{self.mode_name()}。右键托盘可使用全部功能。",
        )

        self._message_loop()

    def _message_loop(self):
        msg = MSG()
        while self.running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == -1:
                self.friendly_error("消息循环异常，程序将安全退出。")
                break
            if ret == 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


def main():
    app = ClipboardPurifierApp()
    try:
        app.start()
    except Exception:
        # top-level fallback: no stack trace popup for users
        try:
            user32.MessageBoxW(None, "程序启动失败，请重新运行。", "剪贴板纯文本净化工具", 0x00000010)
        except Exception:
            pass


if __name__ == "__main__":
    main()
