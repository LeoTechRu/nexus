#/sd/nexus/models/planning.py
'''Модель для планировщика
Единая модель Entity :
Все сущности (проекты, задачи, привычки, заметки) наследуются от базовой модели.
Гибкие связи через Relationship :
Поддержка иерархии (PARA), ссылок (Zettelkasten), временных связей (OCR).
Соответствие методологиям :
GTD: priority, due_date, status.
PARA: Relationship с link_type = 'hierarchy'.
Zettelkasten: tags, Relationship с link_type = 'reference'.
OCR: schedule_type, time_estimated.
Единая точка входа :
Все данные о пользователе хранятся в entities, а специфические детали — в подмоделях.
Гибкость методологий :
PARA: Relationship с link_type = 'hierarchy'.
Zettelkasten: Relationship с link_type = 'reference'.
OCR: Relationship с link_type = 'temporal'.
Без дублирования :
Все сущности наследуются от Entity, избегая повторяющихся полей (title, description, priority).
Безопасность и производительность :
Индексы на user_id, type, link_type ускоряют выборку.
Полиморфизм через __mapper_args__ упрощает работу с сущностями.'''

# Базовая модель для всех сущностей:
class Entity(Base):
    __tablename__ = 'entities'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Владелец
    title = Column(String(255), nullable=False)  # Название
    description = Column(Text)  # Описание
    status = Column(Enum('active', 'completed', 'archived', name='entity_status'), default='active')
    priority = Column(Integer, CheckConstraint('priority BETWEEN 1 AND 5'))  # Приоритет (1-5)
    due_date = Column(DateTime)  # Срок выполнения
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связь с пользователем
    user = relationship("User", back_populates="entities")

    # Тип сущности (полиморфизм через `type`)
    __mapper_args__ = {
        "polymorphic_on": "type",
        "confirm_deleted_rows": False
    }

