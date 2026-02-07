"""
File Tracker Module for Zyron Desktop Assistant
Tracks all file opens/access in real-time and logs activity
"""

import os
import json
import time
import threading
import sqlite3
import shutil
import urllib.parse
from datetime import datetime, timedelta
from collections import defaultdict
import win32gui
import win32process
import psutil

# Configuration
FILE_ACTIVITY_LOG = "file_activity_log.json"
MAX_LOG_DAYS = 30  # Keep last 30 days of activity
CHECK_INTERVAL = 2  # Check every 2 seconds

# Global state
file_activity_log = []
tracking_active = False
tracker_thread = None
currently_open_files = {}  # Track files currently being accessed

# List of apps that are browsers (need special handling for local files)
BROWSER_APPS = {
    'chrome.exe': 'Google Chrome',
    'msedge.exe': 'Microsoft Edge',
    'brave.exe': 'Brave Browser',
    'firefox.exe': 'Mozilla Firefox',
    'opera.exe': 'Opera'
}

# System/temp paths to ignore
IGNORE_PATHS = [
    "\\AppData\\Local\\Temp",
    "\\Windows\\",
    "\\System32\\",
    "\\Program Files\\",
    "\\ProgramData\\",
    "\\$Recycle.Bin",
    "\\.git",
    "\\node_modules",
    "\\venv\\",
    "\\__pycache__",
]

# File extensions we care about
TRACKED_EXTENSIONS = [
    # Documents
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
    # Spreadsheets
    '.xlsx', '.xls', '.csv', '.ods',
    # Presentations
    '.pptx', '.ppt', '.odp',
    # Images
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
    # Videos
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
    # Audio
    '.mp3', '.wav', '.flac', '.aac', '.ogg',
    # Code
    '.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.json', '.xml',
    # Archives
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # Others
    '.exe', '.msi', '.apk', '.dmg'
]


def load_activity_log():
    """Load existing activity log from file"""
    global file_activity_log
    
    if os.path.exists(FILE_ACTIVITY_LOG):
        try:
            with open(FILE_ACTIVITY_LOG, 'r', encoding='utf-8') as f:
                file_activity_log = json.load(f)
                print(f"📁 Loaded {len(file_activity_log)} file activity records")
        except Exception as e:
            print(f"Error loading file activity log: {e}")
            file_activity_log = []
    else:
        file_activity_log = []
        # Create empty file immediately to ensure it exists
        save_activity_log()


