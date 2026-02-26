import asyncio
import random
import time

from db import (
    init_db,
    add_word,
    get_words,
    get_word_for_training,
    update_word_success,
    update_word_fail
)

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from translate import translate_word
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

LEVEL_1 = [
    "apple", "book", "water", "dog", "cat",
    "house", "car", "street", "food", "milk",
    "bread", "coffee", "tea", "sun", "moon",
    "day", "night", "time", "hand", "eye",
    "head", "face", "friend", "family", "child",
    "man", "woman", "boy", "girl", "school",
    "work", "city", "country", "room", "door",
    "window", "table", "chair", "bed", "phone",
    "computer", "money", "shop", "market", "store",
    "go", "come", "see", "look", "eat",
    "drink", "sleep", "run", "walk", "sit",
    "stand", "take", "give", "make", "say",
    "speak", "read", "write", "open", "close",
    "big", "small", "good", "bad", "happy",
    "sad", "hot", "cold", "new", "old",
    "fast", "slow", "easy", "hard", "long",
    "short", "right", "left", "up", "down",
    "yes", "no", "hello", "bye", "please",
    "thanks", "sorry", "today", "tomorrow", "now"
]

LEVEL_2 = [
    "morning", "evening", "week", "month", "year",
    "weather", "rain", "snow", "wind", "cloud",
    "river", "lake", "forest", "mountain", "beach",
    "travel", "trip", "ticket", "airport", "train",
    "bus", "station", "hotel", "room", "key",
    "doctor", "nurse", "hospital", "medicine", "health",
    "strong", "weak", "clean", "dirty", "beautiful",
    "ugly", "angry", "tired", "hungry", "thirsty",
    "music", "song", "movie", "film", "game",
    "sport", "football", "basketball", "tennis", "swim",
    "jump", "drive", "fly", "build", "fix",
    "cook", "wash", "help", "learn", "teach",
    "understand", "remember", "forget", "start", "finish",
    "buy", "sell", "pay", "cost", "price",
    "color", "red", "blue", "green", "yellow",
    "black", "white", "brown", "pink", "orange",
    "animal", "bird", "fish", "horse", "cow",
    "sheep", "pig", "chicken", "mouse", "rabbit",
    "body", "arm", "leg", "foot", "back",
    "hair", "nose", "mouth", "teeth", "heart",
    "family", "parents", "mother", "father", "sister",
    "brother", "cousin", "uncle", "aunt", "grandmother",
    "grandfather", "job", "boss", "worker", "company",
    "office", "meeting", "project", "task", "plan",
    "question", "answer", "idea", "problem", "solution",
    "happy", "excited", "bored", "worried", "calm",
    "early", "late", "always", "never", "sometimes",
    "often", "usually", "together", "alone", "again"
]

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить слово")],
        [KeyboardButton(text="📚 Список слов")],
        [KeyboardButton(text="🎯 Тренировка")],
        [KeyboardButton(text="📦 Готовые уровни слов")],
    ],
    resize_keyboard=True
)

training_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⛔ Стоп")],
    ],
    resize_keyboard=True
)

API_TOKEN = "8286686650:AAE1Gjz3URWB9_UYMJqtjfjeey6-aiGtTWY"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_training_word = {}

class AddWordState(StatesGroup):
    waiting_for_word = State()

class TrainingState(StatesGroup):
    waiting_for_answer = State()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я помогу тебе учить английские слова.\n\n"
        "Выбери действие на клавиатуре ниже:",
        reply_markup=main_kb
    )

@dp.message(F.text == "📚 Список слов")
async def list_words_button(message: types.Message):
    words = await get_words(message.from_user.id)
    if not words:
        await message.answer("У тебя пока нет сохранённых слов.")
        return

    text = "📚 Твои слова:\n\n" + "\n".join(f"• {w}" for w in words)
    await message.answer(text)

async def start_training(message: types.Message, state: FSMContext):
    words = await get_words(message.from_user.id)
    if not words:
        await message.answer("У тебя пока нет слов для тренировки.", reply_markup=main_kb)
        return

    word = random.choice(words)
   
    user_training_word[message.from_user.id] = word

    await message.answer(
        f"Переведи слово: {word}",
        reply_markup=training_kb
    )

    await state.set_state(TrainingState.waiting_for_answer)

@dp.message(lambda m: m.text == "🎯 Тренировка")
async def training_button(message: types.Message, state: FSMContext):
    await start_training(message, state)

@dp.message(TrainingState.waiting_for_answer)
async def training_answer(message: types.Message, state: FSMContext):
    # Стоп
    if "стоп" in message.text.lower():
        await state.clear()
        await message.answer("Тренировка остановлена.", reply_markup=main_kb)
        return

    word = user_training_word.get(message.from_user.id)
    if not word:
        await message.answer("Ошибка. Начни тренировку заново.", reply_markup=main_kb)
        await state.clear()
        return

   
    user_answer = message.text.strip().lower()
    correct_answer = await translate_word(word)  

    correct_ru = correct_answer["translation"].strip().lower()

    if user_answer == correct_ru:         
        await message.answer("Верно! 👍")
    else:
        await message.answer(f"Неверно ❌\nПравильный ответ: {correct_ru}")

    words = await get_words(message.from_user.id)
    if not words:
        await message.answer("Слова закончились.", reply_markup=main_kb)
        await state.clear()
        return

    new_word = random.choice(words)
    user_training_word[message.from_user.id] = new_word

    await message.answer(
        f"Переведи слово: {new_word}",
        reply_markup=training_kb
    ) 

@dp.message(lambda m: m.text == "➕ Добавить слово")
async def add_word_button(message: types.Message, state: FSMContext):
    await message.answer("Напиши слово, которое хочешь сохранить:")
    await state.set_state(AddWordState.waiting_for_word)

@dp.message(F.text == "📦 Готовые уровни слов")
async def choose_level(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Уровень 1")],
            [KeyboardButton(text="Уровень 2")],
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери уровень:", reply_markup=kb)

@dp.message(F.text.startswith("Уровень"))
async def add_level_words(message: types.Message, state: FSMContext):
    level = message.text.split()[1]  # "1" или "2"

    if level == "1":
        words = LEVEL_1
    elif level == "2":
        words = LEVEL_2
    else:
        await message.answer("Такого уровня нет.")
        return

    count = 0
    for w in words:
        saved = await add_word(message.from_user.id, w)
        if saved:
            count += 1

    await message.answer(f"Готово! Добавлено {count} слов.")
    # СРАЗУ запускаем тренировку
    await start_training(message, state)

@dp.message(Command("add"))
async def add_word_command(message: types.Message, state: FSMContext):
    await message.answer("Напиши слово, которое хочешь добавить.")
    await state.set_state(AddWordState.waiting_for_word)

@dp.message(AddWordState.waiting_for_word)
async def catch_word(message: types.Message, state: FSMContext):
    print("Received message:", message.text)
    word = message.text.strip()

    saved = await add_word(message.from_user.id, word)

    if not saved:
        await message.answer(f"Слово '{word}' уже есть в твоём списке.")
        await state.clear()
        return

    info = await translate_word(word)

    text = f"Слово '{word}' сохранено.\n\n"
    text += f"🇷🇺 Перевод: {info['translation']}\n"
    text += f"📘 Значение: {info['definition_ru']}\n"

    if info["phonetic"]:
        text += f"🔊 Транскрипция: {info['phonetic']}\n"

    text += "\n✏️ Пример:\n"
    text += f"EN: {info['example_en']}\n"
    text += f"RU: {info['example_ru']}\n"

    await message.answer(text)
    await state.clear()

async def main():
    await init_db()
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
