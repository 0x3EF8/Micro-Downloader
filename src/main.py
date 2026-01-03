"""
Micro Downloader - Compact Video/Audio Downloader
Author: 0x3EF8
Version: 2.0.0
License: MIT

A modern compact GUI-based video downloader with bundled FFmpeg and Deno support.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import threading
import subprocess
import platform
from PIL import Image, ImageTk
import pystray
from typing import Tuple

# Platform detection
IS_WINDOWS = platform.system().lower() == "windows"
IS_MACOS = platform.system().lower() == "darwin"
IS_LINUX = platform.system().lower() == "linux"

# Import ctypes only on Windows (used for window styling)
if IS_WINDOWS:
    import ctypes

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

APP_NAME = "Micro Downloader"
APP_VERSION = "2.0.0"
APP_AUTHOR = "0x3EF8"
APP_ID = f"{APP_AUTHOR}.MicroDownloader.{APP_VERSION}"

# Cross-platform font selection
def get_system_font() -> str:
    """Get the appropriate system font for the current platform."""
    if IS_WINDOWS:
        return "Segoe UI"
    elif IS_MACOS:
        return "SF Pro Display"  # Falls back to Helvetica Neue if not available
    else:  # Linux
        return "Ubuntu"  # Falls back to DejaVu Sans if not available

SYSTEM_FONT = get_system_font()

# Color scheme
COLORS = {
    'bg_dark': '#1E1E1E',
    'bg_medium': '#2C2C2C',
    'bg_light': '#3D3D3D',
    'accent': '#E31937',
    'accent_hover': '#B8152C',
    'accent_success': '#28A745',
    'accent_warning': '#FFC107',
    'text_primary': '#FFFFFF',
    'text_secondary': '#B0B0B0',
    'border': '#444444',
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_binary_path(binary_name: str) -> str:
    """Get the path to a bundled binary executable."""
    if IS_WINDOWS:
        binary_name = f"{binary_name}.exe"
    return resource_path(os.path.join("bin", binary_name))


def verify_binary(binary_path: str, version_arg: str = "-version", min_size: int = 0) -> Tuple[bool, str]:
    """
    Verify that a binary exists and is functional.
    Returns (is_valid, error_message)
    """
    if not os.path.exists(binary_path):
        return False, f"Binary not found: {binary_path}"
    
    if min_size > 0:
        try:
            if os.path.getsize(binary_path) < min_size:
                return False, f"Binary appears corrupted (file too small)"
        except OSError as e:
            return False, f"Cannot read binary: {e}"
    
    try:
        kwargs = {'capture_output': True, 'timeout': 10}
        if IS_WINDOWS:
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run([binary_path, version_arg], **kwargs)
        if result.returncode != 0:
            return False, "Binary failed to execute"
    except subprocess.TimeoutExpired:
        return False, "Binary timed out"
    except PermissionError:
        return False, "Permission denied"
    except Exception as e:
        return False, f"Verification failed: {e}"
    
    return True, ""


def format_file_size(size_bytes: int) -> str:
    """Format bytes into human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ============================================================================
# PATHS & VERIFICATION
# ============================================================================

def get_icon_path() -> str:
    """Get the appropriate icon path for the current platform."""
    assets_dir = resource_path("assets")
    if IS_WINDOWS:
        icon_file = "logo.ico"
    elif IS_MACOS:
        # macOS prefers .icns, fallback to .png
        icon_file = "logo.icns" if os.path.exists(os.path.join(assets_dir, "logo.icns")) else "logo.png"
    else:
        # Linux prefers .png
        icon_file = "logo.png" if os.path.exists(os.path.join(assets_dir, "logo.png")) else "logo.ico"
    return os.path.join(assets_dir, icon_file)

ICON_PATH = get_icon_path()
FFMPEG_PATH = get_binary_path("ffmpeg")
DENO_PATH = get_binary_path("deno")


