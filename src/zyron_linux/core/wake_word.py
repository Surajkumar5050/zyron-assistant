import os
import json
import sounddevice as sd
import queue
import sys
from vosk import Model, KaldiRecognizer

class WakeWordEngine:
    def __init__(self, model_path="model"):
        if not os.path.exists(model_path):
            raise Exception(f"Vosk model not found at '{model_path}'. Please run download_model.py first.")
            
        print(f"⚡ Loading Wake Word Model ({model_path})...")
        # Surpress Vosk logs
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.audio_queue = queue.Queue()
        
        # Wake words to listen for (lower case)
        self.wake_words = ["pikachu", "pika", "hey pikachu"]
        print("✅ Offline Wake Word Engine Ready.")

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.audio_queue.put(bytes(indata))

    def listen(self):
        """
        Blocks until a wake word is detected.
        Returns the detected wake word.
        """
        print("\n👂 Waiting for 'Pikachu' (Offline)...")
        
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self._callback):
             while True:
                data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    
                    if any(word in text for word in self.wake_words):
                        print(f"⚡ Wake Word Detected: '{text}'")
                        return text

    def capture_command(self, timeout=5):
        """
        Listens for a command for a specific duration (timeout).
        Returns the transcribed text.
        """
        print("🎤 Command Mode: Speak now... (Offline)")
        full_text = []
        
        # Helper to stop after timeout
        import time
        start_time = time.time()
        
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self._callback):
             # Clear queue
             while not self.audio_queue.empty():
                 self.audio_queue.get()
                 
             while (time.time() - start_time) < timeout:
                if not self.audio_queue.empty():
                    data = self.audio_queue.get()
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "")
                        if text:
                            print(f"   -> '{text}'")
                            full_text.append(text)
                else:
                    sd.sleep(50) # Tiny sleep to prevent cpu hog
        
        # Get final bit
        final = json.loads(self.recognizer.FinalResult())
        if final.get("text"):
            full_text.append(final["text"])
            
        return " ".join(full_text)

    def capture_audio(self, timeout=5):
        """
        Captures raw audio for a specific duration.
        Returns (raw_bytes, sample_rate).
        Used for Hybrid Mode (sending this audio to Google).
        """
        print("🎤 Command Mode: Speak now... (Hybrid/SoundDevice)")
        frames = []
        
        import time
        start_time = time.time()
        
        with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                               channels=1, callback=self._callback):
             # Clear queue
             while not self.audio_queue.empty():
                 self.audio_queue.get()
                 
             while (time.time() - start_time) < timeout:
                if not self.audio_queue.empty():
                    data = self.audio_queue.get()
                    frames.append(data)
                else:
                    sd.sleep(50)
                    
        return b''.join(frames), 16000

if __name__ == "__main__":
    # Test run
    engine = WakeWordEngine()
    try:
        engine.listen()
    except KeyboardInterrupt:
        engine.cleanup()
