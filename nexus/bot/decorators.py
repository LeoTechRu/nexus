# /sd/nexus/bot/decorators.py
from functools import wraps
from aiogram.types import Message
from models import db_session
from services.telegram import UserService
from logger import logger

# ------------------------------
# Декоратор role_required
# ------------------------------
from models.tg import TelegramUserRole

def role_required(role: TelegramUserRole):
    """Декоратор для проверки прав доступа к командам через TelegramProfile"""
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: Message, *args, **kwargs):
            try:
                async with UserService() as user_service:
                    # Получение или создание Telegram-профиля
                    telegram_profile, is_new = await user_service.get_or_create_telegram_profile(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        language_code=message.from_user.language_code,
                        is_premium=message.from_user.is_premium
                    )

                    # Проверка роли
                    if telegram_profile.role >= role.value:
                        return await handler(message, *args, **kwargs)

                    await message.answer(f"Недостаточно прав. Требуется роль: {role.name}")

            except Exception as e:
                logger.error(f"Ошибка проверки роли: {e}")
                await message.answer("Произошла ошибка при проверке прав")

        return wrapper
    return decorator

# ------------------------------
# Декоратор group_required
# ------------------------------
from models.tg import ChatType

def group_required(handler):
    """Декоратор для проверки членства в чате (TelegramChat)"""
    @wraps(handler)
    async def wrapper(message: Message, *args, **kwargs):
        try:
            async with UserService() as user_service:
                chat = message.chat
                telegram_id = message.from_user.id

                # Получение или создание Telegram-профиля
                telegram_profile = await user_service.get_or_create_telegram_profile(telegram_id)

                # Получение или создание чата
                telegram_chat = await user_service.get_or_create_telegram_chat(
                    chat.id,
                    title=chat.title,
                    type=ChatType(chat.type),
                    owner_id=telegram_profile.id
                )

                # Проверка членства
                is_member = await user_service.is_user_in_chat(telegram_profile.id, telegram_chat.id)

                if not is_member:
                    success, response = await user_service.add_user_to_chat(telegram_profile.id, telegram_chat.id)
                    if not success:
                        await message.answer(f"Не удалось добавить вас в чат: {response}")
                        return

                return await handler(message, *args, **kwargs)

        except Exception as e:
            logger.error(f"Ошибка проверки чата: {e}")
            await message.answer("Произошла ошибка при проверке членства в чате")

    return wrapper