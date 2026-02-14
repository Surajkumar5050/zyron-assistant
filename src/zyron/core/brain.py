import ollama
import json
from .memory import get_context_string
from src.zyron.utils.settings import settings


BASE_SYSTEM_PROMPT = """
You are Zyron, a smart laptop assistant with memory.
Your ONLY output must be valid JSON.

*** CORE CLASSIFICATION RULES ***
1. ACTION COMMAND: If the user wants you to DO something on the laptop (open/close apps, files, browser tabs, screenshots, check battery/health, etc.).
2. WEB RESEARCH: If the user asks a QUESTION about facts, people, prices, or current events (e.g. "Who is Sam Altman?", "Bitcoin price").
3. GENERAL CHAT: Only for greetings, simple conversation, or if no other action fits.

If the request is a QUESTION requiring a search, ALWAYS use "web_research".
If the request is an instruction to OPERATE the computer, use the specific ACTION command.

COMMANDS:
1. Camera: {"action": "camera_stream", "value": "on/off"}
   (Triggers: turn on/off camera, live video, stop video)
   
2. Sleep:  {"action": "system_sleep"}
   (Triggers: sleep, go to sleep, /sleep)
   
3. Screenshot: {"action": "take_screenshot"}
   (Triggers: screenshot, capture screen, ss)

4. Apps:   {"action": "open_app" or "close_app", "app_name": "name"}
   (Triggers: open/close notepad, chrome, spotify)

5. URLs:   {"action": "open_url", "url": "https://site.com", "browser": "chrome"} 
   (Triggers: "open youtube in chrome", "launch google on firefox", "open brave")
   * If no browser is specified, set "browser": "default".

6. Files:  
   - Send: {"action": "send_file", "path": "path"} (Triggers: give me, send, upload)
   - List: {"action": "list_files", "path": "path"} (Triggers: show files, list directory)

7. Memory: {"action": "save_memory", "key": "preference_key", "value": "value"}
   (Triggers: "My name is X", "I prefer Chrome")

8. Battery: {"action": "check_battery"}
   (Triggers: battery percentage, check battery, power status)

9. Health: {"action": "check_health"}
   (Triggers: system health, cpu usage, ram check, how is the pc)

10. Audio Record: {"action": "record_audio", "duration": 10}
    (Triggers: record audio, capture audio, /recordaudio)

11. Activities: {"action": "get_activities"}
    (Triggers: current activities, what's open, running apps, active windows, show activities, /current_activities, /activities, what is happening, open tabs)

12. Clear Recycle Bin: {"action": "clear_recycle_bin"}
    (Triggers: clear recycle bin, empty recycle bin, delete recycle bin, clear bin, empty bin, /clear_bin, clean recycle bin)

13. Storage Check: {"action": "check_storage"}
    (Triggers: check storage, disk space, storage space, drive space, how much storage, /storage, storage status, check drives)

14. Clipboard History: {"action": "get_clipboard_history"}
    (Triggers: copied texts, clipboard history, show copied texts, /copied_texts, what did i copy, clipboard)

15. Find File: {"action": "find_file", "time_query": "yesterday afternoon", "file_type": "pdf", "keyword": "report"}
    (Triggers: find that file, get me that PDF, that document I opened, file I was working on, send that file, give me that Excel, that image I saw)

16. Media Control: 
    - Playback: {"action": "control_media", "media_action": "playpause/nexttrack/prevtrack/volumemute"}
      (Triggers: pause music, next song, previous track, skip song, play music, mute audio)
    - Volume: {"action": "set_volume", "level": 50}
      (Triggers: volume 50, set volume to 80, volume to 30 percent)

17. Chat:  {"action": "general_chat", "response": "text"}

*** PRIORITY RULE: "CLICK ON X" ***
If user says "click on [something]", "press [something]", "tap [something]", "type [text]", or mentions "search" in the context of input:
ALWAYS use browser_nav with sub_action="click" or "type", NOT browser_control!
- "click on music" -> {"action": "browser_nav", "sub_action": "click", "target": "music"}
- "type Hello" -> {"action": "browser_nav", "sub_action": "type", "target": "search", "text": "Hello"}
browser_control is ONLY for "close TAB", "mute TAB", or "screenshot TAB" - operations on the TAB itself!

17. Browser Tab Control: {"action": "browser_control", "command": "close/mute/screenshot", "query": "which tab"}
    (Triggers: "close youtube TAB", "mute spotify TAB", "screenshot the TAB")
    *** ONLY when user explicitly refers to the TAB or its status (close/mute/snap) ***

18. Power Control: 
    - Shutdown: {"action": "shutdown_pc"} (Triggers: shutdown, turn off computer, kill power)
    - Restart:  {"action": "restart_pc"}  (Triggers: restart, reboot, cycle power)

19. Caffeine Mode (Keep Awake): 
    - Enable:  {"action": "toggle_caffeine", "state": true}  (Triggers: keep awake, don't sleep, stay awake, enable caffeine, disable sleep, caffeine mode on, keep system awake, prevent sleep)
    - Disable: {"action": "toggle_caffeine", "state": false} (Triggers: go to sleep, disable caffeine, normal mode, can sleep now, caffeine mode off, allow sleep)

20. Browser Page Interaction: {"action": "browser_nav", "sub_action": "read/scroll/click/type/scan", ...}
    *** Use this for interacting with CONTENT ON THE PAGE (buttons, links, forms) ***
    - Read page: {"action": "browser_nav", "sub_action": "read"}
    - Scroll:    {"action": "browser_nav", "sub_action": "scroll", "direction": "down/up/top/bottom"}
    - Click button/link: {"action": "browser_nav", "sub_action": "click", "target": "button text"}
    - Type in field:     {"action": "browser_nav", "sub_action": "type", "target": "field name", "text": "what to type"}
    (Triggers: "click on X", "click the button", "scroll down", "type Y in search", "read page")

20. Web Research: {"action": "web_research", "query": "search query"}
    (Triggers: "Who is...", "What is...", "How much is...", "Look up...", "Research...", "Find info about...")

*** MULTI-COMMAND CHAINING ***
If the user wants MULTIPLE actions in sequence, return a JSON ARRAY of actions.
Example: "Open YouTube and search Pikachu" -> [{"action": "open_url", ...}, {"action": "browser_nav", "sub_action": "type", ...}]

*** CRITICAL RULE: CONTEXT AWARENESS ***
Use the [CURRENT CONTEXT STATE] to resolve "it", "that", "there".
- If user says "click it" and Last Focused Tab is "YouTube" -> Assume the user is talking about the content inside that YouTube tab.
- NEVER used browser_control if the intent is to INTERACT with content.
"""

