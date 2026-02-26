import aiosqlite
import time
import random

DB_PATH = "words.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                word TEXT,
                status TEXT DEFAULT 'new',
                correct_streak INTEGER DEFAULT 0,
                next_review INTEGER
            )
        """)
        await db.commit()

async def add_word(user_id, word):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM words WHERE user_id = ? AND word = ?",
            (user_id, word)
        )
        exists = await cursor.fetchone()

        if exists:
            return False  # слово уже есть

        await db.execute(
            "INSERT INTO words (user_id, word, status, correct_streak, next_review) VALUES (?, ?, 'new', 0, NULL)",
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


async def get_word_for_training(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        now = int(time.time())

        # 1. Слова, которые пора повторить
        cursor = await db.execute(
            "SELECT word FROM words WHERE user_id = ? AND status = 'repeat' AND next_review IS NOT NULL AND next_review <= ?",
            (user_id, now)
        )
        rows = await cursor.fetchall()
        if rows:
            return random.choice(rows)[0]

        # 2. Новые слова
        cursor = await db.execute(
            "SELECT word FROM words WHERE user_id = ? AND status = 'new'",
            (user_id,)
        )
        rows = await cursor.fetchall()
        if rows:
            return random.choice(rows)[0]

        # 3. Остальные на повторении
        cursor = await db.execute(
            "SELECT word FROM words WHERE user_id = ? AND status = 'repeat'",
            (user_id,)
        )
        rows = await cursor.fetchall()
        if rows:
            return random.choice(rows)[0]

        return None


async def update_word_success(user_id, word):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT correct_streak FROM words WHERE user_id = ? AND word = ?",
            (user_id, word)
        )
        row = await cursor.fetchone()
        streak = (row[0] if row and row[0] is not None else 0) + 1

        intervals = [0, 4*3600, 24*3600, 3*24*3600, 7*24*3600, 30*24*3600]
        next_review = int(time.time()) + intervals[min(streak, 5)]

        status = "learned" if streak >= 3 else "repeat"

        await db.execute(
            "UPDATE words SET correct_streak = ?, next_review = ?, status = ? WHERE user_id = ? AND word = ?",
            (streak, next_review, status, user_id, word)
        )
        await db.commit()


async def update_word_fail(user_id, word):
    async with aiosqlite.connect(DB_PATH) as db:
        now = int(time.time())
        await db.execute(
            "UPDATE words SET correct_streak = 0, status = 'repeat', next_review = ? WHERE user_id = ? AND word = ?",
            (now, user_id, word)
        )
        await db.commit()