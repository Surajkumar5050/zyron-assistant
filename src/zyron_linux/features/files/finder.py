"""
File Finder Module for Zyron Desktop Assistant
Intelligent search engine that understands natural language time/type queries
Part 2 of Context-Aware File Finder
"""

import json
import os
from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher

# File to load activity logs from
FILE_ACTIVITY_LOG = "file_activity_log.json"


def load_file_activity_log():
    """Load file activity log from JSON"""
    if os.path.exists(FILE_ACTIVITY_LOG):
        try:
            with open(FILE_ACTIVITY_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading file activity log: {e}")
            return []
    return []


def parse_time_query(query_text: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Convert natural language time expressions to datetime range
    
    Args:
        query_text: Natural language time query
        
    Returns:
        Tuple of (start_datetime, end_datetime) or None if no time found
    """
    query_lower = query_text.lower()
    now = datetime.now()
    
    
    def start_of_day(dt):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    
    def end_of_day(dt):
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    
    time_match = re.search(r'(\d{1,2})[:.](\d{2})\s*(am|pm)?|(\d{1,2})\s*(am|pm)', query_lower)
    
    if time_match:
        try:
            is_pm = False
            hour = 0
            minute = 0
            
            if time_match.group(1): # Format 17.43 or 17:43
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                is_pm = time_match.group(3) == 'pm'
            else: # Format 5 pm
                hour = int(time_match.group(4))
                minute = 0
                is_pm = time_match.group(5) == 'pm'
            
            # Convert 12h to 24h
            if is_pm and hour < 12: 
                hour += 12
            if not is_pm and hour == 12 and (time_match.group(3) == 'am' or time_match.group(5) == 'am'):
                hour = 0
                
            # Assume "today" unless "yesterday" is mentioned
            target_day = now
            if "yesterday" in query_lower:
                target_day = now - timedelta(days=1)
                
            target_time = target_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Create a 30-minute window around the specific time
            return (target_time - timedelta(minutes=30), target_time + timedelta(minutes=30))
        except:
            pass

    # --- 2. EXISTING LOGIC: TODAY ---
    if "today" in query_lower:
        # Check for time of day modifiers
        if "morning" in query_lower or "this morning" in query_lower:
            start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        elif "afternoon" in query_lower or "this afternoon" in query_lower:
            start_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        elif "evening" in query_lower or "tonight" in query_lower or "night" in query_lower:
            start_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Whole day
            start_time = start_of_day(now)
            end_time = end_of_day(now)
        return (start_time, end_time)
    
    # YESTERDAY
    if "yesterday" in query_lower:
        yesterday = now - timedelta(days=1)
        
        if "morning" in query_lower or "yesterday morning" in query_lower:
            start_time = yesterday.replace(hour=6, minute=0, second=0, microsecond=0)
            end_time = yesterday.replace(hour=12, minute=0, second=0, microsecond=0)
        elif "afternoon" in query_lower or "yesterday afternoon" in query_lower:
            start_time = yesterday.replace(hour=12, minute=0, second=0, microsecond=0)
            end_time = yesterday.replace(hour=17, minute=0, second=0, microsecond=0)
        elif "evening" in query_lower or "night" in query_lower or "last night" in query_lower:
            start_time = yesterday.replace(hour=17, minute=0, second=0, microsecond=0)
            end_time = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            # Whole day
            start_time = start_of_day(yesterday)
            end_time = end_of_day(yesterday)
        return (start_time, end_time)
    
    # THIS MORNING/AFTERNOON/EVENING/NIGHT (without "today")
    if "this morning" in query_lower or ("morning" in query_lower and "yesterday" not in query_lower):
        start_time = now.replace(hour=6, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        return (start_time, end_time)
    
    if "this afternoon" in query_lower or ("afternoon" in query_lower and "yesterday" not in query_lower):
        start_time = now.replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        return (start_time, end_time)
    
    if "this evening" in query_lower or "tonight" in query_lower or ("evening" in query_lower and "yesterday" not in query_lower):
        start_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return (start_time, end_time)
    
    # X HOURS AGO
    hours_match = re.search(r'(\d+)\s*hour[s]?\s*ago', query_lower)
    if hours_match:
        hours = int(hours_match.group(1))
        target_time = now - timedelta(hours=hours)
        # ±30 minutes window
        start_time = target_time - timedelta(minutes=30)
        end_time = target_time + timedelta(minutes=30)
        return (start_time, end_time)
    
    # X MINUTES AGO
    minutes_match = re.search(r'(\d+)\s*minute[s]?\s*ago', query_lower)
    if minutes_match:
        minutes = int(minutes_match.group(1))
        target_time = now - timedelta(minutes=minutes)
        # ±5 minutes window
        start_time = target_time - timedelta(minutes=5)
        end_time = target_time + timedelta(minutes=5)
        return (start_time, end_time)
    
    # LAST WEEK
    if "last week" in query_lower:
        last_week_start = now - timedelta(days=7)
        start_time = start_of_day(last_week_start)
        end_time = end_of_day(now)
        return (start_time, end_time)
    
    # THIS WEEK
    if "this week" in query_lower:
        # Start from Monday
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        start_time = start_of_day(monday)
        end_time = end_of_day(now)
        return (start_time, end_time)
    
    # SPECIFIC WEEKDAY (Monday, Tuesday, etc.)
    weekdays = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in query_lower:
            # Check if it's "last Monday" or just "Monday"
            if "last" in query_lower or "previous" in query_lower:
                # Find the most recent occurrence of this weekday
                days_back = (now.weekday() - day_num) % 7
                if days_back == 0:
                    days_back = 7  # If today is Monday and they say "last Monday", go back 7 days
                target_day = now - timedelta(days=days_back)
            else:
                # This week's occurrence
                days_back = (now.weekday() - day_num) % 7
                target_day = now - timedelta(days=days_back)
            
            start_time = start_of_day(target_day)
            end_time = end_of_day(target_day)
            return (start_time, end_time)
    
    # RECENT / JUST NOW / JUST OPENED
    if any(word in query_lower for word in ["recent", "just now", "just opened", "just accessed", "moments ago"]):
        # Last 15 minutes
        start_time = now - timedelta(minutes=15)
        end_time = now
        return (start_time, end_time)
    
    # No specific time found - return None
    return None


def normalize_file_type(query_text: str) -> Optional[List[str]]:
    """
    Extract and normalize file types from natural language query
    
    Args:
        query_text: Natural language query
        
    Returns:
        List of file extensions to match, or None if no type specified
    """
    query_lower = query_text.lower()
    
    # File type mappings
    type_mappings = {
        # Documents
        'pdf': ['pdf'],
        'document': ['doc', 'docx', 'txt', 'odt', 'rtf', 'pdf'],
        'doc': ['doc', 'docx'],
        'word': ['doc', 'docx'],
        'text': ['txt', 'rtf'],
        
        # Spreadsheets
        'excel': ['xlsx', 'xls', 'csv'],
        'spreadsheet': ['xlsx', 'xls', 'csv', 'ods'],
        'csv': ['csv'],
        'xlsx': ['xlsx'],
        'xls': ['xls'],
        
        # Presentations
        'powerpoint': ['pptx', 'ppt'],
        'presentation': ['pptx', 'ppt', 'odp'],
        'ppt': ['ppt', 'pptx'],
        
        # Images
        'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
        'picture': ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
        'photo': ['jpg', 'jpeg', 'png'],
        'png': ['png'],
        'jpg': ['jpg', 'jpeg'],
        'jpeg': ['jpg', 'jpeg'],
        
        # Videos
        'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'],
        'mp4': ['mp4'],
        'movie': ['mp4', 'avi', 'mkv', 'mov'],
        
        # Audio
        'audio': ['mp3', 'wav', 'flac', 'aac', 'ogg'],
        'music': ['mp3', 'wav', 'flac', 'aac'],
        'mp3': ['mp3'],
        
        # Code
        'code': ['py', 'js', 'java', 'cpp', 'c', 'html', 'css', 'json', 'xml'],
        'python': ['py'],
        'javascript': ['js'],
        'html': ['html'],
        
        # Archives
        'zip': ['zip'],
        'archive': ['zip', 'rar', '7z', 'tar', 'gz'],
        'compressed': ['zip', 'rar', '7z'],
    }
    
    # Search for type mentions
    for file_type, extensions in type_mappings.items():
        if file_type in query_lower:
            return extensions
    
    # Check for direct extension mentions (e.g., ".pdf file")
    for ext in ['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'csv', 'ppt', 'pptx', 
                'jpg', 'jpeg', 'png', 'gif', 'mp4', 'mp3', 'zip']:
        if f".{ext}" in query_lower or f" {ext} " in query_lower:
            return [ext]
    
    return None


def extract_keyword(query_text: str) -> Optional[str]:
    """
    Extract potential filename keywords from query
    
    Args:
        query_text: Natural language query
        
    Returns:
        Keyword to search for in filenames, or None
    """
    query_lower = query_text.lower()
    
    # Remove common filler words and time expressions
    remove_words = [
        'find', 'get', 'give', 'send', 'show', 'that', 'the', 'file', 'document',
        'i', 'was', 'reading', 'working', 'on', 'opened', 'accessed', 'yesterday',
        'today', 'morning', 'afternoon', 'evening', 'night', 'last', 'this',
        'hours', 'ago', 'minutes', 'recent', 'just', 'pdf', 'excel', 'word',
        'image', 'video', 'audio', 'me', 'my', 'a', 'an', 'at', 'in'
    ]
    
    # Remove time strings (like "17.43") to prevent them being treated as keywords
    query_lower = re.sub(r'\d{1,2}[:.]\d{2}', '', query_lower)
    
    # Split into words
    words = query_lower.split()
    
    # Filter out common words
    meaningful_words = [word for word in words if word not in remove_words and len(word) > 2]
    
    # If we have remaining words, use the first one as keyword
    if meaningful_words:
        # Prefer the longest word as it's likely the project name
        return max(meaningful_words, key=len)
    
    return None


def calculate_relevance_score(entry: Dict, time_range: Optional[Tuple[datetime, datetime]], 
                              file_types: Optional[List[str]], keyword: Optional[str],
                              target_app: Optional[str] = None) -> float:
    """
    Calculate relevance score for a file entry
    Higher score = more relevant
    
    Args:
        entry: File activity log entry
        time_range: Optional time range filter
        file_types: Optional file type filter
        keyword: Optional keyword filter
        target_app: Optional app filter (e.g. "edge", "chrome")
        
    Returns:
        Relevance score (0-100)
    """
    score = 0.0
    
    try:
        entry_time = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
    except:
        return 0
        
    # 1. TIME SCORE (Crucial - Added Logic)
    if time_range:
        start_dt, end_dt = time_range
        if start_dt <= entry_time <= end_dt:
            score += 100  # Huge bonus for matching specific time
        else:
            # If user gave a specific time, strictly penalize files outside it
            # This prevents finding random files when a specific time was asked
            return 0 
            
    # 2. RECENCY SCORE (Base - Existing)
    hours_old = (datetime.now() - entry_time).total_seconds() / 3600
    if hours_old < 1: score += 40
    elif hours_old < 6: score += 35
    elif hours_old < 24: score += 30
    elif hours_old < 72: score += 20
    else: score += 10
    
    # Duration score (max 20 points)
    duration = entry.get('duration_seconds', 0)
    if duration > 300:  # >5 minutes
        score += 20
    elif duration > 60:  # >1 minute
        score += 15
    elif duration > 0:
        score += 10
    
    # 3. TYPE MATCH (Existing)
    if file_types and entry['file_type'] in file_types:
        score += 20
    elif file_types:
        score -= 20 # Penalty for wrong type
        
    # 4. NEW: APP MATCH
    if target_app:
        app_used = entry.get('app_used', '').lower()
        if target_app in app_used:
            score += 50
        else:
            score -= 20
    
    # 5. KEYWORD MATCH (Existing + Improved Fuzzy)
    if keyword:
        filename_lower = entry['file_name'].lower()
        if keyword in filename_lower:
            score += 40
        else:
            # Fuzzy match using SequenceMatcher
            match_ratio = SequenceMatcher(None, keyword, filename_lower).ratio()
            if match_ratio > 0.6:
                score += (match_ratio * 30)
    
    # --- FINAL CAP: Ensure score never exceeds 100 ---
    return min(score, 100.0)


def find_files(time_query: Optional[str] = None, file_type: Optional[str] = None, 
               keyword: Optional[str] = None, limit: int = 5) -> List[Dict]:
    """
    Main search function - finds files based on natural language query
    
    Args:
        time_query: Natural language time expression
        file_type: File type (will be normalized)
        keyword: Keyword to search in filename
        limit: Maximum number of results to return
        
    Returns:
        List of matching file entries with confidence scores
    """
    # Load activity log
    activity_log = load_file_activity_log()
    
    if not activity_log:
        return []
    
    # Parse time range
    time_range = None
    if time_query:
        time_range = parse_time_query(time_query)
    
    # Normalize file type
    file_types = None
    if file_type:
        file_types = normalize_file_type(file_type)
    
    # Filter and score results
    scored_results = []
    
    for entry in activity_log:
        # Calculate relevance score (Uses default None for target_app here)
        score = calculate_relevance_score(entry, time_range, file_types, keyword)
        
        if score > 0:
            result = entry.copy()
            result['confidence_score'] = score
            scored_results.append(result)
    
    # Sort by score (highest first)
    scored_results.sort(key=lambda x: x['confidence_score'], reverse=True)
    
    # Return top N results
    return scored_results[:limit]


def find_files_from_query(natural_query: str, limit: int = 5) -> List[Dict]:
    """
    Convenience function - extract all parameters from a single natural language query
    Updated to handle App detection as well.
    
    Args:
        natural_query: Full natural language query
        limit: Maximum results to return
        
    Returns:
        List of matching file entries
    """
    # Extract components
    time_range = parse_time_query(natural_query)
    file_types = normalize_file_type(natural_query)
    keyword = extract_keyword(natural_query)
    
    # NEW: Detect Target App from query
    target_app = None
    q_lower = natural_query.lower()
    if "edge" in q_lower: target_app = "edge"
    elif "chrome" in q_lower: target_app = "chrome"
    elif "brave" in q_lower: target_app = "brave"
    elif "firefox" in q_lower: target_app = "firefox"
    elif "code" in q_lower or "vscode" in q_lower: target_app = "code"
    elif "notepad" in q_lower: target_app = "notepad"
    
    # Load logs
    activity_log = load_file_activity_log()
    if not activity_log:
        return []
        
    scored_results = []
    
    for entry in activity_log:
        # Pass all extracted info to the score calculator
        score = calculate_relevance_score(entry, time_range, file_types, keyword, target_app)
        
        if score > 0:
            result = entry.copy()
            result['confidence_score'] = score
            scored_results.append(result)
            
    # Sort results
    scored_results.sort(key=lambda x: x['confidence_score'], reverse=True)
    return scored_results[:limit]


def format_search_results(results: List[Dict], include_paths: bool = True) -> str:
    """
    Format search results as readable text for display/Telegram
    
    Args:
        results: List of file entries from find_files()
        include_paths: Whether to include full file paths
        
    Returns:
        Formatted string for display
    """
    if not results:
        return "🔍 **FILE SEARCH RESULTS**\n\n❌ No matching files found.\n\nTry:\n• 'files opened today'\n• 'PDFs from yesterday'\n• 'recent documents'"
    
    lines = [f"🔍 **FILE SEARCH RESULTS** (Found {len(results)} match{'es' if len(results) > 1 else ''})\n"]
    
    for i, entry in enumerate(results, 1):
        file_name = entry['file_name']
        timestamp = entry['timestamp']
        app_used = entry['app_used']
        confidence = entry.get('confidence_score', 0)
        
        # Parse timestamp for readable format
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        time_str = dt.strftime('%I:%M %p')  # 3:45 PM
        date_str = dt.strftime('%b %d')      # Feb 03
        
        # Calculate how long ago
        hours_ago = (datetime.now() - dt).total_seconds() / 3600
        if hours_ago < 1:
            ago_str = "just now"
        elif hours_ago < 24:
            ago_str = f"{int(hours_ago)}h ago"
        else:
            days_ago = int(hours_ago / 24)
            ago_str = f"{days_ago}d ago"
        
        # Confidence emoji
        if confidence >= 90:
            conf_emoji = "🎯"
        elif confidence >= 60:
            conf_emoji = "✅"
        else:
            conf_emoji = "📄"
        
        lines.append(f"{i}. {conf_emoji} **{file_name}** ({int(confidence)}%)")
        lines.append(f"   📅 {date_str} at {time_str} ({ago_str})")
        lines.append(f"   📱 {app_used}")
        
        if include_paths:
            lines.append(f"   📂 `{entry['file_path']}`")
        
        lines.append("")  # Empty line between results
    
    return "\n".join(lines)


def get_file_path(results: List[Dict], index: int = 0) -> Optional[str]:
    """
    Get file path from search results by index
    
    Args:
        results: Search results from find_files()
        index: Index of result to get (0 = top result)
        
    Returns:
        File path or None if index out of range
    """
    if 0 <= index < len(results):
        return results[index]['file_path']
    return None


# ==================== TESTING FUNCTIONS ====================

def test_time_parser():
    """Test the time parsing function"""
    print("\n" + "="*80)
    print("TESTING TIME PARSER")
    print("="*80)
    
    test_queries = [
        "PDF yesterday afternoon",
        "Excel this morning",
        "image 2 hours ago",
        "document last Monday",
        "file from today",
        "that PDF I opened yesterday",
        "something from last week",
        "files from this morning",
        "video 30 minutes ago",
        "PDF at 17.43",
        "file opened at 5:30 pm"
    ]
    
    for query in test_queries:
        result = parse_time_query(query)
        if result:
            start, end = result
            print(f"\nQuery: '{query}'")
            print(f"  Start: {start.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  End:   {end.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"\nQuery: '{query}' - No time found")


def test_file_type_normalizer():
    """Test the file type normalization"""
    print("\n" + "="*80)
    print("TESTING FILE TYPE NORMALIZER")
    print("="*80)
    
    test_queries = [
        "that PDF file",
        "Excel sheet",
        "Word document",
        "image file",
        "video I watched",
        "music file",
        "Python code",
        "compressed file",
    ]
    
    for query in test_queries:
        result = normalize_file_type(query)
        print(f"\nQuery: '{query}'")
        print(f"  Types: {result}")


def test_search():
    """Test the complete search functionality"""
    print("\n" + "="*80)
    print("TESTING COMPLETE SEARCH")
    print("="*80)
    
    test_queries = [
        "PDF yesterday afternoon",
        "Excel this morning",
        "image 2 hours ago",
        "document last Monday",
        "recent files",
        "that test document",
        "page 2 pdf 17.43"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"QUERY: '{query}'")
        print('='*80)
        
        results = find_files_from_query(query, limit=3)
        print(format_search_results(results, include_paths=True))


if __name__ == "__main__":
    print("🔍 FILE FINDER MODULE - TESTING")
    print("="*80)
    
    # Run all tests
    test_time_parser()
    test_file_type_normalizer()
    test_search()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETE")
    print("="*80)