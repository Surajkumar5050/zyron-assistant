import psutil
import json
import os
import subprocess
import sqlite3
import shutil
from collections import defaultdict
from pathlib import Path
import time

try:
    import win32gui
    import win32process
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("Warning: pywin32 not available. Tab detection will use fallback method.")

# Browser executable names
BROWSER_PROCESSES = {
    'chrome.exe': 'Google Chrome',
    'msedge.exe': 'Microsoft Edge',
    'brave.exe': 'Brave Browser',
    'firefox.exe': 'Mozilla Firefox',
    'opera.exe': 'Opera'
}

def escape_markdown(text):
    """
    Escapes special characters for Telegram Markdown V1 to prevent parse errors.
    Characters escaped: _ * [ ] `
    """
    if not text:
        return ""
    
    # In Markdown V1, primarily _ * [ ] ` need escaping to avoid "Can't parse entities"
    escape_chars = ['_', '*', '[', ']', '`']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def get_running_processes():
    """Get all running processes with their details"""
    processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'exe': proc.info['exe'],
                    'cmdline': proc.info['cmdline']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error getting processes: {e}")
    
    return processes


def get_chrome_tabs():
    """Get all Chrome tabs from session storage"""
    tabs = []
    
    try:
        # Chrome user data path
        chrome_path = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Google', 'Chrome', 'User Data', 'Default'
        )
        
        # Try to read History file
        history_db = os.path.join(chrome_path, 'History')
        
        if os.path.exists(history_db):
            # Copy to temp to avoid locking
            temp_db = os.path.join(os.environ.get('TEMP', ''), 'chrome_history_temp.db')
            try:
                shutil.copy2(history_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                # Get recent URLs
                cursor.execute("""
                    SELECT url, title, last_visit_time 
                    FROM urls 
                    ORDER BY last_visit_time DESC 
                    LIMIT 50
                """)
                
                results = cursor.fetchall()
                conn.close()
                
                # Clean up temp file
                try:
                    os.remove(temp_db)
                except:
                    pass
            
                for url, title, _ in results[:30]:  # Limit to 30 recent
                    if url:
                        # Use URL as title if title is missing
                        display_title = title if title else url
                        tabs.append({
                            'title': display_title,
                            'url': url
                        })
                        
            except Exception as e:
                print(f"Error reading Chrome history: {e}")
                
    except Exception as e:
        print(f"Error getting Chrome tabs: {e}")
    
    return tabs


def get_brave_tabs():
    """Get all Brave tabs from session storage"""
    tabs = []
    
    try:
        # Brave user data path
        brave_path = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'BraveSoftware', 'Brave-Browser', 'User Data', 'Default'
        )
        
        history_db = os.path.join(brave_path, 'History')
        
        if os.path.exists(history_db):
            temp_db = os.path.join(os.environ.get('TEMP', ''), 'brave_history_temp.db')
            try:
                shutil.copy2(history_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT url, title, last_visit_time 
                    FROM urls 
                    ORDER BY last_visit_time DESC 
                    LIMIT 50
                """)
                
                results = cursor.fetchall()
                conn.close()
                
                try:
                    os.remove(temp_db)
                except:
                    pass
                
                for url, title, _ in results[:30]:
                    if url:
                        display_title = title if title else url
                        tabs.append({
                            'title': display_title,
                            'url': url
                        })
                        
            except Exception as e:
                print(f"Error reading Brave history: {e}")
                
    except Exception as e:
        print(f"Error getting Brave tabs: {e}")
    
    return tabs


def get_edge_tabs():
    """Get all Edge tabs from session storage"""
    tabs = []
    
    try:
        # Edge user data path
        edge_path = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Microsoft', 'Edge', 'User Data', 'Default'
        )
        
        history_db = os.path.join(edge_path, 'History')
        
        if os.path.exists(history_db):
            temp_db = os.path.join(os.environ.get('TEMP', ''), 'edge_history_temp.db')
            try:
                shutil.copy2(history_db, temp_db)
                
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT url, title, last_visit_time 
                    FROM urls 
                    ORDER BY last_visit_time DESC 
                    LIMIT 50
                """)
                
                results = cursor.fetchall()
                conn.close()
                
                try:
                    os.remove(temp_db)
                except:
                    pass
                
                for url, title, _ in results[:30]:
                    if url:
                        display_title = title if title else url
                        tabs.append({
                            'title': display_title,
                            'url': url
                        })
                        
            except Exception as e:
                print(f"Error reading Edge history: {e}")
                
    except Exception as e:
        print(f"Error getting Edge tabs: {e}")
    
    return tabs


