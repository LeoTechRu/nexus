# /sd/tg/LeonidBot/models.py
from psycopg2.extensions import JSONB
from sqlalchemy import Column, Integer, BigInteger, String, Date, Boolean, DateTime, Enum, ForeignKey
from base import Base
from datetime import datetime
from enum import IntEnum, Enum as PyEnum

__mapper_args__ = {
    "confirm_deleted_rows": False  # Для PostgreSQL
}

# ------------------------------
# Перечисления (Enums)
# ------------------------------
class UserRole(IntEnum):  # Числовая иерархия ролей
    ban = 0  # Запрещает доступ к боту
    single = 1  # Только личные данные
    multiplayer = 2  # Просмотр участников группы
    moderator = 3  # Редактирование данных участников
    admin = 4  # Полный доступ ко всем функциям


class GroupType(PyEnum):  # Типы групп и каналов
    private = "private"
    public = "public"
    supergroup = "supergroup"
    channel = "channel"


class ChannelType(PyEnum):
    channel = "channel"
    supergroup = "supergroup"

# ------------------------------
# TG профиль
# ------------------------------
class TelegramProfile(Base):
    __tablename__ = 'telegram_profiles'

    # Связь с аккаунтом
    telegram_id = Column(BigInteger, ForeignKey("telegram_accounts.account_id"), primary_key=True)
    user_id = Column(BigInteger, nullable=False)  # Уникальный ID пользователя в Telegram

    # Данные из Bot API (доступны через aiogram)
    username = Column(String(32))  # Имя пользователя (если указано)
    first_name = Column(String(64), nullable=False)  # Имя пользователя
    last_name = Column(String(64))  # Фамилия (если указана)
    is_premium = Column(Boolean, default=False)  # Наличие Telegram Premium
    language_code = Column(String(10))  # Язык интерфейса пользователя
    added_to_attachment_menu = Column(Boolean, default=False)  # Добавлен ли бот в меню вложений
    allows_write_to_pm = Column(Boolean, default=True)  # Разрешено ли отправлять сообщения

    # Фотографии профиля (Bot API: get_user_profile_photos)
    avatar_thumbnail_url = Column(String(500))  # Ссылка на миниатюру аватара
    avatar_small_file_id = Column(String(255))  # ID файла для загрузки маленького аватара
    avatar_big_file_id = Column(String(255))  # ID файла для загрузки большого аватара

    # Данные из MTProto API (доступны через telethon/pyrogram)
    bio = Column(String(500))  # Биография (доступна только для пользователей, разрешивших это)
    phone_number = Column(String(20))  # Номер телефона (доступен только для контактов)
    status = Column(String(50))  # Статус (online, offline, recently, last_week, last_month, long_time_ago)
    last_seen = Column(DateTime)  # Последнее время активности (требует MTProto)
    is_active = Column(Boolean, default=True)  # Активен ли пользователь (на основе последних сообщений)

    # Дополнительные данные (MTProto)
    avatar_full_file_id = Column(String(255))  # Полный ID файла аватара (через MTProto)
    avatar_full_url = Column(String(500))  # Прямая ссылка на полный аватар
    mutual_contacts = Column(JSONB)  # Взаимные контакты (через MTProto)
    pinned_messages = Column(Integer, default=0)  # Количество закрепленных сообщений
    restrictions = Column(JSONB)  # Ограничения пользователя (например, блокировки)

    # Системные поля
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с TelegramAccount  
    account = relationship("TelegramAccount", back_populates="profile")

class User(Base):  # Пользователь
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(32))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    language_code = Column(String(10))
    is_premium = Column(Boolean, default=False)
    full_display_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    birthday = Column(Date)
    role = Column(Integer, default=UserRole.single.value)  # Роль пользователя
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Group(Base):  # Группа
    __tablename__ = 'groups'

    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)  # ID группы в Telegram
    title = Column(String(255), nullable=False)  # Название группы
    type = Column(Enum(GroupType), default=GroupType.private)  # Тип группы
    owner_id = Column(BigInteger, ForeignKey("users.telegram_id"))  # Создатель
    description = Column(String(500))  # Описание
    participants_count = Column(Integer, default=0)  # Кол-во участников
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Channel(Base):  # Канал
    __tablename__ = 'channels'

    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    type = Column(Enum(ChannelType), default=ChannelType.channel)
    owner_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    username = Column(String(32))  # Имя канала
    participants_count = Column(Integer, default=0)
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserGroup(Base):  # Связь пользователь-группа (многие ко многим)
    __tablename__ = 'user_group'

    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), primary_key=True)
    group_id = Column(BigInteger, ForeignKey("groups.telegram_id"), primary_key=True)
    is_owner = Column(Boolean, default=False)
    is_moderator = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)


# Модели для логера:
class LogLevel(PyEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    ERROR = "ERROR"


class LogSettings(Base):
    __tablename__ = 'log_settings'

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)  # ID группы для логов
    level = Column(Enum(LogLevel), default=LogLevel.ERROR)  # Уровень логирования
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def __repr__(self):
    return f"<LogSettings(level='{self.level}', chat_id='{self.chat_id}')>"