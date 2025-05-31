# InvisChatBot

**InvisChatBot** is a lightweight, privacy-focused Telegram bot that allows users to chat anonymously with others. Built with Python, it offers fast performance and strong privacy by design—no messages or personal data are stored.

## 🚀 Features

- 🔒 **Privacy-First**: No chat history is saved, ensuring full anonymity.
- 💬 **Anonymous Chatting**: Connects users for anonymous conversations.
- ⚡ **Lightweight**: Minimal dependencies and resource usage.
- 🔧 **Simple Configuration**: Uses environment variables for easy setup.

## Prerequisites

- Python 3.10+
- A Telegram bot from BotFather.
- A mongodb database.
- Required Python main libraries:
    - `pyTelegramBotAPI` (telebot)
    - `pymongo`

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/DiarTor/invischatbot.git
    ```

2. **Navigate to the bot folder**
    ```bash
    cd invischatbot
    ```

3. **Set up environment variables**

   Copy the example file and update with your own values:

   ```bash
   cp .env.example .env
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the bot**

   ```bash
   python main.py
   ```

## ⚙️ Configuration

All runtime configuration is handled through the `.env` file. Common settings:

## 🛠 Usage

Once running, users can interact with the bot via Telegram:

* `/start` – Begin using the bot.
* `/ahelp` – For admin commands.

## 🤝 Contributing

This project is open-source for transparency and user assurance only.
Contributions (PRs, issues, forks) are not accepted—please use the code as-is.

## 📬 Contact

For questions, suggestions, or support, contact: [@DiarTor](https://t.me/diartor) in Telegram.