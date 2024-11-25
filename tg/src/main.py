from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LoginUrl
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000/api"
BOT_TOKEN = "YOUR_BOT_TOKEN"
WEBAPP_URL = "https://your-webapp-url.com"  # Your Next.js webapp URL

# States for conversation handler
START, MAIN_MENU = range(2)

class SmartGarageBot:
    def __init__(self):
        self.active_sessions: Dict[int, dict] = {}
        self.application = Application.builder().token(BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        # Basic commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Callback queries
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        user = update.effective_user
        
        # Check if user exists in the system
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{API_BASE_URL}/auth/telegram",
                    json={
                        "telegram_id": str(user.id),
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }
                ) as response:
                    if response.status == 200:
                        await self.show_main_menu(update, context)
                    else:
                        await self.show_registration_message(update, context)
            except Exception as e:
                logger.error(f"Error during start command: {e}")
                await self.show_error_message(update, context)

    async def show_registration_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show registration message with web app link"""
        webapp_login_url = LoginUrl(
            url=f"{WEBAPP_URL}/auth/telegram",
            bot_username=context.bot.username
        )
        
        keyboard = [
            [InlineKeyboardButton("🔐 Register via Web", url=webapp_login_url.url)],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Welcome to Smart Garage Bot! 🏠\n\n"
            "Please register using our web interface to continue.",
            reply_markup=reply_markup
        )

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu with garage controls"""
        # Fetch available garages for the user
        user_id = update.effective_user.id
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{API_BASE_URL}/garages",
                    headers={"Authorization": f"Bearer {self._get_user_token(user_id)}"}
                ) as response:
                    if response.status == 200:
                        garages = await response.json()
                        keyboard = self._create_garage_keyboard(garages)
                        
                        # Add web interface button
                        keyboard.append([
                            InlineKeyboardButton(
                                "🌐 Open Web Interface",
                                url=WEBAPP_URL
                            )
                        ])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        message_text = "🏠 Smart Garage Control Panel\n\n"
                        for garage in garages:
                            message_text += f"• {garage['name']}: {garage['current_state']}\n"
                        
                        if update.callback_query:
                            await update.callback_query.edit_message_text(
                                text=message_text,
                                reply_markup=reply_markup
                            )
                        else:
                            await update.message.reply_text(
                                text=message_text,
                                reply_markup=reply_markup
                            )
            except Exception as e:
                logger.error(f"Error showing main menu: {e}")
                await self.show_error_message(update, context)

    def _create_garage_keyboard(self, garages: List[dict]) -> List[List[InlineKeyboardButton]]:
        """Create keyboard markup for garage controls"""
        keyboard = []
        for garage in garages:
            garage_row = []
            current_state = garage['current_state'].lower()
            
            if current_state == "closed":
                garage_row.append(InlineKeyboardButton(
                    f"🔓 Open {garage['name']}",
                    callback_data=f"garage_open_{garage['id']}"
                ))
            elif current_state == "open":
                garage_row.append(InlineKeyboardButton(
                    f"🔒 Close {garage['name']}",
                    callback_data=f"garage_close_{garage['id']}"
                ))
            elif current_state in ["opening", "closing"]:
                garage_row.append(InlineKeyboardButton(
                    f"⏹ Stop {garage['name']}",
                    callback_data=f"garage_stop_{garage['id']}"
                ))
            
            keyboard.append(garage_row)
        
        # Add refresh button
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh")
        ])
        
        return keyboard

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()  # Answer the callback query
        
        if query.data == "refresh":
            await self.show_main_menu(update, context)
            return
        
        if query.data.startswith("garage_"):
            _, action, garage_id = query.data.split("_")
            await self._control_garage(update, context, garage_id, action)

    async def _control_garage(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        garage_id: str,
        action: str
    ):
        """Send garage control commands to the API"""
        user_id = update.effective_user.id
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{API_BASE_URL}/garages/{garage_id}/control",
                    headers={"Authorization": f"Bearer {self._get_user_token(user_id)}"},
                    json={"action": action}
                ) as response:
                    if response.status == 200:
                        # Show success message and update menu
                        await update.callback_query.answer(
                            f"Garage {action} command sent successfully!"
                        )
                        await self.show_main_menu(update, context)
                    else:
                        await self.show_error_message(update, context)
            except Exception as e:
                logger.error(f"Error controlling garage: {e}")
                await self.show_error_message(update, context)

    async def show_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show error message to user"""
        message_text = (
            "❌ Sorry, something went wrong. Please try again later or "
            "contact support if the problem persists."
        )
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text=message_text)
        else:
            await update.message.reply_text(text=message_text)

    def _get_user_token(self, user_id: int) -> str:
        """Get user token from active sessions"""
        return self.active_sessions.get(user_id, {}).get("token")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error: {context.error} for update {update}")
        try:
            await self.show_error_message(update, context)
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    def run(self):
        """Run the bot"""
        self.application.run_polling()

if __name__ == "__main__":
    bot = SmartGarageBot()
    bot.run()
from dataclasses import dataclass
from typing import Optional
import jwt
from datetime import datetime, timedelta

@dataclass
class TelegramUser:
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username

class TelegramAuth:
    def __init__(self, bot_token: str, secret_key: str):
        self.bot_token = bot_token
        self.secret_key = secret_key

    def create_auth_token(self, user: TelegramUser) -> str:
        """Create JWT token for Telegram user"""
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_telegram_data(self, auth_data: dict) -> Optional[TelegramUser]:
        """Verify Telegram authentication data"""
        # Implement Telegram login widget data verification
        # https://core.telegram.org/widgets/login#checking-authorization
        try:
            # Implementation here
            pass
        except Exception as e:
            return None