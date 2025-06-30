from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def extract_tasks_prompt() -> str:
    """
    Промпт для извлечения задач из текста пользователя
    """
    current_datetime = datetime.now()
    current_date_str = current_datetime.strftime("%Y-%m-%d")
    current_time_str = current_datetime.strftime("%H:%M")
    current_weekday = current_datetime.strftime("%A")
    
    # Переводим день недели на русский
    weekday_translation = {
        "Monday": "понедельник",
        "Tuesday": "вторник", 
        "Wednesday": "среда",
        "Thursday": "четверг",
        "Friday": "пятница",
        "Saturday": "суббота",
        "Sunday": "воскресенье"
    }
    current_weekday_ru = weekday_translation.get(current_weekday, current_weekday)
    logger.info(f"Current datetime: {current_datetime.strftime('%Y-%m-%d %H:%M')}")
    
    # Рассчитываем ключевые даты для примеров
    tomorrow = (current_datetime + timedelta(days=1)).strftime('%Y-%m-%d')
    day_after_tomorrow = (current_datetime + timedelta(days=2)).strftime('%Y-%m-%d')
    
    return f"""Ты умный ассистент для извлечения задач из текста.

ТЕКУЩАЯ ДАТА И ВРЕМЯ: {current_date_str} {current_time_str} ({current_weekday_ru})

ЗАДАЧА: Найди в тексте задачи/события и верни JSON в формате:
{{"tasks": [{{"title": "описание", "datetime": "YYYY-MM-DD HH:MM", "duration_minutes": "30"}}]}}

КРИТИЧЕСКИ ВАЖНО - ПРАВИЛА ОБРАБОТКИ ОТНОСИТЕЛЬНЫХ ДАТ:
1. "завтра" = {tomorrow} (НЕ {current_date_str}!)
2. "послезавтра" = {day_after_tomorrow}
3. "сегодня" = {current_date_str}

АЛГОРИТМ ОБРАБОТКИ:
Шаг 1: Найди в тексте упоминания времени/даты
Шаг 2: Если есть "завтра" - используй дату {tomorrow}
Шаг 3: Если есть "послезавтра" - используй дату {day_after_tomorrow}
Шаг 4: Если есть "сегодня" - используй дату {current_date_str}
Шаг 5: Преобразуй время в 24-часовой формат

ПРИМЕРЫ ВРЕМЕНИ:
- "в девять" = 09:00
- "в 9 утра" = 09:00  
- "в 2 дня" = 14:00
- "в 5 вечера" = 17:00
- "утром" = 09:00
- "днем" = 12:00
- "вечером" = 18:00

ТЕСТОВЫЕ ПРИМЕРЫ:
Текст: "завтра в девять мне нужно быть на участке"
Результат: {{"tasks": [{{"title": "быть на участке", "datetime": "{tomorrow} 09:00", "duration_minutes": "30"}}]}}

Текст: "сегодня в 15:00 встреча"
Результат: {{"tasks": [{{"title": "встреча", "datetime": "{current_date_str} 15:00", "duration_minutes": "60"}}]}}

ВАЖНО: 
- Всегда используй формат YYYY-MM-DD HH:MM
- Если дата не указана - НЕ добавляй задачу
- Если задач нет - верни {{"tasks": []}}
- НЕ добавляй лишних пояснений, только JSON

ПЕРЕД ОТВЕТОМ ПОДУМАЙ:
1. Есть ли в тексте слово "завтра"? Если да, дата = {tomorrow}
2. Есть ли в тексте слово "сегодня"? Если да, дата = {current_date_str}
3. Есть ли в тексте слово "послезавтра"? Если да, дата = {day_after_tomorrow}
4. Какое время указано? Преобразуй в 24-часовой формат.

НАПОМИНАНИЕ: "завтра" = {tomorrow}, НЕ {current_date_str}!

Обработай следующий текст:"""
