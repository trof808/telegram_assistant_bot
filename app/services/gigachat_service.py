from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from app.config import settings
import json
from typing import Dict, List
import logging
from app.prompts.extract_tasks import extract_tasks_prompt

logger = logging.getLogger(__name__)

class GigaChatService:
    def __init__(self, api_key: str):
        self.giga = GigaChat(
            credentials=api_key,
            verify_ssl_certs=False,  # As per documentation for ease of use
            # model="GigaChat-Pro", # Consider making this configurable if needed
        )

    def extract_tasks_from_text(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Extracts tasks from a given text using GigaChat.
        Tasks should be in the format: {task_description} - {YYYY-MM-DD HH:MM}
        Returns a dictionary with a list of tasks.
        Example:
        {
            "tasks": [
                {"title": "Buy milk", "datetime": "2024-07-21 10:00", "duration_minutes": "30"},
                {"title": "Call John", "datetime": "2024-07-22 15:00", "duration_minutes": "15"}
            ]
        }
        """
        
        messages = [
            SystemMessage(content=extract_tasks_prompt()),
            HumanMessage(content=text),
        ]

        try:
            res = self.giga.invoke(messages)
            tasks_data = json.loads(res.content)
            logger.info(f"GigaChat response: {tasks_data}")
            if isinstance(tasks_data, dict) and "tasks" in tasks_data and isinstance(tasks_data["tasks"], list):
                return tasks_data
            else:
                return {"tasks": [], "error": "Invalid overall structure"}

        except json.JSONDecodeError:
            return {"tasks": [], "error": "JSONDecodeError"}
        except Exception as e:
            return {"tasks": []}

gigachat_service = GigaChatService(api_key=settings.GIGACHAT_API_KEY)

if __name__ == '__main__':
    pass