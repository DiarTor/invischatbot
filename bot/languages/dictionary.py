"""
    This file contains the translations for the bot's messages.
    The translations are stored in a dictionary format, where the keys are the language codes
    and the values are dictionaries containing the translations for various messages.
    The translations are organized into categories such as 'greeting', 'nickname', 'texting', etc...
    Each category contains subcategories for different types of messages, such as 'welcome', etc...
    The translations are written in a format that allows for easy formatting with variables,
    such as using curly braces {} to indicate where variables should be inserted into the message.
"""
from textwrap import dedent

translations = {
    'fa': {
        'greeting': {
            'welcome': dedent("""
        سلام {nickname} عزیز🌹، به ربات چت ناشناس خوش اومدی🙌

        _شما میتونی با استفاده از دکمه های پایین از ربات استفاده کنی. اگه هم سوالی داشتی حتما از پشتیبانی بپرس 😉
    """),
            'first_time': dedent("""
به ربات چت ناشناس خوش اومدی🙌

از آنجایی که این اولین بار است که از این ربات استفاده می‌کنید، نام مستعار شما به طور پیش‌فرض به *{nickname}* تنظیم شده است. 📝

برای تغییر آن، می‌توانید به بخش *'👤 حساب کاربری'* بروید و سپس روی دکمه *'♻️ تغییر نام نمایشی'* کلیک کنید.
""")

        },
        'link': {
                        'link': dedent("""
        🕵️‍♂️ لینک پایین لینک ناشناس شماست. هرکی این  لینک رو داشته باشه میتونه بهت ناشناس پیام بده!
        🔐 تمام پیام ها مستقیم تحت رمزگذاری خود تلگرام هستن.
        ✅ لینک های ناشناس هم برای محافظت از هویت کاربران کاملا ناشناس رمزگذاری شدن.
        🔗 {link} 👈
        <b>❓اگه دوست داشتین برای مدتی از کسی پیامی نگیرید میتونید ربات رو از قسمت "👤 حساب کاربری" خاموش کنید.</b>
    """),
            'send_link': dedent("""
        ☝️ پیام بالا رو به دوستات و گروه‌ها فوروارد کن یا لینک داخلش رو تو شبکه‌های اجتماعی بذار تا بقیه بتونن بهت پیام ناشناس بفرستن. پیام‌ها از طریق همین ربات بهت می‌رسه.
        """),
            'share_link': dedent("""
        تا حالا شده بخوای یه چیزی بهم بگی ولی خجالت بکشی؟ 😅  
        خب این فرصتشه! 🎉  
        با زدن روی دکمه پایین می‌تونی یه پیام کاملاً ناشناس برام بفرستی—بدون اسم، بدون سرنخ، فقط حرفای خودت! 🫣  
        یه راز، یه تعریف، یا هرچی که میخوای رو بهم بگو بدون اینکه بفهمم کی هستی! 😎  
        ❤️ راستی تو هم میتونی لینک خودتو به صورت رایگان از ربات بگیری و برای دوستات بفرستی که اونا هم پیام ناشناس بهت بدن!
        """),
            'regenerate_link': {
                'confirm': dedent("""
        ❗️مطمئنی که می‌خوای لینک ناشناس خودتو باطل کنی؟ با اینکار دیگه کسی نمیتونه از لینک قبلی برات پیام ناشناس بفرسته.
        ⚠️ *این عمل غیرقابل بازگشت است و دیگه امکان بازگردانی لینک قبلی وجود نداره.*
        ♻️ با ابطال لینک قبلی، یک لینک جدید برای شما ایجاد می‌شود که می‌توانید از آن استفاده کنید.
        """),
            'cancel': dedent("""
        خیالت راحت لینک باطل نشد 😉
        """),
            'regenerated': dedent("""
        ✅ لینک ناشناس شما با موفقیت باطل شد و یک لینک جدید برای شما ایجاد شد.
        ⚠️ توجه داشته باشید که لینک قبلی دیگر قابل استفاده نیست و تمام پیام‌های ناشناس از لینک جدید ارسال خواهد شد.
        🔗 لینک جدید شما: {link}
        """),
            }
        },
        'nickname': {
            'ask_nickname': dedent("""
        🪪 نام نمایشی فعلی: `{current_nickname}`
        💠 نام اکانت تلگرام شما: `{current_firstname}`
        ⏳ لطفا نام نمایشی که میخوای بجای اسم اصلیت برای بقیه نمایش داده بشه رو برام بفرست.
        """),
            'nickname_was_set': dedent("""
        ✅ نام نمایشی شما با موفقیت به *{}* تغییر یافت.
        از این به بعد کاربران به این اسم شمارو میبینن.
        """),
            'cancelled': dedent("""
        ❌ تغییر نام نمایشی لغو شد.
        😊 می‌توانید هر زمان که خواستید دوباره درخواست تغییر نام نمایشی بدید
        """)
        },
        'texting': {
            'sending': {
                'text': {
                    'send': dedent("""
            ✍️ در حال ارسال پیام ناشناس به *{nickname}* هستی...
                    """),
                    'sending': dedent("""
                _⏳درحال ارسال_
                """),
                    'sent': dedent("""
                ✅ پیام شما به صورت ناشناس ارسال شد.
                    """),
                    'recipient': dedent("""
                💬 پیام ناشناس:

                {message}

                👤 آیدی ناشناس کاربر: {sender_anon_id}
                    """),
                },
                'sticker': {
                    'sent': dedent("""
                ✅ استیکر شما به صورت ناشناس ارسال شد.
                """),
                    'recipient': dedent("""
                 📸 استیکر ناشناس 👇

                👤 آیدی ناشناس کاربر: {}
                """)
                },
                'photo': {
                    'sent': dedent("""
                ✅ عکس شما به صورت ناشناس ارسال شد.
                """),

                    'recipient': dedent("""
                 📸 عکس ناشناس:

                 {}

                👤 آیدی ناشناس کاربر: {}
                """)
                },
                'video': {
                    'recipient': dedent("""
                 📸 فیلم ناشناس:

                 {}

                👤 آیدی ناشناس کاربر: {}
                """)
                },
                'cancelled': dedent("""
            🛑 گفت‌وگو لغو شد.
            💬 اگر تمایل دارید مکالمه‌ی جدیدی را شروع کنید.
            """),
            },
            'replying': {
                'send': dedent("""
            جوابتو بنویس براش بفرستم 😁
            """),
                'sent': dedent("""
            جوابتو براش فرستادم 👍
            """),
                'recipient': dedent("""
            💬 جوابه این پیامت :

            {}

            👤 آیدی ناشناس کاربر: {}
            """),
                'cancelled': dedent("""
            ✋ پاسخ دادن لغو شد.
            📩 برای پاسخ دادن، میتونید دوباره روی دکمه پاسخ بزنید.
            """)
            },
            'seen': {
                'sent': dedent("""
            این پیام برای فرستنده به ‌عنوان «دیده شده» علامت‌گذاری شد. ✅
            """),
                'recipient': dedent("""
            پیامت توسط گیرنده دیده شد. 👀️
            """),

            },
            'tools': {
                'announce': dedent("""
            ❓ تا 10 ثانیه دیگر میتونی پیامت رو حذف کنی.
            """),
                'editing': {
                    'send': dedent("""
            ❓ لطفا روی این پیام ریپلای کن و پیام جدید خودت رو بفرست.
            """),
                    'sent': dedent("""
            ✅ پیام مورد نظر با موفقیت ویرایش شد.
            """),
                    'recipient': dedent("""
                💬 پیام ناشناس:

                {message}

                👤 آیدی ناشناس کاربر: {anon_id}
                ♻️ ویرایش شده در {edited_at}
                    """),

                },
                'delete':
                    {
                        'deleted': dedent("""
                    ✅ پیام مورد نظر با موفقیت *حذف* شد.
                    """)
                    }
            }
        },
        'blocking': {
            'block?': dedent("""
        ❗️ مطمئنی که می‌خوای این کاربر رو بلاک کنی؟ 
        """),
            'block_confirm': dedent("""
    ✅ **کاربر مورد نظر با موفقیت بلاک شد!**
    👤 شناسه کاربر بلاک شده: *{}*
    🚫 این کاربر دیگه نمی‌تونه به شما پیام بده!

    📜 برای مشاهده لیست افراد بلاک شده از دکمه های زیر استفاده کن.
    """),
            'blocked_by_user': dedent("""
        🚫🙅‍♂️ متاسفم، شما توسط کاربر بلاک شدی، و یا شما این کابر رو بلاک کردین، به همین دلیل نمیتونی بهش پیام بدی.
        """),
            'blocklist': dedent("""
        *📋 لیست افراد بلاک شده:*
        ❗️ این شناسه‌ها برای ربات منحصر به فرد هستند.
        🔓 برای آنبلاک کردن روی شناسه مورد نظر کلیک کن.
        """),
            'blocklist_empty': dedent("""
        🚫 لیست افراد بلاک شده خالیه ! برو اول یکیو بلاک کن.
        """),
            'unblock?': dedent("""
        ❗️ مطمئنی که می‌خوای این کاربر با شناسه *{}* آنبلاک کنی؟ 
        """),
            'unblock_confirm': dedent("""
        ✅ کاربر مورد نظر به شناسه {anon_id} با موفقیت آنبلاک شد!
        """),
            'self': dedent("""
        نمیتونی خودتو بلاک کنی که 😐
        """),
            'support': dedent("""
        نمینونی پشتیبانی رو بلاک کنی دوست عزیز 😐
        """),
            'already_blocked': dedent("""
        شما قبلا این شخص رو بلاک کردین !
        """)
        },
        'reporting': {
            'send': dedent("""
        لطفا از پیام متخطی عکس بگیرید و به پشتیبانی ارسال کنید.
        """)
        },
        'support': {
            'send': dedent("""
        💬 برای ارتباط با پشتیبانی میتونی به صورت ناشناس به آیدی زیر در ربات پیام بدی.
        🔗 t.me/InvisChatBot?start=support
        """),
            'guide': dedent("""
        *🤖 بات چت ناشناس – سوالات متداول 🤖*

1️⃣ *این بات چیه؟*
• این بات به شما امکان می‌ده تا ناشناس با دیگران صحبت کنید! نیازی به نام کاربری یا پروفایل نیست – فقط کافیه روی لینک کسی که میخوای بهش پیام ناشناس بدی کلیک کنی، و لینک خودتون رو به اشتراک بذاری تا بقیه بهت ناشناس پیام بدن.

2️⃣ *چطور به کسی پیام بدم؟*
• اگه لینک شخصی کسی رو داری، کافیه روش کلیک کنی! اینجوری یک چت خصوصی ناشناس باز می‌شه و می‌تونی بهش پیام بدی و جواب بگیری.

3️⃣ *چطور دیگران می‌تونن به من پیام بدن؟*
• برای اینکه دیگران بتونن با شما چت کنن، لینک مخصوص خودت رو به اشتراک بذار. اون‌ها می‌تونن مستقیم و ناشناس به شما پیام بدن!

4️⃣ *می‌تونم به پیام‌ها جواب بدم؟*
• بله! وقتی چت شروع شد، می‌تونید به پیام‌ها جواب بدید و گفتگو رو ادامه بدید – بدون اینکه هویت‌تون رو فاش کنید.


        """)
        },
        'account': {
            'show': dedent("""
        👤 شناسه ناشناس: `{anon_id}`
        🪪 نام نمایشی: *{nickname}*
        📅 تاریخ عضویت: {joined_at}
        """),
            'referral': {
                'invite_self': dedent("""
            کلک نمیتوتی خودتو دعوت کنی که 😉
            """),
                'referred': dedent("""
            قبلا یکی دعوتت کرده، نمیتونی دوباره دعوت بشی 😕
            """)
            },
            'bot_status': {
                'self': {
                    'status_changed': dedent("""
                    وضعیت ربات به {status} تغییر یافت.
                    """),
                    'off': dedent("""
                    ✋ ربات در حالت خاموش است، برو اول ربات از قسمت حساب کاربری روشن کن.
                    """)
                },
                'recipient': {
                    'off': dedent("""
                    ✋ متاسفانه شخص مورد نظر ربات رو خاموش کرده.
                    """)
                }
            },
            'ban': {
                'banned': dedent("""
                                 شما بن شدید و دیگر نمی‌توانید از ربات استفاده کنید.
                """),
                'unbanned': dedent("""
                                 شما از بن خارج شدید و می‌توانید دوباره از ربات استفاده کنید.
                """),
            },
        },
        'errors': {
            'wrong_id': dedent("""
        ❌ شناسه کاربری اشتباه، لطفاً یک شناسه کاربری معتبر وارد کن.
        """),
            'bot_blocked': dedent("""
        کاربر ربات رو مسدود کرده، پس نمیتونی براش پیامی بفرستی ☹️
        """),
            'no_active_chat': dedent("""
        به کی میخوای پیام بدی ؟! اول برو رو لینک یکی بزن بعد بیا 😒
        """),
            'no_user_found': dedent("""
        متاسفانه شخصی که میخوای بهش پیام بدی تو ربات نیستش 😔
        این میتونه به این دلیل باشه که لینک اشتباهه یا کاربر تاحالا وارد ربات نشده.
        """),
            'restart_required': dedent("""
        ⭕ لطفا با دستور /start ربات را مجددا راه‌اندازی کنید.
        """),
            'no_cancel': dedent("""
        از کجا میخوای انصراف بدی ؟!
        """),
            'unknown_media': dedent("""
        🤔 ببخشید ولی ظاهرا ربات از نوع پیام شما پشتیبانی نمیکنه.
        """),
            'cant_message_self': dedent("""
        میدونم داری به خودت پیام میدیا کلک 😉
        """),
            'cant_mark_message': dedent("""
        متاسفانه قادر برای علامت گذاری این پیام نیستیم 😔
        """),
            'user_not_found': dedent("""
        ❌ کاربر پیدا نشد، لطفا شناسه کاربری صحیح را وارد کنید.
        """),
            'unknown_action': dedent("""
        ❌ عمل ناشناخته، اگه مشکل ادامه داشت ربات رو مجدد استارت بزنید.
        """),
        },
        'admin': {
            'panel':
                dedent("""
                🤝 سلام ادمین *{name}* عزیز!
                به پنل مدیریتی خوش اومدی ❤️
                """),
            'stats': {
                'chats': dedent("""
        🎉 *وضعیت ربات - گزارش چت ها* 🎉
        
        💬 *چت‌های ایجاد شده:*

        🟢 امروز: *{chat_today}*
        🔵 این هفته: *{chat_week}*
        🟠 این ماه: *{chat_month}*
        🔴 امسال: *{chat_year}*
        🌍 مجموع چت‌ها: *{chat_all_time}*
        
         ✍️ مجموع پیام ها: *{total_messages}*
        
        📅 تاریخ این آمار: {stats_date}
        """),
                'users': dedent("""
        🎉 *وضعیت ربات - گزارش کاربران* 🎉
        
        📅 *آمار کاربران جدید:*

        🟢 امروز: *{today}* نفر
        🔵 این هفته: *{week}* نفر
        🟠 این ماه: *{month}* نفر
        🔴 امسال: *{year}* نفر
        🌍 مجموع کل کاربران: *{all_time}* نفر
        
        📅 تاریخ این آمار: {stats_date}
        """),
                'new_user': dedent("""
                🎉 *کاربر جدید* 🎉
                
                👤 {first_name} {last_name} (@{username})
                🪪 {nickname}
                🆔 `{user_id}` `{id}`
                📅 {joined_at}
                ---------------------------------
                """),
            },
            'user': {
                'info': dedent("""
        🎉 *وضعیت کاربر - گزارش اطلاعات* 🎉

        📅 *اطلاعات کاربر:*

        🟢 شناسه کاربر: `{user_id}`
        🔵 شناسه ناشناس: `{anon_id}`
        🟠 نام مستعار: *{nickname}*
        🔴 تاریخ عضویت: *{joined_at}*
        🟢 نام کاربری: {username}
        🔵 نام کاربر: {first_name}
        🔵 فامیلی کاربر: {last_name}
        🔴 وضعیت ربات: *{is_bot_off}*
        🟢 وضعیت ادمین: *{is_admin}*
        🔴 وضعیت بن: *{is_banned}*
        🟠 بن شده توسط: *{banned_by}*
        🟠 تاریخ بن شدن: *{banned_at}*
                               
        💬 *چت‌ها و ارتباطات:*

        🟢 تعداد چت‌ها: *{chats_count}*
        🔴 تعداد کاربران بلاک شده: *{blocks_count}*

        📈 _با آرزوی بهترین‌ها برای شما!_
        """),
                'ban': {
                    'success': dedent("""
        ✅ کاربر با موفقیت بن شد.
        👤 شناسه کاربر بن شده: `{user_id}`
        🟢 شناسه ناشناس: `{anon_id}`
        🔴 نام کاربر: {first_name}
        🔴 فامیلی کاربر: {last_name}
        🔵 نام کاربری: {username}
        🪪 نام مستعار: *{nickname}*
        📅 تاریخ عضویت: *{joined_at}*
        📅 تاریخ بن شدن: *{banned_at}*
        """),
                },
                'unban': {
                    'success': dedent("""
        ✅ کاربر با موفقیت آنبن شد.
        👤 شناسه کاربر آنبن شده: `{user_id}`
        🟢 شناسه ناشناس: `{anon_id}`
        🔴 نام کاربر: {first_name}
        🔴 فامیلی کاربر: {last_name}
        🔵 نام کاربری: {username}
        🪪 نام مستعار: *{nickname}*
        📅 تاریخ عضویت: *{joined_at}*
        📅 تاریخ آنبن شدن: *{unbanned_at}*
        """),
                },
                'ban_list': {
                    'empty': dedent("""
        🚫 لیست کاربران بن شده خالی است.
        """),
                    'list': dedent("""
        *📋 لیست کاربران بن شده:*
        ❗️ این شناسه‌ها برای ربات منحصر به فرد هستند.
                                   {ban_list}
        🔓 برای آنبن کردن روی شناسه مورد نظر کلیک کن
        .
        """),
            },
            'errors': {
                'info': {
                    "wrong_format": dedent("""
                ❌ Wrong Format
                ^ Correct Format: /info <anon_id>
                """),
                    "not_found": dedent("""
                ❌ No User Found, Make Sure The Anonymous Id Is Correct.
                """)
                },
                'ban': {
                    "wrong_format": dedent("""
                ❌ Wrong Format
                ^ Correct Format: /ban <anon_id>
                """),
                    "not_found": dedent("""
                ❌ No User Found, Make Sure The Anonymous Id Is Correct.
                """),
                    "already_banned": dedent("""
                ❌ User Already Banned
                """),
                    "admin_ban": dedent("""
                ❌ You Can't Ban An Admin
                """)
                },
                'unban': {
                    "wrong_format": dedent("""
                ❌ Wrong Format
                ^ Correct Format: /unban <anon_id>
                """),
                    "not_found": dedent("""
                ❌ No User Found, Make Sure The Anonymous Id Is Correct.
                """),
                    "not_banned": dedent("""
                ❌ User Not Banned
                """),
                }
            }
        },
            'errors': {
                'ban': {
                    "wrong_format": dedent("""
                ❌ Wrong Format
                ^ Correct Format: /ban <anon_id>
                """),
                    "not_found": dedent("""
                ❌ No User Found, Make Sure The Anonymous Id Is Correct.
                """),
                    "already_banned": dedent("""
                ❌ User Already Banned
                """),
                    "admin_ban": dedent("""
                ❌ You Can't Ban An Admin
                """)
                },
                'unban': {
                    "wrong_format": dedent("""
                ❌ Wrong Format
                ^ Correct Format: /unban <anon_id>
                """),
                    "not_found": dedent("""
                ❌ No User Found, Make Sure The Anonymous Id Is Correct.
                """),
                    "not_banned": dedent("""
                ❌ User Not Banned
                """),
                },
                'info': {
                    "wrong_format": dedent("""
                ❌ Wrong Format
                ^ Correct Format: /info <anon_id or user_id>
                """),
                    "not_found": dedent("""
                ❌ No User Found, Make Sure The Anonymous Id or User Id Is Correct.
                """)
                },
            },
            'help': dedent("""
                           /admin - Admin Panel
                           /info - User Info
                           /ban - Ban User
                           /unban - Unban User
                           """
                           ),
            'ban_list': {
                'empty': dedent("""
        🚫 لیست کاربران بن شده خالی است.
        """),
                'list': dedent("""
        *📋 لیست کاربران بن شده:*
         ------------------------
        `{ban_list}`
        """),
        },
        'ad': {
            'force_join': dedent("""
        برای استفاده از ربات باید اول عضو کانال های زیر بشی 👇
        """),
            'not_joined': dedent("""
        هنوز عضو کانال ها نشدی !
        """),
            'banner': dedent("""
        محل درج بنر تبلیغات شما، برای ارتباط به پشتیبانی پیام دهید.
        """)
        }
    },
    'en': {}
    }
}
