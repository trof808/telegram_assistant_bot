from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from langchain_core.tools import BaseTool, tool
from app.config import settings
import json
from typing import Dict, List, Union
from pydantic import BaseModel, Field
import logging
from app.prompts.extract_tasks import extract_tasks_prompt
from app.services import google_calendar_service
from app.services.google_calendar import Task

logger = logging.getLogger(__name__)

class ExtractTasksInput(BaseModel):
    text: str = Field(description="Текст пользователя для извлечения задач")

class GetTasksInput(BaseModel):
    query: str = Field(description="Запрос для поиска задач (может быть пустым для получения всех задач)")

class DeleteTaskInput(BaseModel):
    task_description: str = Field(description="Описание задачи для удаления")

class TaskManagementAgent:
    def __init__(self, api_key: str):
        self.model = GigaChat(credentials=api_key, verify_ssl_certs=False)
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self._config = {"configurable": {"thread_id": "default"}}
        self.google_calendar_service = google_calendar_service
    
    def _create_tools(self) -> List[BaseTool]:
        """
        Создает список инструментов для агента
        """
        
        @tool("add_tasks", args_schema=ExtractTasksInput, return_direct=True)
        def add_tasks_tool(text: str) -> Dict[str, Union[List, str]]:
            """
            Извлекает задачи из текста пользователя. 
            И добавляет их в календарь.
            Используйте этот инструмент когда пользователь:
            - Говорит о планах ("завтра встреча", "нужно купить молоко")
            - Описывает что-то что нужно сделать
            - Упоминает события с датами и временем
            - Планирует активности
            
            Примеры использования:
            - "Завтра в 10 утра встреча с клиентом"
            - "Нужно купить молоко в пятницу"
            - "Планирую поехать в отпуск на следующей неделе"
            """
            try:
                tasks_data = self.extract_tasks_from_text(text)
                logger.info(f"Tasks data: {tasks_data}")
                tasks = [Task(**task) for task in tasks_data["tasks"]]
                return self.google_calendar_service.add_task(tasks)
            except Exception as e:
                logger.error(f"Error adding tasks: {e}")
                return {"tasks": [], "error": f"Ошибка добавления задач: {str(e)}"}
        
        @tool("get_tasks", return_direct=True)
        def get_tasks_tool() -> Dict[str, Union[List, str]]:
            """
            Показывает существующие задачи пользователя.
            Используйте этот инструмент когда пользователь:
            - Хочет посмотреть свои задачи ("покажи мои задачи", "что у меня запланировано")
            - Спрашивает о планах ("какие дела на завтра?", "что нужно сделать?")
            - Хочет увидеть список задач
            
            Примеры использования:
            - "Покажи мои задачи"
            - "Что у меня запланировано?"
            - "Какие дела на завтра?"
            """
            return google_calendar_service.get_tasks()
        
        @tool("delete_task", args_schema=DeleteTaskInput, return_direct=True)
        def delete_task_tool(task_description: str) -> Dict[str, str]:
            """
            Удаляет задачу из списка задач пользователя.
            Используйте этот инструмент когда пользователь:
            - Хочет удалить задачу ("удали задачу про встречу")
            - Отменяет планы ("отмени поездку в магазин")
            - Просит убрать что-то из списка
            
            Примеры использования:
            - "Удали задачу про встречу"
            - "Отмени поездку в магазин"
            - "Убери из списка покупку молока"
            """
            return google_calendar_service.delete_task(task_description)
        
        return [add_tasks_tool, get_tasks_tool, delete_task_tool]
    
    def _create_agent(self):
        """Создает LangGraph агента"""
        from langgraph.prebuilt import create_react_agent
        from langgraph.checkpoint.memory import InMemorySaver
        
        custom_prompt = """
        Ты помощник по задачам. Анализируй запрос и выбирай правильный инструмент:

        ИНСТРУМЕНТЫ:
        - extract_tasks: для добавления новых задач
        - get_tasks: для просмотра задач  
        - delete_task: для УДАЛЕНИЯ задач

        ФОРМАТ:
        Вопрос: {input}
        Мысль: какой инструмент использовать?
        Действие: название_инструмента
        Ввод: параметры
        Результат: ответ инструмента
        Ответ: финальный ответ

        Вопрос: {input}
        Мысль: {agent_scratchpad}
        """
        
        return create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=InMemorySaver(),
            prompt=custom_prompt
        )

    def invoke(self, text: str) -> Dict:
        """Вызов LangGraph агента"""
        return self.agent.invoke(
            {"messages": [("user", text)]},
            config=self._config
        )

    def process_user_request(self, text: str) -> Dict[str, Union[List, str]]:
        try:
            logger.info(f"Processing user request: {text}")
            
            # Вызываем LangGraph агента
            result = self.invoke(text)
            messages = result['messages']
            
            # Ищем результат tool вызова в последнем сообщении
            last_message = messages[-1]
            
            # Если это ответ от tool с return_direct=True 
            if hasattr(last_message, 'content') and isinstance(last_message.content, dict):
                return json.dumps(last_message.content, indent=2, ensure_ascii=False)
            
            # Или если это текстовый ответ
            if hasattr(last_message, 'content'):
                return last_message.content
            
            return {"tasks": [], "message": "Не удалось обработать запрос"}
            
        except Exception as e:
            logger.error(f"Error processing user request: {e}")
            return {"tasks": [], "error": f"Ошибка обработки запроса: {str(e)}"}

    def extract_tasks_from_text(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Распарсить текст и получить оттуда список задач или событий с помощью GigaChat.
        Задачи должны быть получены в формате: {task_description} - {YYYY-MM-DD HH:MM}
        Возвращает словарь со списком найденных задачи и событий
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
        logger.info("extract tasks")

        try:
            res = self.model.invoke(messages)
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

task_management_agent = TaskManagementAgent(api_key=settings.GIGACHAT_API_KEY)

if __name__ == '__main__':
    pass