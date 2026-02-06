import json
import os
from pathlib import Path

COMMAND_FILE_PATH = Path(os.environ.get('TEMP', '')) / 'zyron_firefox_commands.json'

def send_browser_command(action, **kwargs):
    """
    Appends a command to the Firefox Native Host communication list.
    """
    command = {"action": action}
    command.update(kwargs)
    
    try:
        commands = []
        if COMMAND_FILE_PATH.exists():
            try:
                with open(COMMAND_FILE_PATH, 'r') as f:
                    content = f.read().strip()
                    if content:
                        commands = json.loads(content)
                        if not isinstance(commands, list):
                            commands = [commands]
            except:
                commands = []
        
        commands.append(command)
        
        with open(COMMAND_FILE_PATH, 'w') as f:
            json.dump(commands, f)
        
        print(f"⚡ Browser Command Queued: {action} (Queue Size: {len(commands)})")
        return True
    except Exception as e:
        print(f"❌ Failed to queue browser command: {e}")
        return False

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
    # We also send windowId if we knew it, but extension finds it from sender or we rely on activeTab
    # Actually background.js uses chrome.tabs.captureVisibleTab(windowId). 
    # But usually we can pass null windowId to capture current window.
    # However, our background.js expects response.windowId. 
    # BUT, activity.py returns windowId in tab data.
    # Wait, capture_tab(tab_id) signature is insufficient if we need windowId.
    # We should update this signature or pass extra args.
    # Let's update send_browser_command to accept windowId if passed.
    # For now, let's assume we pass tabId and background.js figures it out?
    # No, background.js line: chrome.tabs.captureVisibleTab(response.windowId, ...)
    # So we MUST pass windowId.
    pass

def capture_tab_with_window(tab_id, window_id):
    return send_browser_command("capture_tab", tabId=tab_id, windowId=window_id)
