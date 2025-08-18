"""Database action helpers extracted from UI/main.py.
Provide functions that operate on a DatabaseHandler and a QTextEdit for output.
"""
from typing import Any


def add_sample_users(db: Any, output: Any) -> None:
    """Insert sample users into the database and append a message to the output widget."""
    db.insert_user("Alice", 30)
    db.insert_user("Bob", 25)
    output.append("Sample users added.")


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