def save_activity_log():
    """Save activity log to file"""
    try:
        with open(FILE_ACTIVITY_LOG, 'w', encoding='utf-8') as f:
            json.dump(file_activity_log, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving file activity log: {e}")


def should_ignore_file(file_path):
    """Check if file should be ignored based on path or extension"""
    if not file_path or not isinstance(file_path, str):
        return True
    
    # Ignore system/temp paths
    for ignore_path in IGNORE_PATHS:
        if ignore_path.lower() in file_path.lower():
            return True
    
    # Check if extension is tracked
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in TRACKED_EXTENSIONS:
        return True
    
    return False


def get_browser_local_file(browser_process_name, window_title):
    """
    If the active window is a browser, this checks the history
    to see if the user is looking at a local file (file:///...)
    """
    try:
        history_db = None
        user_data_dir = os.environ.get('LOCALAPPDATA', '')

        # Define paths to History DB based on browser
        if browser_process_name == 'chrome.exe':
            history_db = os.path.join(user_data_dir, 'Google', 'Chrome', 'User Data', 'Default', 'History')
        elif browser_process_name == 'msedge.exe':
            history_db = os.path.join(user_data_dir, 'Microsoft', 'Edge', 'User Data', 'Default', 'History')
        elif browser_process_name == 'brave.exe':
            history_db = os.path.join(user_data_dir, 'BraveSoftware', 'Brave-Browser', 'User Data', 'Default', 'History')
        
        if not history_db or not os.path.exists(history_db):
            return None

        # Copy DB to temp to avoid locking issues
        temp_db = os.path.join(os.environ.get('TEMP', ''), 'tracker_history_temp.db')
        try:
            shutil.copy2(history_db, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            # IMPROVEMENT: Get last 20 items, not just 1.
            # This helps if the user opened 3 tabs and we want to find the one matching the window title.
            cursor.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 20")
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                url, db_title = row
                if not url: continue

                # CHECK: Is it a local file?
                if url.startswith('file:///'):
                    # Convert file:///C:/Users/Name%20Here/Doc.pdf -> C:\Users\Name Here\Doc.pdf
                    # 1. Unquote removes %20 and other URL encoding
                    decoded_url = urllib.parse.unquote(url)
                    # 2. Strip prefix and fix slashes
                    clean_path = decoded_url.replace('file:///', '').replace('/', '\\')
                    
                    # 3. Fuzzy Match: Check if the filename appears in the Window Title
                    # Window Title: "Project Proposal.pdf - Google Chrome"
                    # File Name: "Project Proposal.pdf"
                    filename = os.path.basename(clean_path)
                    
                    if filename and (filename.lower() in window_title.lower()):
                        # Verify file actually exists
                        if os.path.exists(clean_path):
                            return clean_path
        except Exception as e:
            # print(f"DB Error: {e}")
            pass
        finally:
            if os.path.exists(temp_db):
                try: os.remove(temp_db)
                except: pass

    except Exception as e:
        print(f"Error checking browser file: {e}")
    
    return None


def get_active_window_file():
    """Get file path from currently active window using multiple detection methods"""
    try:
        # Get active window handle
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        
        # Get window title
        window_title = win32gui.GetWindowText(hwnd)
        if not window_title:
            return None, None
            
        # Get process ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Get process info
        try:
            process = psutil.Process(pid)
            app_name = process.name().lower()
            potential_paths = []

            # DEBUG: Un-comment this line if you want to see every window check in console
            # print(f"[DEBUG] Checking: '{window_title}' ({app_name})")

            # --- METHOD 0: Browser Detection (ENHANCED) ---
            # If app is a browser, check if it's viewing a local file via History
            if app_name in BROWSER_APPS:
                browser_file_path = get_browser_local_file(app_name, window_title)
                if browser_file_path:
                    # Return immediately if we found a browser file
                    return browser_file_path, BROWSER_APPS[app_name]

            # --- METHOD 1: Command Line Arguments (Most Reliable for Notepad, etc.) ---
            try:
                cmdline = process.cmdline()
                if cmdline:
                    # Skip the first argument (executable itself)
                    for arg in cmdline[1:]:
                        clean_arg = arg.strip('"').strip("'")
                        if os.path.exists(clean_arg) and os.path.isfile(clean_arg):
                             # FIX: Get filename without extension to match Notepad titles
                             filename = os.path.basename(clean_arg)      # e.g., "hahahaha.txt"
                             name_no_ext = os.path.splitext(filename)[0] # e.g., "hahahaha"
                             
                             # Check if either full name OR name without extension is in title
                             if (name_no_ext.lower() in window_title.lower()) or (filename.lower() in window_title.lower()) or len(cmdline) == 2:
                                 potential_paths.append(clean_arg)
            except (psutil.AccessDenied, IndexError, Exception):
                pass

            # --- METHOD 2: Open Files Handle (Reliable if Admin, flaky otherwise) ---
            try:
                open_files = process.open_files()
                for f in open_files:
                    if not should_ignore_file(f.path):
                        filename = os.path.basename(f.path)
                        name_no_ext = os.path.splitext(filename)[0]
                        
                        # FIX: Check if name without extension is in title
                        if name_no_ext.lower() in window_title.lower():
                            potential_paths.append(f.path)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # --- METHOD 3: Window Title Parsing (Fallback) ---
            if ':\\' in window_title:
                parts = window_title.split(' ')
                for part in parts:
                    if ':\\' in part and os.path.exists(part):
                         potential_paths.append(part)

            # --- FINAL SELECTION ---
            for path in potential_paths:
                if not should_ignore_file(path):
                    # print(f"[DEBUG] MATCH FOUND: {path}")  # Debug print
                    return path, app_name
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    except Exception as e:
        print(f"[DEBUG] Error in detector: {e}")
    
    return None, None


def log_file_activity(file_path, app_name, duration=None):
    """Log file access activity"""
    global file_activity_log
    
    if should_ignore_file(file_path):
        return
    
    # Create log entry
    entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'file_type': os.path.splitext(file_path)[1].lower().replace('.', ''),
        'app_used': app_name,
        'duration_seconds': duration if duration else 0
    }
    
    # Check if this is a duplicate of the most recent entry
    if file_activity_log:
        last_entry = file_activity_log[-1]
        # If same file accessed within 5 minutes, update duration instead of adding new entry
        if (last_entry['file_path'] == file_path and 
            last_entry['app_used'] == app_name):
            
            last_time = datetime.strptime(last_entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            time_diff = (current_time - last_time).total_seconds()
            
            if time_diff < 300:  # 5 minutes
                # Update existing entry's duration
                last_entry['duration_seconds'] = int(time_diff)
                save_activity_log()
                return
    
    # Add new entry
    file_activity_log.append(entry)
    
    # FIXED: Save immediately after adding new entry
    save_activity_log()
    
    print(f"📁 Tracked: {entry['file_name']} ({app_name})")


def track_files():
    """Background thread that tracks file activity"""
    global tracking_active, currently_open_files
    
    print("👁️ File tracking started...")
    
    # Ensure log file exists at start
    if not os.path.exists(FILE_ACTIVITY_LOG):
        print("[DEBUG] Creating initial JSON log file...")
        save_activity_log()
    
    while tracking_active:
        try:
            # Get currently active file
            file_path, app_name = get_active_window_file()
            
            current_time = time.time()
            
            if file_path and app_name:
                # Track when file was opened
                file_key = f"{file_path}|{app_name}"
                
                if file_key not in currently_open_files:
                    # New file opened
                    currently_open_files[file_key] = {
                        'path': file_path,
                        'app': app_name,
                        'start_time': current_time
                    }
                    log_file_activity(file_path, app_name)
                else:
                    # File still open, calculate duration
                    start_t = currently_open_files[file_key]['start_time']
                    duration = int(current_time - start_t)
                    
                    if duration > 0 and duration % 30 == 0:  # Log every 30 seconds
                        log_file_activity(file_path, app_name, duration)
            
            # Clean up closed files
            closed_files = []
            for file_key, info in currently_open_files.items():
                # If the current active file is NOT this file, consider it "closed"
                if file_path != info['path']:
                    closed_files.append(file_key)
            
            for file_key in closed_files:
                del currently_open_files[file_key]
            
            # Check every N seconds
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            # Silently handle errors
            print(f"File tracking error: {e}")
            time.sleep(CHECK_INTERVAL)
    
    print("👁️ File tracking stopped.")


def start_tracking():
    """Start the file tracking thread"""
    global tracking_active, tracker_thread
    
    if tracking_active:
        print("⚠️ File tracking already active")
        return
    
    # Load existing log
    load_activity_log()
    
    # Cleanup old logs
    cleanup_old_logs(MAX_LOG_DAYS)
    
    # Start tracking
    tracking_active = True
    tracker_thread = threading.Thread(target=track_files, daemon=True)
    tracker_thread.start()
    
    print("✅ File tracking activated")


def stop_tracking():
    """Stop the file tracking thread"""
    global tracking_active
    
    tracking_active = False
    save_activity_log()
    print("🛑 File tracking deactivated")


def get_recent_files(hours=24, file_type=None):
    """Get files accessed in the last N hours, optionally filtered by type"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_files = []
    
    for entry in reversed(file_activity_log):  # Start from most recent
        entry_time = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        if entry_time < cutoff_time:
            break  # Stop if we've gone past the time range
        
        # Filter by file type if specified
        if file_type and entry['file_type'] != file_type.lower():
            continue
        
        recent_files.append(entry)
    
    return recent_files


def get_files_by_timerange(start_time, end_time):
    """Get files accessed within a specific time range"""
    files_in_range = []
    
    for entry in file_activity_log:
        entry_time = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
        
        if start_time <= entry_time <= end_time:
            files_in_range.append(entry)
    
    return files_in_range


def cleanup_old_logs(days=30):
    """Remove log entries older than N days"""
    global file_activity_log
    
    cutoff_date = datetime.now() - timedelta(days=days)
    original_count = len(file_activity_log)
    
    file_activity_log = [
        entry for entry in file_activity_log
        if datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') > cutoff_date
    ]
    
    removed_count = original_count - len(file_activity_log)
    
    if removed_count > 0:
        print(f"🗑️ Cleaned up {removed_count} old file activity records")
        save_activity_log()


def format_file_activity_text(entries, limit=20):
    """Format file activity as readable text for display"""
    if not entries:
        return "📁 **FILE ACTIVITY**\n\n❌ No file activity found."
    
    entries = entries[:limit]  # Limit results
    lines = [f"📁 **FILE ACTIVITY** (Last {len(entries)} files)\n"]
    
    for i, entry in enumerate(entries, 1):
        file_name = entry['file_name']
        timestamp = entry['timestamp']
        app_used = entry['app_used']
        duration = entry.get('duration_seconds', 0)
        
        duration_str = f"{duration}s" if duration > 0 else ""
        
        lines.append(f"{i}. **{file_name}**")
        lines.append(f"   📅 {timestamp} | 📱 {app_used} {duration_str}")
        lines.append(f"   📂 {entry['file_path']}\n")
    
    return "\n".join(lines)


# Auto-start tracking when module is imported
start_tracking()


if __name__ == "__main__":
    # Test the module
    print("Testing file tracker...")
    print("Open some files to test tracking...")
    
    # Keep main thread alive for testing
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_tracking()