def check_dependencies() -> Tuple[bool, bool, str]:
    """
    Check all required dependencies.
    Returns (ffmpeg_ok, deno_ok, error_message)
    """
    ffmpeg_ok, ffmpeg_err = verify_binary(FFMPEG_PATH, "-version", min_size=1_000_000)
    deno_ok, _ = verify_binary(DENO_PATH, "--version")
    
    error_msg = ""
    if not ffmpeg_ok:
        error_msg = f"FFmpeg: {ffmpeg_err}"
    
    return ffmpeg_ok, deno_ok, error_msg


# ============================================================================
# CUSTOM WIDGETS
# ============================================================================

class ToolTip:
    """Create tooltips for widgets."""
    
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.scheduled_id = None
        
        widget.bind('<Enter>', self._schedule_tooltip)
        widget.bind('<Leave>', self._hide_tooltip)
        widget.bind('<Button-1>', self._hide_tooltip)
    
    def _schedule_tooltip(self, event=None):
        self._hide_tooltip()
        self.scheduled_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _show_tooltip(self):
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            tw, text=self.text,
            background=COLORS['bg_light'],
            foreground=COLORS['text_primary'],
            relief='solid', borderwidth=1,
            font=(SYSTEM_FONT, 9),
            padx=6, pady=3
        )
        label.pack()
    
    def _hide_tooltip(self, event=None):
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class RoundedButton(tk.Frame):
    """Modern button with hover effects using tk.Button internally."""
    
    def __init__(self, parent, text: str, command=None, width: int = 80, 
                 height: int = 25, corner_radius: int = 8, 
                 color: str = None, **kwargs):
        super().__init__(parent, bg=COLORS['bg_medium'], **kwargs)
        
        self.command = command
        self.text = text
        self.btn_width = width
        self.btn_height = height
        self.normal_color = color or COLORS['accent']
        self.hover_color = COLORS['accent_hover']
        self.enabled = True
        
        # Create actual button
        self.button = tk.Button(
            self,
            text=text,
            command=self._on_click,
            bg=self.normal_color,
            fg=COLORS['text_primary'],
            activebackground=self.hover_color,
            activeforeground=COLORS['text_primary'],
            relief='flat',
            bd=0,
            font=(SYSTEM_FONT, 9, 'bold'),
            cursor='hand2',
            width=max(1, width // 10),
            height=1,
            padx=6,
            pady=2
        )
        self.button.pack(fill='both', expand=True)
        
        # Hover effects
        self.button.bind('<Enter>', self._on_enter)
        self.button.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event=None):
        if self.enabled:
            self.button.config(bg=self.hover_color)
    
    def _on_leave(self, event=None):
        if self.enabled:
            self.button.config(bg=self.normal_color)
    
    def _on_click(self):
        if self.enabled and self.command:
            self.command()
    
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        if enabled:
            self.button.config(state='normal', bg=self.normal_color)
        else:
            self.button.config(state='disabled', bg=COLORS['bg_light'])
    
    def set_text(self, text: str):
        self.text = text
        self.button.config(text=text)
    
    def config(self, **kwargs):
        if 'state' in kwargs:
            self.set_enabled(kwargs['state'] != 'disabled')


class StatusIndicator(tk.Canvas):
    """Status indicator dot."""
    
    def __init__(self, parent, size: int = 10, **kwargs):
        super().__init__(
            parent, width=size, height=size,
            highlightthickness=0, bg=COLORS['bg_medium'], **kwargs
        )
        self.size = size
        self.status = 'ready'
        self._draw()
    
    def _draw(self):
        self.delete('all')
        colors = {
            'ready': COLORS['text_secondary'],
            'downloading': COLORS['accent_warning'],
            'success': COLORS['accent_success'],
            'error': COLORS['accent']
        }
        color = colors.get(self.status, COLORS['text_secondary'])
        padding = 2
        self.create_oval(
            padding, padding, self.size - padding, self.size - padding,
            fill=color, outline=''
        )
    
    def set_status(self, status: str):
        self.status = status
        self._draw()


