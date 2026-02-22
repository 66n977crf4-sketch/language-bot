import aiohttp
from deep_translator import GoogleTranslator

async def translate_word(word: str):
    # 1. Получаем определение, пример и транскрипцию
    dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    async with aiohttp.ClientSession() as session:
        async with session.get(dict_url) as resp:
            if resp.status != 200:
                definition_en = None
                example_en = None
                phonetic = None
            else:
                data = await resp.json()
                try:
                    definition_en = data[0]["meanings"][0]["definitions"][0]["definition"]
                    example_en = data[0]["meanings"][0]["definitions"][0].get("example")
                    phonetic = data[0].get("phonetic", "")
                except:
                    definition_en = None
                    example_en = None
                    phonetic = None

    # 2. Перевод слова
    translation = GoogleTranslator(source='en', target='ru').translate(word)

    # 3. Перевод значения
    definition_ru = GoogleTranslator(source='en', target='ru').translate(definition_en) if definition_en else None

    # 4. Генерация естественного примера, если словарь не дал
    if not example_en:
        prompt = f"Write one natural English sentence using the word '{word}'."
        example_en = GoogleTranslator(source='auto', target='en').translate(prompt)

    # 5. Перевод примера
    example_ru = GoogleTranslator(source='en', target='ru').translate(example_en)

    return {
        "translation": translation,
        "definition_ru": definition_ru,
        "example_en": example_en,
        "example_ru": example_ru,
        "phonetic": phonetic
    }