def get_firefox_tabs():
    """Get Firefox tabs using Native Bridge (temp JSON) or fall back to Places database"""
    tabs = []
    
    # Try Native Bridge first (Real-time data)
    temp_path = Path(os.environ.get('TEMP', '')) / 'zyron_firefox_tabs.json'
    if temp_path.exists():
        try:
            mtime = temp_path.stat().st_mtime
            age = time.time() - mtime
            # Data must be newer than 5 seconds for real-time Focus Mode
            if age < 5:
                with open(temp_path, 'r') as f:
                    tabs = json.load(f)
                if tabs:
                    return tabs
            elif age > 60:
                # Remove stale data to prevent enforcer acting on zombies
                try:
                    os.remove(temp_path)
                    print(f"🧹 Cleared stale Firefox tab data ({int(age)}s old)")
                except:
                    pass
        except Exception as e:
            print(f"Error reading Firefox Native Bridge data: {e}")

    try:
        # Firefox profiles path
        firefox_path = os.path.join(
            os.environ.get('APPDATA', ''),
            'Mozilla', 'Firefox', 'Profiles'
        )
        
        if not os.path.exists(firefox_path):
            return tabs
        
        # Find default profile
        profiles = [d for d in os.listdir(firefox_path) if os.path.isdir(os.path.join(firefox_path, d))]
        
        for profile in profiles:
            if 'default' in profile.lower() or 'release' in profile.lower():
                profile_path = os.path.join(firefox_path, profile)
                places_db = os.path.join(profile_path, 'places.sqlite')
                
                if os.path.exists(places_db):
                    temp_db = os.path.join(os.environ.get('TEMP', ''), 'firefox_places_temp.db')
                    try:
                        shutil.copy2(places_db, temp_db)
                        
                        conn = sqlite3.connect(temp_db)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT url, title, last_visit_date 
                            FROM moz_places 
                            WHERE url IS NOT NULL 
                            ORDER BY last_visit_date DESC 
                            LIMIT 50
                        """)
                        
                        results = cursor.fetchall()
                        conn.close()
                        
                        try:
                            os.remove(temp_db)
                        except:
                            pass
                        
                        for url, title, _ in results[:30]:
                            if url:
                                display_title = title if title else url
                                tabs.append({
                                    'title': display_title,
                                    'url': url
                                })
                        
                        break # Found and processed the main profile
                        
                    except Exception as e:
                        print(f"Error reading Firefox places: {e}")
                        
    except Exception as e:
        print(f"Error getting Firefox tabs: {e}")
    
    return tabs


def get_browser_tabs_win32():
    """Get browser tabs using win32gui - reads ACTUAL open windows only"""
    if not HAS_WIN32:
        return None
    
    tabs_by_browser = defaultdict(list)
    
    def get_process_name(hwnd):
        """Get process name for a window"""
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['pid'] == pid:
                    return proc.info['name']
        except:
            pass
        return None
    
    def enum_windows_callback(hwnd, _):
        """Callback for enumerating windows"""
        if win32gui.IsWindowVisible(hwnd):
            try:
                proc_name = get_process_name(hwnd)
                
                if proc_name and proc_name in BROWSER_PROCESSES:
                    title = win32gui.GetWindowText(hwnd)
                    
                    if title and title.strip():
                        browser_name = BROWSER_PROCESSES[proc_name]
                        
                        # Clean up browser suffixes from window titles
                        for suffix in [f' - {browser_name}', f' — {browser_name}', 
                                      ' - Google Chrome', ' - Brave', ' - Microsoft Edge',
                                      ' - Mozilla Firefox', ' - Chromium']:
                            if title.endswith(suffix):
                                title = title[:-len(suffix)]
                                break
                        
                        # Filter out generic window titles
                        if title.strip() and title not in ['New Tab', 'Chrome', 'Brave', 'Edge', 'Firefox']:
                            tabs_by_browser[browser_name].append({
                                'title': title.strip(),
                                'url': 'Active Window' # Placeholder as we can't get URL from window title easily
                            })
            except Exception as e:
                pass
    
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception as e:
        print(f"Error enumerating windows: {e}")
    
    return dict(tabs_by_browser)


def get_browser_tabs_all():
    """Get browser tabs from all detected browsers using their databases"""
    
    tabs_by_browser = defaultdict(list)
    
    # 1. Detect running browsers
    processes = get_running_processes()
    running_browsers = set()
    
    for proc in processes:
        if proc['name'] in BROWSER_PROCESSES:
            browser_name = BROWSER_PROCESSES[proc['name']]
            running_browsers.add(browser_name)
    
    print(f"   → Detected running browsers: {running_browsers}")
    
    # 2. Fetch tabs for running browsers using Database methods (Gets ALL tabs, not just active)
    if 'Google Chrome' in running_browsers:
        print("   → Fetching Chrome tabs...")
        chrome_tabs = get_chrome_tabs()
        if chrome_tabs:
            tabs_by_browser['Google Chrome'] = chrome_tabs
            print(f"      ✓ Found {len(chrome_tabs)} Chrome tabs")
    
    if 'Brave Browser' in running_browsers:
        print("   → Fetching Brave tabs...")
        brave_tabs = get_brave_tabs()
        if brave_tabs:
            tabs_by_browser['Brave Browser'] = brave_tabs
            print(f"      ✓ Found {len(brave_tabs)} Brave tabs")
    
    if 'Microsoft Edge' in running_browsers:
        print("   → Fetching Edge tabs...")
        edge_tabs = get_edge_tabs()
        if edge_tabs:
            tabs_by_browser['Microsoft Edge'] = edge_tabs
            print(f"      ✓ Found {len(edge_tabs)} Edge tabs")
    
    if 'Mozilla Firefox' in running_browsers:
        print("   → Fetching Firefox tabs...")
        firefox_tabs = get_firefox_tabs()
        if firefox_tabs:
            tabs_by_browser['Mozilla Firefox'] = firefox_tabs
            print(f"      ✓ Found {len(firefox_tabs)} Firefox tabs")
    
    return dict(tabs_by_browser)


def get_desktop_applications():
    """Get list of desktop applications currently running"""
    apps = []
    
    # App mappings: Process Name -> Display Name
    desktop_apps = {
    # System / Default
    'notepad.exe': 'Notepad',
    'calc.exe': 'Calculator',
    'mspaint.exe': 'Paint',
    'explorer.exe': 'File Explorer',
    'taskmgr.exe': 'Task Manager',
    'cmd.exe': 'Command Prompt',
    'powershell.exe': 'Windows PowerShell',
    'wt.exe': 'Windows Terminal',
    'control.exe': 'Control Panel',

    # Browsers
    'chrome.exe': 'Google Chrome',
    'msedge.exe': 'Microsoft Edge',
    'firefox.exe': 'Mozilla Firefox',
    'opera.exe': 'Opera Browser',
    'brave.exe': 'Brave Browser',
    'vivaldi.exe': 'Vivaldi Browser',
    'tor.exe': 'Tor Browser',

    # Microsoft Office
    'EXCEL.EXE': 'Microsoft Excel',
    'WINWORD.EXE': 'Microsoft Word',
    'POWERPNT.EXE': 'Microsoft PowerPoint',
    'OUTLOOK.EXE': 'Microsoft Outlook',
    'ONENOTE.EXE': 'Microsoft OneNote',
    'MSACCESS.EXE': 'Microsoft Access',

    # Code Editors / IDEs
    'Code.exe': 'Visual Studio Code',
    'devenv.exe': 'Visual Studio',
    'notepad++.exe': 'Notepad++',
    'sublime_text.exe': 'Sublime Text',
    'atom.exe': 'Atom Editor',
    'pycharm64.exe': 'PyCharm',
    'idea64.exe': 'IntelliJ IDEA',
    'webstorm64.exe': 'WebStorm',
    'phpstorm64.exe': 'PhpStorm',
    'clion64.exe': 'CLion',
    'rider64.exe': 'Rider',
    'studio64.exe': 'Android Studio',
    'eclipse.exe': 'Eclipse IDE',
    'netbeans64.exe': 'NetBeans IDE',

    # Communication / Meetings
    'Discord.exe': 'Discord',
    'Telegram.exe': 'Telegram',
    'WhatsApp.exe': 'WhatsApp Desktop',
    'Zoom.exe': 'Zoom',
    'Teams.exe': 'Microsoft Teams',
    'slack.exe': 'Slack',
    'Skype.exe': 'Skype',
    'Signal.exe': 'Signal',
    'Viber.exe': 'Viber',

    # Media Players / Streaming
    'vlc.exe': 'VLC Media Player',
    'wmplayer.exe': 'Windows Media Player',
    'iTunes.exe': 'iTunes',
    'Spotify.exe': 'Spotify',
    'MusicBee.exe': 'MusicBee',
    'foobar2000.exe': 'Foobar2000',

    # Design / Creative
    'photoshop.exe': 'Adobe Photoshop',
    'illustrator.exe': 'Adobe Illustrator',
    'InDesign.exe': 'Adobe InDesign',
    'PremierePro.exe': 'Adobe Premiere Pro',
    'AfterFX.exe': 'Adobe After Effects',
    'Lightroom.exe': 'Adobe Lightroom',
    'Figma.exe': 'Figma',
    'XD.exe': 'Adobe XD',
    'gimp.exe': 'GIMP',
    'krita.exe': 'Krita',
    'blender.exe': 'Blender',
    'canva.exe': 'Canva Desktop',

    # Screen Recording / Streaming
    'obs64.exe': 'OBS Studio',
    'Streamlabs OBS.exe': 'Streamlabs OBS',
    'bandicam.exe': 'Bandicam',
    'camtasia.exe': 'Camtasia',

    # File Compression / ISO
    'WinRAR.exe': 'WinRAR',
    '7zFM.exe': '7-Zip',
    'peazip.exe': 'PeaZip',
    'PowerISO.exe': 'PowerISO',
    'UltraISO.exe': 'UltraISO',

    # Cloud Storage / Sync
    'OneDrive.exe': 'Microsoft OneDrive',
    'GoogleDriveFS.exe': 'Google Drive',
    'Dropbox.exe': 'Dropbox',
    'Box.exe': 'Box Drive',

    # Gaming Launchers
    'steam.exe': 'Steam',
    'steamwebhelper.exe': 'Steam',
    'EpicGamesLauncher.exe': 'Epic Games Launcher',
    'Battle.net.exe': 'Blizzard Battle.net',
    'UbisoftConnect.exe': 'Ubisoft Connect',
    'Origin.exe': 'EA Origin',
    'EADesktop.exe': 'EA App',
    'GOG Galaxy.exe': 'GOG Galaxy',
    'RiotClientServices.exe': 'Riot Client',

    # Virtualization / Containers
    'VirtualBox.exe': 'Oracle VirtualBox',
    'vmware.exe': 'VMware Workstation',
    'Docker Desktop.exe': 'Docker Desktop',

    # Databases / Dev Tools
    'mysqlworkbench.exe': 'MySQL Workbench',
    'pgAdmin4.exe': 'pgAdmin',
    'dbeaver.exe': 'DBeaver',
    'MongoDBCompass.exe': 'MongoDB Compass',
    'Postman.exe': 'Postman',
    'Insomnia.exe': 'Insomnia API Client',

    # Torrent / Downloaders
    'uTorrent.exe': 'uTorrent',
    'BitTorrent.exe': 'BitTorrent',
    'qbittorrent.exe': 'qBittorrent',
    'IDMan.exe': 'Internet Download Manager',
    'JDownloader2.exe': 'JDownloader',

    # Utilities / Others
    'AnyDesk.exe': 'AnyDesk',
    'TeamViewer.exe': 'TeamViewer',
    'RustDesk.exe': 'RustDesk',
    'Everything.exe': 'Everything Search',
    'ShareX.exe': 'ShareX',
    'Greenshot.exe': 'Greenshot',
}   

    
    processes = get_running_processes()
    found_apps = set()
    
    for proc in processes:
        proc_name = proc['name']
        
        # Skip browsers since they are handled separately
        if proc_name in BROWSER_PROCESSES:
            continue
        
        # Check against known apps
        if proc_name in desktop_apps:
            app_name = desktop_apps[proc_name]
            if app_name not in found_apps:
                apps.append({
                    'name': app_name,
                    'process': proc_name,
                    'pid': proc['pid']
                })
                found_apps.add(app_name)
    
    # Sort by name
    apps.sort(key=lambda x: x['name'])
    
    return apps


def get_current_activities():
    """
    Main function to get all current activities
    Returns a structured dictionary with browsers, desktop apps, and system info
    """
    
    print("🔍 Collecting current activities...")
    
    activities = {
        'browsers': {},
        'desktop_apps': [],
        'system_info': {}
    }
    
    # 1. Browsers
    print("   → Checking browsers...")
    browser_tabs = get_browser_tabs_all()
    activities['browsers'] = browser_tabs
    
    # 2. Desktop Apps
    print("   → Checking desktop applications...")
    activities['desktop_apps'] = get_desktop_applications()
    
    # 3. System Info
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        
        activities['system_info'] = {
            'cpu_usage': f"{cpu_percent}%",
            'ram_usage': f"{mem.percent}%",
            'ram_available': f"{round(mem.available / (1024**3), 2)} GB",
            'total_processes': len(list(psutil.process_iter()))
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
    
    print("✅ Activity collection complete!")
    return activities


def format_activities_text(activities, max_message_length=4000):
    """
    Format activities into a readable text format for Telegram
    Handles message length limits by splitting into multiple parts if needed
    Returns either a single string or a list of strings
    """
    
    lines = ["📊 **CURRENT ACTIVITIES**\n"]
    
    # Browsers
    if activities['browsers']:
        lines.append("🌐 **BROWSERS:**")
        for browser, tabs in activities['browsers'].items():
            lines.append(f"\n▫️ **{browser}**")
            if tabs:
                for i, tab in enumerate(tabs[:15], 1): # Limit to 15 recent tabs per browser
                    # SAFETY: Escape titles and URLs to prevent parse errors
                    title = escape_markdown(tab.get('title', 'Unknown'))
                    url = escape_markdown(tab.get('url', 'N/A'))
                    
                    # Truncate if too long
                    if len(title) > 60:
                        title = title[:57] + "..."
                    
                    lines.append(f"   {i}. {title}")
                    
                    # Show URL if valid
                    if url and url != 'Install extension for URLs' and url != 'Active Window' and url != 'N/A':
                        if len(url) > 100:
                            url = url[:97] + "..."
                        lines.append(f"      🔗 {url}")
            else:
                lines.append("   (No recent tabs found)")
        lines.append("")
    else:
        lines.append("🌐 **BROWSERS:**")
        lines.append("   (No browsers running)\n")
    
    # Apps
    if activities['desktop_apps']:
        lines.append("🖥️ **DESKTOP APPLICATIONS:**")
        for app in activities['desktop_apps']:
            # SAFETY: Escape app name
            safe_name = escape_markdown(app['name'])
            lines.append(f"   • {safe_name}")
        lines.append("")
    else:
        lines.append("🖥️ **DESKTOP APPLICATIONS:**")
        lines.append("   (No major applications detected)\n")
    
    # System Stats
    if activities['system_info']:
        info = activities['system_info']
        lines.append("⚙️ **SYSTEM STATUS:**")
        lines.append(f"   CPU: {info.get('cpu_usage', 'N/A')}")
        lines.append(f"   RAM: {info.get('ram_usage', 'N/A')} (Free: {info.get('ram_available', 'N/A')})")
        lines.append(f"   Processes: {info.get('total_processes', 'N/A')}")
    
    full_text = "\n".join(lines)
    
    # Split if too long
    if len(full_text) > max_message_length:
        print(f"   ⚠️ Message too long ({len(full_text)} chars), splitting...")
        return split_long_message(activities, max_message_length)
    
    return full_text


def split_long_message(activities, max_length=4000):
    """
    Split activities into multiple messages if too long
    Returns a list of message strings
    """
    messages = []
    
    # PART 1: Summary + Start of Browsers
    lines = ["📊 **CURRENT ACTIVITIES**\n"]
    lines.append("🌐 **BROWSERS:**")
    
    if activities['browsers']:
        for browser, tabs in activities['browsers'].items():
            lines.append(f"▫️ **{browser}**: {len(tabs)} detected tabs")
        
        messages.append("\n".join(lines))
        
        # Detailed Tab Lists
        for browser, tabs in activities['browsers'].items():
            if tabs:
                browser_lines = [f"\n🌐 **{browser} Details:**\n"]
                current_batch = []
                
                for i, tab in enumerate(tabs[:20], 1): # Limit split messages too
                    # SAFETY: Escape titles and URLs
                    title = escape_markdown(tab.get('title', 'Unknown'))
                    url = escape_markdown(tab.get('url', 'N/A'))
                    
                    if len(title) > 70:
                        title = title[:67] + "..."
                    
                    current_batch.append(f"{i}. {title}")
                    
                    # Show URL if valid
                    if url and url != 'Install extension for URLs' and url != 'Active Window' and url != 'N/A':
                        if len(url) > 90:
                            url = url[:87] + "..."
                        current_batch.append(f"   🔗 {url}")
                    
                    # Check length
                    test_text = "\n".join(browser_lines + current_batch)
                    if len(test_text) > max_length - 300:
                        # Send current batch
                        messages.append("\n".join(browser_lines + current_batch))
                        browser_lines = [f"\n🌐 **{browser} (continued):**\n"]
                        current_batch = []
                
                # Remaining items
                if current_batch:
                    messages.append("\n".join(browser_lines + current_batch))
    else:
        lines.append("   (No browsers running)")
        messages.append("\n".join(lines))
    
    # PART 2: Apps and System Info
    final_lines = []
    
    if activities['desktop_apps']:
        final_lines.append("\n🖥️ **DESKTOP APPLICATIONS:**")
        for app in activities['desktop_apps']:
            # SAFETY: Escape app name
            safe_name = escape_markdown(app['name'])
            final_lines.append(f"   • {safe_name}")
        final_lines.append("")
    
    if activities['system_info']:
        info = activities['system_info']
        final_lines.append("⚙️ **SYSTEM STATUS:**")
        final_lines.append(f"   CPU: {info.get('cpu_usage', 'N/A')}")
        final_lines.append(f"   RAM: {info.get('ram_usage', 'N/A')} (Free: {info.get('ram_available', 'N/A')})")
        final_lines.append(f"   Processes: {info.get('total_processes', 'N/A')}")
    
    if final_lines:
        messages.append("\n".join(final_lines))
    
    return messages


if __name__ == "__main__":
    # Test Output
    activities = get_current_activities()
    print("\n" + "="*60)
    result = format_activities_text(activities)
    
    if isinstance(result, list):
        for i, msg in enumerate(result, 1):
            print(f"\n--- MESSAGE {i} ---")
            print(msg)
            print("="*60)
    else:
        print(result)
        print("="*60)