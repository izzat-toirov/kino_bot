import aiosqlite
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Ma'lumotlar bazasi jadvallarini yaratish"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                code INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                file_id TEXT NOT NULL,
                description TEXT DEFAULT '',
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                invite_link TEXT NOT NULL
            );
            """)
            await db.commit()

    # ================= FOYDALANUVCHILAR ================= #
    async def add_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                    (user_id, username, first_name)
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def get_total_users_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_all_user_ids(self) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    # ================= KINOLAR ================= #
    async def add_movie(self, code: int, title: str, file_id: str, description: str = "") -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT OR REPLACE INTO movies (code, title, file_id, description) VALUES (?, ?, ?, ?)",
                    (code, title, file_id, description)
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def movie_exists(self, code: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM movies WHERE code = ?", (code,)) as cursor:
                row = await cursor.fetchone()
                return row is not None

    async def get_movie(self, code: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT code, title, file_id, description, views, created_at FROM movies WHERE code = ?",
                (code,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    await db.execute("UPDATE movies SET views = views + 1 WHERE code = ?", (code,))
                    await db.commit()
                    return dict(row)
                return None

    async def delete_movie(self, code: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM movies WHERE code = ?", (code,))
            await db.commit()
            return cursor.rowcount > 0

    async def search_movies(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            param = f"%{query}%"
            async with db.execute(
                "SELECT code, title, views FROM movies WHERE title LIKE ? OR description LIKE ? ORDER BY views DESC LIMIT ?",
                (param, param, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_random_movie(self) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT code, title, file_id, description, views FROM movies ORDER BY RANDOM() LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    code = row["code"]
                    await db.execute("UPDATE movies SET views = views + 1 WHERE code = ?", (code,))
                    await db.commit()
                    return dict(row)
                return None

    async def get_latest_movies(self, limit: int = 8) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT code, title, views, created_at FROM movies ORDER BY code DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_top_movies(self, limit: int = 5) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT code, title, views FROM movies ORDER BY views DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_total_movies_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ================= MAJBURIY OBUNA KANALLARI ================= #
    async def add_channel(self, channel_id: str, name: str, invite_link: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT OR REPLACE INTO channels (channel_id, name, invite_link) VALUES (?, ?, ?)",
                    (channel_id, name, invite_link)
                )
                await db.commit()
                return True
            except Exception:
                return False

    async def delete_channel(self, channel_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def get_all_channels(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT channel_id, name, invite_link FROM channels") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

db = Database()
