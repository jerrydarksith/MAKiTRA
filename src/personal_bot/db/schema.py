from personal_bot.db.database import Database


def _ensure_user_columns(database: Database) -> None:
    existing_columns = {
        row["name"] for row in database.execute("PRAGMA table_info(users)").fetchall()
    }

    column_definitions = [
        ("is_bot", "INTEGER"),
        ("full_name", "TEXT"),
        ("phone_number", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
        ("last_activity_at", "TEXT"),
        ("timezone", "TEXT"),
        ("language_code", "TEXT"),
        ("is_premium", "INTEGER"),
        ("added_to_attachment_menu", "INTEGER"),
        ("allows_write_to_pm", "INTEGER"),
        ("can_join_groups", "INTEGER"),
        ("can_read_all_group_messages", "INTEGER"),
        ("supports_inline_queries", "INTEGER"),
        ("can_connect_to_business", "INTEGER"),
        ("has_main_web_app", "INTEGER"),
        ("has_topics_enabled", "INTEGER"),
        ("allows_users_to_create_topics", "INTEGER"),
        ("can_manage_bots", "INTEGER"),
        ("supports_guest_queries", "INTEGER"),
    ]

    for column_name, column_type in column_definitions:
        if column_name not in existing_columns:
            database.execute(
                f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
            )


def initialize_database_schema(database: Database) -> None:
    """Create the first-stage schema when it does not exist yet."""
    database.execute_script(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER NOT NULL UNIQUE,
            is_bot INTEGER NOT NULL DEFAULT 0,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            full_name TEXT,
            phone_number TEXT,
            role TEXT NOT NULL CHECK (role IN ('super_admin', 'admin', 'user')),
            status TEXT NOT NULL CHECK (status IN ('active', 'blocked')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_activity_at TEXT,
            timezone TEXT,
            language_code TEXT,
            is_premium INTEGER,
            added_to_attachment_menu INTEGER,
            allows_write_to_pm INTEGER,
            can_join_groups INTEGER,
            can_read_all_group_messages INTEGER,
            supports_inline_queries INTEGER,
            can_connect_to_business INTEGER,
            has_main_web_app INTEGER,
            has_topics_enabled INTEGER,
            allows_users_to_create_topics INTEGER,
            can_manage_bots INTEGER,
            supports_guest_queries INTEGER
        );

        CREATE TABLE IF NOT EXISTS access_requests (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER NOT NULL,
            is_bot INTEGER NOT NULL DEFAULT 0,
            username TEXT,
            first_name TEXT NOT NULL,
            last_name TEXT,
            full_name TEXT,
            phone_number TEXT NOT NULL,
            language_code TEXT,
            is_premium INTEGER,
            added_to_attachment_menu INTEGER,
            can_join_groups INTEGER,
            can_read_all_group_messages INTEGER,
            supports_inline_queries INTEGER,
            can_connect_to_business INTEGER,
            has_main_web_app INTEGER,
            has_topics_enabled INTEGER,
            allows_users_to_create_topics INTEGER,
            can_manage_bots INTEGER,
            supports_guest_queries INTEGER,
            status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
            reviewed_by_user_id INTEGER REFERENCES users(id),
            reviewed_at TEXT,
            created_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS unique_pending_access_request
            ON access_requests(telegram_id)
            WHERE status = 'pending';

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            timezone TEXT NOT NULL,
            currency TEXT NOT NULL,
            date_format TEXT NOT NULL,
            language TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            parent_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
            name TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '📁',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS unique_root_category_name
            ON categories(owner_user_id, name)
            WHERE parent_id IS NULL;

        CREATE UNIQUE INDEX IF NOT EXISTS unique_child_category_name
            ON categories(owner_user_id, parent_id, name)
            WHERE parent_id IS NOT NULL;

        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY,
            owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            parent_id INTEGER REFERENCES folders(id) ON DELETE RESTRICT,
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS unique_root_folder_name
            ON folders(owner_user_id, name)
            WHERE parent_id IS NULL;

        CREATE UNIQUE INDEX IF NOT EXISTS unique_child_folder_name
            ON folders(owner_user_id, parent_id, name)
            WHERE parent_id IS NOT NULL;

        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY,
            owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE RESTRICT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            payload TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            preview_text TEXT
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY,
            record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('active', 'sent')),
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS records_by_folder_and_owner
            ON records(folder_id, owner_user_id, sort_order);

        CREATE INDEX IF NOT EXISTS reminders_by_time_and_status
            ON reminders(remind_at, status);
        """
    )

    _ensure_user_columns(database)

    access_request_columns = {
        row["name"]
        for row in database.execute("PRAGMA table_info(access_requests)").fetchall()
    }
    access_request_definitions = [
        ("is_bot", "INTEGER"),
        ("full_name", "TEXT"),
        ("language_code", "TEXT"),
        ("is_premium", "INTEGER"),
        ("added_to_attachment_menu", "INTEGER"),
        ("can_join_groups", "INTEGER"),
        ("can_read_all_group_messages", "INTEGER"),
        ("supports_inline_queries", "INTEGER"),
        ("can_connect_to_business", "INTEGER"),
        ("has_main_web_app", "INTEGER"),
        ("has_topics_enabled", "INTEGER"),
        ("allows_users_to_create_topics", "INTEGER"),
        ("can_manage_bots", "INTEGER"),
        ("supports_guest_queries", "INTEGER"),
    ]
    for column_name, column_type in access_request_definitions:
        if column_name not in access_request_columns:
            database.execute(
                f"ALTER TABLE access_requests ADD COLUMN {column_name} {column_type}"
            )

    reminder_columns = {
        row["name"]
        for row in database.execute("PRAGMA table_info(reminders)").fetchall()
    }
    if "owner_user_id" in reminder_columns:
        database.execute("DROP INDEX IF EXISTS reminders_by_owner_and_time")
        database.execute("ALTER TABLE reminders RENAME TO reminders_legacy")
        database.execute_script(
            """
            CREATE TABLE reminders (
                id INTEGER PRIMARY KEY,
                record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('active', 'sent')),
                created_at TEXT NOT NULL
            );

            INSERT INTO reminders (id, record_id, text, remind_at, status, created_at)
            SELECT id, record_id, text, remind_at, status, created_at
            FROM reminders_legacy;

            DROP TABLE reminders_legacy;
            """
        )
        database.execute_script(
            """
            CREATE INDEX IF NOT EXISTS reminders_by_time_and_status
                ON reminders(remind_at, status);
            """
        )

    folder_columns = {
        row["name"]
        for row in database.execute("PRAGMA table_info(folders)").fetchall()
    }
    if "owner_user_id" not in folder_columns and "user_id" in folder_columns:
        database.execute("ALTER TABLE folders RENAME COLUMN user_id TO owner_user_id")
        database.execute("DROP INDEX IF EXISTS unique_root_folder_name")
        database.execute("DROP INDEX IF EXISTS unique_child_folder_name")
        database.execute_script(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS unique_root_folder_name
                ON folders(owner_user_id, name)
                WHERE parent_id IS NULL;

            CREATE UNIQUE INDEX IF NOT EXISTS unique_child_folder_name
                ON folders(owner_user_id, parent_id, name)
                WHERE parent_id IS NOT NULL;
            """
        )
