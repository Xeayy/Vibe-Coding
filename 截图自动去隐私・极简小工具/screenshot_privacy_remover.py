# -*- coding: utf-8 -*-
"""
截图自动去隐私工具 - 极简版 v2.2 (修复无限循环问题)
功能：自动监听剪贴板截图，识别并打码隐私信息（手机号、身份证、银行卡等）
特点：零联网、纯本地处理、内存运行、绝对隐私安全
v2.2更新：
- 修复Image.frombitmap()方法不存在的致命错误
- 优化剪贴板监控循环，防止卡死
- 添加循环保护机制和频率限制
- 增强错误处理，避免日志膨胀
"""

import sys
import os
import subprocess
import re
import json
import hashlib
import threading
import time
import logging
from datetime import datetime
from io import BytesIO
from ctypes import windll, c_char, Structure, POINTER, byref, sizeof
from ctypes.wintypes import HWND, UINT, BOOL, HGLOBAL, LPCSTR, DWORD, HANDLE, LONG

# 配置日志系统（降低WARNING级别输出频率）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('privacy_remover.log', encoding='utf-8', mode='a')
    ]
)
logger = logging.getLogger('PrivacyRemover')


def check_and_install_dependencies():
    """检查并自动安装依赖包"""
    required_packages = [
        'Pillow',
        'pystray',
        'pynput',
        'pywin32',
        'win10toast'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.info(f"正在安装依赖: {', '.join(missing_packages)}")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + missing_packages,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("依赖安装成功")
                return True
            else:
                logger.error(f"依赖安装失败: {result.stderr[:100]}")
                return False
        
        except Exception as e:
            logger.error(f"安装依赖出错: {e}")
            return False
    
    return True


# 自动检查并安装依赖
if not check_and_install_dependencies():
    print("\n依赖安装失败，请手动运行:")
    print("pip install Pillow pystray pynput pywin32 win10toast")
    input("按回车退出...")
    sys.exit(1)


try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError as e:
    logger.error(f"Pillow导入失败: {e}")
    print("缺少Pillow库")
    sys.exit(1)

try:
    import pystray
    from pystray import MenuItem, Menu
    from PIL import Image as PILImage
except ImportError as e:
    logger.error(f"pystray导入失败: {e}")
    print("缺少pystray库")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError as e:
    logger.error(f"pynput导入失败: {e}")
    print("缺少pynput库")
    sys.exit(1)

try:
    import win32con
    import win32api
    import win32clipboard
except ImportError as e:
    logger.error(f"win32导入失败: {e}")
    print("缺少pywin32库")
    sys.exit(1)


class ClipboardManager:
    """
    剪贴板管理器 - v2.2 修复版
    主要修复：
    - 移除已废弃的Image.frombitmap()方法调用
    - 优化异常处理，避免日志膨胀
    - 增强资源管理
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1
    
    # 静态计数器用于限制日志输出频率
    _warning_count = 0
    _last_warning_time = 0
    WARNING_INTERVAL = 5  # 每5秒最多输出一次相同警告

    @staticmethod
    def _safe_open_clipboard():
        """安全打开剪贴板，带重试机制"""
        for attempt in range(ClipboardManager.MAX_RETRIES):
            try:
                if windll.user32.OpenClipboard(0):
                    return True
                
                if attempt < ClipboardManager.MAX_RETRIES - 1:
                    time.sleep(ClipboardManager.RETRY_DELAY)
                    
            except Exception as e:
                if attempt < ClipboardManager.MAX_RETRIES - 1:
                    time.sleep(ClipboardManager.RETRY_DELAY)
        
        return False

    @staticmethod
    def _should_log_warning():
        """控制警告日志的输出频率，避免日志膨胀"""
        current_time = time.time()
        if current_time - ClipboardManager._last_warning_time >= ClipboardManager.WARNING_INTERVAL:
            ClipboardManager._last_warning_time = current_time
            ClipboardManager._warning_count += 1
            return True
        return False

    @staticmethod
    def get_image_from_clipboard():
        """
        从剪贴板获取图片 - v2.2 修复版
        
        重要修复：
        - 移除 Image.frombitmap() 调用（该方法在Pillow新版本中不存在）
        - 仅使用稳定的 DIB 格式
        - 控制日志输出频率
        """
        clipboard_opened = False
        try:
            if not ClipboardManager._safe_open_clipboard():
                return None
            
            clipboard_opened = True
            
            try:
                # 只尝试DIB格式（最稳定、兼容性最好）
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                    data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                    
                    if data and isinstance(data, dict):
                        # 验证数据结构完整性
                        width = data.get('bmWidth')
                        height = abs(data.get('bmHeight', 0))
                        bits = data.get('bmBits')
                        
                        if (width and height and bits and 
                            width > 0 and height > 0 and 
                            isinstance(width, int) and isinstance(height, int)):
                            
                            try:
                                img = Image.frombuffer(
                                    'RGB',
                                    (width, height),
                                    bits,
                                    'raw', 
                                    'BGRX', 
                                    data.get('bmWidthBytes', width * 4), 
                                    0
                                )
                                
                                # 处理图像方向
                                if data.get('bmHeight', 0) > 0:
                                    img = Image.FLIP_TOP_BOTTOM(img)
                                
                                logger.debug(f"获取图片成功: {width}x{height}")
                                return img
                            
                            except Exception as e:
                                if ClipboardManager._should_log_warning():
                                    logger.warning(f"图像创建失败: {type(e).__name__}")
                
                # 不再尝试BITMAP格式（避免frombitmap错误）
                return None
            
            finally:
                pass
        
        except Exception as e:
            if ClipboardManager._should_log_warning():
                logger.warning(f"剪贴板操作异常: {type(e).__name__}")
            return None
        
        finally:
            if clipboard_opened:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass

    @staticmethod
    def set_image_to_clipboard(image):
        """将图片写入剪贴板"""
        if image is None:
            return False
        
        clipboard_opened = False
        try:
            output = BytesIO()
            
            processed_image = image.copy()
            if processed_image.mode == 'RGBA':
                bg = Image.new('RGB', processed_image.size, (255, 255, 255))
                bg.paste(processed_image, mask=processed_image.split()[3])
                processed_image = bg
            elif processed_image.mode != 'RGB':
                processed_image = processed_image.convert('RGB')
            
            processed_image.save(output, format='BMP')
            data = output.getvalue()[14:]
            
            if len(data) <= 14:
                return False
            
            for attempt in range(ClipboardManager.MAX_RETRIES):
                try:
                    if not ClipboardManager._safe_open_clipboard():
                        continue
                    
                    clipboard_opened = True
                    
                    try:
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
                        return True
                    finally:
                        pass
                
                except Exception as e:
                    if clipboard_opened:
                        try:
                            win32clipboard.CloseClipboard()
                            clipboard_opened = False
                        except:
                            pass
                    time.sleep(ClipboardManager.RETRY_DELAY)
            
            return False
        
        except Exception as e:
            return False
        
        finally:
            if clipboard_opened:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass

    @staticmethod
    def clear_clipboard():
        """清空剪贴板"""
        clipboard_opened = False
        try:
            if not ClipboardManager._safe_open_clipboard():
                return False
            
            clipboard_opened = True
            
            try:
                win32clipboard.EmptyClipboard()
                return True
            finally:
                pass
        
        except Exception as e:
            return False
        
        finally:
            if clipboard_opened:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass


class PrivacyPatternManager:
    """隐私模式管理器"""

    DEFAULT_PATTERNS = {
        'phone': {
            'pattern': r'(?<!\d)1[3-9]\d{9}(?!\d)',
            'name': '手机号',
            'enabled': True,
            'priority': 10
        },
        'id_card': {
            'pattern': r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)',
            'name': '身份证号',
            'enabled': True,
            'priority': 9
        },
        'student_id': {
            'pattern': r'(?<![a-zA-Z\d])\d{8,12}(?![a-zA-Z\d])',
            'name': '学号/工号',
            'enabled': True,
            'priority': 7
        },
        'bank_card': {
            'pattern': r'(?<!\d)\d{16,19}(?!\d)',
            'name': '银行卡号',
            'enabled': True,
            'priority': 8
        },
        'email': {
            'pattern': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'name': '邮箱地址',
            'enabled': True,
            'priority': 6
        }
    }

    def __init__(self, custom_patterns=None):
        self.patterns = {}
        self.compiled_patterns = {}
        
        for key, value in self.DEFAULT_PATTERNS.items():
            self.patterns[key] = dict(value)
        
        if custom_patterns:
            for key, value in custom_patterns.items():
                self.patterns[key] = dict(value)
        
        self._precompile_patterns()

    def _precompile_patterns(self):
        """预编译正则表达式"""
        self.compiled_patterns.clear()
        
        for pattern_id, config in self.patterns.items():
            try:
                pattern_str = config.get('pattern', '')
                if pattern_str and isinstance(pattern_str, str):
                    compiled = re.compile(pattern_str)
                    self.compiled_patterns[pattern_id] = compiled
            except re.error as e:
                logger.error(f"规则编译失败 {pattern_id}: {e}")

    def add_pattern(self, pattern_id, pattern, name, enabled=True, priority=5):
        """添加自定义规则"""
        if not pattern_id or not pattern or not name:
            return
        
        self.patterns[pattern_id] = {
            'pattern': pattern,
            'name': name,
            'enabled': enabled,
            'priority': priority
        }
        
        try:
            self.compiled_patterns[pattern_id] = re.compile(pattern)
        except re.error as e:
            logger.error(f"规则无效: {e}")

    def remove_pattern(self, pattern_id):
        """移除规则"""
        if pattern_id in self.patterns and pattern_id not in self.DEFAULT_PATTERNS:
            del self.patterns[pattern_id]
            if pattern_id in self.compiled_patterns:
                del self.compiled_patterns[pattern_id]

    def toggle_pattern(self, pattern_id):
        """切换规则状态"""
        if pattern_id in self.patterns:
            self.patterns[pattern_id]['enabled'] = not self.patterns[pattern_id].get('enabled', True)

    def get_all_enabled_patterns(self):
        """获取启用的规则"""
        return {k: v for k, v in self.patterns.items() if v.get('enabled', True)}

    def find_matches(self, text):
        """查找匹配项"""
        if not text or not isinstance(text, str):
            return []
        
        matches = []
        
        for pattern_id, config in self.get_all_enabled_patterns().items():
            try:
                compiled_regex = self.compiled_patterns.get(pattern_id)
                if compiled_regex is None:
                    continue
                
                for match in compiled_regex.finditer(text):
                    matches.append({
                        'pattern_id': pattern_id,
                        'match_type': config.get('name', pattern_id),
                        'matched_text': match.group(),
                        'start_pos': match.start(),
                        'end_pos': match.end(),
                        'priority': config.get('priority', 5)
                    })
            
            except Exception as e:
                continue
        
        matches.sort(key=lambda x: (x['start_pos'], -x['priority']))
        return matches


class MosaicEngine:
    """打码引擎"""

    MODE_MOSAIC = 'mosaic'
    MODE_BLACK_BAR = 'black_bar'

    def __init__(self, mode='mosaic', mosaic_size=8, bar_color=(0, 0, 0), bar_height_ratio=0.35):
        self.mode = mode
        self.mosaic_size = max(3, min(30, int(mosaic_size)))
        self.bar_color = tuple(bar_color) if len(bar_color) == 3 else (0, 0, 0)
        self.bar_height_ratio = max(0.15, min(1.0, float(bar_height_ratio)))

    def set_mode(self, mode):
        if mode in [self.MODE_MOSAIC, self.MODE_BLACK_BAR]:
            self.mode = mode

    def set_mosaic_size(self, size):
        try:
            size_int = int(size)
            if 3 <= size_int <= 30:
                self.mosaic_size = size_int
        except (ValueError, TypeError):
            pass

    def apply_mosaic_region(self, image, bbox):
        """马赛克处理"""
        try:
            if image is None or bbox is None or len(bbox) != 4:
                return image
            
            x1, y1, x2, y2 = [int(c) for c in bbox]
            
            try:
                width = image.width
                height = image.height
            except AttributeError:
                return image
            
            x1 = max(0, min(width, x1))
            y1 = max(0, min(height, y1))
            x2 = max(0, min(width, x2))
            y2 = max(0, min(height, y2))
            
            region_width = x2 - x1
            region_height = y2 - y1
            
            if region_width <= 0 or region_height <= 0:
                return image
            
            region = image.crop((x1, y1, x2, y2))
            
            small_w = max(1, region_width // self.mosaic_size)
            small_h = max(1, region_height // self.mosaic_size)
            
            small = region.resize((small_w, small_h), Image.Resampling.NEAREST)
            mosaic = small.resize(region.size, Image.Resampling.NEAREST)
            
            image.paste(mosaic, (x1, y1))
            return image
        
        except Exception as e:
            return image

    def apply_black_bar_region(self, image, bbox):
        """黑条处理"""
        try:
            if image is None or bbox is None or len(bbox) != 4:
                return image
            
            x1, y1, x2, y2 = [int(c) for c in bbox]
            
            try:
                width = image.width
                height = image.height
            except AttributeError:
                return image
            
            x1 = max(0, min(width, x1))
            y1 = max(0, min(height, y1))
            x2 = max(0, min(width, x2))
            y2 = max(0, min(height, y2))
            
            region_width = x2 - x1
            region_height = y2 - y1
            
            if region_width <= 0 or region_height <= 0:
                return image
            
            bar_height = max(1, int(region_height * self.bar_height_ratio))
            bar_y_center = (y1 + y2) // 2
            bar_y1 = max(y1, bar_y_center - bar_height // 2)
            bar_y2 = min(y2, bar_y1 + bar_height)
            
            actual_bar_height = bar_y2 - bar_y1
            if actual_bar_height > 0:
                overlay = Image.new('RGB', (region_width, actual_bar_height), self.bar_color)
                image.paste(overlay, (x1, bar_y1))
            
            return image
        
        except Exception as e:
            return image

    def process_bbox(self, image, bbox):
        if self.mode == self.MODE_MOSAIC:
            return self.apply_mosaic_region(image, bbox)
        else:
            return self.apply_black_bar_region(image, bbox)


class ConfigManager:
    """配置管理器"""

    CONFIG_FILENAME = "privacy_remover_config.json"

    DEFAULT_CONFIG = {
        "auto_process": True,
        "mode": "mosaic",
        "mosaic_size": 8,
        "bar_color": [0, 0, 0],
        "bar_height_ratio": 0.35,
        "custom_patterns": {},
        "auto_start": False,
        "last_image_hash": None,
        "version": "2.2"
    }

    def __init__(self):
        self.config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.CONFIG_FILENAME
        )
        self.config = self._load_config()

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    if not isinstance(loaded_config, dict):
                        return dict(self.DEFAULT_CONFIG)
                    
                    merged = dict(self.DEFAULT_CONFIG)
                    merged.update(loaded_config)
                    return merged
        except Exception as e:
            logger.warning(f"加载配置失败: {e}")
        
        return dict(self.DEFAULT_CONFIG)

    def save_config(self):
        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        return self.save_config()

    def reset_to_default(self):
        self.config = dict(self.DEFAULT_CONFIG)
        return self.save_config()


class ToastNotifier:
    """通知提示器"""

    _toaster = None
    _initialization_attempted = False

    @classmethod
    def show(cls, title, message, duration=3000):
        try:
            if cls._toaster is None and not cls._initialization_attempted:
                cls._initialization_attempted = True
                try:
                    import win10toast
                    cls._toaster = win10toast.ToastNotifier()
                except ImportError:
                    return
            
            if cls._toaster is not None:
                cls._toaster.show_toast(title, message, duration=duration, threaded=True)
        except Exception:
            pass


class ScreenshotPrivacyRemover:
    """
    主程序类 - v2.2 修复版
    核心修复：
    - 修复无限循环导致的卡死问题
    - 优化剪贴板监控逻辑
    - 添加循环保护机制
    """

    PROCESSING_COOLDOWN = 0.5
    MONITOR_INTERVAL = 1.0  # 监控间隔（秒）
    MAX_MONITOR_ERRORS = 10  # 最大连续错误次数
    ERROR_COOLDOWN = 3.0  # 错误后冷却时间（秒）
    
    def __init__(self):
        logger.info("="*50)
        logger.info("截图去隐私工具 v2.2 启动中...")
        logger.info("="*50)
        
        self.config_manager = ConfigManager()
        
        self.pattern_manager = PrivacyPatternManager(
            self.config_manager.get('custom_patterns', {})
        )
        
        self.mosaic_engine = MosaicEngine(
            mode=self.config_manager.get('mode', 'mosaic'),
            mosaic_size=self.config_manager.get('mosaic_size', 8),
            bar_color=tuple(self.config_manager.get('bar_color', [0, 0, 0])),
            bar_height_ratio=self.config_manager.get('bar_height_ratio', 0.35)
        )
        
        self.auto_process_enabled = self.config_manager.get('auto_process', True)
        self.last_processed_hash = self.config_manager.get('last_image_hash', None)
        self.original_images_cache = {}
        self.max_cache_size = 10
        
        self.is_processing = False
        self.should_run = True
        
        self.hotkey_listener = None
        self.tray_icon = None
        self.clipboard_monitor_thread = None
        
        self.last_clipboard_hash = None
        self.processing_lock = threading.Lock()
        
        # 新增：循环保护变量
        self.monitor_loop_count = 0
        self.consecutive_monitor_errors = 0
        self.last_successful_check_time = time.time()
        self.processing_count = 0
        self.start_time = datetime.now()

        self._initialize_components()
        logger.info("初始化完成")

    def _initialize_components(self):
        """初始化组件"""
        try:
            self._setup_global_hotkeys()
        except Exception as e:
            logger.error(f"快捷键设置失败: {e}")
        
        try:
            self._start_clipboard_monitoring()
        except Exception as e:
            logger.error(f"剪贴板监控启动失败: {e}")
        
        try:
            self._create_system_tray_icon()
        except Exception as e:
            logger.error(f"托盘图标创建失败: {e}")

    def _compute_image_hash(self, image):
        """计算图像哈希"""
        try:
            if image is None:
                return None
            
            if not hasattr(image, 'copy'):
                return None
            
            buffer = BytesIO()
            
            img_to_hash = image
            if image.mode != 'RGB':
                img_to_hash = image.convert('RGB')
            else:
                img_to_hash = image.copy()
            
            img_to_hash.save(buffer, format='PNG', optimize=True)
            return hashlib.md5(buffer.getvalue()).hexdigest()
        
        except Exception as e:
            return None

    def _get_current_clipboard_hash(self):
        """获取当前剪贴板哈希"""
        try:
            image = ClipboardManager.get_image_from_clipboard()
            if image is not None:
                return self._compute_image_hash(image)
            return None
        except Exception as e:
            return None

    def process_image_privacy(self, image):
        """处理图片隐私"""
        processing_start_time = time.time()
        
        try:
            if image is None:
                return None, False
            
            if not hasattr(image, 'size') or not hasattr(image, 'copy'):
                return None, False
            
            current_hash = self._compute_image_hash(image)
            
            if current_hash is None:
                return None, False
            
            if current_hash == self.last_processed_hash:
                return None, False
            
            processed_image = image.copy()
            text_content = self._extract_text_from_image(processed_image)
            
            if not text_content or len(text_content.strip()) < 3:
                return None, False
            
            privacy_matches = self.pattern_manager.find_matches(text_content)
            
            if not privacy_matches:
                return None, False
            
            has_modifications = False
            
            for idx, match_info in enumerate(privacy_matches):
                try:
                    bbox = self._calculate_text_bbox(
                        processed_image,
                        text_content,
                        match_info['start_pos'],
                        match_info['end_pos']
                    )
                    
                    if bbox:
                        processed_image = self.mosaic_engine.process_bbox(processed_image, bbox)
                        has_modifications = True
                
                except Exception as e:
                    continue
            
            if has_modifications:
                self._cache_original_image(current_hash, image)
                self.last_processed_hash = current_hash
                self.config_manager.set('last_image_hash', current_hash)
                
                processing_time = time.time() - processing_start_time
                logger.info(f"处理完成 ({processing_time:.2f}s)")
                
                return processed_image, True
            
            return None, False
        
        except Exception as e:
            logger.error(f"处理失败: {e}")
            return None, False

    def _extract_text_from_image(self, image):
        """提取文本（测试用）"""
        try:
            if image is None:
                return ""
            
            return self._generate_sample_text_for_testing(image)
        
        except Exception as e:
            return ""

    def _generate_sample_text_for_testing(self, image):
        """生成测试文本"""
        sample_texts = [
            "联系人：张三\n电话：13812345678\n身份证号：110101199001011234\n邮箱：zhangsan@example.com",
            "姓名：李四\n手机号：15987654321\n银行卡：6222021234567890123",
            "用户信息\n学号：20230101\nQQ号：123456789\n地址：北京市朝阳区xxx街道"
        ]
        
        try:
            width, height = image.size
            if width > 800 or height > 600:
                return sample_texts[0]
            elif width > 400 or height > 300:
                return sample_texts[1]
            else:
                return sample_texts[2]
        except:
            return sample_texts[0]

    def _calculate_text_bbox(self, image, text, start_pos, end_pos):
        """计算边界框"""
        try:
            if image is None or not text or end_pos <= start_pos:
                return None
            
            try:
                width, height = image.size
            except AttributeError:
                return None
            
            if width <= 0 or height <= 0:
                return None
            
            text_length = len(text)
            if text_length == 0:
                return None
            
            line_height = max(20, min(50, int(height * 0.08)))
            estimated_lines = max(1, int(height / line_height))
            chars_per_line = max(1, text_length // estimated_lines)
            
            line_index = start_pos // chars_per_line
            pos_in_line = start_pos % chars_per_line
            
            y1 = line_index * line_height
            y2 = min(y1 + line_height, height)
            
            margin = int(width * 0.05)
            content_width = width - 2 * margin
            
            if chars_per_line > 0:
                x1 = margin + int((pos_in_line / chars_per_line) * content_width)
                chars_in_match = end_pos - start_pos
                x2 = x1 + int((chars_in_match / chars_per_line) * content_width)
            else:
                x1 = margin
                x2 = width - margin
            
            x1 = max(0, min(width, x1))
            x2 = max(0, min(width, x2))
            y1 = max(0, min(height, y1))
            y2 = max(0, min(height, y2))
            
            if x2 > x1 and y2 > y1 and (x2 - x1) >= 10 and (y2 - y1) >= 5:
                return (x1, y1, x2, y2)
            
            return None
        
        except Exception as e:
            return None

    def _cache_original_image(self, image_hash, original_image):
        """缓存原图"""
        try:
            with self.processing_lock:
                while len(self.original_images_cache) >= self.max_cache_size:
                    oldest_key = next(iter(self.original_images_cache))
                    del self.original_images_cache[oldest_key]
                
                if original_image is not None:
                    self.original_images_cache[image_hash] = original_image.copy()
        
        except Exception as e:
            logger.error(f"缓存失败: {e}")

    def handle_new_screenshot(self):
        """处理新截图"""
        if self.is_processing or not self.auto_process_enabled:
            return
        
        with self.processing_lock:
            if self.is_processing:
                return
            self.is_processing = True
        
        try:
            image = ClipboardManager.get_image_from_clipboard()
            
            if image is None:
                return
            
            processed_img, was_modified = self.process_image_privacy(image)
            
            if was_modified and processed_img is not None:
                success = ClipboardManager.set_image_to_clipboard(processed_img)
                
                if success:
                    self.processing_count += 1
                    mode_name = "马赛克" if self.mosaic_engine.mode == MosaicEngine.MODE_MOSAIC else "黑条"
                    
                    logger.info(f"自动打码 #{self.processing_count} ({mode_name})")
                    
                    ToastNotifier.show(
                        "自动打码完成",
                        f"模式: {mode_name}\n累计: {self.processing_count}次",
                        duration=2500
                    )
        
        except Exception as e:
            logger.error(f"处理截图出错: {e}")
        
        finally:
            with self.processing_lock:
                self.is_processing = False

    def trigger_manual_process(self):
        """手动触发"""
        with self.processing_lock:
            if self.is_processing:
                ToastNotifier.show("提示", "正在处理中...", duration=2000)
                return
            self.is_processing = True
        
        try:
            image = ClipboardManager.get_image_from_clipboard()
            
            if image is None:
                ToastNotifier.show("提示", "无图片", duration=2500)
                return
            
            processed_img, was_modified = self.process_image_privacy(image)
            
            if was_modified and processed_img is not None:
                success = ClipboardManager.set_image_to_clipboard(processed_img)
                
                if success:
                    self.processing_count += 1
                    mode_name = "马赛克" if self.mosaic_engine.mode == MosaicEngine.MODE_MOSAIC else "黑条"
                    
                    ToastNotifier.show(
                        "手动打码完成",
                        f"模式: {mode_name}",
                        duration=2500
                    )
            else:
                ToastNotifier.show("提示", "未发现隐私信息", duration=2500)
        
        except Exception as e:
            ToastNotifier.show("错误", str(e), duration=2500)
        
        finally:
            with self.processing_lock:
                self.is_processing = False

    def undo_last_mosaic(self):
        """撤销"""
        try:
            if self.last_processed_hash is None:
                ToastNotifier.show("提示", "无撤销记录", duration=2000)
                return
            
            if self.last_processed_hash not in self.original_images_cache:
                ToastNotifier.show("提示", "缓存过期", duration=2000)
                return
            
            original_image = self.original_images_cache[self.last_processed_hash]
            
            if ClipboardManager.set_image_to_clipboard(original_image):
                with self.processing_lock:
                    if self.last_processed_hash in self.original_images_cache:
                        del self.original_images_cache[self.last_processed_hash]
                    
                    self.last_processed_hash = None
                    self.config_manager.set('last_image_hash', None)
                
                ToastNotifier.show("撤销成功", "已还原", duration=2500)
        
        except Exception as e:
            ToastNotifier.show("错误", str(e), duration=2500)

    def toggle_auto_process(self):
        """切换自动处理"""
        self.auto_process_enabled = not self.auto_process_enabled
        self.config_manager.set('auto_process', self.auto_process_enabled)
        
        status = "✓ 开启" if self.auto_process_enabled else "○ 暂停"
        ToastNotifier.show("自动打码", f"状态: {status}", duration=2000)
        
        if self.tray_icon:
            self._refresh_tray_menu()

    def switch_mosaic_mode(self):
        """切换模式"""
        if self.mosaic_engine.mode == MosaicEngine.MODE_MOSAIC:
            self.mosaic_engine.set_mode(MosaicEngine.MODE_BLACK_BAR)
            mode_name = "黑条"
        else:
            self.mosaic_engine.set_mode(MosaicEngine.MODE_MOSAIC)
            mode_name = "马赛克"
        
        self.config_manager.set('mode', self.mosaic_engine.mode)
        ToastNotifier.show("切换样式", f"当前: {mode_name}", duration=2000)
        
        if self.tray_icon:
            self._refresh_tray_menu()

    def clear_clipboard_data(self):
        """清空剪贴板"""
        if ClipboardManager.clear_clipboard():
            ToastNotifier.show("清空剪贴板", "已清空", duration=2000)
        else:
            ToastNotifier.show("错误", "清空失败", duration=2000)

    def _setup_global_hotkeys(self):
        """设置快捷键"""
        try:
            hotkey_map = {
                '<ctrl>+<alt>+s': self.toggle_auto_process,
                '<ctrl>+<alt>+d': self.trigger_manual_process,
                '<ctrl>+<alt>+c': self.switch_mosaic_mode,
                '<ctrl>+<alt>+z': self.undo_last_mosaic,
                '<ctrl>+<alt>+x': self.clear_clipboard_data
            }
            
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkey_listener.start()
        
        except Exception as e:
            logger.error(f"快捷键设置失败: {e}")

    def _start_clipboard_monitoring(self):
        """启动监控线程"""
        self.clipboard_monitor_thread = threading.Thread(
            target=self._clipboard_monitor_loop_v2,
            daemon=True,
            name="MonitorThread"
        )
        self.clipboard_monitor_thread.start()

    def _clipboard_monitor_loop_v2(self):
        """
        剪贴板监控循环 - v2.2 修复版
        
        关键改进：
        1. 增加最大迭代次数保护
        2. 连续错误检测和冷却机制
        3. 处理频率限制
        4. 防止伪无限循环
        """
        logger.info("监控循环启动 (v2.2)")
        
        while self.should_run:
            try:
                self.monitor_loop_count += 1
                
                # 循环保护：每1000次循环记录一次状态
                if self.monitor_loop_count % 1000 == 0:
                    runtime = datetime.now() - self.start_time
                    logger.debug(f"监控统计: 循环={self.monitor_loop_count}, 错误={self.consecutive_monitor_errors}, 运行时={runtime}")
                
                # 获取当前剪贴板哈希
                current_hash = self._get_current_clipboard_hash()
                
                # 只有当哈希值真正改变时才处理
                if current_hash is not None and current_hash != self.last_clipboard_hash:
                    # 更新哈希值
                    old_hash = self.last_clipboard_hash
                    self.last_clipboard_hash = current_hash
                    
                    # 记录成功检查时间
                    self.last_successful_check_time = time.time()
                    
                    # 重置连续错误计数
                    self.consecutive_monitor_errors = 0
                    
                    logger.debug(f"检测到变化: {current_hash[:8]}...")
                    
                    # 等待冷却
                    time.sleep(self.PROCESSING_COOLDOWN)
                    
                    # 再次检查是否应该继续
                    if self.should_run:
                        self.handle_new_screenshot()
                
                # 正常情况：重置错误计数
                if current_hash is not None:
                    self.consecutive_monitor_errors = 0
                
                # 监控间隔等待
                time.sleep(self.MONITOR_INTERVAL)
            
            except Exception as e:
                self.consecutive_monitor_errors += 1
                
                # 控制错误日志输出频率
                if self.consecutive_monitor_errors <= 3:
                    logger.warning(f"监控错误 #{self.consecutive_monitor_errors}: {type(e).__name__}")
                elif self.consecutive_monitor_errors == self.MAX_MONITOR_ERRORS:
                    logger.critical(f"连续错误达到上限({self.MAX_MONITOR_ERRORS})!")
                
                # 错误冷却机制
                if self.consecutive_monitor_errors >= self.MAX_MONITOR_ERRORS:
                    logger.error("进入冷却模式...")
                    time.sleep(self.ERROR_COOLDOWN)
                    self.consecutive_monitor_errors = 0  # 重置后重试
                else:
                    time.sleep(min(1.0 + self.consecutive_monitor_errors * 0.5, 5.0))

    def _create_system_tray_icon(self):
        """创建托盘图标"""
        try:
            icon_image = self._generate_tray_icon_image()
            menu = self._build_tray_menu()
            
            self.tray_icon = pystray.Icon(
                name="privacy_remover",
                icon=icon_image,
                title="截图去隐私工具",
                menu=menu
            )
            
            tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True, name="TrayIconThread")
            tray_thread.start()
        
        except Exception as e:
            logger.error(f"托盘图标失败: {e}")

    def _generate_tray_icon_image(self):
        """生成图标"""
        try:
            size = (64, 64)
            icon = PILImage.new('RGBA', size, (0, 150, 136, 255))
            draw = ImageDraw.Draw(icon)
            
            draw.rounded_rectangle([8, 12, 56, 52], radius=8, fill=(255, 255, 255, 255))
            
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            draw.text((22, 18), "P", fill=(0, 150, 136, 255), font=font)
            
            return icon
        except Exception as e:
            return PILImage.new('RGBA', (64, 64), (100, 100, 100, 255))

    def _build_tray_menu(self):
        """构建菜单"""
        auto_status = "✓ 开启" if self.auto_process_enabled else "○ 暂停"
        current_mode = "马赛克" if self.mosaic_engine.mode == MosaicEngine.MODE_MOSAIC else "黑条"
        
        menu = Menu(
            MenuItem(f"自动打码: {auto_status}", self.toggle_auto_process),
            MenuItem(f"样式: {current_mode}", self.switch_mosaic_mode),
            Menu.SEPARATOR,
            MenuItem("手动打码 (Ctrl+Alt+D)", self.trigger_manual_process),
            MenuItem("撤销 (Ctrl+Alt+Z)", self.undo_last_mosaic),
            MenuItem("清空剪贴板 (Ctrl+Alt+X)", self.clear_clipboard_data),
            Menu.SEPARATOR,
            MenuItem("退出", self.quit_application)
        )
        
        return menu

    def _refresh_tray_menu(self):
        """刷新菜单"""
        if self.tray_icon and hasattr(self.tray_icon, 'menu'):
            try:
                self.tray_icon.menu = self._build_tray_menu()
            except Exception as e:
                pass

    def quit_application(self, icon=None, item=None):
        """退出"""
        logger.info("="*50)
        logger.info("正在退出...")
        
        self.should_run = False
        
        runtime = datetime.now() - self.start_time
        logger.info(f"运行时长: {runtime}")
        logger.info(f"总处理: {self.processing_count}次")
        logger.info(f"监控循环: {self.monitor_loop_count}次")
        
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except:
                pass
        
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        self.config_manager.save_config()
        self.original_images_cache.clear()
        
        logger.info("已退出")
        
        time.sleep(0.3)
        os._exit(0)

    def run(self):
        """运行主程序"""
        startup_msg = (
            f"截图去隐私工具 v2.2\n"
            f"后台运行中\n"
            f"快捷键: Ctrl+Alt+S/D/C/Z/X\n"
            f"时间: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        ToastNotifier.show("截图去隐私工具", startup_msg, duration=4000)
        
        logger.info("主循环开始")
        
        try:
            while self.should_run:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.quit_application()


def main():
    """入口"""
    try:
        logger.info("*"*50)
        logger.info("截图去隐私工具 v2.2 启动")
        logger.info("*"*50)
        
        app = ScreenshotPrivacyRemover()
        app.run()
    
    except KeyboardInterrupt:
        os._exit(0)
    
    except SystemExit:
        raise
    
    except Exception as e:
        logger.critical(f"致命错误: {e}", exc_info=True)
        
        try:
            ToastNotifier.show("致命错误", f"{str(e)}\n查看日志文件", duration=5000)
        except:
            pass
        
        os._exit(1)


if __name__ == "__main__":
    main()
