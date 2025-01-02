import re


class NicknameValidator:
    def __init__(self):
        # Define restricted or inappropriate words
        self.restricted_words = [
            # Administrative and Reserved Terms (English)
            "admin", "administrator", "moderator", "support", "help", "system", "bot", "mod", "staff",
            "official", "operator", "root", "server", "superuser", "adminpanel", "superadmin",
            "team", "owner", "developer", "webmaster",

            # Administrative and Reserved Terms (Persian)
            "ادمین", "مدیر", "پشتیبانی", "راهنما", "سیستم", "ربات", "سرور", "سرپرست", "اپراتور",
            "کارشناس", "توسعه‌دهنده", "مالک",

            # Inappropriate Language and Offensive Terms (English)
            "curse", "hate", "abuse", "insult",  # Add more offensive terms as needed

            # Inappropriate Language and Offensive Terms (Persian)
            "توهین", "لعنت", "فحش", "نفرت",  # Add more Persian offensive terms as needed

            # VIP and Exclusive Terms (English)
            "vip", "premium", "elite", "pro", "verified", "gold", "platinum", "official", "certified",
            "guest", "exclusive",

            # VIP and Exclusive Terms (Persian)
            "ویژه", "طلایی", "برنزی", "نقره‌ای", "رسمی", "تأیید‌شده", "مهمان",

            # System Functions and Commands (English)
            "root", "sudo", "cmd", "bash", "script", "admin", "server", "system", "console", "database",
            "query", "sql", "mysql", "mongodb", "redis", "log", "debug", "error", "shutdown",
            "reboot", "kill", "block", "kick", "ban", "delete", "remove", "api", "config",
            "cron", "task",

            # System Functions and Commands (Persian)
            "سیستم", "سرور", "پایگاه داده", "دیتابیس", "کنسول", "اشکال زدایی", "حذف", "بانک",
            "بستن", "اجرای", "بازنشانی", "مسدود", "پاک کردن",

            # Religious and Political Terms (English)
            "god", "allah", "prophet", "angel", "buddha", "jesus", "leader", "president", "minister",
            "politics", "vote", "party", "leftwing", "rightwing", "republic", "democrat",
            "congress", "government", "parliament", "senate", "king", "queen", "dictator",
            "czar", "sultan",

            # Religious and Political Terms (Persian)
            "خدا", "الله", "پیامبر", "مسیح", "مومن", "سیاسی", "رهبر", "رئیس‌جمهور", "وزیر",
            "حکومت", "نماینده", "انتخابات", "مجلس", "سنا", "پادشاه", "وزارت",

            # Sensitive Health-Related and Harmful Terms (English)
            "drugs", "alcohol", "smoke", "cigarette", "marijuana", "cocaine", "violence",
            "death", "kill", "suicide", "mental", "depression", "harm",

            # Sensitive Health-Related and Harmful Terms (Persian)
            "اعتیاد", "مواد مخدر", "سیگار", "مرگ", "خودکشی", "کشتن", "آزار", "روحی", "افسردگی",

            # Restricted Place Names and Titles (English)
            "president", "congress", "senator", "police", "army", "military", "navy", "airforce",
            "us", "uk", "canada", "eu", "america", "embassy", "official", "ambassador",

            # Restricted Place Names and Titles (Persian)
            "پلیس", "ارتش", "نیروی دریایی", "نیروی هوایی", "سفارت", "رئیس", "نماینده", "وزارت",
            "کشور", "استان", "شهر"
        ]

    def validate_nickname(self, nickname: str) -> (bool, str):
        if len(nickname) < 3 or len(nickname) > 20:
            return False, "⛔️ نام مستعار باید بین ۳ تا ۲۰ کاراکتر باشد."

        if nickname.startswith("/"):
            return False, "⚠️ نام مستعار نمی‌تواند با علامت '/' شروع شود."

        if re.match(r'^\W', nickname):
            return False, "🚫 نام مستعار نباید با کاراکترهای خاص شروع شود."

        if any(word in nickname.lower() for word in self.restricted_words):
            return False, "❌ نام مستعار شامل کلمات محدودشده است."

        # if not re.match(r'^\w+$', nickname):
        #     return False, "🔤 نام مستعار باید فقط حروف، اعداد یا زیرخط (_) باشد."

        return True, "✅ نام مستعار معتبر است."


class MessageValidator:
    """
    A class for validating and formatting messages to prevent formatting errors.
    """

    # Define special characters for Markdown formatting
    MARKDOWN_SPECIAL_CHARS = r'_*[]()~`>#+-=|{}.!'

    @classmethod
    def escape_markdown(cls, text: str) -> str:
        """
        Escapes special characters in Markdown text.
        :param text: The input text to escape.
        :return: Escaped text safe for Markdown.
        """
        return re.sub(f'([{re.escape(cls.MARKDOWN_SPECIAL_CHARS)}])', r'\\\1', text)

    @classmethod
    def validate_and_format(cls, text: str, parse_mode: str = 'Markdown') -> str:
        """
        Validates and formats the input text based on the specified parse mode.
        :param text: The input message text.
        :param parse_mode: The parsing mode ('Markdown', 'HTML', or None).
        :return: Validated and formatted text.
        """
        if parse_mode == 'Markdown':
            # Escape Markdown special characters
            return cls.escape_markdown(text)
        elif parse_mode == 'HTML':
            # Escape HTML special characters
            import html
            return html.escape(text)
        else:
            # Return plain text if no parsing is required
            return text
