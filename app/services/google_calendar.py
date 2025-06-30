from typing import Dict, List, Union
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Task(BaseModel):
    title: str
    datetime: str
    duration_minutes: str


def format_tasks_for_reply(tasks: List[Task], source_type: str = "сообщения") -> str:
    if tasks and len(tasks) > 0:
        response_lines = [f"Я извлек следующие задачи из вашего {source_type}:"]
        for task in tasks:
            title = task.title
            dt_str = task.datetime
            duration = task.duration_minutes

            formatted_dt = dt_str
            # Improve datetime readability if it's in YYYY-MM-DDTHH:MM format
            if "T" in dt_str and len(dt_str.split("T")) == 2:
                date_part, time_part = dt_str.split("T")
                formatted_dt = f"{date_part} в {time_part}"

            response_lines.append(
                f"✅ {title} - {formatted_dt} (длительность: {duration} мин.)"
            )
        return "\n".join(response_lines)
    else:
        return f"Я не смог извлечь задачи из вашего {source_type} или получил неожиданный ответ от сервиса задач."


class GoogleCalendarService:
    def add_task(self, tasks: List[Task]) -> Dict[str, str]:
        """
        Добавить новую задачу или событие в базу данных
        """
        response_message = ""
        for task in tasks:
            logger.info(
                f"Adding task: {task.title} {task.datetime} {task.duration_minutes}"
            )

        response_message = format_tasks_for_reply(
            tasks, source_type="текстового сообщения"
        )
        logger.info(f"Response message: {response_message}")
        return {"message": response_message}

    def get_tasks(self, text: str = "") -> Dict[str, Union[List, str]]:
        """
        Получить список всех запланированных задач из базы данных
        """
        logger.info("get_tasks")
        return {"tasks": [], "message": "Показ задач (пока не реализовано)"}

    def delete_task(self, text: str) -> Dict[str, str]:
        """
        Удаление задач из базы данных
        """
        logger.info("delete_task")
        return {"message": "Задача удалена (пока не реализовано)"}


google_calendar_service = GoogleCalendarService()

if __name__ == "__main__":
    pass
