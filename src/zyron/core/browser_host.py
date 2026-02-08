import sys
import json
import struct
import os
from pathlib import Path

# The native messaging host must read and write from/to stdin/stdout.
# Each message is prefixed by a 32-bit (4-byte) length field.

def get_message():
    """Reads a message from standard input and decodes it."""
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    message_length = struct.unpack('=I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

def send_message(message):
    """Encodes and writes a message to standard output."""
    content = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('=I', len(content)))
    sys.stdout.buffer.write(content)
    sys.stdout.buffer.flush()

import threading
import time

# --- Command Queue Logic ---
COMMAND_FILE_PATH = Path(os.environ.get('TEMP', '')) / 'zyron_firefox_commands.json'

def poll_command_queue():
    """Background thread to check for commands from Zyron."""
    while True:
        try:
            if COMMAND_FILE_PATH.exists():
                try:
                    with open(COMMAND_FILE_PATH, 'r') as f:
                        commands = json.load(f)
                    
                    # Clear the file after reading
                    os.remove(COMMAND_FILE_PATH)
                    
                    # Process commands
                    if isinstance(commands, list):
                        for cmd in commands:
                            if cmd:
                                send_message(cmd)
                    elif isinstance(commands, dict):
                        send_message(commands)
                    
                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    pass
            
            time.sleep(0.5) # Check every 500ms
        except Exception:
            time.sleep(1)

def main():
    """Main loop of the native messaging host."""
    
    # Start polling thread
    t = threading.Thread(target=poll_command_queue, daemon=True)
    t.start()

    try:
        while True:
            message = get_message()
            if message is None:
                break
            
            # Action: Ping
            if message.get("action") == "ping":
                send_message({"status": "ok", "message": "Zyron Native Host is alive"})
            
            # Action: Update Tabs
            elif message.get("action") == "update_tabs":
                # For now, we'll just save this to a local file that activity.py can read
                # In the future, we might use a faster IPC or shared memory
                temp_path = Path(os.environ.get('TEMP', '')) / 'zyron_firefox_tabs.json'
                try:
                    with open(temp_path, 'w') as f:
                        json.dump(message.get("tabs", []), f)
                    send_message({"status": "success", "received": len(message.get("tabs", []))})
                except Exception as e:
                    send_message({"status": "error", "message": str(e)})
            
            # Action: Save Screenshot
            elif message.get("action") == "capture_result":
                import base64
                data_url = message.get("data", "")
                if data_url and "base64," in data_url:
                    try:
                        header, encoded = data_url.split(",", 1)
                        img_data = base64.b64decode(encoded)
                        
                        shot_path = Path(os.environ.get('TEMP', '')) / 'zyron_tab_screenshot.png'
                        with open(shot_path, 'wb') as f:
                            f.write(img_data)
                            
                        # Signal success? Optional.
                    except Exception as e:
                        # Log error
                        pass
            
            # Action: Navigation Result
            elif message.get("action") == "navigation_result":
                # Save the result from the content script to a file
                nav_path = Path(os.environ.get('TEMP', '')) / 'zyron_nav_result.json'
                try:
                    with open(nav_path, 'w') as f:
                        json.dump(message.get("data", {}), f)
                except Exception as e:
                    send_message({"status": "error", "message": str(e)})

            else:
                send_message({"status": "unknown_action", "received": message})
                
    except Exception as e:
        # We can't easily log to a console, so we might want to log to a file
        log_path = Path(os.environ.get('TEMP', '')) / 'zyron_native_host_error.log'
        with open(log_path, 'a') as f:
            f.write(f"Error: {str(e)}\n")

if __name__ == "__main__":
    main()
