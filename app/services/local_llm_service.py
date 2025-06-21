from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
import json
import logging
from typing import Dict, List
from app.prompts.extract_tasks import extract_tasks_prompt

logger = logging.getLogger(__name__)

class LocalLLMService:
    def __init__(self, model_name: str, base_url: str):
        try:
            self.llm = ChatOllama(
                model=model_name,
                base_url=base_url,
                format="json"
            )

            logger.info(f"LocalLLMService initialized with model: {model_name} at {base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize ChatOllama with model {model_name} at {base_url}: {e}")
            logger.error("Please ensure Ollama is running and the model is available.")
            self.llm = None

    def extract_tasks_from_text(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Extracts tasks from a given text using local LLM.
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
        if not self.llm:
            logger.error("LocalLLMService not initialized properly. Cannot extract tasks.")
            return {"tasks": []}
        
        messages = [
            SystemMessage(content=extract_tasks_prompt()),
            HumanMessage(content=text),
        ]

        try:
            res = self.llm.invoke(messages)
            logger.debug(f"Local LLM raw response: {res.content}")
            tasks_data = json.loads(res.content)
            
            if isinstance(tasks_data, dict) and "tasks" in tasks_data and isinstance(tasks_data["tasks"], list):
                return tasks_data
            else:
                logger.warning(f"Unexpected JSON structure from local LLM: {tasks_data}")
                return {"tasks": []}

        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError from local LLM response: {res.content}. Error: {e}")
            return {"tasks": []}
        except Exception as e:
            logger.error(f"An unexpected error occurred with local LLM: {e}")
            return {"tasks": []}


local_llm_service = LocalLLMService(
    model_name=settings.LOCAL_LLM_MODEL_NAME,
    base_url=settings.OLLAMA_BASE_URL
)

if __name__ == '__main__':
    pass 