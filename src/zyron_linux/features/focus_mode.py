"""
Focus Mode Module (Feature #11)
Handles blocking of distracting apps and websites.
"""

import json
import os
import time
import threading
import psutil
from datetime import datetime

# Define paths - Use project root directly, similar to other log files
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BLACKLIST_FILE = os.path.join(PROJECT_ROOT, "blacklist.json")

# Ensure data directory is not needed for now as we use project root

# Global State
focus_mode_active = False
enforcer_thread = None
stop_event = threading.Event()

# Default Blacklist
DEFAULT_BLACKLIST = {
    "apps": ["steam", "discord", "spotify", "netflix", "epicgameslauncher"],
    "sites": ["youtube.com", "facebook.com", "instagram.com", "twitter.com", "tiktok.com", "reddit.com"]
}

def load_blacklist():
    """Load blacklist from JSON or create default."""
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading blacklist: {e}")
            return DEFAULT_BLACKLIST
    else:
        save_blacklist(DEFAULT_BLACKLIST)
        return DEFAULT_BLACKLIST

def save_blacklist(data):
    """Save blacklist to JSON."""
    try:
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving blacklist: {e}")

def add_to_blacklist(item):
    """Add an app or site to blacklist with smart classification."""
    blacklist = load_blacklist()
    item = item.lower().strip()
    
    # Smart Classification
    is_app = False
    if ".exe" in item:
        is_app = True
    elif "." not in item:
        is_app = True
    # If it has a dot but isn't .exe, it's likely a site (e.g. youtube.com)

    if is_app:
        clean_name = item.replace(".exe", "")
        if clean_name not in blacklist["apps"]:
            blacklist["apps"].append(clean_name)
            save_blacklist(blacklist)
            return f"✅ Added app to blacklist: {clean_name}"
        return f"⚠️ App already in blacklist: {clean_name}"
    else:
        # Assume it's a site (URL/Domain)
        if item not in blacklist["sites"]:
            blacklist["sites"].append(item)
            save_blacklist(blacklist)
            return f"✅ Added site to blacklist: {item}"
        return f"⚠️ Site already in blacklist: {item}"

def remove_from_blacklist(items_input):
    """Remove one or more items from blacklist with smart matching."""
    blacklist = load_blacklist()
    
    # Handle both single string and list of strings
    if isinstance(items_input, str):
        items = [i.strip().lower() for i in items_input.split() if i.strip()]
    else:
        items = [str(i).strip().lower() for i in items_input]

    removed_count = 0
    not_found = []
    
    for item in items:
        found_this = False
        clean_name = item.replace(".exe", "")
        
        # Check Apps
        if item in blacklist["apps"]:
            blacklist["apps"].remove(item)
            found_this = True
        elif clean_name in blacklist["apps"]:
            blacklist["apps"].remove(clean_name)
            found_this = True
        # Reverse check: if user provided 'steam.exe' but list has 'steam'
        elif item.endswith(".exe") and clean_name in blacklist["apps"]:
            blacklist["apps"].remove(clean_name)
            found_this = True
        # Forward check: if user provided 'steam' but list has 'steam.exe'
        elif clean_name + ".exe" in blacklist["apps"]:
            blacklist["apps"].remove(clean_name + ".exe")
            found_this = True
            
        # Check Sites
        if not found_this:
            if item in blacklist["sites"]:
                blacklist["sites"].remove(item)
                found_this = True
        
        if found_this:
            removed_count += 1
        else:
            not_found.append(item)
            
    if removed_count > 0:
        save_blacklist(blacklist)
        
    msg = f"🗑️ Removed {removed_count} items from blacklist."
    if not_found:
        msg += f"\n❌ Could not find: {', '.join(not_found)}"
    return msg

def get_blacklist_status():
    """Return comprehensive info about Focus Mode and the current blacklist."""
    blacklist = load_blacklist()
    apps = ", ".join(blacklist.get("apps", [])) if blacklist.get("apps") else "_None_"
    sites = ", ".join(blacklist.get("sites", [])) if blacklist.get("sites") else "_None_"
    
    status_emoji = "🔴 ON" if focus_mode_active else "🟢 OFF"
    
    return (
        f"🎯 **Advanced Focus Mode**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Status: **{status_emoji}**\n\n"
        f"Boost your productivity by auto-blocking distractions. When active, I will periodically kill blacklisted processes and close browser tabs matching restricted sites.\n\n"
        f"🚫 **Blocked Apps:**\n`{apps}`\n\n"
        f"🌐 **Blocked Sites:**\n`{sites}`\n\n"
        f"💡 **How to Use:**\n"
        f"• `/focus_mode_on` - Start the enforcer\n"
        f"• `/focus_mode_off` - Stop the enforcer\n"
        f"• `/blacklist add [name]` - Block an app or site\n"
        f"• `/blacklist remove [name]` - Unblock an item\n\n"
        f"_Examples: `/blacklist add spotify` or `/blacklist add youtube.com`_"
    )

