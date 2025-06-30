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
from app.services import speech_to_text_service
import json 
import asyncio
from app.agents import task_management_agent

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


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle text messages."""
    user_message = update.message.text
    logger.info(f"Received text message from {update.effective_user.first_name}: {user_message}")

    try:
        result_data = task_management_agent.process_user_request(user_message)
        logger.info(f"Service response: {result_data}")

        # Если результат - строка (JSON), парсим её
        if isinstance(result_data, str):
            try:
                parsed_data = json.loads(result_data)
                response_message = parsed_data.get("message", result_data)
            except json.JSONDecodeError:
                response_message = result_data
        elif isinstance(result_data, dict) and "message" in result_data:
            response_message = result_data["message"]
        else:
            response_message = "Запрос обработан, но результат неясен."
        
        await update.message.reply_text(response_message)

    except Exception as e:
        logger.error(f"Error processing text message: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке вашего сообщения."
        )


async def handle_voice_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Обработка голосовых сообщений."""
    if not update.message.voice:
        return

    file_id = update.message.voice.file_id
    try:
        voice_file = await context.bot.get_file(file_id)
        file_path = f"{file_id}.oga"
        await voice_file.download_to_drive(custom_path=file_path)
        logger.info(f"Voice message saved to {file_path}")

        transcribed_text = speech_to_text_service.transcribe_audio(file_path)
        logger.info(f"Transcribed text: {transcribed_text}")

        if transcribed_text and not transcribed_text.startswith("Error:"):
            result_data = task_management_agent.process_user_request(
                transcribed_text
            )
            logger.info(
                f"GigaChat extracted data from voice: {json.dumps(result_data, indent=2, ensure_ascii=False)}"
            )

            if isinstance(result_data, str):
                try:
                    parsed_data = json.loads(result_data)
                    response_message = parsed_data.get("message", result_data)
                except json.JSONDecodeError:
                    response_message = result_data
            elif isinstance(result_data, dict) and "message" in result_data:
                response_message = result_data["message"]
            else:
                response_message = "Запрос обработан, но результат неясен."
            
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
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Temporary voice file {file_path} removed.")
            except OSError as e:
                logger.error(f"Error removing temporary voice file {file_path}: {e}")



async def main_async():
    """Start the bot and FastAPI app."""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    logger.info("Бот запускается...")

    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Бот запущен и принимает обновления.")

        stop_event = asyncio.Event()
        await stop_event.wait()

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
            await application.stop()

        try:
            await application.shutdown()
            logger.info("Приложение успешно завершено.")
        except Exception as e:
            logger.error(f"Ошибка во время application.shutdown(): {e}")


if __name__ == "__main__":
    asyncio.run(main_async())
