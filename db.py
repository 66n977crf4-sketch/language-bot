import aiosqlite

DB_PATH = "words.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                word TEXT
            )
        """)
        await db.commit()

async def add_word(user_id, word):
    async with aiosqlite.connect("words.db") as db:
        # Проверяем, есть ли слово уже в базе
        cursor = await db.execute(
            "SELECT 1 FROM words WHERE user_id = ? AND word = ?",
            (user_id, word)
        )
        exists = await cursor.fetchone()

        if exists:
            return False  # слово уже есть

        # Если нет — добавляем
        await db.execute(
            "INSERT INTO words (user_id, word) VALUES (?, ?)",
            (user_id, word)
        )
        await db.commit()
        return True

async def get_words(user_id):
    async with aiosqlite.connect("words.db") as db:
        cursor = await db.execute(
            "SELECT word FROM words WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]