# from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from app.config import settings
import logging
import os
from app.services import gigachat_service, speech_to_text_service, local_llm_service  # Updated import
import json  # For printing the dict nicely
import asyncio  # Import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context):
    """Handle the /start command"""
    await update.message.reply_text(
        "Привет! Я бот, который может обрабатывать ваши текстовые и голосовые сообщения. Отправьте мне что-нибудь!"
    )


# Helper function to format tasks for reply
def format_tasks_for_reply(extracted_data: dict, source_type: str = "сообщения") -> str:
    if extracted_data and "tasks" in extracted_data:
        tasks = extracted_data.get("tasks", [])
        if tasks:
            response_lines = [f"Я извлек следующие задачи из вашего {source_type}:"]
            for task in tasks:
                title = task.get("title", "Без названия")
                dt_str = task.get("datetime", "не указано")
                duration = task.get("duration_minutes", "не указана")

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
            return f"Я не смог извлечь задачи из вашего {source_type}. Попробуйте сформулировать по-другому."
    else:
        return f"Я не смог извлечь задачи из вашего {source_type} или получил неожиданный ответ от сервиса задач."


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text messages."""
    user_message = update.message.text
    logger.info(
        f"Received text message from {update.effective_user.first_name}: {user_message}"
    )

    # Process the message with GigaChat
    try:
        extracted_data = local_llm_service.extract_tasks_from_text(user_message)
        print(extracted_data)
        logger.info(
            f"GigaChat extracted data for text: {json.dumps(extracted_data, indent=2, ensure_ascii=False)}"
        )
        response_message = format_tasks_for_reply(
            extracted_data, source_type="текстового сообщения"
        )
        await update.message.reply_text(response_message)

    except Exception as e:
        logger.error(f"Error processing text message with GigaChat: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке вашего текстового сообщения моделью."
        )


async def handle_voice_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle voice messages."""
    if not update.message.voice:
        return

    file_id = update.message.voice.file_id
    try:
        voice_file = await context.bot.get_file(file_id)
        # Define a path to save the voice file, e.g., in a temporary directory or just locally
        # Ensure the directory exists if you use a subdirectory
        file_path = f"{file_id}.oga"  # Telegram voice files are often .oga
        await voice_file.download_to_drive(custom_path=file_path)
        logger.info(f"Voice message saved to {file_path}")

        # Transcribe using the service
        transcribed_text = speech_to_text_service.transcribe_audio(file_path)
        logger.info(f"Transcribed text: {transcribed_text}")

        if transcribed_text and not transcribed_text.startswith("Error:"):
            extracted_data_voice = local_llm_service.extract_tasks_from_text(
                transcribed_text
            )
            logger.info(
                f"GigaChat extracted data from voice: {json.dumps(extracted_data_voice, indent=2, ensure_ascii=False)}"
            )
            response_message = format_tasks_for_reply(
                extracted_data_voice, source_type="голосового сообщения"
            )
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text(
                f"Не удалось распознать речь или произошла ошибка: {transcribed_text}"
            )

    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке вашего голосового сообщения."
        )
    finally:
        # Clean up the downloaded voice file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Temporary voice file {file_path} removed.")
            except OSError as e:
                logger.error(f"Error removing temporary voice file {file_path}: {e}")


def run_bot(application: Application) -> None:
    # Get the dispatcher to register handlers
    # application.add_handler(CommandHandler("start", start_command))
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    # application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    pass  # Handlers are added in main_async


async def main_async():
    """Start the bot and FastAPI app."""
    # Initialize Telegram Application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    logger.info("Бот запускается...")

    try:
        # Initialize and start the application components
        await application.initialize()
        await application.start()
        # Start polling. This is a blocking call in the sense that it runs until stopped.
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Бот запущен и принимает обновления.")

        # Keep the main coroutine alive until updater is stopped (e.g., by Ctrl+C / SIGINT)
        # Polling itself now runs in the background managed by application.updater
        # We need a way to keep main_async alive and responsive to shutdown signals.
        # A common way is to wait for a future that only completes on shutdown.
        stop_event = asyncio.Event()
        await stop_event.wait()  # This will wait indefinitely until stop_event.set() is called

    except (KeyboardInterrupt, SystemExit):
        logger.info(
            "Получен сигнал остановки (KeyboardInterrupt/SystemExit), завершаю работу..."
        )
    finally:
        logger.info("Начинаю процедуру остановки бота...")
        if application.updater and application.updater.running:
            logger.info("Останавливаю polling...")
            await application.updater.stop()

        if application.running:
            logger.info("Останавливаю приложение...")
            await application.stop()  # This stops the handlers and other application components

        # Shutdown should be called after stopping everything else.
        # Check if application was initialized before trying to shut it down
        # This requires a small refactor or assuming it was if we reach here after start()
        try:
            # This is important to release resources and call application.shutdown_connections etc.
            await application.shutdown()
            logger.info("Приложение успешно завершено.")
        except Exception as e:
            logger.error(f"Ошибка во время application.shutdown(): {e}")


if __name__ == "__main__":
    # main_async() # Old incorrect call
    asyncio.run(main_async())  # Correct way to run the async function
