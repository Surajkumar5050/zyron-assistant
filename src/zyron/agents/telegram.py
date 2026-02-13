import logging
import asyncio
import os
import re # Support regex for better scoring
from dotenv import load_dotenv
from telegram import Update, constants, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from zyron.core.brain import process_command
from zyron.agents.system import execute_command, capture_webcam
import zyron.features.browser_control as browser_control
import zyron.core.memory as memory
import zyron.features.activity as activity_monitor
import zyron.features.clipboard as clipboard_monitor
import zyron.features.files.tracker as file_tracker
import zyron.features.focus_mode as focus_mode
import zyron.features.zombie_reaper as zombie_reaper
from zyron.utils.env_check import check_dependencies

# Run health check before anything else
check_dependencies()

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

ALLOWED_USERS = os.getenv("ALLOWED_TELEGRAM_USERNAME", "").split(",")
# Store chat ID in saved_media folder for persistence
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CHAT_ID_FILE = os.path.join(PROJECT_ROOT, "saved_media", "telegram_chat_id.txt")

def save_chat_id(chat_id):
    try:
        os.makedirs(os.path.dirname(CHAT_ID_FILE), exist_ok=True)
        with open(CHAT_ID_FILE, 'w') as f:
            f.write(str(chat_id))
    except Exception as e:
        print(f"⚠️ Failed to save Chat ID: {e}")

