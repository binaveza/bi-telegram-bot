import json
import logging
import threading
import time

import telebot
from admin import create_assistant, get_assistant_id, get_thread_id, upload_file
from chat import process_message
from config import TG_BOT_ADMIN, TG_BOT_TOKEN
from telebot.types import InputFile

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(TG_BOT_TOKEN, threaded=False)


is_typing = False


def start_typing(chat_id):
    global is_typing
    is_typing = True
    typing_thread = threading.Thread(target=typing, args=(chat_id,))
    typing_thread.start()


def typing(chat_id):
    global is_typing
    while is_typing:
        bot.send_chat_action(chat_id, "typing")
        time.sleep(4)


def stop_typing():
    global is_typing
    is_typing = False


def check_setup(message):
    if not get_assistant_id():
        if message.from_user.username != TG_BOT_ADMIN:
            bot.send_message(
                message.chat.id, "Бот еще не настроен. Свяжитесь с администратором."
            )
        else:
            bot.send_message(
                message.chat.id,
                "Бот еще не настроен. Используйте команду /create для создания ассистента.",
            )
        return False
    return True


def check_admin(message):
    if message.from_user.username != TG_BOT_ADMIN:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return False
    return True


@bot.message_handler(commands=["help", "start"])
def send_welcome(message):
    if not check_setup(message):
        return

    bot.send_message(
        message.chat.id,
        (
            f"Привет! Я твой карманный дата-аналитик. Загрузи файл и задавай вопросы по нему. Я умею проводить анализ данных и строить графики."
        ),
    )


@bot.message_handler(commands=["create"])
def create_assistant_command(message):
    if not check_admin(message):
        return

    instructions = message.text.split("/create")[1].strip()
    if len(instructions) == 0:
        bot.send_message(
            message.chat.id,
            """
Введите подробные инструкции для работы ассистента после команды /create и пробела.

Например: 
/create Ты - дата-аналитик. Пользователь загружает файл для анализа, а ты, используя инструменты, отвечаешь на вопросы и, если нужно, строишь графики.

Если ассистент уже был ранее создан, инструкции будут обновлены.
            """,
        )
        return

    name = bot.get_me().full_name
    create_assistant(name, instructions)

    bot.send_message(
        message.chat.id,
        "Ассистент успешно создан. Теперь вы можете добавлять документы в базу знаний с помощью команды /upload.",
    )


@bot.message_handler(commands=["upload"])
def upload_file_command(message):
    if not check_setup(message):
        return

    return bot.send_message(message.chat.id, "Загрузите файл с данными для анализа.")


@bot.message_handler(content_types=["document"])
def upload_file_handler(message):
    if not check_setup(message):
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    try:
        upload_file(message.chat.id, message.document.file_name, downloaded_file)
    except Exception as e:
        return bot.send_message(message.chat.id, f"Ошибка при загрузке файла: {e}")

    return bot.send_message(
        message.chat.id,
        "Файл успешно загружен и новая сессия анализа начата. Задавайте ваши вопросы.",
    )


@bot.message_handler(content_types=["text"])
def handle_message(message):
    if not check_setup(message):
        return

    if not get_thread_id(str(message.chat.id)):
        return bot.send_message(
            message.chat.id,
            "Для начала работы загрузите файл с данными для анализа с помощью команды /upload.",
        )

    start_typing(message.chat.id)

    try:
        answers = process_message(str(message.chat.id), message.text)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при обработке сообщения: {e}")
        return

    stop_typing()

    for answer in answers:
        if answer["type"] == "text":
            bot.send_message(message.chat.id, answer["text"])
        elif answer["type"] == "image":
            bot.send_photo(message.chat.id, InputFile(answer["file"]))
        elif answer["type"] == "file":
            bot.send_document(
                message.chat.id,
                InputFile(answer["file"]),
                visible_file_name=answer["filename"],
            )


def handler(event, context):
    message = json.loads(event["body"])
    update = telebot.types.Update.de_json(message)

    if update.message is not None:
        try:
            bot.process_new_updates([update])
        except Exception as e:
            print(e)

    return {
        "statusCode": 200,
        "body": "ok",
    }