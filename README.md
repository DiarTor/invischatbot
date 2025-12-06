# InvisChatBot
![photo_2025-12-06_14-19-08_imgupscaler ai_Beasdta_2K](https://github.com/user-attachments/assets/0cd3610b-ce47-479b-acdd-f99d7f1d048d)

Lightweight, modular Python chatbot project (Telegram-compatible) with features like managing accounts, admin flows, callbacks and multilingual responses.

This repository contains the bot logic, database helpers, language dictionaries, and manager modules organized to be easy to extend.

**Key points**
- Python 3.12+ (project pyc files indicate 3.12 compatibility)
- Minimal dependencies listed in `requirements.txt`
- Entrypoint: `main.py`
- MongoDB Database

**Getting started**

1. Create a virtual environment and install dependencies

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. Configuration

    The bot expects runtime configuration via environment variables or a small config file. Typical variables:
    ```- BOT_TOKEN = your bot token (required)
    - BOT_USERNAME = your bot username without @
    - MONGO_URI = your mongo database uri
    - DATABASE_NAME = your databse name
    - USERS_COLLECTION = the collection name where you store users data
    - BOT_COLLECTION = the collection name where you store the bot data
    ```

    *Check `bot/database/database.py` and `bot/admin` modules for any additional configuration keys used by your project.*

3. Run the bot

    ```bash
    # from project root
    python main.py
    ```

**Project structure (high level)**

- `main.py` — application entrypoint
- `bot/` — bot-related code
  - `admin/` — admin handlers and administration utilities
  - `callbacks/` — callback handlers (inline keyboard callbacks)
  - `languages/` — dictionaries and response templates for multiple languages
  - `database/` — database connection and helpers
  - `common/` — shared utilities, keyboard helpers, validators, threading helpers
  - `managers/` — per-feature managers (account, chat, link, nickname, settings, start, support, etc.)

- `requirements.txt` — Python dependencies

**Development notes**

- Follow the modular structure: add features as new manager modules under `bot/managers` and route them from the main dispatcher.
- Use `bot/languages` to add or update localized messages.
- Keep database changes backward-compatible or provide migration steps in `migration.log`.

**Contributing**

1. Fork the repository
2. Create a feature branch
3. Add tests where appropriate
4. Open a pull request with a clear description of changes

**License**

This project is licensed under the GNU General Public License version 3 (GPL-3.0). See the included `LICENSE` file at the repository root for the full license text.

Short summary: GPL-3.0 is a strong copyleft license — you are free to run, study, share, and modify the software, but if you distribute modified versions they must also be licensed under GPL-3.0 and accompanied by source code. For the complete license terms see: https://www.gnu.org/licenses/gpl-3.0.en.html

Copyright (c) 2025 DiarTor