def load_chat_id():
    try:
        if os.path.exists(CHAT_ID_FILE):
            with open(CHAT_ID_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        return None

if not TOKEN:
    print("❌ Error: TELEGRAM_TOKEN not found in .env file.")
    exit()

if not ALLOWED_USERS or ALLOWED_USERS == ['']: # Check if it's empty or just an empty string from split
    print("⚠️ Warning: ALLOWED_TELEGRAM_USERNAME not found in .env file. Bot will be open to everyone!")
    ALLOWED_USERS = []
else:
    ALLOWED_USERS = [u.strip() for u in ALLOWED_USERS if u.strip()]
    print(f"🔒 Security: Only accepting commands from @{', '.join(ALLOWED_USERS)}")

CAMERA_ACTIVE = False

# Security Decorator
from functools import wraps

def auth_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or (ALLOWED_USERS and user.username not in ALLOWED_USERS):
            print(f"⛔ Unauthorized access attempt from: @{user.username if user else 'Unknown'} (ID: {user.id if user else 'Unknown'})")
            if update.message:
                await update.message.reply_text("⛔ Unauthorized access.")
            elif update.callback_query:
                await update.callback_query.answer("⛔ Unauthorized access.", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

CAMERA_ACTIVE = False

# FIXED: Changed level to WARNING to stop the console spam
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

def get_main_keyboard():
    # Main control keyboard
    keyboard = [
        [KeyboardButton("/screenshot"), KeyboardButton("/camera_on"), KeyboardButton("/camera_off")],
        [KeyboardButton("🚨 PANIC")],
        [KeyboardButton("/sleep"), KeyboardButton("/restart"), KeyboardButton("/shutdown")],
        [KeyboardButton("/batterypercentage"), KeyboardButton("/systemhealth")],
        [KeyboardButton("/location"), KeyboardButton("/recordaudio")],
        [KeyboardButton("/clear_bin"), KeyboardButton("/storage")], 
        [KeyboardButton("/activities"), KeyboardButton("/copied_texts")],
        [KeyboardButton("/media"), KeyboardButton("/focus_mode_on"), KeyboardButton("/blacklist")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def safe_send_action(bot, chat_id, action):
    """Safely send chat action (typing/uploading) without crashing on timeout"""
    try:
        await bot.send_chat_action(chat_id=chat_id, action=action)
    except Exception as e:
        print(f"⚠️ Network Warning: Could not send chat action: {e}")

@auth_required
async def handle_clipboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks for clipboard items"""
    query = update.callback_query
    await query.answer()
    
    # Extract the clipboard index from callback data (format: "copy_0", "copy_1", etc.)
    try:
        _, index = query.data.split("_")
        index = int(index)
        
        # Get the clipboard item from the monitor
        item = clipboard_monitor.get_clipboard_item(index)
        
        if item:
            # Copy to user's clipboard by sending as code block (user can tap to copy)
            text = item['text']
            timestamp = item['timestamp']
            
            # Send the text with formatting
            await query.message.reply_text(
                f"📋 **Copied Text #{index + 1}**\n"
                f"🕐 {timestamp}\n\n"
                f"```\n{text}\n```\n\n"
                f"✅ _Tap the code block above to copy to your clipboard_",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        else:
            await query.message.reply_text("❌ Clipboard item not found.", reply_markup=get_main_keyboard())
            
    except Exception as e:
        print(f"Error handling clipboard callback: {e}")
    except Exception as e:
        print(f"Error handling clipboard callback: {e}")
        await query.message.reply_text(f"❌ Error: {e}", reply_markup=get_main_keyboard())

async def zombie_alert_callback(bot, chat_id, zombie_list):
    """
    Called by the reaper thread when zombies are found.
    Sends a formatted message to Telegram with actions.
    """
    if not zombie_list: return

    for z in zombie_list:
        pid = z['pid']
        name = z['name']
        ram = z['ram_mb']
        idle = z['idle_time_str']

        # Create interactive keyboard
        keyboard = [
            [
                InlineKeyboardButton("🪓 Kill Process", callback_data=f"zkill_{pid}"),
                InlineKeyboardButton("🛡️ Whitelist", callback_data=f"zallow_{name}")
            ],
            [InlineKeyboardButton("⏳ Ignore for 1h", callback_data=f"zignore_{pid}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"🧟 **Zombie Process Detected!**\n\n"
            f"**App:** `{name}`\n"
            f"**Memory:** {ram} MB\n"
            f"**Idle Time:** {idle}\n\n"
            f"This process is consuming resources but hasn't been used in hours. What should I do?"
        )
        
        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown', reply_markup=reply_markup)
        except Exception as e:
            print(f"⚠️ Failed to send Zombie Alert: {e}")

@auth_required
async def handle_zombie_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks on Zombie Alerts."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, target = data.split("_", 1)
    
    if action == "zkill":
        # Kill Process
        try:
            pid = int(target)
            result = zombie_reaper.kill_process(pid)
            await query.edit_message_text(f"{result}\n\n_Memory reclaimed!_ 🧠", parse_mode='Markdown')
        except ValueError:
            await query.edit_message_text("❌ Invalid Process ID.")

    elif action == "zallow":
        # Whitelist
        result = zombie_reaper.add_to_whitelist(target)
        await query.edit_message_text(f"{result}\n\n_I won't alert you about this app again._", parse_mode='Markdown')

    elif action == "zignore":
        # Ignore (Just delete message for now, logic later)
        await query.edit_message_text("⏳ Ignored for now.")


@auth_required
async def handle_media_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks on Media Controller."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Importing system--functions
    from zyron.agents.system import control_media, set_volume
    from telegram.error import BadRequest
    
    # Handle media playback controls
    if data.startswith("media_"):
        action = data.replace("media_", "")
        
        # Mapping to actual media actions
        action_map = {
            "prev": "prevtrack",
            "play": "playpause",
            "next": "nexttrack"
        }
        
        media_action = action_map.get(action, action)
        result = control_media(media_action)
        
        # Update message with confirmation
        try:
            await query.edit_message_text(
                f"🎵 **Media Controller**\n\n✅ {result}",
                parse_mode='Markdown',
                reply_markup=query.message.reply_markup  # Keep the keyboard
            )
        except BadRequest:
            # Message content is the same, ignore this error
            pass
    
    # Volume controls handler
    elif data.startswith("vol_"):
        level_str = data.replace("vol_", "")
        
        # Smart mute toggle for vol_0
        if level_str == "0":
            from pycaw.pycaw import AudioUtilities
            
            # Check current volume to decide mute or unmute
            try:
                devices = AudioUtilities.GetSpeakers()
                volume = devices.EndpointVolume
                current_level = int(volume.GetMasterVolumeLevelScalar() * 100)
                
                if current_level > 0:
                    # Currently audible, so mute it
                    result = set_volume(0)
                    action_msg = "🔇 Muted"
                else:
                    # Currently muted, so unmute to 50%
                    result = set_volume(50)
                    action_msg = "🔊 Unmuted to 50%"
            except Exception as e:
                # Fallback to simple toggle
                result = control_media("volumemute")
                action_msg = "🔇 Toggled mute"
        else:
            # Regular volume setting
            level = int(level_str)
            result = set_volume(level)
            action_msg = f"🔊 Volume set to {level}%"
        
        # Updates message with confirmation
        try:
            await query.edit_message_text(
                f"🎵 **Media Controller**\n\n✅ {action_msg}",
                parse_mode='Markdown',
                reply_markup=query.message.reply_markup  # Keep the keyboard
            )
        except BadRequest:
            # Message content is the same, ignore this error
            pass


async def camera_monitor_loop(bot, chat_id):
    global CAMERA_ACTIVE
    try:
        await bot.send_message(chat_id, "🔴 Live Feed Started...")
    except: pass
    
    while CAMERA_ACTIVE:
        photo_path = capture_webcam()
        if photo_path and os.path.exists(photo_path):
            try:
                await bot.send_photo(chat_id, photo=open(photo_path, 'rb'))
            except Exception:
                pass # Ignore network errors during stream
        await asyncio.sleep(3) 
    
    try:
        await bot.send_message(chat_id, "⏹️ Camera Feed Stopped.")
    except: pass


@auth_required
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    save_chat_id(update.effective_chat.id) # Save for auto-start next time
    
    await update.message.reply_text(
        f"⚡ **Zyron Online!**\nHello {user}. Use the buttons below.",
        reply_markup=get_main_keyboard()
    )
    
    # Start the Reaper!
    start_reaper_task(context.bot, update.effective_chat.id)

def start_reaper_task(bot, chat_id):
    """Helper to start the reaper with a specific bot/chat context"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        print("⚠️ Could not get running loop for Reaper.")
        return

    def reaper_bridge(zombies):
        asyncio.run_coroutine_threadsafe(
            zombie_alert_callback(bot, chat_id, zombies),
            loop
        )
    
    zombie_reaper.start_reaper(callback_func=reaper_bridge)
    print("🧟 Zombie Reaper attached to Telegram.")

@auth_required
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CAMERA_ACTIVE
    user_text = update.message.text
    sender = update.message.from_user.username
    chat_id = update.effective_chat.id
    lower_text = user_text.lower()
    
    print(f"\n📩 Message from @{sender}: {user_text}")

    # 1. Safe "Typing" Indicator (Won't crash if internet lags)
    await safe_send_action(context.bot, chat_id, constants.ChatAction.TYPING)

    # Pre-process common commands
    command_json = None
    
    if "/battery" in lower_text or "battery" in lower_text:
        command_json = {"action": "check_battery"}
    elif "/systemhealth" in lower_text or "system health" in lower_text:
        command_json = {"action": "check_health"}
    elif ("/screenshot" in lower_text or "screenshot" in lower_text) and not ("tab" in lower_text or "browser" in lower_text):
        command_json = {"action": "take_screenshot"}
    elif "/sleep" in lower_text:
        command_json = {"action": "system_sleep"}
    elif "/shutdown" in lower_text or "shutdown" in lower_text:
        command_json = {"action": "shutdown_pc"}
    elif "/restart" in lower_text or "restart" in lower_text:
        command_json = {"action": "restart_pc"}
    elif "/panic" in lower_text or "🚨 panic" in lower_text:
        command_json = {"action": "system_panic"}
    elif "/camera_on" in lower_text:
        command_json = {"action": "camera_stream", "value": "on"}
    elif "/camera_off" in lower_text:
        command_json = {"action": "camera_stream", "value": "off"}
    elif "/recordaudio" in lower_text:
        parts = lower_text.split()
        if len(parts) > 1:
            arg = parts[1]
            try:
                duration = 10
                if arg.endswith('m'):
                    duration = int(arg[:-1]) * 60
                elif arg.endswith('s'):
                    duration = int(arg[:-1])
                else:
                    duration = int(arg)
                
                # Cap duration check (Max 1 hour)
                if duration > 3600: 
                    duration = 3600
                    await update.message.reply_text("⚠️ Duration capped at 1 hour.")

                command_json = {"action": "record_audio", "duration": duration}
            except ValueError:
                await update.message.reply_text("❌ Invalid format. try `/recordaudio 10s` or `/recordaudio 1m`.", reply_markup=get_main_keyboard())
                return
        else:
            await update.message.reply_text(
                "🎙️ **Audio Recording**\n\nPlease specify your desired duration. For example:\n• `/recordaudio 10s` (for 10 seconds)\n• `/recordaudio 2m` (for 2 minutes)\n\n*Maximum duration is 1 hour.*", 
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
            return
            
    elif "/location" in lower_text or any(x in lower_text for x in ["my location", "where am i", "laptop location", "where is my laptop", "find location"]):
        command_json = {"action": "get_location"}
    # --- EXISTING BUTTON TRIGGERS ---
    elif "/clear_bin" in lower_text or "clear bin" in lower_text:
        command_json = {"action": "clear_recycle_bin"}
    elif "/storage" in lower_text or "check storage" in lower_text:
        command_json = {"action": "check_storage"}
    elif "/activities" in lower_text or "activities" in lower_text:
        command_json = {"action": "get_activities"}
    
    # --- MEDIA CONTROLLER ---
    elif "/media" in lower_text:
        # Send inline keyboard for media controls
        keyboard = [
            [
                InlineKeyboardButton("⏮️ Prev", callback_data="media_prev"),
                InlineKeyboardButton("⏯️ Play/Pause", callback_data="media_play"),
                InlineKeyboardButton("⏭️ Next", callback_data="media_next")
            ],
            [
                InlineKeyboardButton("🔇 Mute", callback_data="vol_0"),
                InlineKeyboardButton("🔉 30%", callback_data="vol_30"),
                InlineKeyboardButton("🔉 60%", callback_data="vol_60"),
                InlineKeyboardButton("🔊 100%", callback_data="vol_100")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎵 **Media Controller**\n\nControl your media playback and volume:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return  # Exit early since we handled this
    
    # --- NEW CLIPBOARD TRIGGER ---
    elif "/copied_texts" in lower_text or any(x in lower_text for x in ["copied texts", "clipboard history", "what did i copy", "show copied"]):
        command_json = {"action": "get_clipboard_history"}

    # --- FEATURE #11: FOCUS MODE COMMANDS ---
    elif "/focus_mode_on" in lower_text or "focus on" in lower_text:
        command_json = {"action": "focus_mode", "sub_action": "on"}
    elif "/focus_mode_off" in lower_text or "focus off" in lower_text:
        command_json = {"action": "focus_mode", "sub_action": "off"}
    elif "/blacklist" in lower_text:
        # Check for arguments: /blacklist add steam discord
        parts = lower_text.split()
        if len(parts) >= 3:
            sub_action = parts[1]
            items = parts[2:] # Capture all remaining parts
            if sub_action == "add":
                command_json = {"action": "focus_mode", "sub_action": "add", "items": items}
            elif sub_action == "remove":
                command_json = {"action": "focus_mode", "sub_action": "remove", "items": items}
            else:
                command_json = {"action": "focus_mode", "sub_action": "status"}
        else:
            command_json = {"action": "focus_mode", "sub_action": "status"}

    # --- NAVIGATION AGENT TRIGGERS ---
    elif "/read" in lower_text or "read page" in lower_text:
        command_json = {"action": "browser_nav", "sub_action": "read"}
        
    elif "/scan" in lower_text:
        command_json = {"action": "browser_nav", "sub_action": "scan"}
        
    elif "/scroll" in lower_text or "scroll down" in lower_text:
        direction = "down"
        if "up" in lower_text: direction = "up"
        if "top" in lower_text: direction = "top"
        if "bottom" in lower_text: direction = "bottom"
        command_json = {"action": "browser_nav", "sub_action": "scroll", "direction": direction}
        
    elif "/type" in lower_text:
        try:
            parts = user_text.split(" ", 2)
            if len(parts) >= 3:
                command_json = {"action": "browser_nav", "sub_action": "type", "selector": parts[1], "text": parts[2]}
        except: pass
        
    elif "/click" in lower_text:
        try:
            parts = user_text.split(" ", 1)
            if len(parts) >= 2:
                command_json = {"action": "browser_nav", "sub_action": "click", "selector": parts[1]}
        except: pass

    # Show processing message (with error handling)
    status_msg = None
    try:
        feedback_text = "⚡ Thinking..."
        
        # Specific feedback for recording
        if command_json and command_json.get('action') == "record_audio":
            d = command_json.get('duration', 10)
            if d < 60:
                feedback_text = f"🎙️ Recording for {d} seconds..."
            else:
                feedback_text = f"🎙️ Recording for {d//60} mins..."

        status_msg = await update.message.reply_text(feedback_text, reply_markup=get_main_keyboard())
    except Exception:
        pass # If we can't send "Thinking", just continue

    if not command_json:
        loop = asyncio.get_running_loop()
        try:
            # Use AI to process command - now returns list
            command_list = await loop.run_in_executor(None, process_command, user_text)
        except Exception as e:
            # If AI fails, send error
            if status_msg: await status_msg.delete()
            await update.message.reply_text(f"❌ Brain Error: {e}", reply_markup=get_main_keyboard())
            return
    else:
        # Normalize pre-parsed command to list
        command_list = [command_json] if isinstance(command_json, dict) else command_json

    # --- MULTI-COMMAND EXECUTION LOOP ---
    total_commands = len(command_list) if command_list else 0
    
    for cmd_index, command_json in enumerate(command_list or []):
        # Show step indicator for multi-command chains
        if total_commands > 1:
            step_msg = f"⚙️ Step {cmd_index + 1}/{total_commands}: {command_json.get('action', 'Processing')}..."
            try:
                if status_msg:
                    await status_msg.edit_text(step_msg)
                else:
                    status_msg = await update.message.reply_text(step_msg, reply_markup=get_main_keyboard())
            except:
                pass

        action = command_json.get('action')
        query = user_text.lower() # Ensure 'query' is always defined for matching logic
        
        # --- BROWSER INTERACTION AUTO-CORRECTION ---
        # If LLM sends 'browser_control' but query contains interactive verbs (click/type),
        # re-route to 'browser_nav' for better page interaction.
        if action == "browser_control":
            query = command_json.get("query", "").lower()
            # Comprehensive list of junk words to strip from targets
            junk_words = [
                "click", "type", "press", "search", "scroll", "read", "first", "there", 
                "the", "on", "to", "at", "of", "a", "an", "in", "with", "is", "into",
                "and", "or", "button", "link", "element", "item", "select", "go",
                "then", "for", "open", "opn", "show", "me", "find", "search"
            ]
            is_interaction = any(v in query for v in junk_words) or "target" in command_json
            
            if is_interaction:
                 print(f"🔄 Auto-Correcting: Redirecting Browser Control ({query}) to Browser Nav")
                 action = "browser_nav"
                 command_json["sub_action"] = "click" if "click" in query else "scan"
                 # Clean up the target using token-based filtering (e.g., "click on first video" -> "video")
                 target_tokens = query.split()
                 clean_tokens = [t for t in target_tokens if t not in junk_words]
                 command_json["target"] = " ".join(clean_tokens).strip()
                 print(f"🎯 Cleaned target for nav: '{command_json['target']}'")
        
        # --- ACTIVITIES HANDLER (Supports splitting messages) ---
        if action == "get_activities":
            if status_msg: await status_msg.delete()
            # 1. Get raw data from muscles (which calls activity_monitor)
            raw_data = execute_command(command_json)
            
            if raw_data:
                # 2. Format the data using the helper function in activity_monitor
                formatted_message = activity_monitor.format_activities_text(raw_data)
                
                # 3. Send the formatted text - handle both single message and multiple messages
                try:
                    if isinstance(formatted_message, list):
                        # Multiple messages - send each one
                        for i, msg in enumerate(formatted_message):
                            await update.message.reply_text(
                                msg, 
                                parse_mode='Markdown', 
                                reply_markup=get_main_keyboard() if i == len(formatted_message) - 1 else None
                            )
                            # Small delay between messages to avoid rate limiting
                            if i < len(formatted_message) - 1:
                                await asyncio.sleep(0.5)
                    else:
                        # Single message
                        await update.message.reply_text(formatted_message, parse_mode='Markdown', reply_markup=get_main_keyboard())
                except Exception as e:
                    await update.message.reply_text(f"❌ Error displaying activities: {e}", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text("❌ Could not fetch activities.", reply_markup=get_main_keyboard())

        # --- NEW: CLIPBOARD HISTORY HANDLER ---
        elif action == "get_clipboard_history":
            if status_msg: await status_msg.delete()
            
            # Get clipboard history from muscles -> clipboard_monitor
            clipboard_items = execute_command(command_json)
            
            if clipboard_items and len(clipboard_items) > 0:
                # Create inline keyboard with copy buttons for each item
                keyboard = []
                
                # Show up to 20 items
                for i, item in enumerate(clipboard_items[:20]):
                    text = item['text']
                    # Truncate text for button label
                    if len(text) > 50:
                        button_text = text[:47] + "..."
                    else:
                        button_text = text
                    
                    # Replace newlines for button display
                    button_text = button_text.replace('\n', ' ').replace('\r', '')
                    
                    # Create button with callback data
                    keyboard.append([InlineKeyboardButton(
                        f"{i+1}. {button_text}",
                        callback_data=f"copy_{i}"
                    )])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send message with buttons
                await update.message.reply_text(
                    f"📋 **CLIPBOARD HISTORY**\n\n"
                    f"Found {len(clipboard_items)} copied items.\n"
                    f"Tap any item below to view and copy it:\n",
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    "📋 **CLIPBOARD HISTORY**\n\n"
                    "❌ No copied texts found yet.\n"
                    "Copy some text on your desktop and try again!",
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard()
                )

        # --- LOCATION TRACKING ---
        elif action == "get_location":
            if status_msg: await status_msg.delete()
            loader = await update.message.reply_text("🔍 Checking multiple location sources...", reply_markup=get_main_keyboard())
            
            # Get location data
            location_data = execute_command(command_json)
            
            if location_data:
                # Format location message
                location_text = f"""🌍 **Laptop Location**

🌆 **Location:** {location_data['city']}, {location_data['region']}
🏳️ **Country:** {location_data['country']} ({location_data['country_code']})
📮 **Postal Code:** {location_data['postal']}
🌐 **IP Address:** {location_data['ip']}
📡 **ISP:** {location_data['org']}
🕐 **Timezone:** {location_data['timezone']}

📌 **Coordinates:**
Latitude: {location_data['latitude']}
Longitude: {location_data['longitude']}

🔍 **Data Source:** {location_data['source']}

🗺️ [**Open in Google Maps**]({location_data['maps_url']})
"""
                
                # Add comparison if multiple sources were checked
                if location_data.get('comparison'):
                    location_text += f"\n\n⚠️ **Location Comparison:**\n{location_data['comparison']}\n\n_Note: IP-based location may be 50-200km from your actual position. This shows your ISP's server location._"
                
                await loader.delete()
                
                # Send location as text
                await update.message.reply_text(
                    location_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=False,
                    reply_markup=get_main_keyboard()
                )
                
                # Send location on map (Telegram native location)
                try:
                    await update.message.reply_location(
                        latitude=location_data['latitude'],
                        longitude=location_data['longitude'],
                        reply_markup=get_main_keyboard()
                    )
                except Exception as e:
                    print(f"Could not send map location: {e}")
                    
            else:
                await loader.edit_text("❌ Failed to get location. Check internet connection.", reply_markup=get_main_keyboard())
        
        # --- BATTERY CHECK ---
        elif action == "check_battery":
            status = execute_command(command_json)
            if status_msg: await status_msg.delete()
            await update.message.reply_text(f"🔋 {status}", reply_markup=get_main_keyboard())
            
        elif action == "check_health":
            report = execute_command(command_json)
            if status_msg: await status_msg.delete()
            await update.message.reply_text(report, reply_markup=get_main_keyboard())
            
        elif action == "take_screenshot":
            # Screenshot
            if status_msg: await status_msg.delete()
            loader = await update.message.reply_text("📸 Capture...", reply_markup=get_main_keyboard())
            path = execute_command(command_json)
            if path:
                try:
                    await update.message.reply_photo(photo=open(path, 'rb'))
                    await loader.delete()
                except Exception as e:
                    await loader.edit_text(f"❌ Upload Failed: {e}")
            else:
                await loader.edit_text("❌ Screenshot failed.")
        elif action == "shutdown_pc":
            if status_msg: await status_msg.delete()
            await update.message.reply_text("🔌 **Shutting down immediately.**\nGoodbye!", parse_mode='Markdown')
            # Small delay to ensure message sends before OS kills the network
            await asyncio.sleep(1) 
            execute_command(command_json)

        elif action == "restart_pc":
            if status_msg: await status_msg.delete()
            await update.message.reply_text("🔄 **Restarting system...**\nI'll be back online shortly.", parse_mode='Markdown')
            await asyncio.sleep(1)
            execute_command(command_json)  
        
        elif action == "system_panic":
            if status_msg: await status_msg.delete()
            await update.message.reply_text("🔒 System Locked & Secured.")
            await asyncio.sleep(0.5)  # Brief delay to ensure message sends
            execute_command(command_json)
        
        elif action == "system_sleep":
            if status_msg: await status_msg.delete()
            await update.message.reply_text("💤 Goodnight.", reply_markup=get_main_keyboard())
            execute_command(command_json)

        elif action == "camera_stream":
            val = command_json.get("value")
            if status_msg: await status_msg.delete()
            if val == "on":
                if not CAMERA_ACTIVE:
                    CAMERA_ACTIVE = True
                    asyncio.create_task(camera_monitor_loop(context.bot, chat_id))
            else:
                CAMERA_ACTIVE = False
                await update.message.reply_text("🛑 Stopping Camera...", reply_markup=get_main_keyboard())

        elif action == "record_audio":
            if status_msg: await status_msg.delete()
            duration = command_json.get("duration", 10)
            
            # Nice duration format
            if duration < 60:
                dur_str = f"{duration} seconds"
            else:
                dur_str = f"{duration//60} mins"

            loader = await update.message.reply_text(f"🎙️ Recording audio for {dur_str}...", reply_markup=get_main_keyboard())
            
            # Execute audio recording in executor to avoid blocking
            loop = asyncio.get_running_loop()
            audio_path = await loop.run_in_executor(None, execute_command, command_json)
            
            if audio_path and os.path.exists(audio_path):
                try:
                    await loader.edit_text("✅ Recording complete. Sending...")
                except:
                    pass  # Ignore if message already deleted
                
                # Send the audio file
                try:
                    await update.message.reply_audio(audio=open(audio_path, 'rb'), caption=f"🎵 Recorded Audio ({dur_str})")
                except Exception as e:
                     await update.message.reply_text(f"❌ Upload Failed: {e}")
            else:
                try:
                    await loader.edit_text("❌ Audio recording failed.")
                except:
                    await update.message.reply_text("❌ Audio recording failed.", reply_markup=get_main_keyboard())

        elif action == "general_chat":
            response = command_json.get('response', "...")
            # AI chat response
            if status_msg: await status_msg.delete()
            await update.message.reply_text(f"💬 {response}", reply_markup=get_main_keyboard())

        # --- RECYCLE BIN & STORAGE HANDLERS ---
        elif action == "clear_recycle_bin":
            result = execute_command(command_json)
            if status_msg: await status_msg.delete()
            await update.message.reply_text(f"🗑️ {result}", reply_markup=get_main_keyboard())

        elif action == "check_storage":
            result = execute_command(command_json)
            if status_msg: await status_msg.delete()
            await update.message.reply_text(result, parse_mode='Markdown', reply_markup=get_main_keyboard())
        # --------------------------------------

        # --- File / App Handling ---
        elif action == "list_files":
            if status_msg: await status_msg.delete()
            raw_path = command_json.get('path')
            if "desktop" in raw_path.lower(): raw_path = os.path.join(os.path.expanduser("~"), "Desktop")
            elif "downloads" in raw_path.lower(): raw_path = os.path.join(os.path.expanduser("~"), "Downloads")
            
            if os.path.exists(raw_path):
                try:
                    files = os.listdir(raw_path)[:20]
                    text = "\n".join([f"📹 {f}" for f in files])
                    await update.message.reply_text(f"📂 **Files:**\n{text}", reply_markup=get_main_keyboard())
                except: 
                    await update.message.reply_text("❌ Failed to read folder.", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text("❌ Folder not found.", reply_markup=get_main_keyboard())

        elif action == "send_file":
             if status_msg: await status_msg.delete()
             raw_path = command_json.get('path')
             if os.path.exists(raw_path):
                 try:
                     await update.message.reply_text("📤 Uploading...", reply_markup=get_main_keyboard())
                     await update.message.reply_document(open(raw_path, 'rb'))
                 except Exception as e:
                     print(f"Upload Error: {e}")
                     await update.message.reply_text("❌ Error: File upload timed out or failed.", reply_markup=get_main_keyboard())
             else:
                 await update.message.reply_text("❌ File not found.", reply_markup=get_main_keyboard())

        # --- FIND FILE HANDLER (Context-Aware File Finder) ---
        elif action == "find_file":
            if status_msg: await status_msg.delete()
            
            # Show searching message
            search_msg = await update.message.reply_text("🔍 Searching for file...", reply_markup=get_main_keyboard())
            
            # Execute file search in background thread
            loop = asyncio.get_running_loop()
            try:
                search_result = await loop.run_in_executor(None, execute_command, command_json)
                
                if not search_result:
                    await search_msg.edit_text("❌ File search failed.", reply_markup=get_main_keyboard())
                    return
                
                status = search_result.get("status")
                
                if status == "found":
                    # File found!
                    file_path = search_result.get("file_path")
                    file_name = search_result.get("file_name")
                    file_size_mb = search_result.get("file_size_mb", 0)
                    confidence = search_result.get("confidence", 0)
                    
                    # --- NEW METADATA DISPLAY ---
                    app_used = search_result.get("app_used", "Unknown App")
                    timestamp = search_result.get("timestamp", "Unknown Time")
                    duration = search_result.get("duration", 0)
                    
                    # Format duration string
                    if duration < 60:
                        duration_str = f"{duration}s"
                    else:
                        m, s = divmod(duration, 60)
                        duration_str = f"{m}m {s}s"
                    
                    # Create Detailed Caption
                    caption_text = (
                        f"✅ **Found:** {file_name}\n"
                        f"📱 **App:** {app_used}\n"
                        f"📅 **Time:** {timestamp}\n"
                        f"⏱️ **Duration:** {duration_str}\n"
                        f"🎯 **Confidence:** {confidence}%"
                    )
                    # -----------------------------
                    
                    await search_msg.delete()
                    
                    # Send file size warning if large
                    size_warning = ""
                    if file_size_mb > 20:
                        size_warning = f"\n\n⚠️ _Large file: {file_size_mb:.1f} MB_"
                    
                    # Send loading message
                    upload_msg = await update.message.reply_text(
                        f"📤 Uploading: **{file_name}**{size_warning}",
                        parse_mode='Markdown',
                        reply_markup=get_main_keyboard()
                    )
                    
                    # Upload the file with new caption
                    try:
                        await update.message.reply_document(
                            document=open(file_path, 'rb'),
                            caption=caption_text,
                            parse_mode='Markdown',
                            reply_markup=get_main_keyboard()
                        )
                        await upload_msg.delete()
                        
                        # Update memory with successful file type preference
                        file_ext = os.path.splitext(file_name)[1].replace('.', '').lower()
                        memory.track_file_preference(file_ext)
                        
                    except Exception as e:
                        print(f"Upload Error: {e}")
                        await upload_msg.edit_text(f"❌ Upload failed: {e}", reply_markup=get_main_keyboard())
                
                elif status == "not_found":
                    # No files found
                    message = search_result.get("message", "No files found.")
                    await search_msg.edit_text(message, reply_markup=get_main_keyboard())
                
                elif status == "file_deleted":
                    # File was found but doesn't exist anymore
                    message = search_result.get("message", "File no longer exists.")
                    await search_msg.edit_text(message, reply_markup=get_main_keyboard())
                
                elif status == "too_large":
                    # File too large for Telegram
                    message = search_result.get("message", "File too large.")
                    await search_msg.edit_text(message, reply_markup=get_main_keyboard())
                
                else:
                    # Unknown status or error
                    message = search_result.get("message", "Search completed with unknown status.")
                    await search_msg.edit_text(message, reply_markup=get_main_keyboard())
                    
            except Exception as e:
                print(f"Find file error: {e}")
                await search_msg.edit_text(f"❌ Search error: {e}", reply_markup=get_main_keyboard())
        # ---------------------------------------------------------

        # --- FEATURE #11: FOCUS MODE HANDLERS ---
        elif action == "focus_mode":
            sub_action = command_json.get("sub_action")
            
            if sub_action == "on":
                result = focus_mode.start_focus_mode()
                await update.message.reply_text(result, reply_markup=get_main_keyboard(), parse_mode='Markdown')
                
            elif sub_action == "off":
                result = focus_mode.stop_focus_mode()
                await update.message.reply_text(result, reply_markup=get_main_keyboard(), parse_mode='Markdown')
                
            elif sub_action == "status":
                result = focus_mode.get_blacklist_status()
                await update.message.reply_text(result, reply_markup=get_main_keyboard(), parse_mode='Markdown')
                
            elif sub_action == "add":
                items = command_json.get("items")
                if items:
                    results = []
                    for item in items:
                        results.append(focus_mode.add_to_blacklist(item))
                    await update.message.reply_text("\n".join(results), reply_markup=get_main_keyboard())
                else:
                    await update.message.reply_text("❌ Please specify app(s) or site(s) to block.\nUsage: `/blacklist add spotify steam youtube.com`", reply_markup=get_main_keyboard())

            elif sub_action == "remove":
                items = command_json.get("items")
                if items:
                    result = focus_mode.remove_from_blacklist(items)
                    await update.message.reply_text(result, reply_markup=get_main_keyboard())
                else:
                    await update.message.reply_text("❌ Please specify item(s) to remove.", reply_markup=get_main_keyboard())
        # ----------------------------------------

        # --- BROWSER CONTROL (Smart Tab Management) ---
        elif action == "browser_control":
            if status_msg: await status_msg.delete()
            
            command = command_json.get("command") # close, mute, screenshot
            query = command_json.get("query", "").lower()
            
            # Proceed with standard Tab Management
            # 1. Get all open tabs
            tabs = activity_monitor.get_firefox_tabs()
            
            if not tabs:
                await update.message.reply_text("❌ No Firefox tabs found (or bridge not connected).", reply_markup=get_main_keyboard())
                return

            # 2. Tokenize the user query
            interaction_verbs = ["click", "type", "press", "search", "scroll", "read", "first", "there", "the"]
            stop_words = ["close", "mute", "unmute", "the", "tab", "window", "browser", "video", "music", "about", "play", "pause"] + interaction_verbs
            query_words = [w for w in query.split() if w not in stop_words and len(w) > 2]
            
            # --- FAILOVER TO STICKY TAB ---
            best_match = None
            highest_score = 0
            
            if not query_words and memory.short_term.get("last_focused_tab"):
                 print(f"🎯 Sticky Tab: Using last focused tab: {memory.short_term['last_focused_tab']}")
                 for tab in tabs:
                     if tab.get('title') == memory.short_term['last_focused_tab']:
                         best_match = tab
                         highest_score = 100
                         break
            
            if not best_match:
                if not query_words:
                     await update.message.reply_text("❓ Please specify which tab (e.g., 'Close YouTube').", reply_markup=get_main_keyboard())
                     return
                print(f"🔍 Searching tabs for keywords: {query_words}")
                for tab in tabs:
                    score = 0
                    title = tab.get('title', '').lower()
                    url = tab.get('url', '').lower()
                    for word in query_words:
                        if word in title: score += 2
                        elif word in url: score += 1
                    if " ".join(query_words) in title: score += 5
                    
                    print(f"   - Checking: {title[:20]}... Score: {score}")
                    if score > highest_score:
                        highest_score = score
                        best_match = tab
            
            # 4. Execute on best match if score is sufficient
            if best_match and highest_score > 0:
                tab_id = best_match.get('id')
                tab_title = best_match.get('title')
                memory.update_context("browser_interaction", tab_title)
                
                if tab_id:
                    if command == "close":
                        browser_control.close_tab(tab_id)
                        await update.message.reply_text(f"🗑️ Closed: **{best_match.get('title')}**", parse_mode='Markdown', reply_markup=get_main_keyboard())
                    elif command == "mute":
                        browser_control.mute_tab(tab_id, True)
                        await update.message.reply_text(f"🔇 Muted: **{best_match.get('title')}**", parse_mode='Markdown', reply_markup=get_main_keyboard())
                    elif command == "unmute":
                        browser_control.mute_tab(tab_id, False)
                        await update.message.reply_text(f"🔊 Unmuted: **{best_match.get('title')}**", parse_mode='Markdown', reply_markup=get_main_keyboard())
                    elif command in ["play", "pause"]:
                        await update.message.reply_text(f"🎬 Command {command} sent to **{tab_title}**", reply_markup=get_main_keyboard())
                    elif command == "screenshot":
                        window_id = best_match.get('windowId')
                        browser_control.capture_tab_with_window(tab_id, window_id)
                        loader = await update.message.reply_text("📸 Capturing tab...", reply_markup=get_main_keyboard())
                        shot_path = os.path.join(os.environ.get('TEMP', ''), 'zyron_tab_screenshot.png')
                        if os.path.exists(shot_path):
                            try: os.remove(shot_path)
                            except: pass
                        found = False
                        for _ in range(10):
                            if os.path.exists(shot_path):
                                found = True
                                break
                            await asyncio.sleep(0.5)
                        if found:
                            await update.message.reply_photo(photo=open(shot_path, 'rb'), caption=f"📸 **{best_match.get('title')}**")
                            await loader.delete()
                        else:
                            await loader.edit_text("❌ Screenshot timeout.")
                else:
                    await update.message.reply_text(f"❌ Found '**{best_match.get('title', 'Unknown')}**' but it has no ID.", reply_markup=get_main_keyboard())
                return
            else:
                 await update.message.reply_text(f"❌ No tab found matching your description.", reply_markup=get_main_keyboard())
                 return

        # --- NAVIGATION AGENT COMMANDS ---
        elif action == "browser_nav":
            try:
                if status_msg:
                    try: await status_msg.delete()
                    except: pass
                
                sub_action = command_json.get("sub_action")
                
                if sub_action == "read":
                    print("📖 Navigation Agent: Reading page...")
                    loader = await update.message.reply_text("📖 Reading page content...", reply_markup=get_main_keyboard())
                    
                    loop = asyncio.get_running_loop()
                    try:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, browser_control.read_page),
                            timeout=8.0
                        )
                    except asyncio.TimeoutError:
                        await loader.edit_text("❌ Read timeout. Native Host not responding.")
                        return

                    if result and result.get("success"):
                        title = result.get("title", "No Title")
                        url = result.get("url", "Unknown URL")
                        memory.update_context("browser_interaction", title) # Update Sticky Tab context
                        content = result.get("content", "")
                        
                        if len(content) > 3000:
                            preview = content[:1000] + "..."
                            msg_text = f"📄 {title}\n🔗 {url}\n\n{preview}\n\n(Content truncated)"
                        else:
                            msg_text = f"📄 {title}\n🔗 {url}\n\n{content}"
                            
                        try:
                            await loader.edit_text(msg_text, disable_web_page_preview=True)
                        except Exception as e:
                            import io
                            full_file_text = f"📄 {title}\n🔗 {url}\n\n{content}"
                            file_obj = io.BytesIO(full_file_text.encode('utf-8'))
                            file_obj.name = "page_content.txt"
                            await update.message.reply_document(document=file_obj, caption="📄 Page Content (Full)")
                    else:
                        err = result.get("error", "Unknown error") if result else "No data returned"
                        await loader.edit_text(f"❌ Read failed: {err}")

                elif sub_action == "scroll":
                    direction = command_json.get("direction", "down")
                    browser_control.scroll_page(direction)
                    try: await update.message.set_reaction(reaction="👇" if direction == "down" else "👆")
                    except: await update.message.reply_text(f"📜 Scrolled {direction}", reply_markup=get_main_keyboard())

                elif sub_action == "type":
                    target = command_json.get("target") or command_json.get("selector")
                    text = command_json.get("text")
                    
                    if target and text:
                        target_id = target
                        found_label = target
                        
                        if not str(target).isdigit():
                            loader = await update.message.reply_text(f"🔍 Finding input '{target}'...", reply_markup=get_main_keyboard())
                            
                            loop = asyncio.get_running_loop()
                            scan_result = await loop.run_in_executor(None, browser_control.scan_page)
                            
                            if scan_result and scan_result.get("success"):
                                elements = scan_result.get("elements", [])
                                input_elements = [el for el in elements if el['type'] in ['input', 'textarea']]
                                
                                best_match = None
                                best_score = 0
                                target_lower = target.lower()
                                
                                for el in input_elements:
                                    el_text = el['text'].lower()
                                    score = 0
                                    if el_text == target_lower: score = 100
                                    elif target_lower in el_text: score = 50
                                    elif el_text in target_lower: score = 30
                                    if score > best_score:
                                        best_score = score
                                        best_match = el
                                        
                                if best_match:
                                    target_id = str(best_match['id'])
                                    found_label = best_match['text']
                                    try: await loader.edit_text(f"🎯 Found input: **{found_label}**", parse_mode='Markdown')
                                    except: pass
                                else:
                                    try: await loader.edit_text(f"❌ Could not find input matching '{target}'")
                                    except: await update.message.reply_text(f"❌ Could not find input matching '{target}'")
                                    return
                            else:
                                await update.message.reply_text("❌ Scan failed during typing.")
                                return

                        browser_control.type_text(target_id, text)
                        await update.message.reply_text(f"⌨️ Typed `{text}` into `{found_label}`", parse_mode='Markdown')
                        
                        if "search" in target_lower or "find" in target_lower:
                            browser_control.press_key(target_id, "Enter")
                            await update.message.reply_text("⌨️ Pressed **Enter**", parse_mode='Markdown')
                    else:
                        await update.message.reply_text("❌ Usage: `/type [field] [text]`")

                elif sub_action == "scan":
                    loader = await update.message.reply_text("🔍 Scanning page elements...", reply_markup=get_main_keyboard())
                    
                    loop = asyncio.get_running_loop()
                    try:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, browser_control.scan_page),
                            timeout=8.0
                        )
                    except asyncio.TimeoutError:
                        await loader.edit_text("❌ Scan timeout.")
                        return

                    if result and result.get("success"):
                        elements = result.get("elements", [])
                        if not elements:
                            try: await loader.edit_text("❌ No interactive elements found.")
                            except: await update.message.reply_text("❌ No interactive elements found.")
                        else:
                            lines = ["🎯 **Interactive Elements:**\n"]
                            for el in elements:
                                lines.append(f"`[{el['id']}]` {el['text']} ({el['type']})")
                            msg = "\n".join(lines)
                            if len(msg) > 4000: msg = msg[:4000] + "\n...(truncated)"
                            try: await loader.edit_text(msg, parse_mode='Markdown')
                            except: await update.message.reply_text(msg, parse_mode='Markdown')
                    else:
                        err_msg = f"❌ Scan failed: {result.get('error') if result else 'Unknown'}"
                        try: await loader.edit_text(err_msg)
                        except: await update.message.reply_text(err_msg)

                elif sub_action == "click":
                    target = command_json.get("target") or command_json.get("selector")
                    if target:
                        target_id = target
                        clicked_text = target
                        
                        if not str(target).isdigit():
                            loader = await update.message.reply_text(f"🔍 Searching for '{target}'...", reply_markup=get_main_keyboard())
                            
                            loop = asyncio.get_running_loop()
                            scan_result = await loop.run_in_executor(None, browser_control.scan_page)
                            
                            if scan_result and scan_result.get("success"):
                                elements = scan_result.get("elements", [])
                                scores = []
                                target_lower = target.lower()
                                
                                # Detect positional request
                                ordinals = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "last": -1}
                                skip_n = 0
                                for ord_word, pos in ordinals.items():
                                    if ord_word in query: # check the original user query for ordinals
                                        skip_n = pos
                                        break

                                for el in elements:
                                    el_text = el['text'].lower()
                                    el_area = el.get('area', 'main')
                                    el_url = el.get('url', '').lower()
                                    
                                    score = 0
                                    # 1. Text Similarity Score
                                    if el_text == target_lower: score = 100
                                    elif target_lower in el_text: score = 50
                                    elif el_text in target_lower: score = 30
                                    else:
                                        target_words = set(target_lower.split())
                                        el_words = set(el_text.split())
                                        overlap = len(target_words & el_words)
                                        if overlap > 0: score = overlap * 15

                                    # 2. Area Penalty/Boost (STRENGTHENED)
                                    if el_area in ["nav", "aside", "header", "footer"]:
                                        score -= 80
                                    elif el_area == "main":
                                        score += 30

                                    # 3. Contextual URL Boost (STRENGTHENED)
                                    if "video" in target_lower or "watch" in target_lower:
                                        if "watch?v=" in el_url: score += 100
                                    
                                    # 4. Filter out common nav-only matches (STRENGTHENED)
                                    nav_junk = ["liked", "history", "playlist", "library", "home", "shorts", "subscriptions", "your videos", "library"]
                                    if any(j in el_text for j in nav_junk) and el_text != target_lower:
                                        score -= 60
                                    
                                    # 5. Penalize numeric-only "videos" counts (e.g. "9 videos")
                                    if re.search(r'^\d+ videos?$', el_text):
                                        score -= 100
                                    elif re.search(r'^\d+ views?$', el_text):
                                        score -= 100

                                    if score > 0:
                                        scores.append((score, el))
                                
                                # Sort by score descending
                                scores.sort(key=lambda x: x[0], reverse=True)
                                
                                # --- DEBUG SCORE LOGGING ---
                                print(f"🔍 Top scores for '{target}':")
                                for s, el in scores[:10]:
                                    print(f"   [{s:3}] {el['text'][:30]:30} (Area: {el['area']})")
                                
                                # Apply ordinal selection if requested
                                best_match = None
                                if scores:
                                    if skip_n == -1: # "last"
                                        best_match = scores[-1][1]
                                    elif skip_n > 0:
                                        # Pick the N-th high-scoring item
                                        idx = min(skip_n - 1, len(scores) - 1)
                                        best_match = scores[idx][1]
                                    else:
                                        best_match = scores[0][1]
                                        
                                if best_match:
                                    target_id = str(best_match['id'])
                                    clicked_text = best_match['text']
                                    # Update short-term memory with the last clicked text/context if possible
                                    # We don't have the tab title here, but we can update a generic interaction context
                                    memory.short_term["last_interaction"] = clicked_text
                                    safe_text = clicked_text.replace("*", "").replace("_", "").replace("[", "").replace("`", "")
                                    try: await loader.edit_text(f"🎯 Found: **{safe_text}** (ID: {target_id})", parse_mode='Markdown')
                                    except: await update.message.reply_text(f"🎯 Found: {clicked_text} (ID: {target_id})")
                                else:
                                    try: await loader.edit_text(f"❌ Could not find element matching '{target}'")
                                    except: await update.message.reply_text(f"❌ Could not find element matching '{target}'")
                                    return
                            else:
                                err = scan_result.get("error", "Unknown error") if scan_result else "No result from browser"
                                try: await loader.edit_text(f"❌ Failed to scan page: {err}")
                                except: await update.message.reply_text(f"❌ Failed to scan page: {err}")
                                return

                        browser_control.click_element(target_id)
                        await update.message.reply_text(f"🖱️ Clicked `{clicked_text}`", parse_mode='Markdown')
                    else:
                        await update.message.reply_text("❌ Usage: `/click [text or ID]`")
            except Exception as e:
                print(f"Browser Nav Error: {e}")
                await update.message.reply_text(f"❌ Browser Error: {e}")

        # --- NAVIGATION AGENT COMMANDS ---
        elif action == "browser_nav":
            try:
                if status_msg:
                    try: await status_msg.delete()
                    except: pass
                
                sub_action = command_json.get("sub_action")
                
                if sub_action == "read":
                    print("📖 Navigation Agent: Reading page...")
                    loader = await update.message.reply_text("📖 Reading page content...", reply_markup=get_main_keyboard())
                    
                    loop = asyncio.get_running_loop()
                    try:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, browser_control.read_page),
                            timeout=8.0
                        )
                    except asyncio.TimeoutError:
                        await loader.edit_text("❌ Read timeout. Native Host not responding.")
                        return

                    if result and result.get("success"):
                        title = result.get("title", "No Title")
                        url = result.get("url", "Unknown URL")
                        content = result.get("content", "")
                        
                        if len(content) > 3000:
                            preview = content[:1000] + "..."
                            msg_text = f"📄 {title}\n🔗 {url}\n\n{preview}\n\n(Content truncated)"
                        else:
                            msg_text = f"📄 {title}\n🔗 {url}\n\n{content}"
                            
                        try:
                            await loader.edit_text(msg_text, disable_web_page_preview=True)
                        except Exception as e:
                            import io
                            full_file_text = f"📄 {title}\n🔗 {url}\n\n{content}"
                            file_obj = io.BytesIO(full_file_text.encode('utf-8'))
                            file_obj.name = "page_content.txt"
                            await update.message.reply_document(document=file_obj, caption="📄 Page Content (Full)")
                    else:
                        err = result.get("error", "Unknown error") if result else "No data returned"
                        await loader.edit_text(f"❌ Read failed: {err}")

                elif sub_action == "scroll":
                    direction = command_json.get("direction", "down")
                    browser_control.scroll_page(direction)
                    try: await update.message.set_reaction(reaction="👇" if direction == "down" else "👆")
                    except: await update.message.reply_text(f"📜 Scrolled {direction}", reply_markup=get_main_keyboard())

                elif sub_action == "type":
                    target = command_json.get("target") or command_json.get("selector")
                    text = command_json.get("text")
                    
                    if target and text:
                        target_id = target
                        found_label = target
                        
                        if not str(target).isdigit():
                            loader = await update.message.reply_text(f"🔍 Finding input '{target}'...", reply_markup=get_main_keyboard())
                            
                            loop = asyncio.get_running_loop()
                            scan_result = await loop.run_in_executor(None, browser_control.scan_page)
                            
                            if scan_result and scan_result.get("success"):
                                elements = scan_result.get("elements", [])
                                input_elements = [el for el in elements if el['type'] in ['input', 'textarea']]
                                
                                best_match = None
                                best_score = 0
                                target_lower = target.lower()
                                
                                for el in input_elements:
                                    el_text = el['text'].lower()
                                    score = 0
                                    if el_text == target_lower: score = 100
                                    elif target_lower in el_text: score = 50
                                    elif el_text in target_lower: score = 30
                                    if score > best_score:
                                        best_score = score
                                        best_match = el
                                        
                                if best_match:
                                    target_id = str(best_match['id'])
                                    found_label = best_match['text']
                                    try: await loader.edit_text(f"🎯 Found input: **{found_label}**", parse_mode='Markdown')
                                    except: pass
                                else:
                                    try: await loader.edit_text(f"❌ Could not find input matching '{target}'")
                                    except: await update.message.reply_text(f"❌ Could not find input matching '{target}'")
                                    return
                            else:
                                await update.message.reply_text("❌ Scan failed during typing.")
                                return

                        browser_control.type_text(target_id, text)
                        await update.message.reply_text(f"⌨️ Typed `{text}` into `{found_label}`", parse_mode='Markdown')
                        
                        if "search" in target_lower or "find" in target_lower:
                            browser_control.press_key(target_id, "Enter")
                            await update.message.reply_text("⌨️ Pressed **Enter**", parse_mode='Markdown')
                    else:
                        await update.message.reply_text("❌ Usage: `/type [field] [text]`")

                elif sub_action == "scan":
                    loader = await update.message.reply_text("🔍 Scanning page elements...", reply_markup=get_main_keyboard())
                    
                    loop = asyncio.get_running_loop()
                    try:
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, browser_control.scan_page),
                            timeout=8.0
                        )
                    except asyncio.TimeoutError:
                        await loader.edit_text("❌ Scan timeout.")
                        return

                    if result and result.get("success"):
                        elements = result.get("elements", [])
                        if not elements:
                            try: await loader.edit_text("❌ No interactive elements found.")
                            except: await update.message.reply_text("❌ No interactive elements found.")
                        else:
                            lines = ["🎯 **Interactive Elements:**\n"]
                            for el in elements:
                                lines.append(f"`[{el['id']}]` {el['text']} ({el['type']})")
                            msg = "\n".join(lines)
                            if len(msg) > 4000: msg = msg[:4000] + "\n...(truncated)"
                            try: await loader.edit_text(msg, parse_mode='Markdown')
                            except: await update.message.reply_text(msg, parse_mode='Markdown')
                    else:
                        err_msg = f"❌ Scan failed: {result.get('error') if result else 'Unknown'}"
                        try: await loader.edit_text(err_msg)
                        except: await update.message.reply_text(err_msg)

                elif sub_action == "click":
                    target = command_json.get("target") or command_json.get("selector")
                    if target:
                        target_id = target
                        clicked_text = target
                        
                        if not str(target).isdigit():
                            loader = await update.message.reply_text(f"🔍 Searching for '{target}'...", reply_markup=get_main_keyboard())
                            
                            loop = asyncio.get_running_loop()
                            scan_result = await loop.run_in_executor(None, browser_control.scan_page)
                            
                            if scan_result and scan_result.get("success"):
                                elements = scan_result.get("elements", [])
                                best_match = None
                                best_score = 0
                                target_lower = target.lower()
                                
                                for el in elements:
                                    el_text = el['text'].lower()
                                    score = 0
                                    if el_text == target_lower: score = 100
                                    elif target_lower in el_text: score = 50
                                    elif el_text in target_lower: score = 30
                                    else:
                                        target_words = set(target_lower.split())
                                        el_words = set(el_text.split())
                                        overlap = len(target_words & el_words)
                                        if overlap > 0: score = overlap * 10
                                    if score > best_score:
                                        best_score = score
                                        best_match = el
                                        
                                if best_match:
                                    target_id = str(best_match['id'])
                                    clicked_text = best_match['text']
                                    safe_text = clicked_text.replace("*", "").replace("_", "").replace("[", "").replace("`", "")
                                    try: await loader.edit_text(f"🎯 Found: **{safe_text}** (ID: {target_id})", parse_mode='Markdown')
                                    except: await update.message.reply_text(f"🎯 Found: {clicked_text} (ID: {target_id})")
                                else:
                                    try: await loader.edit_text(f"❌ Could not find element matching '{target}'")
                                    except: await update.message.reply_text(f"❌ Could not find element matching '{target}'")
                                    return
                            else:
                                err = scan_result.get("error", "Unknown error") if scan_result else "No result from browser"
                                try: await loader.edit_text(f"❌ Failed to scan page: {err}")
                                except: await update.message.reply_text(f"❌ Failed to scan page: {err}")
                                return

                        browser_control.click_element(target_id)
                        await update.message.reply_text(f"🖱️ Clicked `{clicked_text}`", parse_mode='Markdown')
                    else:
                        await update.message.reply_text("❌ Usage: `/click [text or ID]`")
            except Exception as e:
                print(f"Browser Nav Error: {e}")
                await update.message.reply_text(f"❌ Browser Error: {e}")

        else:
            # Generic action execution
            try:
                result = execute_command(command_json)
                if status_msg: await status_msg.delete()
                
                if action == "web_research" and result:
                    # Professional synthesis delivery
                    await update.message.reply_text(f"🔍 **Research Result:**\n\n{result}", parse_mode='Markdown', reply_markup=get_main_keyboard())
                else:
                    await update.message.reply_text(f"✅ Action Complete: {action}", reply_markup=get_main_keyboard())
            except Exception as e:
                if status_msg: await status_msg.delete()
                await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_main_keyboard())

        # --- DELAY BETWEEN CHAINED BROWSER COMMANDS ---
        if total_commands > 1 and cmd_index < total_commands - 1:
            # Delay for browser actions to allow page to load
            if action in ["open_url", "browser_nav", "browser_control"]:
                await asyncio.sleep(2.5)
            else:
                await asyncio.sleep(0.5)

