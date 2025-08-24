"""Database action helpers extracted from UI/main.py.
Provide functions that operate on a DatabaseHandler and a QTextEdit for output.
"""
from typing import Any


def add_sample_users(db: Any, output: Any) -> None:
    """Insert the current system user (name, email, consent) and a single placeholder blink event.
    This replaces the previous behavior of inserting multiple sample users.
    """
    import time
    import datetime
    import getpass
    import socket

    try:
        username = getpass.getuser()
    except Exception:
        username = "unknown_user"

    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "localhost"

    email = f"{username}@{hostname}"
    consent = 1

    user_id = None
    try:
        # Try preferred signature first (name, age, email=..., consent=...)
        try:
            user_id = db.insert_user(username, None, email=email, consent=consent)
        except TypeError:
            # fallback to older signature (name, age)
            user_id = db.insert_user(username, None)
        except Exception as e:
            output.append(f"Failed to insert current user {username}: {e}")
            return
    except Exception as e:
        output.append(f"Unexpected failure inserting user {username}: {e}")
        return

    # If insert_user didn't return an id, try to look it up
    if not user_id:
        try:
            if hasattr(db, "get_user_by_email"):
                row = db.get_user_by_email(email)
                if row:
                    user_id = row[0]
            else:
                users = db.get_users()
                for row in users:
                    if email in map(str, row) or username == (row[1] if len(row) > 1 else None):
                        user_id = row[0]
                        break
        except Exception:
            user_id = None

    if not user_id:
        output.append(f"Inserted/ensured user '{username}' but could not determine user id.")
        return

    output.append(f"Current system user inserted/ensured: {username} (id={user_id}, email={email})")

    # Insert a single placeholder blink event if the DB handler supports it
    if hasattr(db, "insert_blink_event"):
        try:
            ts = datetime.datetime.utcnow().isoformat() + "Z"
            epoch_ms = int(time.time() * 1000)
            db.insert_blink_event(
                user_id=user_id,
                session_id="system-start",
                event_ts=ts,
                event_epoch_ms=epoch_ms,
                duration_ms=None,
                event_type="placeholder",
                ear=None,
                source="local",
                metadata=None,
            )
            output.append("Inserted one placeholder blink event for the current user.")
        except Exception as e:
            output.append(f"Failed to insert placeholder blink event: {e}")
    else:
        output.append("DB handler has no insert_blink_event method; skipped blink event insertion.")


def show_users(db: Any, output: Any) -> None:
    """Fetch users from the database and display them in the output widget."""
    users = db.get_users()
    output.clear()
    for user in users:
        output.append(f"ID: {user[0]} | Name: {user[1]} | Age: {user[2]}")


def update_user_prompt(db: Any, output: Any) -> None:
    """Prompt-style helper using simple text prompts in `output` to update a user.
    This is intentionally minimal for a simple desktop app without extra dialogs.
    Expected input format appended to the output: update:<id>:<name>:<age>
    Example: update:2:Charlie:28
    """
    output.append("To update a user, append a line in the format: update:<id>:<name>:<age>")


def delete_user_prompt(db: Any, output: Any) -> None:
    """Prompt-style helper guiding deletion. Expected format: delete:<id>"""
    output.append("To delete a user, append a line in the format: delete:<id>")


def process_output_commands(db: Any, output: Any) -> None:
    """Scan the QTextEdit contents for commands and execute them.
    Recognized commands:
      - update:<id>:<name>:<age>
      - delete:<id>

    After processing, append results and refresh the shown users.
    """
    text = output.toPlainText()
    lines = text.splitlines()
    did_change = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("update:"):
            parts = line.split(":", 3)
            if len(parts) == 4:
                try:
                    user_id = int(parts[1])
                    name = parts[2]
                    age = int(parts[3])
                    rows = db.update_user(user_id, name, age)
                    output.append(f"Updated {rows} row(s) for id={user_id}.")
                    did_change = True
                except Exception as e:
                    output.append(f"Failed to update user: {e}")
        elif line.startswith("delete:"):
            parts = line.split(":", 2)
            if len(parts) == 2:
                try:
                    user_id = int(parts[1])
                    rows = db.delete_user(user_id)
                    output.append(f"Deleted {rows} row(s) for id={user_id}.")
                    did_change = True
                except Exception as e:
                    output.append(f"Failed to delete user: {e}")
    if did_change:
        output.append("Refreshing user list:")
        show_users(db, output)