# Модель проектов
class Project(Entity):
    __tablename__ = 'projects'
    __mapper_args__ = {'polymorphic_identity': 'project'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Управление через FAB
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    kpi_target = Column(JSONB)  # Цели в формате JSON
    kpi_current = Column(JSONB)  # Текущие показатели

    owner = relationship("User", foreign_keys=[owner_id])

# Модель задач
class Task(Entity):
    __tablename__ = 'tasks'
    __mapper_args__ = {'polymorphic_identity': 'task'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    recurrence = Column(Enum('none', 'daily', 'weekly', 'monthly', 'yearly', 'custom'))
    schedule_type = Column(Enum('fixed', 'adaptive'))  # Жёсткое или гибкое планирование
    time_estimated = Column(Integer)  # Примерное время на выполнение
    time_spent = Column(Integer)  # Затраченное время

    # Связь с проектом (если задача привязана к проекту)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    project = relationship("Project", foreign_keys=[project_id])

# Модель привычек
class Habit(Entity):
    __tablename__ = 'habits'
    __mapper_args__ = {'polymorphic_identity': 'habit'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    area_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))  # Сфера жизни
    target_metric = Column(JSONB)  # Цель (например, "30 минут в день")
    current_metric = Column(JSONB)  # Прогресс
    exception_notes = Column(JSONB)  # Исключения (например, праздники)

    # Связь с областью (PARA-методология)
    area = relationship("Entity", foreign_keys=[area_id])

# Модель ресурсов
class Resource(Entity):
    __tablename__ = 'resources'
    __mapper_args__ = {'polymorphic_identity': 'resource'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    content = Column(Text)  # Текст заметки или описания ссылки
    media_url = Column(String(500))  # Внешняя ссылка на файл
    tags = Column(ARRAY(String(50)))  # Теги для поиска (Zettelkasten)
    is_permanent = Column(Boolean, default=False)  # Постоянная ли заметка (или временная)

    # Связь с пользователем
    user = relationship("User", back_populates="resources")

# Модель архивов
class Archive(Entity):
    __tablename__ = 'archives'
    __mapper_args__ = {'polymorphic_identity': 'archive'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    archived_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # Кто архивировал
    archived_from = Column(UUID(as_uuid=True), ForeignKey("entities.id"))  # Из какого состояния
    archived_at = Column(DateTime, default=datetime.utcnow)  # Дата архивации

    # Связь с пользователем
    user = relationship("User", foreign_keys=[archived_by])

# Модель связей для реализации иерархии (PARA), зависимостей (Zettelkasten) и временных связей (OCR):
class Relationship(Base):
    __tablename__ = 'relationships'

    source_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    link_type = Column(Enum('hierarchy', 'reference', 'dependency', 'attachment', 'temporal', 'metadata'))
    weight = Column(Float, default=0.5)  # Важность связи (0.0-1.0)

    # Связь с сущностями
    source = relationship("Entity", foreign_keys=[source_id])
    target = relationship("Entity", foreign_keys=[target_id])

    # Уникальность: один источник → одна цель → один тип связи
    __table_args__ = (UniqueConstraint('source_id', 'target_id', 'link_type'),)

# Модель триггер-действие (например, Достижения и Награды)
class TriggerType(PyEnum):
    """Типы триггеров"""
    TASK_COMPLETION = "task_completion"  # Задача завершена
    HABIT_STREAK = "habit_streak"  # Серия привычки
    ENTITY_ARCHIVED = "entity_archived"  # Сущность архивирована
    CUSTOM = "custom"  # Пользовательский триггер

class ActionType(PyEnum):
    """Типы действий при срабатывании триггера"""
    UNLOCK_REWARD = "unlock_reward"  # Выдача награды
    SEND_NOTIFICATION = "send_notification"  # Отправка уведомления
    UPDATE_PROGRESS = "update_progress"  # Обновление прогресса
    CUSTOM = "custom"  # Пользовательское действие

class TriggerAction(Base):
    __tablename__ = 'trigger_actions'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Владелец
    title = Column(String(255), nullable=False)  # Название триггера
    description = Column(Text)  # Описание
    trigger_type = Column(Enum(TriggerType), nullable=False)  # Тип триггера
    action_type = Column(Enum(ActionType), nullable=False)  # Тип действия
    condition = Column(JSONB, nullable=False)  # Условие срабатывания (например, {"streak": 7})
    action_params = Column(JSONB)  # Параметры действия (например, {"reward": "cup_of_coffee"})
    is_active = Column(Boolean, default=True)  # Активен ли триггер
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)  # Последнее срабатывание
    repeatable = Column(Boolean, default=False)  # Может ли триггер срабатывать повторно

    # Связь с пользователем
    user = relationship("User", back_populates="trigger_actions")

    # Связь с сущностью (проект, задача, привычка)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    entity = relationship("Entity", foreign_keys=[entity_id])

    # Связь с наградой (если action_type == UNLOCK_REWARD)
    reward_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"))
    reward = relationship("Entity", foreign_keys=[reward_id])


# Планировщик задач
class ScheduledTask(Base):
    __tablename__ = 'scheduled_tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("trigger_actions.id"), nullable=False)
    cron_schedule = Column(String(50))  # Расписание (например, "0 0 * * *")
    next_run = Column(DateTime, default=datetime.utcnow)
    last_run = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Связь с триггером
    trigger = relationship("TriggerAction", foreign_keys=[trigger_id])
    # Связь с пользователем
    user = relationship("User", foreign_keys=[user_id])

# Логирование питания
class MealType(PyEnum):
    """Типы приёмов пищи"""
    BREAKFAST = "breakfast"  # Завтрак
    LUNCH = "lunch"  # Обед
    DINNER = "dinner"  # Ужин
    SNACK = "snack"  # Перекус
    CUSTOM = "custom"  # Кастомный тип

class NutritionEntry(Entity):
    __tablename__ = 'nutrition_entries'
    __mapper_args__ = {'polymorphic_identity': 'nutrition'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    fats = Column(Numeric(5, 2))  # Жиры (г)
    carbs = Column(Numeric(5, 2))  # Углеводы (г)
    proteins = Column(Numeric(5, 2))  # Белки (г)
    calories = Column(Numeric(6, 2))  # Калорийность (ккал)
    meal_type = Column(SQLAlchemyEnum(MealType), nullable=False)  # Тип приёма пищи
    meal_date = Column(DateTime, default=datetime.utcnow)  # Дата приёма пищи
    notes = Column(Text)  # Дополнительные заметки

    # Связь с пользователем
    user = relationship("User", foreign_keys=[Entity.user_id])

    # Связь с проектами (например, "Сбросить 50кг")
    projects = relationship("Project", secondary="relationships", back_populates="nutrition_logs")

    # Автоматический расчёт калорий
    def calculate_calories(self):
        if self.fats is not None and self.carbs is not None and self.proteins is not None:
            self.calories = self.fats * 9 + self.carbs * 4 + self.proteins * 4

class Template(Entity):
    __tablename__ = 'templates'
    __mapper_args__ = {'polymorphic_identity': 'template'}

    id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    title = Column(String(255), nullable=False)  # Название шаблона (например, "Похудеть на N кг")
    description = Column(Text)  # Описание шаблона
    blueprint_data = Column(JSONB, nullable=False)  # Структура шаблона в JSONB
    parameters = Column(JSONB)  # Параметры шаблона (например, {"target_weight_loss": 50})
    is_active = Column(Boolean, default=True)  # Активен ли шаблон
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связь с администратором (создателем шаблона)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    owner = relationship("User", foreign_keys=[owner_id])

    # Связь с проектами и задачами шаблона
    projects = relationship("Project", secondary="relationships", back_populates="templates")
    tasks = relationship("Task", secondary="relationships", back_populates="templates")
    habits = relationship("Habit", secondary="relationships", back_populates="templates")
    rewards = relationship("Resource", secondary="relationships", back_populates="templates")

class TemplateInstance(Base):
    __tablename__ = 'template_instances'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    parameters = Column(JSONB)  # Пользовательские параметры (например, {"target_weight_loss": 50})

    # Связь с шаблоном и пользователем
    template = relationship("Template", foreign_keys=[template_id])
    user = relationship("User", foreign_keys=[user_id])

    # Связь с созданными сущностями (проекты, задачи, привычки)
    created_entities = relationship("Entity", secondary="relationships", foreign_keys=[Relationship.source_id, Relationship.target_id])