class MarqueeLabel(tk.Label):
    """Label with marquee (scrolling) effect for long text like a news ticker."""
    
    def __init__(self, parent, max_width: int = 50, scroll_speed: int = 100, **kwargs):
        super().__init__(parent, **kwargs)
        self.max_width = max_width
        self.scroll_speed = scroll_speed
        self.full_text = ""
        self.base_text = ""  # Text without changing parts like percentage
        self.scroll_position = 0
        self.is_scrolling = False
        self.scroll_job = None
        self.display_text = ""
    
    def set_text(self, text: str):
        """Set the label text, enabling marquee if text is too long."""
        self.full_text = text
        
        # Extract base text (remove percentage and speed which change frequently)
        # This prevents marquee from resetting on every progress update
        import re
        base = re.sub(r': \d+%.*$', '', text)
        
        if len(text) > self.max_width:
            # Only reset scroll if the base content changed (not just percentage)
            if base != self.base_text:
                self.base_text = base
                self.scroll_position = 0
            
            # Create text that loops: text + separator + text
            self.display_text = text + "  ◆  " + text
            self._start_marquee()
        else:
            self._stop_marquee()
            self.base_text = base
            self.config(text=text)
    
    def _start_marquee(self):
        """Start the marquee scrolling effect."""
        if not self.is_scrolling:
            self.is_scrolling = True
            self._scroll()
    
    def _stop_marquee(self):
        """Stop the marquee scrolling effect."""
        self.is_scrolling = False
        if self.scroll_job:
            self.after_cancel(self.scroll_job)
            self.scroll_job = None
    
    def _scroll(self):
        """Perform one step of the marquee scroll - continuous left scroll."""
        if not self.is_scrolling:
            return
        
        # Get current window of text to display
        end_pos = self.scroll_position + self.max_width
        visible_text = self.display_text[self.scroll_position:end_pos]
        self.config(text=visible_text)
        
        # Move scroll position forward (scroll left)
        self.scroll_position += 1
        
        # Reset when we've scrolled past the first copy of the text
        reset_point = len(self.full_text) + 5  # length of "  ◆  "
        if self.scroll_position >= reset_point:
            self.scroll_position = 0
        
        self.scroll_job = self.after(self.scroll_speed, self._scroll)
    
    def destroy(self):
        """Clean up before destroying."""
        self._stop_marquee()
        super().destroy()


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class YouTubeDownloaderGUI:
    """Main application class for Micro Downloader."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self._style_applied = False
        self._is_restoring = False
        self._offset_x = 0
        self._offset_y = 0
        self.downloading = False
        self.stop_requested = False
        self.tray_icon = None
        
        # Check dependencies
        self.ffmpeg_ok, self.deno_ok, self.dep_error = check_dependencies()
        
        # Initialize UI
        self._setup_window()
        self._setup_icon()
        self._setup_styles()
        self._create_title_bar()
        self._create_main_content()
        self._setup_bindings()
        
        # Show dependency warning if needed
        if not self.ffmpeg_ok:
            self.root.after(100, lambda: self._show_dependency_error())
    
    def _setup_window(self):
        """Configure main window properties."""
        # Hide window initially to prevent flickering
        self.root.withdraw()
        self.root.config(bg=COLORS['bg_medium'])
        
        # Platform-specific window setup
        if IS_WINDOWS:
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
            except Exception:
                pass
        elif IS_MACOS:
            # macOS specific settings
            try:
                self.root.tk.call('tk', 'scaling', 2.0)  # Retina display support
            except Exception:
                pass
    
    def _setup_icon(self):
        """Load and set application icon (cross-platform)."""
        self.logo_image = None
        try:
            # Try to load icon from various formats
            icon_loaded = False
            for icon_name in ["logo.ico", "logo.png", "logo.icns"]:
                icon_path = resource_path(os.path.join("assets", icon_name))
                if os.path.exists(icon_path):
                    pil_image = Image.open(icon_path).resize((20, 20), Image.Resampling.LANCZOS)
                    self.logo_image = ImageTk.PhotoImage(pil_image)
                    self.root.iconphoto(True, self.logo_image)
                    icon_loaded = True
                    break
            
            # Windows-specific: set .ico file for taskbar
            if IS_WINDOWS:
                ico_path = resource_path(os.path.join("assets", "logo.ico"))
                if os.path.exists(ico_path):
                    self.root.iconbitmap(ico_path)
        except Exception:
            self.logo_image = None
    
    def _setup_styles(self):
        """Configure ttk styles."""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure('Modern.TFrame', background=COLORS['bg_medium'])
        self.style.configure(
            'Modern.TLabel',
            background=COLORS['bg_medium'],
            foreground=COLORS['text_primary'],
            font=(SYSTEM_FONT, 10)
        )
        self.style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=COLORS['bg_light'],
            background=COLORS['accent'],
            borderwidth=0,
            relief='flat'
        )
        self.style.configure(
            "Dark.TCombobox",
            foreground=COLORS['text_primary'],
            background=COLORS['bg_medium'],
            fieldbackground=COLORS['bg_light'],
            bordercolor=COLORS['border'],
            arrowcolor=COLORS['text_primary'],
            borderwidth=1
        )
        self.style.map(
            "Dark.TCombobox",
            fieldbackground=[('readonly', COLORS['bg_light'])],
            foreground=[('readonly', COLORS['text_primary'])],
            background=[('readonly', COLORS['bg_medium'])]
        )
        
        # Combobox listbox styling
        self.root.option_add('*TCombobox*Listbox.background', COLORS['bg_light'])
        self.root.option_add('*TCombobox*Listbox.foreground', COLORS['text_primary'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLORS['accent'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', COLORS['text_primary'])
    
    def _create_title_bar(self):
        """Create custom title bar."""
        self.title_bar = tk.Frame(
            self.root, bg=COLORS['bg_dark'], height=25
        )
        self.title_bar.pack(fill='x', side='top')
        
        # Logo
        if self.logo_image:
            logo_label = tk.Label(
                self.title_bar, image=self.logo_image,
                bg=COLORS['bg_dark']
            )
            logo_label.pack(side='left', padx=(5, 2))
            logo_label.bind('<Button-1>', self._click_title_bar)
            logo_label.bind('<B1-Motion>', self._drag_window)
            ToolTip(logo_label, f"Developed by {APP_AUTHOR}", delay=300)
        
        # Title
        title_text = f"{APP_NAME} v{APP_VERSION}"
        self.title_label = tk.Label(
            self.title_bar, text=title_text,
            bg=COLORS['bg_dark'], fg=COLORS['text_primary'],
            font=(SYSTEM_FONT, 10, 'bold')
        )
        self.title_label.pack(side='left', padx=(0, 5))
        ToolTip(self.title_label, f"Developed by {APP_AUTHOR}", delay=300)
        
        # Window controls
        btn_style = {
            'bg': COLORS['bg_dark'],
            'fg': COLORS['text_primary'],
            'bd': 0,
            'font': (SYSTEM_FONT, 10),
            'width': 3,
            'activeforeground': COLORS['text_primary']
        }
        
        self.close_btn = tk.Button(
            self.title_bar, text='x', command=self.exit_app,
            activebackground=COLORS['accent'], **btn_style
        )
        self.close_btn.pack(side='right', padx=(0, 5))
        
        self.minimize_btn = tk.Button(
            self.title_bar, text='-', command=self.minimize_to_tray,
            activebackground=COLORS['bg_light'], **btn_style
        )
        self.minimize_btn.pack(side='right')
        
        # Tooltips
        ToolTip(self.minimize_btn, "Minimize to tray")
        ToolTip(self.close_btn, "Close")
    
    def _create_main_content(self):
        """Create main content area."""
        self.main_frame = ttk.Frame(self.root, padding=8, style='Modern.TFrame')
        self.main_frame.pack(fill='both', expand=True)
        
        # URL Input
        url_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        url_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(url_frame, text="URL:", style='Modern.TLabel').pack(side='left')
        
        self.url_entry = tk.Entry(
            url_frame, width=30,
            bg=COLORS['bg_light'], fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief='flat', font=(SYSTEM_FONT, 10),
            highlightthickness=1, highlightcolor=COLORS['accent'],
            highlightbackground=COLORS['border']
        )
        self.url_entry.pack(side='left', padx=(5, 5), fill='x', expand=True)
        ToolTip(self.url_entry, "Paste video URL")
        
        # Paste button
        self.paste_btn = RoundedButton(
            url_frame, text="Paste",
            command=self._do_paste, width=60, height=25
        )
        self.paste_btn.pack(side='left')
        ToolTip(self.paste_btn, "Paste URL from clipboard (Ctrl+V)")
        
        # Save Location
        save_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        save_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(save_frame, text="Save:", style='Modern.TLabel').pack(side='left')
        
        default_path = os.path.join(os.path.expanduser("~/Downloads"), "mdl").replace("\\", "/")
        self.save_path = tk.StringVar(value=default_path)
        self.location_entry = tk.Entry(
            save_frame, textvariable=self.save_path, width=28,
            bg=COLORS['bg_light'], fg=COLORS['text_primary'],
            relief='flat', font=(SYSTEM_FONT, 10),
            highlightthickness=1, highlightbackground=COLORS['border']
        )
        self.location_entry.pack(side='left', padx=(5, 5), fill='x', expand=True)
        
        self.browse_btn = RoundedButton(
            save_frame, text="Browse",
            command=self._browse_location, width=60, height=25
        )
        self.browse_btn.pack(side='left')
        
        # Format Selection
        format_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        format_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(format_frame, text="Format:", style='Modern.TLabel').pack(side='left')
        
        self.format_type = tk.StringVar(value="video")
        radio_style = {
            'bg': COLORS['bg_medium'],
            'fg': COLORS['text_primary'],
            'selectcolor': COLORS['accent'],
            'activebackground': COLORS['bg_medium'],
            'activeforeground': COLORS['text_primary'],
            'font': (SYSTEM_FONT, 9),
            'highlightthickness': 0
        }
        
        video_radio = tk.Radiobutton(
            format_frame, text="Video",
            variable=self.format_type, value="video",
            command=self._update_quality_options, **radio_style
        )
        video_radio.pack(side='left', padx=(10, 8))
        
        audio_radio = tk.Radiobutton(
            format_frame, text="Audio",
            variable=self.format_type, value="audio",
            command=self._update_quality_options, **radio_style
        )
        audio_radio.pack(side='left')
        
        # Quality Selection
        quality_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        quality_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(quality_frame, text="Quality:", style='Modern.TLabel').pack(side='left')
        
        self.quality_var = tk.StringVar()
        self.quality_combo = ttk.Combobox(
            quality_frame, textvariable=self.quality_var,
            state='readonly', style='Dark.TCombobox',
            font=(SYSTEM_FONT, 10), width=25
        )
        self.quality_combo.pack(side='left', padx=(5, 0), fill='x', expand=True)
        self._update_quality_options()
        
        # Progress Section
        progress_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        progress_frame.pack(fill='x', pady=(5, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var,
            maximum=100, style="Modern.Horizontal.TProgressbar",
            length=180
        )
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 8))
        
        self.download_btn = RoundedButton(
            progress_frame, text="Download",
            command=self._start_download, width=100, height=28
        )
        self.download_btn.pack(side='left')
        
        # Status Bar
        status_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        status_frame.pack(fill='x', pady=(2, 0))
        
        self.status_indicator = StatusIndicator(status_frame, size=8)
        self.status_indicator.pack(side='left', padx=(0, 5))
        
        self.status_label = MarqueeLabel(
            status_frame, max_width=50, scroll_speed=150,
            text="Ready",
            bg=COLORS['bg_medium'], fg=COLORS['text_secondary'],
            font=(SYSTEM_FONT, 8)
        )
        self.status_label.pack(side='left')
    
    def _setup_bindings(self):
        """Setup event bindings (cross-platform keyboard shortcuts)."""
        self.title_bar.bind('<Button-1>', self._click_title_bar)
        self.title_bar.bind('<B1-Motion>', self._drag_window)
        self.title_label.bind('<Button-1>', self._click_title_bar)
        self.title_label.bind('<B1-Motion>', self._drag_window)
        
        # Keyboard shortcuts - support both Ctrl (Windows/Linux) and Command (macOS)
        self.root.bind('<Control-v>', lambda e: self._paste_url())
        self.root.bind('<Return>', lambda e: self._start_download())
        self.root.bind('<Escape>', lambda e: self._stop_download())
        
        # macOS uses Command key instead of Control
        if IS_MACOS:
            self.root.bind('<Command-v>', lambda e: self._paste_url())
    
    def _initialize_window_style(self):
        """Initialize custom window style - kept for compatibility."""
        pass
    
    def _apply_window_style(self):
        """Apply platform-specific window style for taskbar/dock visibility."""
        if self._style_applied:
            return
        
        if IS_WINDOWS:
            try:
                # Need to update to get window handle
                self.root.update_idletasks()
                
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if hwnd == 0:
                    hwnd = self.root.winfo_id()
                
                GWL_EXSTYLE = -20
                WS_EX_APPWINDOW = 0x00040000
                WS_EX_TOOLWINDOW = 0x00000080
                
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
                
                SWP_FRAMECHANGED = 0x0020
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOZORDER = 0x0004
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
                )
                
                self._style_applied = True
            except Exception:
                pass
        elif IS_MACOS or IS_LINUX:
            # macOS and Linux don't need special handling for dock/taskbar
            self._style_applied = True
    
    def _show_dependency_error(self):
        """Show dependency error message (cross-platform)."""
        ffmpeg_name = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
        if IS_MACOS:
            install_hint = "Install via Homebrew: brew install ffmpeg"
        elif IS_LINUX:
            install_hint = "Install via package manager:\n  Ubuntu/Debian: sudo apt install ffmpeg\n  Fedora: sudo dnf install ffmpeg\n  Arch: sudo pacman -S ffmpeg"
        else:
            install_hint = "Download from: https://ffmpeg.org/download.html"
        
        msg = (
            f"FFmpeg is required but not found.\n\n"
            f"Please place {ffmpeg_name} in:\n{os.path.dirname(FFMPEG_PATH)}\n\n"
            f"{install_hint}"
        )
        messagebox.showerror("Missing Dependency", msg)
    
    def _do_paste(self):
        """Paste URL from clipboard."""
        try:
            self.url_entry.focus_set()
            url = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url.strip())
        except tk.TclError:
            pass
        except Exception:
            pass
    
    def _paste_url(self):
        """Paste URL from clipboard - keyboard shortcut."""
        self._do_paste()
    
    def _click_title_bar(self, event):
        """Store click position for dragging."""
        self._offset_x = event.x
        self._offset_y = event.y
    
    def _drag_window(self, event):
        """Handle window dragging."""
        x = self.root.winfo_x() + (event.x - self._offset_x)
        y = self.root.winfo_y() + (event.y - self._offset_y)
        self.root.geometry(f"+{x}+{y}")
    
    def _browse_location(self):
        """Open folder browser dialog."""
        directory = filedialog.askdirectory(initialdir=self.save_path.get())
        if directory:
            self.save_path.set(directory)
    
    def _update_quality_options(self):
        """Update quality dropdown based on format selection."""
        if self.format_type.get() == "video":
            qualities = [
                "2160p (4K)", "1440p (2K)", "1080p (Full HD)",
                "720p (HD)", "480p", "360p", "240p", "144p"
            ]
            default = qualities[2]
        else:
            qualities = [
                "320kbps (High)", "256kbps (Good)",
                "192kbps (Medium)", "128kbps (Low)"
            ]
            default = qualities[0]
        
        self.quality_combo['values'] = qualities
        self.quality_combo.set(default)
    
    def _get_format_string(self) -> str:
        """Build yt-dlp format string."""
        if self.format_type.get() == "video":
            resolution = self.quality_var.get().split()[0].replace('p', '')
            return f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]/bestvideo+bestaudio/best'
        else:
            bitrate = self.quality_var.get().split()[0].replace('kbps', '')
            return f'bestaudio[abr<={bitrate}]/bestaudio/best'
    
    def _update_status(self, text: str, status: str = 'ready'):
        """Update status bar."""
        self.status_label.set_text(text)
        self.status_indicator.set_status(status)
    
    def _download_video(self):
        """Execute download in background thread."""
        url = self.url_entry.get().strip()
        
        if not url:
            self._reset_download_state()
            return
        
        if not self.ffmpeg_ok:
            self._show_dependency_error()
            self._reset_download_state()
            return
        
        self._update_status("Fetching video info...", 'downloading')
        
        # First extract info to get playlist entries
        extract_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        
        if self.deno_ok:
            extract_opts['js_runtimes'] = {'deno': {'path': DENO_PATH}}
        
        playlist_entries = []
        playlist_title = None
        
        try:
            with yt_dlp.YoutubeDL(extract_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    # Check if it's a playlist
                    if 'entries' in info:
                        playlist_title = info.get('title', 'Playlist')
                        entries = list(info['entries'])
                        for entry in entries:
                            if entry:
                                playlist_entries.append({
                                    'title': entry.get('title', 'Unknown'),
                                    'url': entry.get('url') or entry.get('webpage_url') or f"https://youtube.com/watch?v={entry.get('id')}",
                                    'id': entry.get('id')
                                })
                    else:
                        # Single video
                        playlist_entries.append({
                            'title': info.get('title', 'Unknown'),
                            'url': url,
                            'id': info.get('id')
                        })
        except Exception as e:
            # If extraction fails, just try to download directly
            playlist_entries = [{'title': 'Unknown', 'url': url, 'id': None}]
        
        # Show playlist info
        if playlist_title and len(playlist_entries) > 1:
            self._update_status(f"Playlist: {playlist_title} ({len(playlist_entries)} videos)", 'downloading')
        
        # Now download each entry
        ydl_opts = {
            'format': self._get_format_string(),
            'outtmpl': os.path.join(self.save_path.get(), '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'ffmpeg_location': os.path.dirname(FFMPEG_PATH),
            'postprocessors': [],
            'quiet': True,
            'no_warnings': True,
            'remote_components': ['ejs:github'],
            'noplaylist': True,  # Download one at a time
        }
        
        if self.deno_ok:
            ydl_opts['js_runtimes'] = {'deno': {'path': DENO_PATH}}
        
        if self.format_type.get() == "video":
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            })
        else:
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.quality_var.get().split()[0]
            })
        
        completed_count = 0
        total_count = len(playlist_entries)
        
        for i, entry in enumerate(playlist_entries):
            if self.stop_requested:
                break
            
            # Create progress hook for this specific download
            def make_progress_hook(entry_index, entry_data):
                def hook(d):
                    if self.stop_requested:
                        raise Exception("Download stopped by user")
                    
                    if d.get('status') == 'downloading':
                        try:
                            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                            downloaded = d.get('downloaded_bytes', 0)
                            progress = (downloaded / total) * 100 if total else 0
                            
                            title = d.get('info_dict', {}).get('title', entry_data['title'])
                            
                            speed = d.get('speed')
                            speed_str = f" - {format_file_size(int(speed))}/s" if speed else ""
                            
                            self.progress_var.set(progress)
                            self._update_status(f"[{entry_index+1}/{total_count}] {title}: {progress:.0f}%{speed_str}", 'downloading')
                            
                            self.root.update_idletasks()
                        except Exception:
                            pass
                    elif d.get('status') == 'finished':
                        self._update_status(f"[{entry_index+1}/{total_count}] Processing...", 'downloading')
                return hook
            
            ydl_opts['progress_hooks'] = [make_progress_hook(i, entry)]
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([entry['url']])
                
                completed_count += 1
                
            except Exception as e:
                error_msg = str(e)
                if "Download stopped by user" in error_msg:
                    break
                # Continue to next video on error
        
        # Final status
        save_folder = self.save_path.get()
        if self.stop_requested:
            self._update_status("Download cancelled", 'ready')
        elif completed_count == total_count:
            self.progress_var.set(100)
            self._update_status(f"Completed {completed_count}/{total_count} downloads!", 'success')
            if total_count == 1:
                result = messagebox.askyesno("Success", "Download completed successfully!\n\nOpen download folder?")
            else:
                result = messagebox.askyesno("Success", f"Downloaded {completed_count} videos successfully!\n\nOpen download folder?")
            if result:
                self._open_folder(save_folder)
        else:
            self._update_status(f"Completed {completed_count}/{total_count} (some failed)", 'error')
        
        self._reset_download_state()
    
    def _open_folder(self, folder_path: str):
        """Open the folder in file explorer (cross-platform)."""
        try:
            # Create folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            if IS_WINDOWS:
                os.startfile(folder_path)
            elif IS_MACOS:
                subprocess.run(["open", folder_path], check=False)
            elif IS_LINUX:
                subprocess.run(["xdg-open", folder_path], check=False)
        except Exception:
            pass
    
    def _start_download(self):
        """Start or stop download."""
        if not self.downloading:
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter a video URL")
                return
            
            self.downloading = True
            self.stop_requested = False
            self.download_btn.set_text("Stop")
            threading.Thread(target=self._download_video, daemon=True).start()
        else:
            self._stop_download()
    
    def _stop_download(self):
        """Request download stop."""
        if self.downloading:
            self.stop_requested = True
            self._update_status("Stopping...", 'downloading')
    
    def _reset_download_state(self):
        """Reset download UI state."""
        self.download_btn.set_enabled(True)
        self.progress_var.set(0)
        self.download_btn.set_text("Download")
        self.downloading = False
        self.stop_requested = False
    
    def minimize_to_tray(self):
        """Minimize application to system tray."""
        self.root.withdraw()
        
        try:
            tray_image = Image.open(ICON_PATH)
        except Exception:
            self.root.deiconify()
            return
        
        menu = pystray.Menu(
            pystray.MenuItem('Restore', self._restore_from_tray),
            pystray.MenuItem('Exit', self.exit_app)
        )
        self.tray_icon = pystray.Icon(APP_NAME, tray_image, APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def _restore_from_tray(self, icon=None, item=None):
        """Restore window from tray."""
        self._is_restoring = True
        if icon:
            icon.stop()
        
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.after(10, self._finalize_restore)
    
    def _finalize_restore(self):
        """Finalize restore from tray."""
        self.root.overrideredirect(True)
        self._is_restoring = False
    
    def exit_app(self, icon=None, item=None):
        """Clean exit."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Application entry point."""
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    
    # Set window size and position before showing
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    
    # Center on screen
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    
    # Set geometry first
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Apply overrideredirect and window styles before showing
    root.overrideredirect(True)
    app._apply_window_style()
    
    # Now show the window - no flickering
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
