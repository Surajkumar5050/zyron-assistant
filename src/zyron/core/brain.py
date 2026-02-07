import ollama
import json
import os
from dotenv import load_dotenv
from .memory import get_context_string


load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5-coder:7b")


BASE_SYSTEM_PROMPT = """
You are Zyron, a smart laptop assistant with memory.
Your ONLY output must be valid JSON.

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

10. Audio Record: {"action": "record_audio", "duration": 60}
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

16. Chat:  {"action": "general_chat", "response": "text"}

17. Browser Control: {"action": "browser_control", "command": "close/mute", "query": "which tab"}
    (Triggers: "close youtube tab", "mute spotify", "close the video about AI")

18. Power Control: 
    - Shutdown: {"action": "shutdown_pc"} (Triggers: shutdown, turn off computer, kill power)
    - Restart:  {"action": "restart_pc"}  (Triggers: restart, reboot, cycle power)

*** CRITICAL RULE: CONTEXT AWARENESS ***
Use the [CURRENT CONTEXT STATE] below to resolve words like "it", "that", "the app", "the folder".
- If user says "Close it" and Last Focused Tab is "YouTube" -> {"action": "browser_control", "command": "close", "query": "YouTube"} (PRIORITY over close_app)
- If user says "Close it" and Last App Opened is "Chrome" -> {"action": "close_app", "app_name": "Chrome"}
"""

def process_command(user_input):
    print(f"⚡ Sending to Qwen: {user_input}")
    
    
    current_context = get_context_string()
    
    
    full_prompt = BASE_SYSTEM_PROMPT + "\n" + current_context
    
    try:
        response = ollama.chat(
            model=MODEL_NAME, 
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
            data = {"action": "record_audio", "duration": 60}

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

        # 10. Browser Control (NEW)
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

        return data

    except Exception as e:
        print(f"Error: {e}")
        return {"action": "general_chat", "response": "I had a brain glitch."}