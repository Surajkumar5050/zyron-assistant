import time
from .core.voice import listen_for_command, take_user_input, speak
from .core.brain import process_command
from .agents.system import execute_command

# Import file tracker - it will auto-start when imported
import zyron_linux.features.files.tracker as file_tracker

def main():
    print("⚡ ZYRON ONLINE: Say 'Hey Pikachu' to start...")
    
    while True:
    
        if listen_for_command():
            
            user_query = take_user_input()
            
            if user_query:
               
                action_json = process_command(user_query)
                
               
                if action_json:
                   
                    response_text = execute_command(action_json)
                    
                   
                    if response_text and isinstance(response_text, str) and not response_text.endswith(".png"):
                        speak(response_text)
                    else:
                        speak("Done.")
                else:
                    speak("I am not sure how to do that yet.")
            
     
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚡ System shutting down.")
        # Stop file tracking on shutdown
        file_tracker.stop_tracking()
        