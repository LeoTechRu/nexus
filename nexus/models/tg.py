# /sd/nexus/models/tg.py
from sqlalchemy import Column, Integer, BigInteger, String, Date, Boolean, DateTime, Enum, ForeignKey
from flask_appbuilder.models.sqla import Base
from datetime import datetime
from enum import IntEnum, Enum as PyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint
from flask_appbuilder.security.sqla.models import User

__mapper_args__ = {"confirm_deleted_rows": False}

# ------------------------------
# Перечисления (Enums)
# ------------------------------
class TelegramUserRole(IntEnum):
    """Роли пользователей в Telegram-чатах"""
    banned = 0          # Заблокирован
    member = 1         # Обычный участник
    admin = 2          # Администратор
    creator = 3        # Создатель чата

class ChatType(PyEnum):
    """Типы чатов в Telegram"""
    private = "private"
    public = "public"
    supergroup = "supergroup"
    channel = "channel"

class LogLevel(PyEnum):
    """Уровни логирования"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    ERROR = "ERROR"

# ------------------------------
# Telegram-профиль
# ------------------------------
class TelegramProfile(Base):
    __tablename__ = 'telegram_profiles'

    # Уникальный ID профиля и ссылка на пользователя
    id = Column(BigInteger, primary_key=True)  # Telegram ID (уникальный)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)  # Ссылка на пользователя

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
    avatar_small_file_id = Column(String(255))  # ID файла для маленького аватара
    avatar_big_file_id = Column(String(255))  # ID файла для большого аватара

    # Данные из MTProto API (через telethon/pyrogram)
    bio = Column(String(500))  # Биография
    phone_number = Column(String(20))  # Номер телефона
    status = Column(String(50))  # Статус (online, offline и т.д.)
    last_seen = Column(DateTime)  # Последнее время активности
    is_active = Column(Boolean, default=True)  # Активен ли пользователь

    # Дополнительные данные из MTProto
    mutual_contacts = Column(JSONB)  # Взаимные контакты (через MTProto)
    pinned_messages = Column(Integer, default=0)  # Количество закрепленных сообщений
    restrictions = Column(JSONB)  # Ограничения пользователя (например, блокировки)

    # Системные поля
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с Users
    user = relationship("User")

    # Связь с чатами
    chats = relationship("TelegramChat", secondary="chat_member", back_populates="participants")

# ------------------------------
# Telegram-чаты (группы и каналы)
# ------------------------------
class TelegramChat(Base):
    __tablename__ = 'telegram_chats'

    # Уникальный ID чата и тип
    id = Column(BigInteger, primary_key=True)  # Telegram ID чата
    title = Column(String(255), nullable=False)  # Название
    type = Column(Enum(ChatType), default=ChatType.private)  # Тип (private, supergroup, channel)
    username = Column(String(32))  # Username чата (если есть)

    # Данные о владельце и участниках
    owner_id = Column(BigInteger, ForeignKey("telegram_profiles.id"))  # ID владельца
    participants = relationship("TelegramProfile", secondary="chat_member", back_populates="chats")

    # Основные параметры чата
    description = Column(String(500))  # Описание
    invite_link = Column(String(500))  # Пригласительная ссылка
    participants_count = Column(Integer, default=0)  # Количество участников
    is_forum = Column(Boolean, default=False)  # Является ли форумом
    has_protected_content = Column(Boolean, default=False)  # Защита контента
    slow_mode_delay = Column(Integer, default=0)  # Задержка между сообщениями

    # Дополнительные данные из MTProto
    pinned_message = Column(String(500))  # Закрепленное сообщение
    is_verified = Column(Boolean, default=False)  # Верифицирован ли чат
    has_aggressive_anti_spam = Column(Boolean, default=False)  # Анти-спам включен
    sticker_set_name = Column(String(255))  # Название стикерпака
    custom_emoji_status = Column(String(255))  # Кастомный эмодзи-статус
    restriction_reason = Column(String(500))  # Причина ограничения

    # Фотографии чата (хранятся как JSONB)
    photos = Column(JSONB)  # {"small_file_id": "...", "big_file_id": "...", "full_file_id": "..."}

    # Сообщения чата (хранятся как JSONB)
    messages = Column(JSONB)  # [{"message_id": 1, "text": "...", "pinned": true}, ...]

    # Права администраторов (хранятся как JSONB)
    admin_rights = Column(JSONB)  # {"can_manage_chat": true, "can_delete_messages": true, ...}

    # Связь с владельцем
    owner = relationship("TelegramProfile", foreign_keys=[owner_id])

    # Системные поля
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ------------------------------
# Связь пользователь-чат
# ------------------------------
class ChatMember(Base):
    __tablename__ = 'chat_member'

    # Связь профиль-чат
    profile_id = Column(BigInteger, ForeignKey("telegram_profiles.id"), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("telegram_chats.id"), primary_key=True)

    # Роль и права
    role = Column(Enum(TelegramUserRole), default=TelegramUserRole.member)
    can_send_messages = Column(Boolean, default=False)
    can_send_media = Column(Boolean, default=False)
    can_restrict_members = Column(Boolean, default=False)

    # Дополнительные данные
    joined_at = Column(DateTime, default=datetime.utcnow)  # Дата присоединения
    until_date = Column(DateTime)  # Дата истечения прав

    # Связь с профилем и чатом
    profile = relationship("TelegramProfile", overlaps="chats,participants")
    chat = relationship("TelegramChat", overlaps="chats,participants")

    # Уникальность: один профиль не может быть участником одного чата дважды
    __table_args__ = (UniqueConstraint('profile_id', 'chat_id'),)

# ------------------------------
# Настройки логирования
# ------------------------------
class LogSettings(Base):
    __tablename__ = 'log_settings'

    id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey("telegram_chats.id"), nullable=False)  # ID чата для логов
    level = Column(Enum(LogLevel), default=LogLevel.ERROR)  # Уровень логирования

    # Связь с чатом
    chat = relationship("TelegramChat")

    # Системные поля
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LogSettings(level='{self.level}', chat_id='{self.chat_id}')>"

# ------------------------------
# Дополнительные данные о чате (необязательно, можно хранить в JSONB)
# ------------------------------
class ChatExtraData(Base):
    __tablename__ = 'chat_extra_data'

    chat_id = Column(BigInteger, ForeignKey("telegram_chats.id"), primary_key=True)
    key = Column(String(50), primary_key=True)  # Например: "custom_emoji_status"
    value = Column(String(255))  # Значение (можно хранить JSONB для сложных данных)

    # Связь с чатом
    chat = relationship("TelegramChat", back_populates="extra_data")

    # Уникальность: один чат + один ключ → одно значение
    __table_args__ = (UniqueConstraint('chat_id', 'key'),)

TelegramChat.extra_data = relationship("ChatExtraData", back_populates="chat")