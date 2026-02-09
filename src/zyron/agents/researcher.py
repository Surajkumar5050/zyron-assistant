import time
import ollama
import os
import psutil
import requests
from datetime import datetime
from zyron.features.browser_control import navigate, read_page, scan_page, click_element, create_tab, close_tab
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5-coder:7b")

RESEARCH_SYSTEM_PROMPT = """
You are Zyron's Information Synthesis module.
Your goal is to extract a clear, concise, and factual answer to the USER QUERY from the provided PAGE CONTENT.

RULES:
1. **Be Exact**: If the answer is in the text (even if buried), extract it. 
2. **Contextual Awareness**: Look for dates, numbers, names, and snippets in search results.
3. **Handle Failure**: If you genuinely cannot find the answer, summarize what IS there rather than just saying "I couldn't find it".
4. **Natural Tone**: Avoid robotic phrases like "The provided content mentions". Just say the answer.
5. **Conciseness**: Keep it to one or two short sentences unless the user asked for a detailed explanation.
6. **Date/Time Priority**: If the User Query is about the current date, time, or day, ALWAYS use the **CURRENT DATE (Ground Truth)** provided. Ignore any dates in the search results that contradict it.
"""

def is_firefox_running():
    """Checks if any firefox.exe process is active."""
    for proc in psutil.process_iter(['name']):
        try:
            if "firefox" in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def clean_html(html):
    """Very basic HTML text extraction for requests fallback."""
    import re
    # Remove script and style elements
    text = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.DOTALL)
    # Remove all other tags
    text = re.sub(r'<.*?>', ' ', text)
    # Consolidate whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:8000] # Limit to 8k chars for LLM

def perform_research(query):
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    content = ""
    tab_id = None
    method = "None"

    print(f"🔍 Starting research for: '{query}'")

    # 1. Decide: Browser vs Headless
    if is_firefox_running():
        print("   → Firefox is running. Attempting Stealth Browser Bridge...")
        tab_id = create_tab(search_url, active=False)
        if tab_id:
            print(f"   → Created Stealth Tab (ID: {tab_id}). Waiting for load...")
            time.sleep(4) # Increased wait for slow devs
            result = read_page(tab_id=tab_id)
            if result and result.get("success"):
                content = result.get("content", "")
                method = "Stealth Browser (Firefox)"
                print("   ✅ Content extracted via Browser.")
            else:
                print(f"   ⚠️ Browser Read Failed: {result.get('error') if result else 'No result'}")
            close_tab(tab_id)
        else:
            print("   ⚠️ Failed to create tab. Native Host might not be registered.")
    
    # Fallback / Option B: Use Requests (Headless)
    if not content:
        print("   → Falling back to Headless Research (Requests)...")
        try:
            # Randomize UA slightly for better bypass
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                html = response.text
                if "unusual traffic" in html.lower() or "captcha" in html.lower():
                    print("   ❌ HEADLESS BLOCKED BY GOOGLE (CAPTCHA)")
                    return "⚠️ Stealth Research was blocked by Google security. Please open Firefox and try again (ensure the extension is active)."
                
                content = clean_html(html)
                method = "Headless Fallback (Requests)"
                print("   ✅ Content extracted via Headless.")
            else:
                print(f"   ❌ Headless Failed: Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Headless error: {e}")

    if not content:
        return "❌ I tried both browser and network research but couldn't get any results. Please check your internet or ensure Firefox is open with the Zyron extension."

    # 2. Analyze with LLM
    now = datetime.now().strftime("%A, %B %d, %Y")
    prompt = f"METHOD USED: {method}\nCURRENT DATE (Ground Truth): {now}\nUSER QUERY: {query}\n\nPAGE CONTENT (Extracted from Google Search):\n{content}"
    
    try:
        print(f"   → Synthesizing answer using {MODEL_NAME}...")
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {'role': 'system', 'content': RESEARCH_SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ],
            keep_alive=0
        )
        answer = response['message']['content']
        print("✅ Research synthesis complete.")
        return answer
    except Exception as e:
        print(f"❌ Synthesis error: {e}")
        return f"⚠️ I found information via {method} but had trouble processing it with {MODEL_NAME}. Check if the model is pulled correctly."

if __name__ == "__main__":
    print(perform_research("Who is CEO of OpenAI?"))