if __name__ == "__main__":
    print("🚀 TELEGRAM BOT STARTED...")
    try:
        # Increase connection timeout to handle slow uploads better
        
        # Run
        # Initialize Application
        application = ApplicationBuilder().token(TOKEN).read_timeout(60).write_timeout(60).build()
        
        # Handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(handle_clipboard_callback, pattern="^copy_"))
        application.add_handler(CallbackQueryHandler(handle_zombie_callback, pattern="^z(kill|allow|ignore)_"))
        application.add_handler(CallbackQueryHandler(handle_media_callback, pattern="^(media_|vol_)"))
        application.add_handler(MessageHandler(filters.TEXT, handle_message))
        
        # Run
        print("🤖 Bot is pooling...")
        
        # Auto-start Reaper if we remember the user
        saved_id = load_chat_id()
        if saved_id:
            print(f"🔄 Auto-starting Zombie Reaper for Chat ID: {saved_id}")
            # Launch in background after a short delay to let loop start
            async def post_start(app):
                 start_reaper_task(app.bot, saved_id)
            
            # Re-initialize to attach background task (Workaround for post_init)
            
            application = ApplicationBuilder().token(TOKEN).read_timeout(60).write_timeout(60).post_init(post_start).build()
            # Re-add handlers (builder creates new instance)
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CallbackQueryHandler(handle_clipboard_callback, pattern="^copy_"))
            application.add_handler(CallbackQueryHandler(handle_zombie_callback, pattern="^z(kill|allow|ignore)_"))
            application.add_handler(CallbackQueryHandler(handle_media_callback, pattern="^(media_|vol_)"))
            application.add_handler(MessageHandler(filters.TEXT, handle_message))

        application.run_polling()
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")