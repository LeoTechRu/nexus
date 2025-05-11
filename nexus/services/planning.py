class TemplateService:
    def __init__(self):
        self.session = db_session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

    async def apply_template(self, template_id: UUID, user_id: UUID, parameters: dict):
        """Применение шаблона пользователем"""
        template = self.session.query(Template).filter_by(id=template_id).first()
        if not template or not template.is_active:
            return False, "Шаблон не найден или не активен"

        # Подстановка параметров в шаблон
        blueprint = template.blueprint_data
        substituted_blueprint = self.substitute_parameters(blueprint, parameters)

        # Создание области "Здоровье"
        area = substituted_blueprint.get("area", {})
        health_area = Entity(
            id=uuid.uuid4(),
            user_id=user_id,
            title=area.get("title", "Здоровье"),
            description=area.get("description", "Сфера жизни: здоровье, спорт, питание"),
            type="area"
        )
        self.session.add(health_area)

        # Создание проекта "Сбросить N кг"
        project = substituted_blueprint.get("project", {})
        weight_loss_project = Project(
            id=uuid.uuid4(),
            user_id=user_id,
            title=project.get("title", "Сбросить 50 кг"),
            description=project.get("description", "Цель: похудеть на 50 кг"),
            kpi_target=project.get("kpi_target", {"target_weight_loss": 50}),
            kpi_current={"current_weight_loss": 0}
        )
        self.session.add(weight_loss_project)

        # Связь проекта с областью через Relationship
        relationship_area_project = Relationship(
            source_id=health_area.id,
            target_id=weight_loss_project.id,
            link_type="dependency"
        )
        self.session.add(relationship_area_project)

        # Создание ключевых результатов (-10кг, -20кг и т.д.)
        tasks = substituted_blueprint.get("tasks", [])
        for task_data in tasks:
            task = Task(
                id=uuid.uuid4(),
                user_id=user_id,
                title=task_data.get("title", "Сбросить 10кг"),
                description=task_data.get("description", "Контрольная точка"),
                type="task",
                status="active",
                project_id=weight_loss_project.id
            )
            self.session.add(task)

            # Связь задачи с проектом
            relationship_task_project = Relationship(
                source_id=task.id,
                target_id=weight_loss_project.id,
                link_type="dependency"
            )
            self.session.add(relationship_task_project)

        # Создание привычек (тренеровка, питание, вода)
        habits = substituted_blueprint.get("habits", [])
        for habit_data in habits:
            habit = Habit(
                id=uuid.uuid4(),
                user_id=user_id,
                title=habit_data.get("title", "Ежедневная тренировка"),
                description=habit_data.get("description", "30 минут кардио"),
                type="habit",
                area_id=health_area.id,
                target_metric=habit_data.get("target_metric", {"daily_calories_burned": 500}),
                current_metric={"today": 0, "streak": 0}
            )
            self.session.add(habit)

            # Связь привычки с проектом
            relationship_habit_project = Relationship(
                source_id=habit.id,
                target_id=weight_loss_project.id,
                link_type="dependency"
            )
            self.session.add(relationship_habit_project)

        # Создание наград и триггеров
        rewards = substituted_blueprint.get("rewards", [])
        for reward_data in rewards:
            # Создание награды
            reward = Resource(
                id=uuid.uuid4(),
                user_id=user_id,
                title=reward_data.get("title", "Стакан кофе"),
                description=reward_data.get("description", "Награда за 5 дней тренировок"),
                type="resource"
            )
            self.session.add(reward)

            # Создание триггера
            trigger = TriggerAction(
                id=uuid.uuid4(),
                user_id=user_id,
                title=reward_data.get("trigger", {}).get("title", "Награда за 5 дней тренировок"),
                trigger_type=reward_data.get("trigger", {}).get("type", "habit_streak"),
                action_type="unlock_reward",
                condition=reward_data.get("trigger", {}).get("condition", {"streak": 5}),
                action_params={"reward": reward.id},
                is_active=True
            )
            self.session.add(trigger)

            # Связь триггера с привычкой
            habit = self.session.query(Habit).filter_by(title=reward_data.get("trigger", {}).get("habit_title", "Ежедневная тренировка")).first()
            if habit:
                relationship_trigger_habit = Relationship(
                    source_id=trigger.id,
                    target_id=habit.id,
                    link_type="dependency"
                )
                self.session.add(relationship_trigger_habit)

        # Сохранение всех изменений
        self.session.commit()

        return True, f"Создано: {len(tasks)} задач, {len(habits)} привычек, {len(rewards)} наград"

    def substitute_parameters(self, blueprint: dict, parameters: dict):
        """Подстановка пользовательских параметров в шаблон (например, target_weight_loss = 50)"""
        # Рекурсивная замена {target_weight_loss} на значение из parameters
        return substitute_dict_values(blueprint, parameters)

def substitute_dict_values(data: dict, params: dict):
    """Рекурсивная замена параметров в JSON-структуре"""
    if isinstance(data, dict):
        return {k: substitute_dict_values(v, params) for k, v in data.items()}
    elif isinstance(data, str) and data.startswith("{") and data.endswith("}"):
        param_name = data[1:-1]  # Удаление {}
        return params.get(param_name, data)  # Замена на значение из parameters
    return data