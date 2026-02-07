import json
import os

MEMORY_FILE = "long_term_memory.json"


short_term = {
    "last_app_opened": None,
    "last_browser_used": "default",
    "last_focused_tab": None,
    "last_file_path": None,
    "last_action_type": None
}

def load_long_term():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {} 
    return {}

def save_long_term(key, value):
    data = load_long_term()
    data[key] = value
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def update_context(action_type, target=None):
    short_term["last_action_type"] = action_type
    
    if action_type == "open_app":
        short_term["last_app_opened"] = target
    elif action_type == "open_url":
        short_term["last_browser_used"] = target
    elif action_type == "send_file" or action_type == "list_files":
        short_term["last_file_path"] = target
    elif action_type == "browser_interaction":
        short_term["last_focused_tab"] = target

def get_context_string():
    """Returns a summary of BOTH Short-Term and Long-Term memory."""
    long_term_data = load_long_term() 
    
    return f"""
    [CURRENT CONTEXT STATE]
    - KNOWN USER INFO: {long_term_data}
    - Last App Opened: {short_term['last_app_opened']}
    - Last Browser Used: {short_term['last_browser_used']}
    - Last Focused Tab: {short_term['last_focused_tab']}
    - Last File/Folder: {short_term['last_file_path']}
    """

def track_file_preference(file_type):
    """
    Track user's file type preferences based on successful file searches
    This helps prioritize certain file types in future searches
    
    Args:
        file_type: File extension (e.g., 'pdf', 'docx', 'xlsx')
    """
    try:
        data = load_long_term()
        
        # Initialize file preferences if not exists
        if "file_preferences" not in data:
            data["file_preferences"] = {
                "preferred_types": {},
                "total_searches": 0
            }
        
        # Increment count for this file type
        prefs = data["file_preferences"]
        if file_type not in prefs["preferred_types"]:
            prefs["preferred_types"][file_type] = 0
        
        prefs["preferred_types"][file_type] += 1
        prefs["total_searches"] += 1
        
        # Save updated preferences
        with open(MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"📊 Tracked file preference: {file_type} (total: {prefs['preferred_types'][file_type]})")
        
    except Exception as e:
        print(f"Error tracking file preference: {e}")

def get_preferred_file_types(limit=3):
    """
    Get user's most frequently accessed file types
    
    Args:
        limit: Maximum number of types to return
        
    Returns:
        List of file types sorted by frequency
    """
    try:
        data = load_long_term()
        
        if "file_preferences" not in data:
            return []
        
        prefs = data["file_preferences"]["preferred_types"]
        
        # Sort by count (descending)
        sorted_types = sorted(prefs.items(), key=lambda x: x[1], reverse=True)
        
        # Return top N types
        return [file_type for file_type, count in sorted_types[:limit]]
        
    except Exception as e:
        print(f"Error getting file preferences: {e}")
        return []