def kill_process(proc_name):
    """Kill a process by name with robust matching."""
    try:
        # Normalize: spotify.exe -> spotify
        clean_target = proc_name.lower().replace(".exe", "")
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                curr_name = proc.info['name'].lower()
                # Check for exact match or name containing target (e.g. Spotify.exe matches spotify)
                if clean_target == curr_name or clean_target == curr_name.replace(".exe", ""):
                    proc.kill()
                    print(f"💀 Focus Mode killed: {proc.info['name']} (PID: {proc.info['pid']})")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error killing process {proc_name}: {e}")
    return False

def check_and_block():
    """Main Enforcer Loop - Optimized for performance."""
    import zyron.features.activity as activity_monitor
    import zyron.features.browser_control as browser_control
    
    print("🛡️ Focus Mode Enforcer Started.")
    
    while not stop_event.is_set():
        try:
            blacklist = load_blacklist()
            apps_to_kill = [a.lower().replace(".exe", "") for a in blacklist.get("apps", [])]
            sites_to_block = [s.lower() for s in blacklist.get("sites", [])]
            
            # 1. Block Apps (Iterate once)
            if apps_to_kill:
                # Common mappings for the assistant to be "smart"
                APP_MAPPINGS = {
                    "word": ["winword"],
                    "excel": ["excel"],
                    "powerpoint": ["powerpnt"],
                    "chrome": ["chrome"],
                    "browser": ["chrome", "firefox", "msedge"],
                    "games": ["steam", "epicgameslauncher", "riotclient"],
                    "music": ["spotify", "itunes"]
                }
                
                # Expand apps_to_kill with mappings
                expanded_targets = []
                for a in apps_to_kill:
                    expanded_targets.append(a)
                    if a in APP_MAPPINGS:
                        expanded_targets.extend(APP_MAPPINGS[a])
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        curr_name = proc.info['name'].lower()
                        curr_base = curr_name.replace(".exe", "")
                        
                        should_kill = False
                        for target in expanded_targets:
                            # Fuzzy Match: exact base match OR target in base name
                            if target == curr_base or target == curr_name or (len(target) > 3 and target in curr_base):
                                should_kill = True
                                break
                        
                        if should_kill:
                            proc.kill()
                            print(f"💀 Focus Mode killed: {proc.info['name']} (PID: {proc.info['pid']})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            # 2. Block Websites (Firefox Native Bridge)
            if sites_to_block:
                tabs = activity_monitor.get_firefox_tabs()
                if tabs:
                    for tab in tabs:
                        url = tab.get('url', '').lower()
                        title = tab.get('title', '').lower()
                        tab_id = tab.get('id')
                        
                        for site in sites_to_block:
                            if site and (site in url or site in title):
                                print(f"🚫 Focus Mode: Blocking site '{site}' in tab '{title}'")
                                if tab_id:
                                    browser_control.close_tab(tab_id)
        except Exception as e:
            print(f"⚠️ Focus Mode: Loop Error: {e}")
            
        # Sleep 3 seconds
        time.sleep(3)

def start_focus_mode():
    """Start the background enforcer thread."""
    global focus_mode_active, enforcer_thread, stop_event
    
    if focus_mode_active:
        return "⚠️ Focus Mode is already ON!"
        
    focus_mode_active = True
    stop_event.clear()
    enforcer_thread = threading.Thread(target=check_and_block, daemon=True)
    enforcer_thread.start()
    return "🔴 **Focus Mode ACTIVATED!**\nDistractions will be blocked immediately."

def stop_focus_mode():
    """Stop the background enforcer."""
    global focus_mode_active, stop_event
    
    if not focus_mode_active:
        return "⚠️ Focus Mode is already OFF."
        
    focus_mode_active = False
    stop_event.set()
    return "🟢 **Focus Mode DEACTIVATED.**\nYou are free to roam."

if __name__ == "__main__":
    # Test
    print(add_to_blacklist("notepad.exe"))
    # start_focus_mode()
    # time.sleep(10)
    # stop_focus_mode()
