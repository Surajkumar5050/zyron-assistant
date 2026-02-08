import json
import os
import time
from pathlib import Path

COMMAND_FILE_PATH = Path(os.environ.get('TEMP', '')) / 'zyron_firefox_commands.json'

def send_browser_command(action, **kwargs):
    """Writes a command to the shared JSON file for the native host to pick up."""
    command = {"action": action, **kwargs}
    
    try:
        commands = []
        if COMMAND_FILE_PATH.exists():
            try:
                with open(COMMAND_FILE_PATH, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        commands = data
            except: pass
            
        commands.append(command)
        
        with open(COMMAND_FILE_PATH, 'w') as f:
            json.dump(commands, f)
        
        print(f"⚡ Browser Command Queued: {action} (Queue Size: {len(commands)})")
        
        # if the action expects a result (like "read" or "scan"), wait for it
        if action in ["read", "scan"]:
            return wait_for_result()
            
        return True
    except Exception as e:
        print(f"❌ Failed to queue browser command: {e}")
        return False

def wait_for_result(timeout=5):
    """Polls for the result file from the native host."""
    nav_path = Path(os.environ.get('TEMP', '')) / 'zyron_nav_result.json'
    
    # Clear old result first
    if nav_path.exists():
        try: os.remove(nav_path)
        except: pass
        
    start_time = time.time()
    while time.time() - start_time < timeout:
        if nav_path.exists():
            try:
                time.sleep(0.1)
                with open(nav_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                try: os.remove(nav_path)
                except: pass
                return data
            except:
                pass
        time.sleep(0.2)
        
    return {"success": False, "error": "Timeout waiting for browser response"}

def close_tab(tab_id):
    return send_browser_command("close_tab", tabId=tab_id)

def mute_tab(tab_id, mute=True):
    return send_browser_command("mute_tab", tabId=tab_id, value=mute)

def create_tab(url):
    return send_browser_command("create_tab", url=url)

def media_control(tab_id, command):
    """command: play, pause"""
    return send_browser_command("media_control", tabId=tab_id, command=command)

def capture_tab(tab_id):
    """Triggers a screenshot of the visible tab."""
    pass

def capture_tab_with_window(tab_id, window_id):
    return send_browser_command("capture_tab", tabId=tab_id, windowId=window_id)

# --- NAVIGATION AGENT COMMANDS ---
def navigate(url):
    return send_browser_command("create_tab", url=url)

def click_element(selector):
    """Simulates a click on an element (supports CSS selector or Zyron ID)."""
    if str(selector).isdigit():
        selector = f'[data-zyron-id="{selector}"]'
    return send_browser_command("click", selector=selector)

def type_text(selector, text):
    """Types text into an input field (supports CSS selector or Zyron ID)."""
    if str(selector).isdigit():
        selector = f'[data-zyron-id="{selector}"]'
    return send_browser_command("type", selector=selector, text=text)

def press_key(selector, key="Enter"):
    """Presses a key on an element."""
    if str(selector).isdigit():
        selector = f'[data-zyron-id="{selector}"]'
    return send_browser_command("press_key", selector=selector, key=key)

def scroll_page(direction="down"):
    """Scrolls the page up/down/top/bottom."""
    return send_browser_command("scroll", direction=direction)

def read_page():
    """Extracts main text from the page."""
    return send_browser_command("read")

def scan_page():
    """Scans the page for interactive elements."""
    return send_browser_command("scan")