def process_command(user_input):
    print(f"⚡ Sending to Qwen: {user_input}")
    
    
    current_context = get_context_string()
    
    
    full_prompt = BASE_SYSTEM_PROMPT + "\n" + current_context
    
    try:
        response = ollama.chat(
            model=settings.MODEL_NAME, 
            messages=[
                {'role': 'system', 'content': full_prompt},
                {'role': 'user', 'content': user_input},
            ],
            keep_alive=0 
        )
        content = response['message']['content']
        
        
        if "```" in content:
            content = content.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(content)
        
        
        lower = user_input.lower()
        
        # 1. Force Camera
        if "camera" in lower and "on" in lower: 
            data = {"action": "camera_stream", "value": "on"}
        elif "camera" in lower and "off" in lower: 
            data = {"action": "camera_stream", "value": "off"}
            
        # 2. Force Sleep/Screenshot/Battery
        elif "/sleep" in lower: 
            data = {"action": "system_sleep"}
        elif "/shutdown" in lower:
            data = {"action": "shutdown_pc"}
        elif "/restart" in lower:
            data = {"action": "restart_pc"}
        elif ("/screenshot" in lower or "screenshot" in lower) and not ("tab" in lower or "browser" in lower): 
            data = {"action": "take_screenshot"}
        elif "battery" in lower: 
            data = {"action": "check_battery"}
            
        # 3. Force Health Check
        elif any(x in lower for x in ["cpu", "ram", "system health", "lag", "pc status"]):
            data = {"action": "check_health"}

        # 4. Force Memory Save
        elif "my name is" in lower:
            name_part = user_input.split("is")[-1].strip()
            name_part = name_part.replace(".", "").replace("!", "")
            data = {"action": "save_memory", "key": "user_name", "value": name_part}

        # 5. Force Audio Recording
        elif "/recordaudio" in lower or "record audio" in lower:
            data = {"action": "record_audio", "duration": 10}

        # 6. Force Activity Check
        elif any(x in lower for x in ["/activities", "/current_activities", "current activities", "what's open", "running apps", "active windows", "show activities", "what is happening", "open tabs", "what am i doing"]):
            data = {"action": "get_activities"}

        # 7. Force Clear Recycle Bin (FROM OLD CODE)
        elif any(x in lower for x in ["/clear_bin", "clear recycle bin", "empty recycle bin", "delete recycle bin", "clear bin", "empty bin", "clean recycle bin", "clear the bin", "empty the bin"]):
            data = {"action": "clear_recycle_bin"}

        # 8. Force Storage Check (FROM OLD CODE)
        elif any(x in lower for x in ["/storage", "check storage", "disk space", "storage space", "drive space", "how much storage", "storage status", "check drives", "disk usage", "storage left"]):
            data = {"action": "check_storage"}

        # 9. Force Clipboard History (FROM NEW CODE)
        elif any(x in lower for x in ["/copied_texts", "copied texts", "clipboard history", "clipboard", "what did i copy", "show copied", "give me copied texts"]):
            data = {"action": "get_clipboard_history"}

        # 10. Force Caffeine Mode (Keeping Awake)
        elif any(x in lower for x in ["keep awake", "don't sleep", "stay awake", "enable caffeine", "disable sleep", "caffeine mode on", "keep system awake", "prevent sleep", "no sleep"]):
            data = {"action": "toggle_caffeine", "state": True}
        elif any(x in lower for x in ["go to sleep", "disable caffeine", "normal mode", "can sleep now", "caffeine mode off", "allow sleep", "enable sleep"]):
            data = {"action": "toggle_caffeine", "state": False}

        # 11. Browser Control (NEW)
        # "Close the youtube tab", "Mute the music"
        elif "close" in lower and ("tab" in lower or "video" in lower):
            # We need to find the TAB ID first. This logic is usually in main.py or telegram.py
            # But the Brain just decides the INTENT.
            # We will return a "browser_action" command and let the Agent resolve the specific tab ID
            data = {"action": "browser_control", "command": "close", "query": user_input}
            
        elif ("mute" in lower or "silence" in lower) and ("tab" in lower or "video" in lower or "music" in lower):
            data = {"action": "browser_control", "command": "mute", "query": user_input}
            
        elif ("play" in lower or "pause" in lower or "resume" in lower or "video" in lower) and ("music" in lower or "video" in lower or "youtube" in lower):
            command = "play" if "play" in lower or "resume" in lower else "pause"
            data = {"action": "browser_control", "command": command, "query": user_input}

        elif "screenshot" in lower and ("tab" in lower or "browser" in lower or "page" in lower):
            data = {"action": "browser_control", "command": "screenshot", "query": user_input}
        
        # MEDIA CONTROLLER - Playback Controls
        # {"pause music", "next song", "previous track", "play music"}
        elif any(x in lower for x in ["pause music", "pause song", "stop music", "stop song", "pause the music", "pause the song"]):
            data = {"action": "control_media", "media_action": "playpause"}
        
        elif any(x in lower for x in ["play music", "play song", "resume music", "unpause", "play the music", "play the song"]) and "youtube" not in lower and "video" not in lower:
            data = {"action": "control_media", "media_action": "playpause"}
        
        elif any(x in lower for x in ["next track", "next song", "skip song", "skip track", "next music", "play next"]):
            data = {"action": "control_media", "media_action": "nexttrack"}
        
        elif any(x in lower for x in ["previous track", "previous song", "prev track", "prev song", "last song", "go back"]):
            data = {"action": "control_media", "media_action": "prevtrack"}
        
        elif any(x in lower for x in ["mute audio", "mute sound", "mute volume", "silence", "mute the volume"]) and "tab" not in lower:
            data = {"action": "control_media", "media_action": "volumemute"}
        
        # MEDIA CONTROLLER - Volume Control
        # {"volume 50", "set volume to 80", "volume to 30 percent"}
        elif "volume" in lower and any(char.isdigit() for char in user_input):
            import re
            # Extract number from command
            numbers = re.findall(r'\d+', user_input)
            if numbers:
                level = int(numbers[0])
                # Ensure it's within valid range
                level = max(0, min(100, level))
                data = {"action": "set_volume", "level": level}
        
        # 11. Force Find File (Context-Aware File Finder)
        # Detect file finding queries - "find that", "get me that", "send that", "that file", etc.
        find_triggers = ["find that", "get that", "send that", "give me that", "that file", "that pdf", "that document", "that excel", "that image", "that video", "i was reading", "i opened", "i was working on", "file i", "document i"]
        if any(trigger in lower for trigger in find_triggers):
            # Pass query once - file_finder.py will extract time and type
            data = {"action": "find_file", "query": user_input}

        # 11. Force File Send (MERGED LOGIC)
        send_keywords = ["give", "send", "upload", "fetch", "get"]
        safe_to_override = True
        
        # Added 'storage', 'bin', 'clipboard', 'copied' to safe exclusion list
        for k in ["list", "camera", "battery", "cpu", "ram", "health", "record", "audio", "activities", "storage", "bin", "clipboard", "copied", "copy"]:
            if k in lower:
                safe_to_override = False
                break
                
        if any(k in lower for k in send_keywords) and safe_to_override:
            found_path = data.get('path') or data.get('url') or data.get('app_name')
            if found_path:
                data = {"action": "send_file", "path": found_path}

        # 12. Force Web Research
        research_triggers = ["who is", "what is", "how much", "tell me about", "look up", "research", "search for", "find info", "is there", "are there"]
        is_question_str = any(lower.startswith(t) for t in ["who", "what", "how", "where", "why", "when", "is ", "are ", "tell me", "can you find"])
        is_actual_question = lower.endswith("?") or is_question_str
        
        # Only override if it's currently general chat or a weak match
        # AND it doesn't look like a system command (e.g. "What's my battery")
        system_keywords = ["battery", "health", "cpu", "ram", "storage", "recycle", "clipboard", "copied", "screenshot", "activities", "open", "close"]
        looks_like_system = any(k in lower for k in system_keywords)

        current_action = data[0].get("action") if isinstance(data, list) else data.get("action")
        if (is_actual_question or any(t in lower for t in research_triggers)) and current_action == "general_chat" and not looks_like_system:
            data = {"action": "web_research", "query": user_input}

        # Normalize to list for multi-command support
        if isinstance(data, list):
            return data
        return [data]

    except Exception as e:
        print(f"Error: {e}")
        return [{"action": "general_chat", "response": "I had a brain glitch."}]