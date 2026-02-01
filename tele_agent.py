import logging
import asyncio
import os
from dotenv import load_dotenv
from telegram import Update, constants, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from brain import process_command
from muscles import execute_command, capture_webcam
import memory


load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ Error: TELEGRAM_TOKEN not found in .env file.")
    exit()

ALLOWED_USERS = [] 


CAMERA_ACTIVE = False

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def get_main_keyboard():
    keyboard = [
        [KeyboardButton("/screenshot"), KeyboardButton("/sleep")],
        [KeyboardButton("/camera_on"), KeyboardButton("/camera_off")],
        [KeyboardButton("/batterypercentage"), KeyboardButton("/systemhealth")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def camera_monitor_loop(bot, chat_id):
    global CAMERA_ACTIVE
    status_msg = await bot.send_message(chat_id, "🔴 Live Feed Started...")
    
    while CAMERA_ACTIVE:
        photo_path = capture_webcam()
        if photo_path and os.path.exists(photo_path):
            try:
                await bot.send_photo(chat_id, photo=open(photo_path, 'rb'))
            except:
                pass
        await asyncio.sleep(3) 
    
    await bot.send_message(chat_id, "xxxx Camera Feed Stopped.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(
        f"⚡ **Pikachu Online!**\nHello {user}. Use the buttons below.",
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CAMERA_ACTIVE
    user_text = update.message.text
    sender = update.message.from_user.username
    chat_id = update.effective_chat.id
    lower_text = user_text.lower()
    
    print(f"\n📩 Message from @{sender}: {user_text}")

  
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

  
    command_json = None
    
    if "/battery" in lower_text or "battery" in lower_text:
        command_json = {"action": "check_battery"}
    elif "/systemhealth" in lower_text or "system health" in lower_text:
        command_json = {"action": "check_health"}
    elif "/screenshot" in lower_text or "screenshot" in lower_text:
        command_json = {"action": "take_screenshot"}
    elif "/sleep" in lower_text:
        command_json = {"action": "system_sleep"}
    elif "/camera_on" in lower_text:
        command_json = {"action": "camera_stream", "value": "on"}
    elif "/camera_off" in lower_text:
        command_json = {"action": "camera_stream", "value": "off"}

 
    status_msg = await update.message.reply_text("⚡ Thinking...", reply_markup=get_main_keyboard())

    if not command_json:
        loop = asyncio.get_running_loop()
        try:
       
            command_json = await loop.run_in_executor(None, process_command, user_text)
        except Exception as e:
          
            await status_msg.delete()
            await update.message.reply_text(f"❌ Brain Error: {e}", reply_markup=get_main_keyboard())
            return


    if command_json:
        action = command_json.get('action')
        
    
        if action == "check_battery":
            status = execute_command(command_json)
            await status_msg.delete()
            await update.message.reply_text(f"🔋 {status}", reply_markup=get_main_keyboard())
            
        elif action == "check_health":
            report = execute_command(command_json)
            await status_msg.delete()
            await update.message.reply_text(report, reply_markup=get_main_keyboard())
            
        elif action == "take_screenshot":
           
            await status_msg.delete()
            loader = await update.message.reply_text("📸 Capture...", reply_markup=get_main_keyboard())
            path = execute_command(command_json)
            if path:
                await update.message.reply_photo(photo=open(path, 'rb'))
                await loader.delete()
            else:
                await loader.edit_text("❌ Screenshot failed.")
                
        elif action == "system_sleep":
            await status_msg.delete()
            await update.message.reply_text("💤 Goodnight.", reply_markup=get_main_keyboard())
            execute_command(command_json)

        elif action == "camera_stream":
            val = command_json.get("value")
            await status_msg.delete()
            if val == "on":
                if not CAMERA_ACTIVE:
                    CAMERA_ACTIVE = True
                    asyncio.create_task(camera_monitor_loop(context.bot, chat_id))
            else:
                CAMERA_ACTIVE = False
                await update.message.reply_text("🛑 Stopping Camera...", reply_markup=get_main_keyboard())

        elif action == "general_chat":
            response = command_json.get('response', "...")
           
            await status_msg.delete()
            await update.message.reply_text(f"💬 {response}", reply_markup=get_main_keyboard())
            
        # --- File / App Handling ---
        elif action == "list_files":
            await status_msg.delete()
            raw_path = command_json.get('path')
            if "desktop" in raw_path.lower(): raw_path = os.path.join(os.path.expanduser("~"), "Desktop")
            elif "downloads" in raw_path.lower(): raw_path = os.path.join(os.path.expanduser("~"), "Downloads")
            
            if os.path.exists(raw_path):
                try:
                    files = os.listdir(raw_path)[:20]
                    text = "\n".join([f"🔹 {f}" for f in files])
                    await update.message.reply_text(f"📂 **Files:**\n{text}", reply_markup=get_main_keyboard())
                except: 
                    await update.message.reply_text("❌ Failed to read folder.", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text("❌ Folder not found.", reply_markup=get_main_keyboard())

        elif action == "send_file":
             await status_msg.delete()
             raw_path = command_json.get('path')
             if os.path.exists(raw_path):
                 await update.message.reply_text("📤 Uploading...", reply_markup=get_main_keyboard())
                 await update.message.reply_document(open(raw_path, 'rb'))
             else:
                 await update.message.reply_text("❌ File not found.", reply_markup=get_main_keyboard())

        else:
          
            try:
                execute_command(command_json)
                await status_msg.delete()
                await update.message.reply_text(f"✅ Action Complete: {action}", reply_markup=get_main_keyboard())
            except Exception as e:
                await status_msg.delete()
                await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    print("🚀 TELEGRAM BOT STARTED...")
    try:
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(MessageHandler(filters.TEXT | filters.COMMAND, handle_message))
        application.run_polling()
    except Exception as e:
        print(f"❌ Critical Error: {e}")
