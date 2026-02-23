import asyncio
from db import init_db, add_word, get_words
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from translate import translate_word
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить слово")],
        [KeyboardButton(text="📚 Список слов")],
        [KeyboardButton(text="🎯 Тренировка")],
    ],
    resize_keyboard=True
)

API_TOKEN = "8286686650:AAE1Gjz3URWB9_UYMJqtjfjeey6-aiGtTWY"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AddWordState(StatesGroup):
    waiting_for_word = State()

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

@dp.message(lambda m: m.text == "🎯 Тренировка")
async def training_button(message: types.Message):
    await message.answer("Тренировка скоро будет доступна!")

@dp.message(lambda m: m.text == "➕ Добавить слово")
async def add_word_button(message: types.Message, state: FSMContext):
    await message.answer("Напиши слово, которое хочешь сохранить:")
    await state.set_state(AddWordState.waiting_for_word)

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
