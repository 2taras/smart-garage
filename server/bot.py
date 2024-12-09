from dotenv import load_dotenv
load_dotenv()

import os
import math
import random
from datetime import datetime
import logging
from typing import Optional
import json
from misc.garageapi import GarageAPI
from misc.db import get_db, User, SystemConfig, Log
from misc.bankapi import AsyncBankClient, PaymentRequest, PaymentResponse
from misc.config_manager import ConfigManager
from misc.utils import distance
from misc.models import LocationData, LoginData, PurchaseData

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from sqlalchemy.orm import Session

# Load .env

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
API_TOKEN = os.getenv("API_TOKEN")
GARAGE_LOCATION = json.loads(os.getenv("GARAGE_LOCATION"))
GARAGE_PRICE = float(os.getenv("GARAGE_PRICE", "100.0"))

def get_start_keyboard(is_available: bool = True) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton("Купить гараж")] if is_available else [],
        [KeyboardButton("Ввести пароль")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([
        [KeyboardButton("Пароль")],
        [KeyboardButton("Открыть"), KeyboardButton("Закрыть")],
        [KeyboardButton("Статус")]  # New button
    ], resize_keyboard=True)

def get_location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("Переключить", request_location=True)]], 
                              resize_keyboard=True, one_time_keyboard=True)

