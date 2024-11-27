from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
import asyncio
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.crud_user import crud_user
from app.crud.crud_garage import crud_garage
from app.db.session import SessionLocal

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.active_garages: Dict[str, dict] = {}  # Store active garages in instance variable instead

    async def start(self):
        """Initialize and start the bot"""
        self.bot = Bot(self.token)
        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        # Start the bot
        await self.application.initialize()
        await self.application.start()
        
        # No need to update bot data, we'll use instance variable

    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        if not update.effective_user:
            return

        # Get or create user
        db = SessionLocal()
        try:
            user = crud_user.get_by_telegram_id(db, str(update.effective_user.id))
            if not user:
                # Handle new user registration
                await update.message.reply_text(
                    "Welcome! You need to be registered to use this bot. "
                    "Please contact the administrator."
                )
                return
            
            # Show available garages
            garages = crud_garage.get_multi_by_user(db, user.id)
            keyboard = []
            for garage in garages:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{garage.name} - Open",
                        callback_data=f"open_{garage.id}"
                    ),
                    InlineKeyboardButton(
                        f"{garage.name} - Close",
                        callback_data=f"close_{garage.id}"
                    )
                ])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "Select a garage and action:",
                reply_markup=reply_markup
            )
        finally:
            db.close()

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        if not update.callback_query:
            return

        query = update.callback_query
        action, garage_id = query.data.split('_')
        
        db = SessionLocal()
        try:
            user = crud_user.get_by_telegram_id(db, str(update.effective_user.id))
            if not user:
                await query.answer("User not authorized")
                return

            garage = crud_garage.get(db, int(garage_id))
            if not garage:
                await query.answer("Garage not found")
                return

            if not crud_garage.user_has_access(db, user.id, garage.id):
                await query.answer("Access denied")
                return

            # Send command to garage through WebSocket manager
            from app.main import ws_manager  # Import here to avoid circular import
            success = await ws_manager.send_command(garage.esp32_identifier, action)

            if success:
                await query.answer(f"Command {action} sent to {garage.name}")
            else:
                await query.answer(f"Failed to send command to {garage.name}")

        finally:
            db.close()

    async def send_message(self, chat_id: str, text: str):
        """Send a message to a specific chat"""
        if self.bot:
            await self.bot.send_message(chat_id=chat_id, text=text)

    def get_login_url(self, bot_username: str) -> str:
        """Get Telegram login widget URL"""
        return f"https://telegram.org/js/telegram-widget.js?19"

telegram_bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)