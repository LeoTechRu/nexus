# /sd/nexus/models/users.py
from sqlalchemy import (Column, Integer, BigInteger, String, Date, Boolean, DateTime,
                        Enum, ForeignKey, Numeric, UniqueConstraint, CheckConstraint)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from flask_appbuilder.models.sqla import Base
from datetime import datetime
from enum import IntEnum, Enum as PyEnum

from flask_appbuilder.security.sqla.models import User

class UserRole(IntEnum):  # Числовая иерархия ролей
    ban = 0  # Запрещает доступ к боту
    single = 1  # Только личные данные
    multiplayer = 2  # Просмотр участников группы
    moderator = 3  # Редактирование данных участников
    admin = 4  # Полный доступ ко всем функциям

"""class User(Base):
    __tablename__ = 'users'

    #id = Column(BigInteger, primary_key=True)  # Уникальный ID пользователя
    #username = Column(String(32), unique=True, nullable=False)  # Логин
    #password_hash = Column(String(128))  # Хэш пароля
    #created_at = Column(DateTime, default=datetime.utcnow)
    #last_login = Column(DateTime)

    # Связи с другими данными
    tg_profiles = relationship("models.tg.TelegramProfile", back_populates="user")
    profiles = relationship("UserProfile", back_populates="user")
    contacts = relationship("UserContact", back_populates="user")
    addresses = relationship("UserAddress", back_populates="user")
    social_accounts = relationship("UserSocialAccount", back_populates="user")
    health = relationship("UserHealth", back_populates="user", uselist=False)
    educations = relationship("UserEducation", back_populates="user")
    employments = relationship("UserEmployment", back_populates="user")
    pets = relationship("UserPet", back_populates="user")
    finances = relationship("UserFinance", back_populates="user", uselist=False)
    preferences = relationship("UserPreference", back_populates="user")
    connections = relationship("UserConnection", back_populates="user")
    life_events = relationship("UserLifeEvent", back_populates="user")
    activity = relationship("UserActivity", back_populates="user")
    attributes = relationship("UserAttribute", back_populates="user")"""

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    user_id = Column(BigInteger, ForeignKey("ab_user.id"), primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    middle_name = Column(String(255))
    birth_date = Column(Date)
    gender = Column(String(10), CheckConstraint("gender IN ('male', 'female', 'other')"))
    nationality = Column(String(100))
    bio = Column(String(500))

    user = relationship("User")

class UserContact(Base):
    __tablename__ = 'user_contacts'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    contact_type = Column(String(50), nullable=False)
    contact_value = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    label = Column(String(50))

    UniqueConstraint(user_id, contact_type, contact_value)
    user = relationship("User")

class UserAddress(Base):
    __tablename__ = 'user_addresses'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    address_type = Column(String(50), nullable=False)
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False)

    user = relationship("User")

class UserSocialAccount(Base):
    __tablename__ = 'user_social_accounts'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # VK, Facebook и т.д.
    account_id = Column(String(255), nullable=False)  # ID в соцсети
    username = Column(String(255))
    profile_url = Column(String(255))
    extra_data = Column(JSONB)  # Дополнительные данные (контакты, биография)
    is_primary = Column(Boolean, default=False)

    UniqueConstraint('user_id', 'platform', 'account_id')
    user = relationship("User")

class UserHealth(Base):
    __tablename__ = 'user_health'

    user_id = Column(BigInteger, ForeignKey("ab_user.id"), primary_key=True)
    height_cm = Column(Numeric(5, 2))
    weight_kg = Column(Numeric(5, 2))
    eye_color = Column(String(50))
    hair_color = Column(String(50))
    skin_tone = Column(String(50))
    blood_type = Column(String(10))
    rh_factor = Column(String(5))
    body_type = Column(String(50))
    allergies = Column(ARRAY(String(100)))  # Аллергии (массив)
    chronic_conditions = Column(ARRAY(String(100)))  # Хронические заболевания
    medications = Column(ARRAY(String(100)))  # Принимаемые лекарства
    stress_level = Column(Integer, CheckConstraint("stress_level BETWEEN 1 AND 10"))  # Уровень стресса
    sleep_quality = Column(Integer, CheckConstraint("sleep_quality BETWEEN 1 AND 10"))  # Качество сна
    notes = Column(String(500))  # Дополнительные заметки

    user = relationship("User")

