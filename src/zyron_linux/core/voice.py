import speech_recognition as sr
import pyttsx3

# Initialize
recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty('rate', 170)

# --- CONFIGURATION ---
try:
    # Indent everything inside the 'try' block
    from .wake_word import WakeWordEngine
    wake_engine = WakeWordEngine()
    HAS_OFFLINE_WAKE = True

except Exception as e:
    # This block runs only if the code above fails
    print(f"⚠️ Offline Wake Engine missing: {e}")
    HAS_OFFLINE_WAKE = False  # Set to False because it failed

# Load Offline Mode Config
import os
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"

# We accept variations because Google sometimes mishears "Pikachu"
WAKE_WORDS = ["pikachu", "pika", "peek a", "pick a", "picacho", "hey you"]

def speak(text):
    print(f"⚡ Zyron: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass

def listen_for_command():
    # Priority: Offline Wake Word
    if HAS_OFFLINE_WAKE:
        try:
            detected_word = wake_engine.listen()
            if detected_word:
                speak("Pika Pika!")
                return True
            return False
        except Exception as e:
            print(f"⚠️ Offline Wake Error: {e}")
            pass # Fallback to online

    # Fallback: Online Google Speech Recognition (Legacy)
    with sr.Microphone() as source:
        print("\n👂 Listening for 'Hey Pikachu' (Online)...", end="", flush=True)
        
        # Fast adjustment to avoid blocking you
        recognizer.adjust_for_ambient_noise(source, duration=0.2)
        
        try:
            # Listen
            audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)
            print(" Processing...", end="", flush=True)
            
            # Convert to text
            command = recognizer.recognize_google(audio).lower()
            
            # DEBUG: Print exactly what it heard
            print(f"\n   -> I heard: '{command}'")
            
            # Check if any wake word is in the command
            if any(word in command for word in WAKE_WORDS):
                speak("Pika Pika! I am listening.")
                return True
            else:
                return False
                
        except sr.WaitTimeoutError:
            return False
        except sr.UnknownValueError:
            # It heard sound but couldn't make words out of it
            return False
        except sr.RequestError:
            print("\n   -> Network Error")
            return False

def take_user_input():
    # Hybrid Mode: Wake Word (Vosk) -> Command (Google Online)
    # BYPASSING PyAudio: We rely on sounddevice (via wake_engine) to capture raw audio
    # and feed it manually into speech_recognition.
    
    if HAS_OFFLINE_WAKE:
        try:
            # 1. Capture Raw Audio using SoundDevice
            raw_audio, sample_rate = wake_engine.capture_audio(timeout=5)
            
            # 2. Convert to sr.AudioData
            audio_data = sr.AudioData(raw_audio, sample_rate, 2) # 2 bytes per sample (int16)
            
            # 3. SELECT MODE: Offline vs Online
            if OFFLINE_MODE:
                print("   -> Processing Offline (Vosk)...")
                query = wake_engine.capture_command(timeout=5)
                print(f"   -> Command received: {query}")
                return query
            else:
                # 3. Send to Google (Hybrid)
                print("   -> Sending to Google Cloud...")
                query = recognizer.recognize_google(audio_data).lower()
                print(f"   -> Command received: {query}")
                return query
            
        except sr.UnknownValueError:
            print("   -> Google didn't understand.")
            return None
        except Exception as e:
            print(f"⚠️ Hybrid Error: {e}")
            return None

    # Fallback to Online (Needs PyAudio - likely to fail if not installed)
    try:
        with sr.Microphone() as source:
            print("🎤 Command Mode: Speak now... (Online Legacy)")
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            audio = recognizer.listen(source, timeout=5)
            query = recognizer.recognize_google(audio).lower()
            return query
    except:
        return None

if __name__ == "__main__":
    while True:
        listen_for_command()