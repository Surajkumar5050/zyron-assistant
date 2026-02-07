import os
import webbrowser
import pyautogui
import cv2
import screen_brightness_control as sbc
import psutil
import shutil
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import requests
import json
import zyron.features.activity as activity_monitor
import zyron.features.clipboard as clipboard_monitor
import zyron.features.files.finder as file_finder  # Uses the new smart finder we just created

PROCESS_NAMES = {
    # Browsers
    "chrome": "chrome.exe", "googlechrome": "chrome.exe", "google": "chrome.exe",
    "brave": "brave.exe", "bravebrowser": "brave.exe", 
    "edge": "msedge.exe", "msedge": "msedge.exe", "microsoftedge": "msedge.exe",
    "firefox": "firefox.exe", "mozilla": "firefox.exe",
    "opera": "opera.exe",

    # System & Tools
    "notepad": "notepad.exe",
    "calculator": "calc.exe", "calc": "calc.exe",
    "cmd": "cmd.exe", "terminal": "WindowsTerminal.exe",
    "explorer": "explorer.exe", "fileexplorer": "explorer.exe",
    "taskmanager": "Taskmgr.exe",

    # Media
    "spotify": "spotify.exe",
    "vlc": "vlc.exe", 

    # Coding
    "vscode": "Code.exe", "code": "Code.exe", "visualstudiocode": "Code.exe",
    "pycharm": "pycharm64.exe",
    "androidstudio": "studio64.exe",
    "intellij": "idea64.exe",
    "python": "python.exe",

    # Social
    "telegram": "Telegram.exe",
    "discord": "Discord.exe",
    "whatsapp": "WhatsApp.exe",
    "zoom": "Zoom.exe"
}