class UserEducation(Base):
    __tablename__ = 'user_education'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    institution = Column(String(255), nullable=False)  # Учебное заведение
    degree = Column(String(100))  # Степень (бакалавр, магистр и т.д.)
    specialty = Column(String(100))  # Специальность
    start_year = Column(Integer)
    end_year = Column(Integer)
    description = Column(String(500))  # Описание

    user = relationship("User")

class UserEmployment(Base):
    __tablename__ = 'user_employment'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    company = Column(String(255), nullable=False)  # Компания
    position = Column(String(100))  # Должность
    start_date = Column(Date)
    end_date = Column(Date)
    is_current = Column(Boolean, default=False)  # Текущая работа
    description = Column(String(500))  # Описание

    user = relationship("User")

class UserPet(Base):
    __tablename__ = 'user_pets'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    name = Column(String(100), nullable=False)  # Имя питомца
    species = Column(String(100), nullable=False)  # Вид (собака, кошка и т.д.)
    breed = Column(String(100))  # Порода
    birth_date = Column(Date)
    is_healthy = Column(Boolean, default=True)  # Здоров ли питомец
    notes = Column(String(500))  # Дополнительные заметки

    user = relationship("User")

class UserFinance(Base):
    __tablename__ = 'user_finances'

    user_id = Column(BigInteger, ForeignKey("ab_user.id"), primary_key=True)
    income = Column(Numeric(15, 2))  # Доход
    expenses = Column(Numeric(15, 2))  # Расходы
    savings = Column(Numeric(15, 2))  # Накопления
    financial_goals = Column(JSONB)  # Цели в формате JSON
    notes = Column(String(500))  # Дополнительные заметки

    user = relationship("User")

class UserPreference(Base):
    __tablename__ = 'user_preferences'

    preference_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    category = Column(String(100), nullable=False)  # Еда, музыка, спорт и т.д.
    preference = Column(String(255), nullable=False)  # Конкретное предпочтение

    user = relationship("User")

class UserConnection(Base):
    __tablename__ = 'user_connections'

    connection_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    connected_user_id = Column(BigInteger, ForeignKey("ab_user.id"))
    connection_type = Column(String(50), nullable=False)  # друг, семья, коллега и т.д.
    since = Column(Date)
    description = Column(String(500))

    UniqueConstraint('user_id', 'connected_user_id', 'connection_type')
    user = relationship("User", foreign_keys=[user_id])
    connected_user = relationship("User", foreign_keys=[connected_user_id])

class UserLifeEvent(Base):
    __tablename__ = 'user_life_events'

    event_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # рождение, брак, развод и т.д.
    event_date = Column(Date, nullable=False)
    description = Column(String(500))  # Описание

    user = relationship("User")

class UserActivity(Base):
    __tablename__ = 'user_activity'

    activity_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # логин, задача завершена и т.д.
    activity_datetime = Column(DateTime, default=datetime.utcnow)
    details = Column(JSONB)  # Детали события (IP-адрес, действия)

    user = relationship("User")
    
class UserAttribute(Base):  
    __tablename__ = 'user_attributes'  

    attribute_id = Column(BigInteger, primary_key=True)  
    user_id = Column(BigInteger, ForeignKey("ab_user.id"), nullable=False)  
    attribute_name = Column(String(100), nullable=False)  # Название атрибута  
    attribute_value = Column(String(255))  # Значение атрибута  
    attribute_type = Column(String(50))  # Тип (string, int, bool, date, json)  
    created_at = Column(DateTime, default=datetime.utcnow)  

    user = relationship("User")