"""
Clipboard Monitor Module for Zyron Desktop Assistant
Tracks clipboard history and provides access to copied texts
"""

import pyperclip
import time
import threading
import json
import os
import ctypes  # Added for Windows API access
from datetime import datetime

# File to store clipboard history
CLIPBOARD_HISTORY_FILE = "clipboard_history.json"
MAX_HISTORY_ITEMS = 100  # Keep last 100 copied items

# Global clipboard history
clipboard_history = []
last_clipboard_content = ""
monitoring_active = False
monitor_thread = None


def load_clipboard_history():
    """Load clipboard history from file"""
    global clipboard_history
    
    if os.path.exists(CLIPBOARD_HISTORY_FILE):
        try:
            with open(CLIPBOARD_HISTORY_FILE, 'r', encoding='utf-8') as f:
                clipboard_history = json.load(f)
                print(f"📋 Loaded {len(clipboard_history)} clipboard items from history")
        except Exception as e:
            print(f"Error loading clipboard history: {e}")
            clipboard_history = []
    else:
        clipboard_history = []


def save_clipboard_history():
    """Save clipboard history to file"""
    try:
        with open(CLIPBOARD_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(clipboard_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving clipboard history: {e}")


def add_to_history(text):
    """Add new clipboard content to history"""
    global clipboard_history
    
    # Don't add empty strings or duplicates of the last item
    if not text or not text.strip():
        return
    
    # Check if this exact text is already the most recent entry
    if clipboard_history and clipboard_history[0].get('text') == text:
        return
    
    # Create new entry
    entry = {
        'text': text,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'length': len(text)
    }
    
    # Add to beginning of list (most recent first)
    clipboard_history.insert(0, entry)
    
    # Trim history if too long
    if len(clipboard_history) > MAX_HISTORY_ITEMS:
        clipboard_history = clipboard_history[:MAX_HISTORY_ITEMS]
    
    # Save to file
    save_clipboard_history()
    
    print(f"📋 Clipboard updated: {text[:50]}..." if len(text) > 50 else f"📋 Clipboard updated: {text}")


def monitor_clipboard():
    """Background thread that monitors clipboard for changes using optimized checks"""
    global last_clipboard_content, monitoring_active
    
    print("👁️ Clipboard monitoring started...")
    
    # [FIX] Setup Windows API to check sequence number without locking
    try:
        user32 = ctypes.windll.user32
        user32.GetClipboardSequenceNumber.restype = ctypes.c_ulong
        last_sequence_number = user32.GetClipboardSequenceNumber()
        has_ctypes = True
    except Exception as e:
        print(f"⚠️ Windows API not available, falling back to basic polling: {e}")
        has_ctypes = False
    
    while monitoring_active:
        try:
            should_check = False
            
            # [FIX] Logic Step 1: Check Sequence Number if on Windows
            if has_ctypes:
                current_sequence_number = user32.GetClipboardSequenceNumber()
                if current_sequence_number != last_sequence_number:
                    last_sequence_number = current_sequence_number
                    should_check = True
            else:
                # Fallback for non-Windows systems
                should_check = True

            # [FIX] Logic Step 2: Only lock/read clipboard if necessary
            if should_check:
                current_content = pyperclip.paste()
                
                # Check if content has changed (Validation)
                if current_content != last_clipboard_content:
                    last_clipboard_content = current_content
                    add_to_history(current_content)
            
            # [FIX] Logic Step 3: Sleep slightly longer to prevent CPU hogging
            time.sleep(1.0) 
            
        except Exception as e:
            # Silently handle errors to keep monitoring running
            # print(f"Clipboard monitor error: {e}")
            time.sleep(1)
    
    print("👁️ Clipboard monitoring stopped.")


def start_monitoring():
    """Start the clipboard monitoring thread"""
    global monitoring_active, monitor_thread
    
    if monitoring_active:
        print("⚠️ Clipboard monitoring already active")
        return
    
    # Load existing history
    load_clipboard_history()
    
    # Start monitoring
    monitoring_active = True
    monitor_thread = threading.Thread(target=monitor_clipboard, daemon=True)
    monitor_thread.start()
    
    print("✅ Clipboard monitoring activated")


def stop_monitoring():
    """Stop the clipboard monitoring thread"""
    global monitoring_active
    
    monitoring_active = False
    print("🛑 Clipboard monitoring deactivated")


def get_clipboard_history(limit=20):
    """Get recent clipboard history (most recent first)"""
    return clipboard_history[:limit]


def clear_clipboard_history():
    """Clear all clipboard history"""
    global clipboard_history
    
    clipboard_history = []
    save_clipboard_history()
    print("🗑️ Clipboard history cleared")


def format_clipboard_history_text(limit=20):
    """Format clipboard history as readable text for display"""
    
    items = get_clipboard_history(limit)
    
    if not items:
        return "📋 **CLIPBOARD HISTORY**\n\n❌ No copied texts found yet."
    
    lines = [f"📋 **CLIPBOARD HISTORY** (Last {len(items)} items)\n"]
    
    for i, entry in enumerate(items, 1):
        text = entry['text']
        timestamp = entry['timestamp']
        
        # Truncate long texts
        if len(text) > 100:
            display_text = text[:97] + "..."
        else:
            display_text = text
        
        # Replace newlines with spaces for compact display
        display_text = display_text.replace('\n', ' ').replace('\r', '')
        
        lines.append(f"{i}. **[{timestamp}]**")
        lines.append(f"   {display_text}\n")
    
    return "\n".join(lines)


def get_clipboard_item(index):
    """Get a specific clipboard item by index (0-based)"""
    if 0 <= index < len(clipboard_history):
        return clipboard_history[index]
    return None


# Auto-start monitoring when module is imported
start_monitoring()


if __name__ == "__main__":
    # Test the module
    print("Testing clipboard monitor...")
    print("Copy some text to test...")
    
    time.sleep(5)
    
    print("\n" + "="*60)
    print(format_clipboard_history_text(10))
    print("="*60)