class GarageBot:
    def __init__(self):
        self.application = Application.builder().token(API_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("exit", self.exit))
        self.application.add_handler(CommandHandler("logs", self.logs))
        self.application.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        db = next(get_db())
        
        user = db.query(User).get(user_id)
        if not user:
            user = User(id=user_id)
            db.add(user)
            db.commit()
        
        if user.is_owner and user.is_auth:
            await update.message.reply_text(
                "Добро пожаловать в панель управления!", 
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "🏠 Гараж-бот\n\n" +
                ("🔑 Авторизуйтесь с помощью пароля\n"
                 f"🏷 Гараж доступен к покупке за {GARAGE_PRICE} &$%&\n"),
                reply_markup=get_start_keyboard()
            )

    async def get_garage_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            status = await GarageAPI.get_status()
            if "error" in status:
                await update.message.reply_text(
                    f"Ошибка получения статуса: {status['error']}",
                    reply_markup=get_main_keyboard()
                )
                return

            status_text = (
                f"🌡 Температура: {status.get('temperature', 'N/A'):.1f}°C\n"  # .1f for 1 decimal place
                f"💧 Влажность: {status.get('humidity', 'N/A'):.1f}%\n"        # .1f for 1 decimal place
                f"🚪 Состояние: {'Открыто' if status.get('state') == 'open' else 'Закрыто'}"
            )
            
            await update.message.reply_text(
                status_text,
                reply_markup=get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Failed to get garage status: {str(e)}")
            await update.message.reply_text(
                "Ошибка получения статуса гаража",
                reply_markup=get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Failed to get garage status: {str(e)}")
            await update.message.reply_text(
                "Ошибка получения статуса гаража",
                reply_markup=get_main_keyboard()
            )

    async def check_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        db = next(get_db())
        user_id = update.effective_user.id
        current_pass = ConfigManager.get_temp_password(db)
        
        if text == current_pass:
            user = db.query(User).get(user_id)
            user.is_auth = True
            db.commit()
            
            ConfigManager.reset_temp_password(db)
            await update.message.reply_text("Доступ разрешен", reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text("Неверный пароль")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        db = next(get_db())
        user = db.query(User).get(user_id)

        # Если у пользователя есть текущая итерация (ожидание ввода карты)
        if user and user.current_itern == 'awaiting_card':
            user.current_itern = ''
            db.commit()
            await self.handle_card_input(update, user)
            return

        if text == "Купить гараж":
            await update.message.reply_text(
                f"💳 Для покупки гаража введите номер карты (16 цифр).\n"
                f"💰 Стоимость: {GARAGE_PRICE} руб."
            )
            user.current_itern = 'awaiting_card'
            db.commit()
            return
            
        if text == "Ввести пароль":
            await update.message.reply_text("Введите пароль:")
            return
            
        if user and user.is_auth:
            # Handle main keyboard commands
            if text == "Статус":
                await self.get_garage_status(update, context)
            elif text == "Пароль":
                current_pass = ConfigManager.get_temp_password(db)
                await update.message.reply_text(
                    f"Пароль: {current_pass}\n"
                    f"https://t.me/new_garage_opener_Bot?start={current_pass}",
                    reply_markup=get_main_keyboard()
                )
            elif text in ["Открыть", "Закрыть"]:
                command_map = {
                    "Открыть": "left",
                    "Закрыть": "right"
                }
                user.current_itern = command_map[text]
                db.commit()
                await update.message.reply_text(
                    "Нажмите кнопку для действия",
                    reply_markup=get_location_keyboard()
                )
        else:
            # Try to authenticate with password
            current_pass = ConfigManager.get_temp_password(db)
            if text == current_pass:
                user.is_auth = True
                db.commit()
                ConfigManager.reset_temp_password(db)
                await update.message.reply_text(
                    "Доступ разрешен", 
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ Неверный пароль",
                    reply_markup=get_start_keyboard()
                )

    async def handle_card_input(self, update: Update, user: User):
            db = next(get_db())
            card_number = update.message.text

            if not card_number.isdigit() or len(card_number) != 16:
                await update.message.reply_text("❌ Неверный формат карты")
                return

            await update.message.delete()  # Delete card number for security
            user_id = update.effective_user.id
            
            try:
                payment = PaymentRequest(
                    amount=GARAGE_PRICE,
                    card_number=card_number,
                    description=f"Garage purchase by user {user_id}"
                )
                
                # Создаем новый экземпляр клиента для каждой транзакции
                client = AsyncBankClient()
                async with client as bank:
                    response = await bank.process_payment(payment)
                
                if response.status == "success":
                    # Remove all old users
                    db.query(User).delete()
                    db.commit()
                    
                    # Create new owner
                    new_owner = User(
                        id=user_id,
                        is_owner=True,
                        is_auth=True
                    )
                    db.add(new_owner)
                    
                    # Log the purchase
                    log = Log(
                        user=str(user_id),
                        action="garage_purchased",
                        timestamp=int(datetime.utcnow().timestamp())
                    )
                    db.add(log)
                    db.commit()
                    
                    await update.message.reply_text(
                        "🎉 Поздравляем с покупкой гаража!\n"
                        "Теперь вы владелец.",
                        reply_markup=get_main_keyboard()
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Ошибка при оплате: {response.error_message}",
                        reply_markup=get_start_keyboard(True)
                    )
                    
            except Exception as e:
                logger.error(f"Purchase processing error: {str(e)}")
                await update.message.reply_text(
                    "❌ Произошла ошибка при обработке покупки.",
                    reply_markup=get_start_keyboard(True)
                )
            finally:
                # Clear the current iteration
                user.current_itern = None
                db.commit()

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username
        db = next(get_db())
        user = db.query(User).get(user_id)
        
        if not user or not user.current_itern:
            return
            
        location = update.message.location
        dist = distance(location.latitude, location.longitude, *GARAGE_LOCATION)
        
        if dist > 1000:
            await update.message.reply_text(
                "Вы слишком далеко от гаража",
                reply_markup=get_main_keyboard()
            )
            return
            
        result = await GarageAPI.open(user.current_itern, db, user_id)
        
        # Log the action
        log = Log(
            user=username or str(user_id),
            action=user.current_itern,
            timestamp=int(datetime.utcnow().timestamp())
        )
        db.add(log)
        db.commit()
        
        await update.message.reply_text(
            "Выполнено" if result == "Success" else result,
            reply_markup=get_main_keyboard()
        )
        user.current_itern = None
        db.commit()

    async def logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        db = next(get_db())
        user = db.query(User).get(user_id)
        
        if not user or not user.is_auth:
            return
            
        logs = db.query(Log).order_by(Log.timestamp.desc()).limit(50).all()
        log_text = "\n".join([
            f"{datetime.fromtimestamp(log.timestamp)}: User {log.user} - {log.action}"
            for log in logs
        ])
        
        await update.message.reply_text(f"Последние действия:\n{log_text}")

    async def exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        db = next(get_db())
        user = db.query(User).get(user_id)
        
        if user:
            user.is_auth = False
            db.commit()
            await update.message.reply_text("Выход выполнен", reply_markup=ReplyKeyboardMarkup([]))

    def run(self):
        self.application.run_polling()

if __name__ == '__main__':
    bot = GarageBot()
    with next(get_db()) as db:
        print("Current pass:", ConfigManager.get_temp_password(db))
    bot.run()