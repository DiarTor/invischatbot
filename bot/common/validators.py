import re

class AccountValidator:
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

            # VIP and Exclusive Terms (English)
            "vip", "premium", "elite", "pro", "verified", "gold", "platinum", "official", "certified",
            "guest", "exclusive",

            # VIP and Exclusive Terms (Persian)
            "ویژه", "طلایی", "برنزی", "نقره‌ای", "رسمی", "تأیید‌شده", "مهمان",

            # lniks and inappropriate content
            "http", "https", "www", ".com", ".net", ".org", ".io", ".xyz", ".me", "@",
            "درحال حاضر بیوگرافی ندارید!"
        ]

    def validate_nickname(self, nickname: str) -> bool| str:
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

    def validate_bio(self, bio: str) -> bool| str:
        if len(bio) > 200:
            return False, "⛔️ بیوگرافی نباید بیشتر از ۲۰۰ کاراکتر باشد."

        if any(word in bio.lower() for word in self.restricted_words):
            return False, "❌ بیوگرافی شامل کلمات محدودشده است."

        if re.search(r'http://|https://|www\.|\.com|\.net|\.org|\.io|\.xyz|\.me|@', bio.lower()):
            return False, "🚫 بیوگرافی نباید شامل لینک یا آدرس‌های وب باشد."

        return True, "✅ بیوگرافی معتبر است."
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

