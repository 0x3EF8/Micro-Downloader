#!/usr/bin/env python3
"""
Cross-Platform Compatibility Test Script
Run this to verify Micro Downloader will work on your system.

Usage:
    python test_platform.py
"""

import sys
import platform

def print_header(text):
    print(f"\n{'='*50}")
    print(f" {text}")
    print('='*50)

def test_pass(msg):
    print(f"  ✓ {msg}")

def test_fail(msg, error=None):
    print(f"  ✗ {msg}")
    if error:
        print(f"    Error: {error}")
    return False

def main():
    all_passed = True
    
    print_header("System Information")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Python: {sys.version}")
    print(f"  Architecture: {platform.machine()}")
    
    # Test 1: Platform Detection
    print_header("Test 1: Platform Detection")
    try:
        IS_WINDOWS = platform.system().lower() == "windows"
        IS_MACOS = platform.system().lower() == "darwin"
        IS_LINUX = platform.system().lower() == "linux"
        
        detected = "Windows" if IS_WINDOWS else "macOS" if IS_MACOS else "Linux" if IS_LINUX else "Unknown"
        test_pass(f"Platform detected: {detected}")
        
        if not any([IS_WINDOWS, IS_MACOS, IS_LINUX]):
            all_passed = test_fail("Unknown platform - may have issues")
    except Exception as e:
        all_passed = test_fail("Platform detection failed", e)
    
    # Test 2: Tkinter
    print_header("Test 2: Tkinter GUI")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        
        # Test basic widgets
        frame = tk.Frame(root)
        label = tk.Label(frame, text="Test")
        button = tk.Button(frame, text="Test")
        entry = tk.Entry(frame)
        
        root.destroy()
        test_pass("Tkinter imports and basic widgets work")
    except ImportError as e:
        all_passed = test_fail("Tkinter not installed", e)
        print("    Fix: Install python3-tk (Linux) or python-tk (macOS)")
    except Exception as e:
        all_passed = test_fail("Tkinter error", e)
    
    # Test 3: TTK Styles
    print_header("Test 3: TTK Theming")
    try:
        import tkinter as tk
        from tkinter import ttk
        root = tk.Tk()
        root.withdraw()
        
        style = ttk.Style()
        available_themes = style.theme_names()
        test_pass(f"Available themes: {', '.join(available_themes)}")
        
        if 'clam' in available_themes:
            style.theme_use('clam')
            test_pass("'clam' theme available (used by app)")
        else:
            test_fail("'clam' theme not available - UI may look different")
        
        root.destroy()
    except Exception as e:
        all_passed = test_fail("TTK theming error", e)
    
    # Test 4: PIL/Pillow
    print_header("Test 4: PIL/Pillow (Image Processing)")
    try:
        from PIL import Image, ImageTk
        import tkinter as tk
        
        # Create test image
        img = Image.new('RGBA', (64, 64), (255, 0, 0, 255))
        
        root = tk.Tk()
        root.withdraw()
        photo = ImageTk.PhotoImage(img)
        root.destroy()
        
        test_pass("PIL/Pillow works with Tkinter")
    except ImportError as e:
        all_passed = test_fail("Pillow not installed", e)
        print("    Fix: pip install Pillow")
    except Exception as e:
        all_passed = test_fail("PIL error", e)
    
    # Test 5: pystray (System Tray)
    print_header("Test 5: pystray (System Tray)")
    try:
        import pystray
        from PIL import Image
        
        # Just test import, don't actually create tray icon
        test_pass("pystray imported successfully")
        
        if IS_LINUX:
            print("    Note: Linux may need 'libappindicator' for tray support")
    except ImportError as e:
        all_passed = test_fail("pystray not installed", e)
        print("    Fix: pip install pystray")
    except Exception as e:
        all_passed = test_fail("pystray error", e)
    
    # Test 6: yt-dlp
    print_header("Test 6: yt-dlp (Video Downloading)")
    try:
        import yt_dlp
        test_pass(f"yt-dlp version: {yt_dlp.version.__version__}")
    except ImportError as e:
        all_passed = test_fail("yt-dlp not installed", e)
        print("    Fix: pip install yt-dlp")
    except Exception as e:
        all_passed = test_fail("yt-dlp error", e)
    
    # Test 7: FFmpeg
    print_header("Test 7: FFmpeg (Media Processing)")
    try:
        import subprocess
        import shutil
        
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            result = subprocess.run(['ffmpeg', '-version'], 
                                    capture_output=True, text=True, timeout=5)
            version_line = result.stdout.split('\n')[0] if result.stdout else "unknown"
            test_pass(f"FFmpeg found: {ffmpeg_path}")
            test_pass(f"Version: {version_line}")
        else:
            all_passed = test_fail("FFmpeg not in PATH")
            if IS_WINDOWS:
                print("    Fix: Download from ffmpeg.org and add to bin/ folder")
            elif IS_MACOS:
                print("    Fix: brew install ffmpeg")
            else:
                print("    Fix: sudo apt install ffmpeg (Ubuntu/Debian)")
    except Exception as e:
        all_passed = test_fail("FFmpeg check error", e)
    
    # Test 8: File Operations
    print_header("Test 8: File System Operations")
    try:
        import os
        import tempfile
        
        # Test Downloads folder access
        downloads = os.path.expanduser("~/Downloads")
        if os.path.exists(downloads):
            test_pass(f"Downloads folder exists: {downloads}")
        else:
            print(f"    Note: Downloads folder not at default location")
        
        # Test temp file creation
        with tempfile.NamedTemporaryFile(delete=True) as f:
            f.write(b"test")
            test_pass("Temp file creation works")
        
        # Test folder opening command
        if IS_WINDOWS:
            test_pass("Will use os.startfile() for folder opening")
        elif IS_MACOS:
            test_pass("Will use 'open' command for folder opening")
        else:
            test_pass("Will use 'xdg-open' for folder opening")
            
    except Exception as e:
        all_passed = test_fail("File operations error", e)
    
    # Test 9: ctypes (Windows only)
    print_header("Test 9: Platform-Specific Features")
    if IS_WINDOWS:
        try:
            import ctypes
            test_pass("ctypes available for Windows taskbar integration")
        except ImportError as e:
            all_passed = test_fail("ctypes not available", e)
    else:
        test_pass("No Windows-specific features needed")
    
    # Test 10: Font availability
    print_header("Test 10: System Fonts")
    try:
        import tkinter as tk
        from tkinter import font
        
        root = tk.Tk()
        root.withdraw()
        
        available_fonts = list(font.families())
        
        if IS_WINDOWS:
            target_font = "Segoe UI"
        elif IS_MACOS:
            target_font = "SF Pro Display"
        else:
            target_font = "Ubuntu"
        
        # Check for fallback fonts too
        fallbacks = ["Helvetica", "Arial", "DejaVu Sans", "Liberation Sans"]
        
        if target_font in available_fonts:
            test_pass(f"Primary font '{target_font}' available")
        else:
            print(f"    Note: '{target_font}' not found, will use fallback")
            found_fallback = False
            for fb in fallbacks:
                if fb in available_fonts:
                    test_pass(f"Fallback font '{fb}' available")
                    found_fallback = True
                    break
            if not found_fallback:
                test_fail("No suitable fonts found - UI may look off")
        
        root.destroy()
    except Exception as e:
        all_passed = test_fail("Font check error", e)
    
    # Summary
    print_header("SUMMARY")
    if all_passed:
        print("  ✓ All tests passed! Micro Downloader should work on this system.")
    else:
        print("  ⚠ Some tests failed. Review the issues above.")
        print("  The app may still work but with limited functionality.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