def get_laptop_location():
    """
    Gets the approximate location of the laptop using multiple IP geolocation services
    for better accuracy. Tries 3 different APIs and returns the best result.
    """
    try:
        print("🔍 Fetching location from multiple sources...")
        
        results = []
        
        try:
            print("   → Checking ipapi.co...")
            response = requests.get('https://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                results.append({
                    'source': 'ipapi.co',
                    'ip': data.get('ip', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'country_code': data.get('country_code', 'Unknown'),
                    'postal': data.get('postal', 'Unknown'),
                    'latitude': data.get('latitude', 0),
                    'longitude': data.get('longitude', 0),
                    'timezone': data.get('timezone', 'Unknown'),
                    'org': data.get('org', 'Unknown'),
                })
                print(f"      ✓ Found: {data.get('city', 'Unknown')}")
        except Exception as e:
            print(f"      ✗ ipapi.co failed: {e}")
        
        try:
            print("   → Checking ip-api.com...")
            response = requests.get('http://ip-api.com/json/?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    results.append({
                        'source': 'ip-api.com',
                        'ip': data.get('query', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'region': data.get('regionName', 'Unknown'),
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'Unknown'),
                        'postal': data.get('zip', 'Unknown'),
                        'latitude': data.get('lat', 0),
                        'longitude': data.get('lon', 0),
                        'timezone': data.get('timezone', 'Unknown'),
                        'org': data.get('isp', 'Unknown'),
                    })
                    print(f"      ✓ Found: {data.get('city', 'Unknown')}")
        except Exception as e:
            print(f"      ✗ ip-api.com failed: {e}")
        
        try:
            print("   → Checking ipinfo.io...")
            response = requests.get('https://ipinfo.io/json', timeout=5)
            if response.status_code == 200:
                data = response.json()
                loc = data.get('loc', '0,0').split(',')
                results.append({
                    'source': 'ipinfo.io',
                    'ip': data.get('ip', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('country', 'Unknown'),
                    'postal': data.get('postal', 'Unknown'),
                    'latitude': float(loc[0]) if len(loc) > 0 else 0,
                    'longitude': float(loc[1]) if len(loc) > 1 else 0,
                    'timezone': data.get('timezone', 'Unknown'),
                    'org': data.get('org', 'Unknown'),
                })
                print(f"      ✓ Found: {data.get('city', 'Unknown')}")
        except Exception as e:
            print(f"      ✗ ipinfo.io failed: {e}")
        
        if not results:
            print("❌ All location APIs failed")
            return None
        
        best_result = None
        for result in results:
            if result['source'] == 'ip-api.com':  
                best_result = result
                break
        
        if not best_result:
            best_result = results[0] 
        
        
        if len(results) > 1:
            comparison = "\n".join([f"   • {r['source']}: {r['city']}, {r['region']}" for r in results])
            best_result['comparison'] = comparison
        else:
            best_result['comparison'] = None
        
        
        lat = best_result['latitude']
        lon = best_result['longitude']
        best_result['maps_url'] = f"https://www.google.com/maps?q={lat},{lon}"
        
        print(f"✅ Best location: {best_result['city']}, {best_result['region']} (from {best_result['source']})")
        return best_result
            
    except Exception as e:
        print(f"❌ Error getting location: {e}")
        return None


def get_browser_path(browser_name):
    """Finds browser executable dynamically without hardcoded paths."""
    browser_name = browser_name.lower().strip()
    
    exes = {
        "chrome": "chrome.exe",
        "google": "chrome.exe",
        "brave": "brave.exe", 
        "firefox": "firefox.exe",
        "mozilla": "firefox.exe",
        "edge": "msedge.exe",
        "msedge": "msedge.exe",
        "opera": "launcher.exe" 
    }
    
    executable = exes.get(browser_name, f"{browser_name}.exe")
    if not executable.endswith(".exe"): executable += ".exe"
    
    
    path = shutil.which(executable)
    if path: return path
    
    
    possible_roots = [
        os.environ.get("PROGRAMFILES"), 
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA") 
    ]
    
    common_subdirs = [
        "Google\\Chrome\\Application",
        "BraveSoftware\\Brave-Browser\\Application",
        "Microsoft\\Edge\\Application",
        "Mozilla Firefox",
        "Opera"
    ]
    
    for root in possible_roots:
        if not root: continue
        for subdir in common_subdirs:
            full_path = os.path.join(root, subdir, executable)
            if os.path.exists(full_path):
                return full_path
                
    return None


def capture_webcam():
    print("📸 Accessing Webcam...")
    try:
        
        for i in range(2):
            cam = cv2.VideoCapture(i)
            if cam.isOpened():
                ret, frame = cam.read()
                if ret:
                    file_path = os.path.join(os.getcwd(), "webcam_snap.jpg")
                    cv2.imwrite(file_path, frame)
                    cam.release()
                    return file_path
                cam.release()
        print("❌ No active camera found.")
        return None
    except Exception as e:
        print(f"Error accessing webcam: {e}")
        return None


def capture_screen():
    file_path = os.path.join(os.getcwd(), "screenshot.png")
    try:
        print("📸 Taking screenshot...")
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        return file_path
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None


def record_audio(duration=60):
    """Records audio from the default microphone for specified duration (in seconds).
    Uses sounddevice library - Works on Windows Python 3.10 without C++ compiler!"""
    file_path = os.path.join(os.getcwd(), "audio_recording.wav")
    
    # Audio recording parameters
    SAMPLE_RATE = 44100 
    CHANNELS = 1 
    
    print(f"🎤 Recording audio for {duration} seconds...")
    
    try:
      
        recording = sd.rec(
            int(duration * SAMPLE_RATE), 
            samplerate=SAMPLE_RATE, 
            channels=CHANNELS, 
            dtype='int16'
        )
      
        sd.wait()
        
        print("✅ Recording complete.")
        
        
        write(file_path, SAMPLE_RATE, recording)
        
        return file_path
        
    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        return None


def system_sleep():
    print("💤 Going to sleep...")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def shutdown_pc():
    """Immediately shuts down the computer."""
    print("🔌 System Shutdown Initiated...")
    # /s = shutdown, /t 0 = time 0 seconds
    os.system("shutdown /s /t 0")

def restart_pc():
    """Immediately restarts the computer."""
    print("🔄 System Restart Initiated...")
    # /r = restart, /t 0 = time 0 seconds
    os.system("shutdown /r /t 0")


def get_battery_status():
    try:
        battery = psutil.sensors_battery()
        if not battery:
            return "Cannot determine battery status (Device might be a Desktop)."
        
        percent = battery.percent
        charging = battery.power_plugged
        status = "Charging ⚡" if charging else "Discharging 🔋"
        
        return f"Battery is at {percent}% and is currently {status}."
    except Exception as e:
        return f"Error reading battery: {e}"


def get_system_health():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_usage = ram.percent
        ram_available = round(ram.available / (1024 * 1024 * 1024), 2)
        return f"🖥️ **System Health:**\nCPU Usage: {cpu_usage}%\nRAM Usage: {ram_usage}% ({ram_available} GB free)"
    except Exception as e:
        return f"Error reading system health: {e}"


def clear_recycle_bin():
    """
    Clears the Windows Recycle Bin permanently.
    Uses PowerShell command to empty all recycle bins on all drives.
    """
    print("🗑️ Clearing Recycle Bin...")
    
    try:
        # PowerShell command to clear recycle bin for all drives
        ps_command = 'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'
        
        # Execute PowerShell command
        result = os.system(f'powershell -Command "{ps_command}"')
        
        if result == 0:
            print("✅ Recycle Bin cleared successfully!")
            return "Recycle Bin has been emptied successfully. All deleted files have been permanently removed."
        else:
            print("⚠️ Recycle Bin might be already empty or operation completed with warnings.")
            return "Recycle Bin operation completed. It may have been already empty."
            
    except Exception as e:
        error_msg = f"Error clearing recycle bin: {e}"
        print(f"❌ {error_msg}")
        return error_msg


def check_storage():
    """
    Checks storage space for all available drives on the system.
    Returns detailed information about each drive including total, used, and free space.
    """
    print("💾 Checking storage for all drives...")
    
    try:
        storage_info = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            # Skip CD/DVD drives and other removable media
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
                
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                # Convert bytes to GB
                total_gb = round(usage.total / (1024 ** 3), 2)
                used_gb = round(usage.used / (1024 ** 3), 2)
                free_gb = round(usage.free / (1024 ** 3), 2)
                percent_used = usage.percent
                
                # Determine status emoji based on usage
                if percent_used >= 90:
                    status_emoji = "🔴"  # Critical
                elif percent_used >= 75:
                    status_emoji = "🟡"  # Warning
                else:
                    status_emoji = "🟢"  # Good
                
                # FIX: Remove backslashes to prevent Markdown parsing errors
                safe_drive_name = partition.mountpoint.replace('\\', '')
                
                drive_info = {
                    'drive': safe_drive_name,
                    'filesystem': partition.fstype,
                    'total': total_gb,
                    'used': used_gb,
                    'free': free_gb,
                    'percent': percent_used,
                    'status': status_emoji
                }
                
                storage_info.append(drive_info)
                
                print(f"   {status_emoji} {partition.mountpoint} - {percent_used}% used ({free_gb} GB free)")
                
            except PermissionError:
                # Skip drives that we don't have permission to access
                continue
            except Exception as e:
                print(f"   ⚠️ Could not read {partition.mountpoint}: {e}")
                continue
        
        if not storage_info:
            return "No readable drives found."
        
        # Format the response
        response_lines = ["💾 **Storage Status:**\n"]
        
        for drive in storage_info:
            response_lines.append(
                f"{drive['status']} **{drive['drive']}** ({drive['filesystem']})\n"
                f"   Total: {drive['total']} GB\n"
                f"   Used: {drive['used']} GB ({drive['percent']}%)\n"
                f"   Free: {drive['free']} GB\n"
            )
        
        # Add summary
        total_storage = sum(d['total'] for d in storage_info)
        total_used = sum(d['used'] for d in storage_info)
        total_free = sum(d['free'] for d in storage_info)
        avg_percent = round(sum(d['percent'] for d in storage_info) / len(storage_info), 1)
        
        response_lines.append(
            f"\n📊 **Overall Summary:**\n"
            f"   Total Storage: {round(total_storage, 2)} GB\n"
            f"   Used: {round(total_used, 2)} GB\n"
            f"   Free: {round(total_free, 2)} GB\n"
            f"   Average Usage: {avg_percent}%"
        )
        
        result = "\n".join(response_lines)
        print("✅ Storage check complete!")
        return result
        
    except Exception as e:
        error_msg = f"Error checking storage: {e}"
        print(f"❌ {error_msg}")
        return error_msg


def open_browser(url, browser_name="default"):
    print(f"🌐 Request to open '{url}' in '{browser_name}'")
    
    try:
        
        if not browser_name or browser_name.lower() == "default":
            webbrowser.open(url)
            return

        
        path = get_browser_path(browser_name)
        
        if path:
            print(f"   -> Found browser at: {path}")
            
            webbrowser.register(browser_name, None, webbrowser.BackgroundBrowser(path))
            webbrowser.get(browser_name).open(url)
        else:
            print(f"⚠️ Could not find '{browser_name}'. Falling back to default.")
            webbrowser.open(url)
            
    except Exception as e:
        print(f"Error opening browser: {e}")
        webbrowser.open(url)

def close_application(app_name):
    
    clean_name = app_name.lower()
    for word in ["the ", "app ", "application ", "close ", "open "]:
        clean_name = clean_name.replace(word, "")
    
    
    app_key = clean_name.strip().replace(" ", "")
    
  
    if app_key in PROCESS_NAMES:
        exe_name = PROCESS_NAMES[app_key]
    else:
        exe_name = f"{app_key}.exe"
        
    print(f"💀 Killing process target: {exe_name}")
    
    try:
        os.system(f"taskkill /f /im {exe_name} /t")
    except Exception as e:
        print(f"Error closing app: {e}")

def open_file_path(path):
    try:
        if "download" in path.lower():
            path = os.path.join(os.path.expanduser("~"), "Downloads")
        elif "desktop" in path.lower():
            path = os.path.join(os.path.expanduser("~"), "Desktop")
        elif "c drive" in path.lower() or "c:" in path.lower():
            path = "C:/"
            
        if os.path.exists(path):
            os.startfile(path)
        else:
            print(f"❌ Path not found: {path}")
    except Exception as e:
        print(f"Error opening path: {e}")

def set_brightness(level):
    try:
        sbc.set_brightness(level)
    except Exception as e:
        print(f"Error setting brightness: {e}")

def execute_find_file(action_data):
    """
    Execute file finding using the SMART file_finder module
    Returns file path if found (for Telegram sending), or error message
    """
    print("🔍 Searching for file...")
    
    try:
        # Get the search query from brain.py
        query = action_data.get("query")
        
        if not query:
            # Fallback for old format (backward compatibility)
            time_query = action_data.get("time_query")
            file_type = action_data.get("file_type")
            keyword = action_data.get("keyword")
            
            parts = []
            if file_type: parts.append(file_type)
            if keyword: parts.append(keyword)
            if time_query: parts.append(time_query)
            query = " ".join(parts) if parts else "recent files"
        
        # Search for files using the SMART query
        print(f"   Query: '{query}'")
        
        # Uses the new smart finder logic
        results = file_finder.find_files_from_query(query, limit=3)
        
        if not results:
            print("   ❌ No matching files found")
            return {
                "status": "not_found",
                "message": "⚠️ No matching files found.\n\nTry:\n• 'files opened today'\n• 'PDFs from yesterday'\n• 'recent documents'"
            }
        
        # Files found!
        top_result = results[0]
        file_path = top_result['file_path']
        file_name = top_result['file_name']
        confidence = top_result.get('confidence_score', 0)
        
        # Metadata
        app_used = top_result.get('app_used', 'Unknown App')
        timestamp = top_result.get('timestamp', 'Unknown Time')
        
        print(f"   ✅ Found: {file_name} (confidence: {confidence}%)")
        
        # Check if file still exists
        if not os.path.exists(file_path):
            print(f"   ⚠️ File was moved/deleted: {file_path}")
            
            # Try alternate results
            if len(results) > 1:
                for result in results[1:]:
                    if os.path.exists(result['file_path']):
                        file_path = result['file_path']
                        file_name = result['file_name']
                        app_used = result.get('app_used', 'Unknown App')
                        timestamp = result.get('timestamp', 'Unknown Time')
                        print(f"   ✅ Using alternate: {file_name}")
                        break
                else:
                    return {
                        "status": "file_deleted",
                        "message": f"❌ File was found but no longer exists:\n{file_name}"
                    }
            else:
                return {
                    "status": "file_deleted",
                    "message": f"❌ File was found but no longer exists:\n{file_name}"
                }
        
        # Check file size (Telegram limit)
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        except:
            file_size_mb = 0
            
        if file_size_mb > 50:
            return {
                "status": "too_large",
                "message": f"❌ File is too large to send via Telegram:\n{file_name}\nSize: {file_size_mb:.1f} MB"
            }
        
        # Success
        return {
            "status": "found",
            "file_path": file_path,
            "file_name": file_name,
            "file_size_mb": file_size_mb,
            "confidence": confidence,
            "app_used": app_used,
            "timestamp": timestamp
        }
        
    except Exception as e:
        error_msg = f"Error during file search: {e}"
        print(f"   ❌ {error_msg}")
        return {
            "status": "error",
            "message": f"❌ Search error: {e}"
        }
    

def execute_command(cmd_json):
    if not cmd_json: return
    action = cmd_json.get("action")
    
    if action == "take_screenshot": return capture_screen() 
    elif action == "camera_stream" or action == "camera_snap": return capture_webcam()
    elif action == "check_battery": return get_battery_status()
    elif action == "check_health": return get_system_health()
    elif action == "get_location": return get_laptop_location() 
    elif action == "system_sleep": system_sleep()
    elif action == "shutdown_pc": shutdown_pc()
    elif action == "restart_pc": restart_pc()
    elif action == "record_audio": 
        duration = cmd_json.get("duration", 10)
        return record_audio(duration)
    elif action == "clear_recycle_bin": return clear_recycle_bin()
    elif action == "check_storage": return check_storage()
    
    elif action == "open_url": 
        open_browser(cmd_json.get("url"), cmd_json.get("browser", "default"))
        
    elif action == "close_app": close_application(cmd_json.get("app_name"))
    elif action == "open_app":
        app_name = cmd_json.get("app_name")
        print(f"🚀 Launching {app_name}...")
        pyautogui.press("win")
        pyautogui.sleep(0.1)
        pyautogui.write(app_name)
        pyautogui.sleep(0.5)
        pyautogui.press("enter")
    elif action == "system_control":
        feature = cmd_json.get("feature")
        val = cmd_json.get("value")
        if feature == "brightness": set_brightness(val)
    elif action == "open_file": open_file_path(cmd_json.get("path"))

    elif action == "get_activities":
        return activity_monitor.get_current_activities()

    elif action == "get_clipboard_history":
        return clipboard_monitor.get_clipboard_history()

    elif action == "find_file":
        return execute_find_file(cmd_json)