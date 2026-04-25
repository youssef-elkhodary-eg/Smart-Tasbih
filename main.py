"""
                       السبحة الذكية الإصدار 3.0                            
                  Smart Tasbih - Ultimate Islamic Dhikr App     
                           by joseph elkhodary            
المميزات:
- قاعدة بيانات 35+ ذكر مع الأحاديث النبوية الصحيحة
- رسوم متحركة للخرز بـ Canvas + قوس تقدم دائري
- إحصائيات متطورة مع رسم بياني يومي
- وضع داكن/فاتح مع حفظ التفضيلات
- صوت Cross-Platform (winsound/pygame/simpleaudio)
- تراجع/إعادة (Undo/Redo) دقيق
- أذكار مخصصة
- تصدير إحصائيات CSV/JSON
- بحث وفلترة متقدم
- وضع التركيز (Focus Mode)
- إشعارات عند الأهداف والإنجازات
-تم تعطيل القوس الخارجي ال بيترسم والدايره الثابته ال حول السبحه 
-اي شخص يريد الكود لتطويره واعاده نشره ولو باسمه هذا سيسعدني لكم مطلق الحريه
-اللهم انفع بنا الاسلام والمسلمين
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import math
import json
import os
import platform
from datetime import datetime, timedelta
import time
import threading

# ========================== دعم الصوت Cross-Platform ==========================
SOUND_ENABLED = False
SOUND_BACKEND = None
SYSTEM = platform.system()

def init_sound():
    """تهيئة نظام الصوت حسب النظام"""
    global SOUND_ENABLED, SOUND_BACKEND
    try:
        if SYSTEM == "Windows":
            import winsound
            SOUND_ENABLED = True
            SOUND_BACKEND = "winsound"
            return "winsound"
        else:
            # محاولة استخدام pygame
            try:
                import pygame
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                SOUND_ENABLED = True
                SOUND_BACKEND = "pygame"
                return "pygame"
            except ImportError:
                pass

            # محاولة استخدام simpleaudio
            try:
                import simpleaudio as sa
                SOUND_ENABLED = True
                SOUND_BACKEND = "simpleaudio"
                return "simpleaudio"
            except ImportError:
                pass
    except Exception:
        pass
    SOUND_BACKEND = None
    return None

def generate_wave(frequency, duration_ms, sample_rate=22050):
    """توليد موجة صوتية"""
    import numpy as np
    t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000), False)
    wave = np.sin(frequency * t * 2 * np.pi)
    # تطبيق fade in/out لتجنب النقرات
    fade_len = min(len(wave) // 10, int(sample_rate * 0.005))
    if fade_len > 0:
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        wave[:fade_len] *= fade_in
        wave[-fade_len:] *= fade_out
    audio = (wave * 32767).astype(np.int16)
    if SYSTEM != "Darwin":  # macOS يحتاج ستيريو
        return np.column_stack((audio, audio))
    return audio

def play_beep(frequency, duration_ms):
    """تشغيل صوت beep cross-platform"""
    if not SOUND_ENABLED or not SOUND_BACKEND:
        return
    try:
        if SOUND_BACKEND == "winsound":
            import winsound
            winsound.Beep(frequency, duration_ms)
        elif SOUND_BACKEND == "pygame":
            import pygame
            import numpy as np
            audio = generate_wave(frequency, duration_ms)
            sound = pygame.sndarray.make_sound(audio)
            sound.play()
        elif SOUND_BACKEND == "simpleaudio":
            import simpleaudio as sa
            import numpy as np
            audio = generate_wave(frequency, duration_ms)
            if len(audio.shape) == 1:
                audio = np.column_stack((audio, audio))
            sa.play_buffer(audio.astype(np.int16), 2, 2, 22050)
    except Exception:
        pass

# ========================== قاعدة بيانات الأذكار ==========================
DEFAULT_AZKAR = {
    # ========== تسابيح ==========
    "سبحان الله": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال سبحان الله\n في يوم مائة مرة حُطَّت عنه خطاياه ولو كانت مثل زبد البحر». رواه البخاري ومسلم.",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "تسابيح", "fadl": "حُطَّت خطاياه ولو كانت مثل زبد البحر"
    },
    "الحمد لله": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال الحمد لله\n في يوم مائة مرة حُطَّت عنه خطاياه ولو كانت مثل زبد البحر». رواه مسلم.",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "تسابيح", "fadl": "حُطَّت خطاياه ولو كانت مثل زبد البحر"
    },
    "لا إله إلا الله": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال لا إله إلا الله وحده لا شريك له،\n له الملك وله الحمد،\n وهو على كل شيء قدير في يوم مائة مرة كانت له عدل عشر رقاب، وكتبت له مائة حسنة،\n ومحيت عنه مائة سيئة، وكانت له حرزاً من الشيطان يومه ذلك حتى يمسي». رواه البخاري ومسلم.",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "تسابيح", "fadl": "عدل عشر رقاب + مائة حسنة + حرز من الشيطان"
    },
    "الله أكبر": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: \n«من قال الله أكبر مائة مرة حُطَّت عنه خطاياه ولو كانت مثل زبد البحر». رواه مسلم.",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "تسابيح", "fadl": "حُطَّت خطاياه ولو كانت مثل زبد البحر"
    },
    "سبحان الله وبحمده، سبحان الله العظيم": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «كلمتان خفيفتان على اللسان، ثقيلتان في الميزان، حبيبتان إلى الرحمن: سبحان الله وبحمده،\n سبحان الله العظيم». رواه البخاري ومسلم.",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "تسابيح", "fadl": "ثقيلتان في الميزان، حبيبتان إلى الرحمن"
    },
    "سبحان الله وبحمده": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال سبحان \nالله وبحمده في يوم مائة مرة\n حُطَّت خطاياه ولو كانت مثل زبد البحر». رواه البخاري ومسلم.",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "تسابيح", "fadl": "حُطَّت خطاياه ولو كانت مثل زبد البحر"
    },
    "أستغفر الله": {
        "hadith": "عن ابن عمر رضي الله عنهما أن النبي صلى الله عليه وسلم قال:\n «يا أيها الناس، توبوا إلى الله فإني أتوب إليه في اليوم مائة مرة». رواه مسلم.",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "تسابيح", "fadl": "التوبة والمغفرة"
    },
    "لا حول ولا قوة إلا بالله": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: \n«كنز من كنوز الجنة:\n لا حول ولا قوة إلا بالله». رواه البخاري ومسلم.",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "تسابيح", "fadl": "كنز من كنوز الجنة"
    },
    "الصلاة على النبي": {
        "hadith": "عن عبد الله بن عمرو رضي الله عنهما أن النبي صلى الله عليه وسلم قال:\n «من صلى عليّ صلاة واحدة صلى الله عليه عشر صلوات،\n وحطّ عنه عشر خطيئات، ورفع له عشر درجات». رواه مسلم.",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "تسابيح", "fadl": "عشر حسنات + حطّ عشر خطيئات + رفع عشر درجات"
    },
    "لا إله إلا أنت سبحانك إني كنت من الظالمين": {
        "hadith": "عن سعد بن أبي وقاص رضي الله عنه أن النبي صلى الله عليه وسلم قال: «دعوة ذي النون إذ دعا وهو في بطن الحوت:\n لا إله إلا أنت سبحانك إني كنت من الظالمين، فإنه لم يدعُ بها\n رجل مسلم قط في شيء قط إلا استجاب الله له». رواه الترمذي وقال: حديث حسن صحيح.",
        "count": 0, "grade": "حسن صحيح", "source": "الترمذي", "category": "تسابيح", "fadl": "لا يُردّ دعاءها"
    },

    # ========== أذكار الصباح ==========
    "أصبحنا وأصبح الملك لله": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم كان يقول إذا \nأصبح: «أصبحنا وأصبح الملك لله، والحمد لله، لا إله إلا الله\n وحده لا شريك له، له الملك وله الحمد، وهو على كل شيء قدير».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار الصباح", "fadl": "ذكر الصباح المستحب"
    },
    "اللهم بك أصبحنا وبك أمسينا": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال حين يصبح:\n اللهم بك أصبحنا وبك أمسينا، وبك نحيا \nوبك نموت وإليك النشور، فإنه يأخذ بيده خير يومه كله».",
        "count": 0, "grade": "صحيح", "source": "الترمذي", "category": "أذكار الصباح", "fadl": "يأخذ بيده خير يومه كله"
    },
    "اللهم ما أصبح بي من نعمة": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم\n كان يقول: «اللهم ما أصبح بي من نعمة أو بأحد من خلقك فمنك وحدك لا شريك لك، فلك الحمد ولك الشكر».",
        "count": 0, "grade": "صحيح", "source": "أبو داود", "category": "أذكار الصباح", "fadl": "شكر النعم"
    },
    "حسبي الله لا إله إلا هو": {
        "hadith": "عن أبي الدرداء رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «من قال حين يصبح وحين يمسي: حسبي الله لا إله إلا هو عليه توكلت وهو رب العرش العظيم،\n سبع مرات كفاه الله ما أهمه من أمر الدنيا والآخرة».",
        "count": 0, "grade": "صحيح", "source": "ابن ماجه", "category": "أذكار الصباح", "fadl": "كفاه الله ما أهمه من أمر الدنيا والآخرة"
    },
    "بسم الله الذي لا يضر مع اسمه شيء": {
        "hadith": "عن عثمان بن عفان رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «من قال بسم الله الذي لا يضر مع اسمه شيء في الأرض ولا في السماء\n وهو السميع العليم، ثلاث مرات لم تُصبه فجأة بلاء حتى يمسي».",
        "count": 0, "grade": "صحيح", "source": "الترمذي", "category": "أذكار الصباح", "fadl": "حماية من البلاء"
    },
    "رضيت بالله ربا": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n«من قال حين يصبح وحين يمسي: رضيت بالله رباً، \nوبالإسلام ديناً، وبمحمد صلى الله عليه وسلم نبياً، كان حقاً على الله أن يرضيه».",
        "count": 0, "grade": "صحيح", "source": "أبو داود", "category": "أذكار الصباح", "fadl": "حق على الله أن يرضيه"
    },
    "سبحان الله وبحمده عدد خلقه": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «من قال حين يصبح وحين يمسي: سبحان الله وبحمده عدد خلقه،\n ورضا نفسه، وزنة عرشه، ومداد كلماته، ثلاث مرات، كانت له وقاية من كل مكروه».",
        "count": 0, "grade": "صحيح", "source": "ابن ماجه", "category": "أذكار الصباح", "fadl": "وقاية من كل مكروه"
    },
    "أعوذ بكلمات الله التامات من شر ما خلق": {
        "hadith": "عن أبي هريرة رضي الله عنه أن \nالنبي صلى الله عليه وسلم كان يقول إذا أمسى: «أعوذ بكلمات الله التامات من شر ما خلق».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار الصباح", "fadl": "حماية من شر المخلوقات"
    },

    # ========== أذكار المساء ==========
    "أمسينا وأمسى الملك لله": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم كان يقول إذا أمسى:\n «أمسينا وأمسى الملك لله، والحمد لله، لا إله إلا الله وحده لا شريك له،\n له الملك وله الحمد، وهو على كل شيء قدير».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار المساء", "fadl": "ذكر المساء المستحب"
    },
    "اللهم بك أمسينا وبك أصبحنا": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «من قال حين يمسي: اللهم بك أمسينا وبك أصبحنا، وبك نحيا وبك نموت وإليك المصير».",
        "count": 0, "grade": "صحيح", "source": "الترمذي", "category": "أذكار المساء", "fadl": "خير المساء كله"
    },
    "أعوذ بالله من عذاب جهنم": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال حين يصبح وحين يمسي:\n أعوذ بالله من عذاب جهنم، ومن عذاب القبر، ومن فتنة المحيا والممات، ومن شر المسيح الدجال».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار المساء", "fadl": "حماية من العذاب والفتن"
    },

    # ========== أذكار النوم ==========
    "باسمك اللهم أموت وأحيا": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم كان\n إذا أوى إلى فراشه قال: «باسمك اللهم أموت وأحيا».",
        "count": 0, "grade": "صحيح", "source": "البخاري", "category": "أذكار النوم", "fadl": "ذكر قبل النوم"
    },
    "الحمد لله الذي أطعمنا وسقانا": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: «من قال حين يأوي إلى فراشه:\n الحمد لله الذي أطعمنا وسقانا،\n وكفانا وآوانا، فكم ممن لا كافي له ولا مئوي».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار النوم", "fadl": "شكر النعم"
    },
    "اللهم قني عذابك يوم تبعث عبادك": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم كان إذا أوى إلى فراشه وضع يده تحت خده ثم قال:\n «اللهم قني عذابك يوم تبعث عبادك» ثلاث مرات.",
        "count": 0, "grade": "صحيح", "source": "أبو داود", "category": "أذكار النوم", "fadl": "الحماية من العذاب"
    },

    # ========== أذكار بعد الصلاة ==========
    "أستغفر الله (ثلاثاً)": {
        "hadith": "عن ثوبان رضي الله عنه أن النبي صلى الله عليه وسلم كان\n يستغفر بعد الصلاة ثلاث مرات.",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار بعد الصلاة", "fadl": "استغفار بعد كل صلاة"
    },
    "اللهم أنت السلام ومنك السلام": {
        "hadith": "عن عائشة رضي الله عنها أن النبي صلى الله عليه وسلم كان يقول بعد كل صلاة:\n «اللهم أنت السلام ومنك السلام تباركت يا ذا الجلال والإكرام».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أذكار بعد الصلاة", "fadl": "ذكر بعد كل صلاة"
    },
    "لا إله إلا الله وحده لا شريك له (عشر مرات)": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «من قال لا إله إلا الله وحده لا شريك له، له الملك وله الحمد،\n وهو على كل شيء قدير عشر مرات بعد صلاة \nالمغرب كُتب له بكل كلمة حجة وحجة بلا ذنب».",
        "count": 0, "grade": "صحيح", "source": "الترمذي", "category": "أذكار بعد الصلاة", "fadl": "كل كلمة عدل حجة بلا ذنب"
    },

    # ========== الأدعية ==========
    "اللهم إني أسألك علماً نافعاً": {
        "hadith": "عن ابن عباس رضي الله عنهما أن النبي صلى الله عليه \nوسلم كان يدعو: «اللهم إني أسألك علماً نافعاً، ورزقاً طيباً، وعملاً متقبلاً».",
        "count": 0, "grade": "صحيح", "source": "ابن ماجه", "category": "أدعية", "fadl": "طلب العلم والرزق"
    },
    "اللهم اغفر لي ذنبي كله": {
        "hadith": "عن ابن عمر رضي الله عنهما أن النبي صلى الله عليه وسلم كان يقول:\n «اللهم اغفر لي ذنبي كله، دقه وجله، أوله وآخره، وعلانيته وسره».",
        "count": 0, "grade": "صحيح", "source": "مسلم", "category": "أدعية", "fadl": "مغفرة الذنوب كلها"
    },
    "رب اغفر لي وتب علي": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n«والله إني لأستغفر الله وأتوب إليه في اليوم أكثر من سبعين مرة».",
        "count": 0, "grade": "صحيح", "source": "البخاري", "category": "أدعية", "fadl": "التوبة والاستغفار"
    },

    # ========== تكبيرات ==========
    "الله أكبر كبيراً والحمد لله كثيراً": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: \n«كلمتان خفيفتان على اللسان، ثقيلتان في الميزان، حبيبتان إلى الرحمن:\n سبحان الله العظيم وبحمده، سبحان الله العظيم».",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "تكبيرات", "fadl": "ثقيلتان في الميزان"
    },
    "لا إله إلا الله والله أكبر": {
        "hadith": "عن أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «من قال لا إله إلا الله والله أكبر ولا حول ولا قوة إلا بالله، فإنها كنوز من كنوز الجنة».",
        "count": 0, "grade": "صحيح", "source": "ابن ماجه", "category": "تكبيرات", "fadl": "كنوز من كنوز الجنة"
    },

    # ========== الصلاة الإبراهيمية ==========
    "اللهم صل على محمد وعلى آل محمد": {
        "hadith": "عن أبي مسعود الأنصاري رضي الله عنه أن النبي صلى الله عليه وسلم قال:\n «اللهم صل على محمد وعلى آل محمد كما صليت على آل إبراهيم،\n وبارك على محمد وعلى آل محمد كما باركت على آل إبراهيم في العالمين إنك حميد مجيد».",
        "count": 0, "grade": "صحيح", "source": "البخاري ومسلم", "category": "الصلاة الإبراهيمية", "fadl": "الصلاة الإبراهيمية المستحبة"
    },
}


# ========================== الكلاس الرئيسي ==========================
class SmartTasbihApp:
    def __init__(self, root):
        self.root = root
        self.root.title("السبحة الذكية - الإصدار 3.0")
        self.root.geometry("1100x850")
        self.root.minsize(900, 700)
        self.root.configure(bg="#1a1a2e")

        # ===== متغيرات الحالة =====
        self.total_x = 0
        self.target = 100
        self.is_pressed = False
        self.current_screen = "start"
        self.dark_mode = True
        self.sound_on = True
        self.last_click_time = 0
        self.debounce_ms = 120
        self.font_size = 14
        self.undo_stack = []
        self.redo_stack = []
        self.current_category = "الكل"
        self.focus_mode = False
        self.session_start_time = None
        self._animation_in_progress = False

        # ===== تهيئة الصوت =====
        self.sound_backend = init_sound()
        if not SOUND_ENABLED:
            self.sound_on = False

        # ===== الألوان =====
        self.colors = {
            "dark_bg": "#1a1a2e",
            "dark_card": "#16213e",
            "dark_accent": "#0f3460",
            "dark_text": "#e94560",
            "light_bg": "#f5f7fa",
            "light_card": "#ffffff",
            "light_accent": "#e8ecf1",
            "light_text": "#2c3e50",
            "primary": "#e94560",
            "secondary": "#0f3460",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "info": "#3498db",
            "gold": "#f1c40f"
        }

        # ===== ملفات البيانات =====
        self.data_dir = os.path.join(os.path.expanduser("~"), ".smart_tasbih")
        os.makedirs(self.data_dir, exist_ok=True)
        self.stats_file = os.path.join(self.data_dir, "azkar_stats.json")
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.custom_azkar_file = os.path.join(self.data_dir, "custom_azkar.json")

        # ===== تحميل البيانات =====
        self.load_settings()
        self.load_stats()
        self.load_custom_azkar()

        # ===== تحضير بيانات الأذكار =====
        self.azkar_data = {}
        self.azkar_data.update(DEFAULT_AZKAR)

        self.azkar_list = list(self.azkar_data.keys())
        self.categories = ["الكل"] + sorted(list(set(d["category"] for d in self.azkar_data.values())))

        # ===== إنشاء الـ Styles =====
        self.setup_styles()

        # ===== بناء الواجهة =====
        self.setup_ui()
        self.apply_theme()
        self.update_stats_display()

        # ===== ربط الأحداث =====
        self.bind_events()

        # ===== بدء الشاشة الأولى =====
        self.show_frame(self.start_frame, "start")

        # ===== رسالة ترحيبية =====
        self.root.after(500, self.show_welcome)

    # --------------------- إدارة الأنماط (Styles) ---------------------
    def setup_styles(self):
        """إعداد أنماط ttk المخصصة"""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure("TNotebook", background=self.colors["dark_bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 12, "bold"), 
                            padding=[20, 10], background="#0f3460", foreground="white")
        self.style.map("TNotebook.Tab", 
                      background=[("selected", "#e94560"), ("active", "#1a1a2e")],
                      foreground=[("selected", "white")])

        self.style.configure("TProgressbar", thickness=15, background="#e94560", 
                            troughcolor="#0f3460", borderwidth=0)

        self.style.configure("TScrollbar", background="#0f3460", troughcolor="#1a1a2e",
                            borderwidth=0, arrowcolor="white")

    # --------------------- إدارة الإعدادات ---------------------
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.dark_mode = settings.get('dark_mode', True)
                    self.sound_on = settings.get('sound_on', True)
                    self.target = settings.get('target', 100)
                    self.font_size = settings.get('font_size', 14)
                    self.focus_mode = settings.get('focus_mode', False)
            except:
                pass

    def save_settings(self):
        settings = {
            'dark_mode': self.dark_mode,
            'sound_on': self.sound_on,
            'target': self.target,
            'font_size': self.font_size,
            'focus_mode': self.focus_mode
        }
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    # --------------------- إدارة الإحصائيات ---------------------
    def load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            except:
                self.stats = self.init_stats()
        else:
            self.stats = self.init_stats()

    def init_stats(self):
        return {
            'daily': {},
            'total_ever': 0,
            'last_reset': datetime.now().strftime("%Y-%m-%d"),
            'streak_days': 0,
            'last_active': None  # None تعني لا نشاط سابق
        }

    def save_stats(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def update_today_stats(self, zekr_name):
        today = datetime.now().strftime("%Y-%m-%d")
        
        # تحديث الستريك قبل تعديل last_active
        self.update_streak()
        
        if today not in self.stats['daily']:
            self.stats['daily'][today] = {'total': 0, 'azkar': {}}
        self.stats['daily'][today]['total'] += 1
        self.stats['daily'][today]['azkar'][zekr_name] = self.stats['daily'][today]['azkar'].get(zekr_name, 0) + 1
        self.stats['total_ever'] += 1
        self.stats['last_active'] = today
        self.save_stats()
        self.update_stats_display()
        self.draw_chart()

    def update_streak(self):
        """تحديث عدد الأيام المتتالية - يُستدعى قبل تحديث last_active"""
        today = datetime.now().strftime("%Y-%m-%d")
        last_active = self.stats.get('last_active')
        
        if last_active is None:
            # أول نشاط على الإطلاق
            self.stats['streak_days'] = 1
            return
            
        if last_active == today:
            return  # مُحسَّب بالفعل

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if last_active == yesterday:
            self.stats['streak_days'] = self.stats.get('streak_days', 0) + 1
        else:
            # انقطاع - نبدأ من جديد
            self.stats['streak_days'] = 1

    # --------------------- إدارة الأذكار المخصصة ---------------------
    def load_custom_azkar(self):
        """تحميل الأذكار المخصصة"""
        self.custom_azkar = {}
        if os.path.exists(self.custom_azkar_file):
            try:
                with open(self.custom_azkar_file, 'r', encoding='utf-8') as f:
                    self.custom_azkar = json.load(f)
            except:
                pass

    def save_custom_azkar(self):
        with open(self.custom_azkar_file, 'w', encoding='utf-8') as f:
            json.dump(self.custom_azkar, f, ensure_ascii=False, indent=2)

    def add_custom_zekr(self):
        """إضافة ذكر مخصص جديد"""
        win = tk.Toplevel(self.root)
        win.title("إضافة ذكر مخصص")
        win.geometry("500x400")
        win.configure(bg=self.get_bg())
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="✨ إضافة ذكر جديد", font=("Segoe UI", 16, "bold"),
                bg=self.get_bg(), fg=self.get_primary()).pack(pady=15)

        # اسم الذكر
        tk.Label(win, text="الذكر:", font=("Segoe UI", 11), bg=self.get_bg(), 
                fg=self.get_fg()).pack(anchor="e", padx=20, pady=(10, 0))
        entry_name = tk.Entry(win, font=("Segoe UI", 12), width=40, justify="right")
        entry_name.pack(padx=20, pady=5)

        # الحديث
        tk.Label(win, text="الحديث (اختياري):", font=("Segoe UI", 11), bg=self.get_bg(),
                fg=self.get_fg()).pack(anchor="e", padx=20, pady=(10, 0))
        entry_hadith = tk.Text(win, font=("Segoe UI", 11), width=40, height=4, wrap="word")
        entry_hadith.pack(padx=20, pady=5)

        # الفضل
        tk.Label(win, text="الفضل:", font=("Segoe UI", 11), bg=self.get_bg(),
                fg=self.get_fg()).pack(anchor="e", padx=20, pady=(10, 0))
        entry_fadl = tk.Entry(win, font=("Segoe UI", 11), width=40, justify="right")
        entry_fadl.pack(padx=20, pady=5)

        def save():
            name = entry_name.get().strip()
            hadith = entry_hadith.get("1.0", "end").strip()
            fadl = entry_fadl.get().strip()

            if not name:
                messagebox.showerror("خطأ", "يرجى إدخال الذكر", parent=win)
                return

            zekr_data = {
                "hadith": hadith or "ذكر مخصص",
                "count": 0,
                "grade": "مخصص",
                "source": "مستخدم",
                "category": "مخصص",
                "fadl": fadl or "-"
            }

            self.custom_azkar[name] = zekr_data
            self.azkar_data[name] = zekr_data.copy()
            self.azkar_list = list(self.azkar_data.keys())
            self.save_custom_azkar()

            # تحديث الواجهة
            self.zekr_combo['values'] = self.azkar_list
            self.zekr_combo.set(name)
            messagebox.showinfo("تم", "✅ تم إضافة الذكر بنجاح", parent=win)
            win.destroy()

            # إعادة بناء شاشة الأحاديث
            self.populate_hadith_list()

        btn_frame = tk.Frame(win, bg=self.get_bg())
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="حفظ", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["success"], fg="white", bd=0, padx=25, pady=8,
                 command=save).pack(side="left", padx=5)
        tk.Button(btn_frame, text="إلغاء", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["warning"], fg="white", bd=0, padx=25, pady=8,
                 command=win.destroy).pack(side="left", padx=5)

    # --------------------- helper methods للألوان ---------------------
    def get_bg(self):
        return self.colors["dark_bg"] if self.dark_mode else self.colors["light_bg"]

    def get_card_bg(self):
        return self.colors["dark_card"] if self.dark_mode else self.colors["light_card"]

    def get_accent(self):
        return self.colors["dark_accent"] if self.dark_mode else self.colors["light_accent"]

    def get_fg(self):
        return "#ecf0f1" if self.dark_mode else self.colors["light_text"]

    def get_primary(self):
        return self.colors["primary"]

    def get_secondary_text(self):
        return "#bdc3c7" if self.dark_mode else "#7f8c8d"


    # --------------------- بناء الواجهة الرئيسية ---------------------
    def setup_ui(self):
        """بناء الهيكل الأساسي للواجهة"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ===== تبويب التسبيح =====
        self.tab_main = tk.Frame(self.notebook, bg=self.get_bg())
        self.notebook.add(self.tab_main, text="📿  التسبيح")
        self.tab_main.grid_rowconfigure(0, weight=1)
        self.tab_main.grid_columnconfigure(0, weight=1)

        # ===== تبويب الأحاديث =====
        self.tab_hadith = tk.Frame(self.notebook, bg=self.get_bg())
        self.notebook.add(self.tab_hadith, text="📖  الأحاديث النبوية")
        self.setup_hadith_tab()

        # ===== تبويب الإحصائيات =====
        self.tab_stats = tk.Frame(self.notebook, bg=self.get_bg())
        self.notebook.add(self.tab_stats, text="📊  الإحصائيات")
        self.setup_stats_tab()

        # ===== بناء شاشات التسبيح =====
        self.build_start_screen()
        self.build_tasbih_screen()

    # ===================== شاشة البداية =====================
    def build_start_screen(self):
        """بناء شاشة البداية الجميلة"""
        self.start_frame = tk.Frame(self.tab_main, bg=self.get_bg())
        self.start_frame.grid(row=0, column=0, sticky="nsew")
        self.start_frame.grid_rowconfigure(0, weight=1)
        self.start_frame.grid_columnconfigure(0, weight=1)

        # الإطار المركزي
        center = tk.Frame(self.start_frame, bg=self.get_bg())
        center.place(relx=0.5, rely=0.5, anchor="center")

        # الأيقونة المتحركة
        self.start_icon = tk.Label(center, text="📿", font=("Segoe UI", 100),
                                   bg=self.get_bg(), fg=self.colors["gold"])
        self.start_icon.pack(pady=(0, 10))

        # عنوان التطبيق
        tk.Label(center, text="السبحة الذكية", font=("Segoe UI", 38, "bold"),
                bg=self.get_bg(), fg=self.colors["primary"]).pack(pady=5)

        tk.Label(center, text="تسبيحك مع الأحاديث النبوية الصحيحة",
                font=("Segoe UI", 13), bg=self.get_bg(), fg=self.get_secondary_text()).pack(pady=(0, 25))

        # الإحصائيات السريعة
        quick_stats = tk.Frame(center, bg=self.get_card_bg(), highlightbackground=self.colors["primary"],
                              highlightthickness=1, padx=20, pady=15)
        quick_stats.pack(pady=10, fill="x", padx=50)

        self.start_today_label = tk.Label(quick_stats, text="اليوم: 0",
                                         font=("Segoe UI", 12, "bold"),
                                         bg=self.get_card_bg(), fg=self.colors["success"])
        self.start_today_label.pack(side="right", padx=15)

        self.start_total_label = tk.Label(quick_stats, text="الإجمالي: 0",
                                         font=("Segoe UI", 12, "bold"),
                                         bg=self.get_card_bg(), fg=self.colors["info"])
        self.start_total_label.pack(side="right", padx=15)

        self.start_streak_label = tk.Label(quick_stats, text="الأيام المتتالية: 0",
                                          font=("Segoe UI", 12, "bold"),
                                          bg=self.get_card_bg(), fg=self.colors["gold"])
        self.start_streak_label.pack(side="right", padx=15)

        # أزرار الأهداف السريعة
        targets_frame = tk.Frame(center, bg=self.get_bg())
        targets_frame.pack(pady=15)

        tk.Label(targets_frame, text="اختر هدفك:", font=("Segoe UI", 12, "bold"),
                bg=self.get_bg(), fg=self.get_fg()).pack(pady=(0, 10))

        targets_grid = tk.Frame(targets_frame, bg=self.get_bg())
        targets_grid.pack()

        targets = [33, 100, 300, 500, 1000, 5000]
        colors_t = ["#3498db", "#2ecc71", "#9b59b6", "#e67e22", "#e74c3c", "#1abc9c"]

        for i, (val, col) in enumerate(zip(targets, colors_t)):
            btn = tk.Button(targets_grid, text=f"{val}", font=("Segoe UI", 13, "bold"),
                           bg=col, fg="white", bd=0, width=8, height=2,
                           command=lambda v=val: self.set_quick_target(v),
                           activebackground=self.colors["primary"], cursor="hand2")
            btn.grid(row=0, column=i, padx=5, pady=5)

        # إدخال الهدف اليدوي
        input_card = tk.Frame(center, bg=self.get_card_bg(), padx=20, pady=12,
                             highlightbackground="#0f3460", highlightthickness=1)
        input_card.pack(pady=15, fill="x", padx=80)

        tk.Label(input_card, text="هدف مخصص:", font=("Segoe UI", 12, "bold"),
                bg=self.get_card_bg(), fg=self.get_fg()).pack(side="right", padx=10)

        self.entry_target = tk.Entry(input_card, font=("Segoe UI", 18, "bold"),
                                     justify="center", bd=0,
                                     bg="#0f3460" if self.dark_mode else "white",
                                     fg="white" if self.dark_mode else self.colors["light_text"],
                                     width=8, insertbackground="white" if self.dark_mode else "black")
        self.entry_target.insert(0, str(self.target))
        self.entry_target.pack(side="right", padx=10, pady=5)

        # إعدادات سريعة
        settings_bar = tk.Frame(center, bg=self.get_bg())
        settings_bar.pack(pady=15)

        self.btn_theme = tk.Button(settings_bar, text="☀️ وضع فاتح" if self.dark_mode else "🌙 وضع داكن",
                                  font=("Segoe UI", 10, "bold"), bg=self.colors["secondary"],
                                  fg="white", bd=0, padx=15, pady=6, command=self.toggle_theme,
                                  cursor="hand2")
        self.btn_theme.pack(side="left", padx=5)

        self.btn_sound = tk.Button(settings_bar, text="🔊 صوت مفعل" if self.sound_on else "🔇 صوت mute",
                                  font=("Segoe UI", 10, "bold"), bg=self.colors["secondary"],
                                  fg="white", bd=0, padx=15, pady=6, command=self.toggle_sound,
                                  cursor="hand2")
        self.btn_sound.pack(side="left", padx=5)

        self.btn_custom = tk.Button(settings_bar, text="➕ ذكر مخصص",
                                   font=("Segoe UI", 10, "bold"), bg=self.colors["info"],
                                   fg="white", bd=0, padx=15, pady=6, command=self.add_custom_zekr,
                                   cursor="hand2")
        self.btn_custom.pack(side="left", padx=5)
        
        self.btn_focus = tk.Button(settings_bar, text="🧘 وضع التركيز: OFF" if not self.focus_mode else "🧘 وضع التركيز: ON",
                                  font=("Segoe UI", 10, "bold"), bg=self.colors["warning"],
                                  fg="white", bd=0, padx=15, pady=6, command=self.toggle_focus_mode,
                                  cursor="hand2")
        self.btn_focus.pack(side="left", padx=5)

        # زر البدء الرئيسي
        self.btn_start = tk.Button(center, text="✨  ابدأ التسبيح  ✨", font=("Segoe UI", 18, "bold"),
                                  bg=self.colors["primary"], fg="white", bd=0, padx=30, pady=14,
                                  command=self.start_app, activebackground="#c0392b",
                                  cursor="hand2")
        self.btn_start.pack(pady=25)

        # إرشادات الاختصارات
        shortcuts = tk.Label(center, text="⌨️ Enter = تسبيح  |  Backspace = تراجع  |  Esc = تصفير",
                            font=("Consolas", 10), bg=self.get_bg(), fg=self.get_secondary_text())
        shortcuts.pack(pady=(5, 0))

    # ===================== شاشة التسبيح الرئيسية =====================
    def build_tasbih_screen(self):
        """بناء شاشة التسبيح مع الخرز المتحرك"""
        self.tasbih_frame = tk.Frame(self.tab_main, bg=self.get_bg())
        self.tasbih_frame.grid(row=0, column=0, sticky="nsew")
        self.tasbih_frame.grid_rowconfigure(0, weight=1)
        self.tasbih_frame.grid_columnconfigure(0, weight=1)

        # إطار التحكم العلوي
        control_frame = tk.Frame(self.tasbih_frame, bg=self.get_card_bg(), padx=15, pady=10)
        control_frame.pack(fill="x", padx=15, pady=(15, 5))

        # اختيار الذكر
        zekr_label = tk.Label(control_frame, text="📿 الذكر:", font=("Segoe UI", 11, "bold"),
                             bg=self.get_card_bg(), fg=self.colors["primary"])
        zekr_label.pack(side="right", padx=(0, 10))

        self.zekr_combo = ttk.Combobox(control_frame, values=self.azkar_list,
                                      state="readonly", font=("Segoe UI", 11),
                                      justify="right", width=35)
        self.zekr_combo.set(self.azkar_list[0])
        self.zekr_combo.pack(side="right", expand=True, fill="x", padx=(0, 10))
        self.zekr_combo.bind("<<ComboboxSelected>>", self.on_zekr_change)

        # زر عرض الحديث
        self.btn_hadith = tk.Button(control_frame, text="📖 الحديث", font=("Segoe UI", 10, "bold"),
                                   bg=self.colors["info"], fg="white", bd=0, padx=12, pady=5,
                                   command=self.show_hadith_popup, cursor="hand2")
        self.btn_hadith.pack(side="left", padx=5)

        # العداد الجزئي
        self.label_sub_count = tk.Label(self.tasbih_frame,
                                       text="📊 تكرار هذا الذكر: 0",
                                       font=("Segoe UI", 12, "bold"),
                                       bg=self.get_bg(), fg=self.colors["warning"])
        self.label_sub_count.pack(pady=5)

        # ===== Canvas الخرز المتحرك =====
        self.setup_bead_canvas()

        # ===== العداد الرئيسي =====
        counter_card = tk.Frame(self.tasbih_frame, bg=self.get_card_bg(),
                               highlightbackground=self.colors["primary"],
                               highlightthickness=2, padx=30, pady=15)
        counter_card.pack(pady=10)

        self.label_total = tk.Label(counter_card, text="0", font=("Segoe UI", 72, "bold"),
                                   bg=self.get_card_bg(), fg=self.colors["primary"], width=5)
        self.label_total.pack()

        # شريط التقدم
        self.progress_bar = ttk.Progressbar(self.tasbih_frame, orient="horizontal",
                                           length=400, mode="determinate")
        self.progress_bar.pack(pady=5)

        # معلومات إضافية
        self.label_info = tk.Label(self.tasbih_frame, text="",
                                  font=("Segoe UI", 12), bg=self.get_bg(), fg=self.get_secondary_text())
        self.label_info.pack(pady=5)

        # ===== أزرار التحكم =====
        btn_frame = tk.Frame(self.tasbih_frame, bg=self.get_bg())
        btn_frame.pack(pady=10)

        # زر التسبيح الرئيسي (كبير)
        self.btn_tasbih = tk.Button(btn_frame, text="📿  سَبِّح  📿\n(Enter)",
                                   font=("Segoe UI", 16, "bold"),
                                   bg=self.colors["primary"], fg="white", bd=0,
                                   padx=40, pady=12, command=self.count_up,
                                   activebackground="#c0392b", cursor="hand2")
        self.btn_tasbih.pack(pady=5)

        # أزرار ثانوية
        sub_btns = tk.Frame(btn_frame, bg=self.get_bg())
        sub_btns.pack(pady=8)

        tk.Button(sub_btns, text="↩️ تراجع", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["warning"], fg="white", bd=0, padx=15, pady=6,
                 command=self.undo_last, cursor="hand2").pack(side="left", padx=5)

        tk.Button(sub_btns, text="🔄 تصفير", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["secondary"], fg="white", bd=0, padx=15, pady=6,
                 command=self.reset_counter, cursor="hand2").pack(side="left", padx=5)

        tk.Button(sub_btns, text="🔙 رجوع", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["info"], fg="white", bd=0, padx=15, pady=6,
                 command=self.go_back, cursor="hand2").pack(side="left", padx=5)

    # ===================== Canvas الخرز المتحرك =====================
    def setup_bead_canvas(self):
        """إنشاء رسوم الخرز المتحركة"""
        self.anim_canvas = tk.Canvas(self.tasbih_frame, width=350, height=350,
                                    bg=self.get_bg(), highlightthickness=0)
        self.anim_canvas.pack(pady=8)

        self.beads_main = []
        self.beads_shadow = []
        self.bead_centers = []
        cx, cy = 175, 175
        r = 130

        # رسم الدائرة الخارجية
        self.anim_canvas.create_oval(cx-r-5, cy-r-5, cx+r+5, cy+r+5,
                             outline="", width=0) # جعلنا الإطار فارغاً والعرض صفراً

        for i in range(33):
            angle = -math.pi/2 + (i * 2 * math.pi / 33)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            self.bead_centers.append((x, y))

            # الظل
            shadow = self.anim_canvas.create_oval(x-10, y-10, x+10, y+10,
                                                 fill="#1a1a3e" if self.dark_mode else "#d5dbdb",
                                                 outline="")
            self.beads_shadow.append(shadow)

            # الخرزة
            bead = self.anim_canvas.create_oval(x-7, y-7, x+7, y+7,
                                               fill="#34495e", outline="#2c3e50", width=1)
            self.beads_main.append(bead)

        # النص المركزي
        self.cycle_text = self.anim_canvas.create_text(cx, cy, text="0 / 33",
                                                      font=("Segoe UI", 24, "bold"),
                                                      fill=self.colors["gold"])

        # قوس التقدم
# قوس التقدم - تعديل لجعل الخط مخفي
        self.progress_arc_bg = self.anim_canvas.create_arc(cx-r-15, cy-r-15, cx+r+15, cy+r+15,
                                                          start=90, extent=0,
                                                          outline="", width=0, style="arc")
        
        self.progress_arc = self.anim_canvas.create_arc(cx-r-15, cy-r-15, cx+r+15, cy+r+15,
                                                       start=90, extent=0,
                                                       outline="", width=0, style="arc")

    # ===================== شاشة الأحاديث المتقدمة =====================
    def setup_hadith_tab(self):
        """بناء تبويب الأحاديث مع بحث وفلترة"""
        # الشريط العلوي - البحث والفلترة
        top_bar = tk.Frame(self.tab_hadith, bg=self.get_card_bg(), padx=15, pady=12)
        top_bar.pack(fill="x", padx=15, pady=(15, 5))

        # البحث
        search_frame = tk.Frame(top_bar, bg=self.get_card_bg())
        search_frame.pack(fill="x", pady=3)

        tk.Label(search_frame, text="🔍 بحث:", font=("Segoe UI", 11, "bold"),
                bg=self.get_card_bg(), fg=self.get_fg()).pack(side="right", padx=5)

        self.search_entry = tk.Entry(search_frame, font=("Segoe UI", 12), width=30,
                                    bd=1, relief="solid", justify="right")
        self.search_entry.pack(side="right", padx=5, ipady=3)
        self.search_entry.bind("<KeyRelease>", lambda e: self.populate_hadith_list())

        tk.Button(search_frame, text="✖ مسح", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["primary"], fg="white", bd=0, padx=10, pady=3,
                 command=self.clear_search, cursor="hand2").pack(side="right", padx=5)

        # الفلترة حسب الفئة
        filter_frame = tk.Frame(top_bar, bg=self.get_card_bg())
        filter_frame.pack(fill="x", pady=8)

        tk.Label(filter_frame, text="🏷️ الفئة:", font=("Segoe UI", 11, "bold"),
                bg=self.get_card_bg(), fg=self.get_fg()).pack(side="right", padx=5)

        self.category_var = tk.StringVar(value="الكل")
        self.category_combo = ttk.Combobox(filter_frame, values=self.categories,
                                          state="readonly", font=("Segoe UI", 10),
                                          justify="right", width=20, textvariable=self.category_var)
        self.category_combo.pack(side="right", padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.populate_hadith_list())

        # الفلترة حسب الدرجة
        tk.Label(filter_frame, text="⭐ الدرجة:", font=("Segoe UI", 11, "bold"),
                bg=self.get_card_bg(), fg=self.get_fg()).pack(side="right", padx=(15, 5))

        self.grade_var = tk.StringVar(value="الكل")
        grades = ["الكل", "صحيح", "حسن صحيح", "حسن", "مخصص"]
        self.grade_combo = ttk.Combobox(filter_frame, values=grades,
                                       state="readonly", font=("Segoe UI", 10),
                                       justify="right", width=15, textvariable=self.grade_var)
        self.grade_combo.pack(side="right", padx=5)
        self.grade_combo.bind("<<ComboboxSelected>>", lambda e: self.populate_hadith_list())

        # حجم الخط
        font_frame = tk.Frame(top_bar, bg=self.get_card_bg())
        font_frame.pack(fill="x", pady=5)

        tk.Label(font_frame, text="📏 الخط:", font=("Segoe UI", 10),
                bg=self.get_card_bg(), fg=self.get_fg()).pack(side="right", padx=5)

        tk.Button(font_frame, text="▲", font=("Segoe UI", 10, "bold"), width=4,
                 bg=self.colors["success"], fg="white", bd=0,
                 command=lambda: self.change_font(1), cursor="hand2").pack(side="right", padx=2)

        tk.Button(font_frame, text="▼", font=("Segoe UI", 10, "bold"), width=4,
                 bg=self.colors["warning"], fg="white", bd=0,
                 command=lambda: self.change_font(-1), cursor="hand2").pack(side="right", padx=2)

        self.hadith_count_label = tk.Label(font_frame, text=f"📚 عدد الأذكار: {len(self.azkar_data)}",
                                          font=("Segoe UI", 10, "bold"),
                                          bg=self.get_card_bg(), fg=self.get_secondary_text())
        self.hadith_count_label.pack(side="left")

        # منطقة التمرير
        self.container_frame = tk.Frame(self.tab_hadith, bg=self.get_bg())
        self.container_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.hadith_canvas = tk.Canvas(self.container_frame, bg=self.get_bg(), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.container_frame, orient="vertical",
                                 command=self.hadith_canvas.yview)
        self.scrollable_frame = tk.Frame(self.hadith_canvas, bg=self.get_bg())

        self.scrollable_frame.bind("<Configure>",
                                  lambda e: self.hadith_canvas.configure(
                                      scrollregion=self.hadith_canvas.bbox("all")))

        self.canvas_window = self.hadith_canvas.create_window((0, 0), window=self.scrollable_frame,
                                                              anchor="nw")

        def on_canvas_configure(event):
            self.hadith_canvas.itemconfig(self.canvas_window, width=event.width)

        self.hadith_canvas.bind("<Configure>", on_canvas_configure)
        self.hadith_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.hadith_canvas.configure(yscrollcommand=scrollbar.set)

        # عجلة الماوس
        def on_mousewheel(event):
            self.hadith_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.hadith_canvas.bind("<Enter>", lambda e: self.hadith_canvas.bind("<MouseWheel>", on_mousewheel))
        self.hadith_canvas.bind("<Leave>", lambda e: self.hadith_canvas.unbind("<MouseWheel>"))

        self.hadith_labels = []
        self.populate_hadith_list()

    def populate_hadith_list(self):
        """عرض قائمة الأحاديث مع البحث والفلترة"""
        # مسح المحتوى القديم
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.hadith_labels.clear()

        search_text = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
        category = self.category_var.get() if hasattr(self, 'category_var') else "الكل"
        grade = self.grade_var.get() if hasattr(self, 'grade_var') else "الكل"

        # الألوان
        card_bg = self.get_card_bg()
        fg = self.get_fg()
        sec = self.get_secondary_text()

        count = 0
        for zekr, data in self.azkar_data.items():
            # فلترة البحث
            if search_text and search_text not in zekr and search_text not in data.get('hadith', ''):
                continue
            # فلترة الفئة
            if category != "الكل" and data.get('category', '') != category:
                continue
            # فلترة الدرجة
            if grade != "الكل" and data.get('grade', '') != grade:
                continue

            count += 1
            self.create_hadith_card(zekr, data, card_bg, fg, sec)

        self.hadith_count_label.config(text=f"📚 النتائج: {count}")

        # تحديث wraplength
        self.scrollable_frame.update_idletasks()
        c_width = self.hadith_canvas.winfo_width()
        if c_width > 0:
            for lbl in self.hadith_labels:
                lbl.config(wraplength=c_width - 80)

    def create_hadith_card(self, zekr, data, card_bg, fg, sec):
        """إنشاء بطاقة حديث واحدة"""
        # الإطار الرئيسي
        card = tk.Frame(self.scrollable_frame, bg=card_bg, highlightbackground="#0f3460",
                       highlightthickness=1, padx=15, pady=12)
        card.pack(fill="x", pady=8, padx=5)

        # عنوان الذكر
        title = tk.Label(card, text=zekr, font=("Segoe UI", self.font_size + 2, "bold"),
                        bg=card_bg, fg=self.colors["primary"], justify="right")
        title.pack(anchor="e", pady=(0, 8))
        self.hadith_labels.append(title)

        # نص الحديث
        if data.get('hadith'):
            hadith_lbl = tk.Label(card, text=data['hadith'], font=("Segoe UI", self.font_size),
                                 bg=card_bg, fg=fg, justify="right")
            hadith_lbl.pack(anchor="e", pady=(0, 8))
            self.hadith_labels.append(hadith_lbl)

        # الفضل
        if data.get('fadl'):
            fadl_lbl = tk.Label(card, text=f"✨ الفضل: {data['fadl']}",
                               font=("Segoe UI", self.font_size - 1, "bold"),
                               bg=card_bg, fg=self.colors["gold"], justify="right")
            fadl_lbl.pack(anchor="e", pady=(0, 8))
            self.hadith_labels.append(fadl_lbl)

        # إطار المعلومات والأزرار
        info_frame = tk.Frame(card, bg=card_bg)
        info_frame.pack(fill="x", pady=5)

        tk.Label(info_frame, text=f"⭐ {data.get('grade', '-')}",
                font=("Segoe UI", 10, "bold"), bg=card_bg, fg=self.colors["success"]).pack(side="right", padx=8)
        tk.Label(info_frame, text=f"📚 {data.get('source', '-')}",
                font=("Segoe UI", 10, "bold"), bg=card_bg, fg=self.colors["info"]).pack(side="right", padx=8)
        tk.Label(info_frame, text=f"🏷️ {data.get('category', '-')}",
                font=("Segoe UI", 10), bg=card_bg, fg=sec).pack(side="right", padx=8)

        # عداد التكرار
        count_val = data.get('count', 0)
        tk.Label(info_frame, text=f"📊 {count_val}",
                font=("Segoe UI", 10, "bold"), bg=card_bg, fg=self.colors["warning"]).pack(side="left", padx=8)

        tk.Button(info_frame, text="📋 نسخ", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["info"], fg="white", bd=0, padx=12, pady=4,
                 command=lambda z=zekr, d=data: self.copy_hadith(d['hadith'], z, d.get('grade', ''), d.get('source', ''), d.get('fadl', '')),
                 cursor="hand2").pack(side="left", padx=5)

        tk.Button(info_frame, text="▶️ تسبيح", font=("Segoe UI", 9, "bold"),
                 bg=self.colors["primary"], fg="white", bd=0, padx=12, pady=4,
                 command=lambda z=zekr: self.quick_tasbih(z), cursor="hand2").pack(side="left", padx=5)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.category_var.set("الكل")
        self.grade_var.set("الكل")
        self.populate_hadith_list()

    def change_font(self, delta):
        self.font_size += delta
        self.font_size = max(10, min(24, self.font_size))
        self.populate_hadith_list()


    # ===================== شاشة الإحصائيات المتقدمة =====================
    def setup_stats_tab(self):
        """بناء تبويب الإحصائيات مع الرسم البياني"""
        # الشريط العلوي - ملخص سريع
        summary = tk.Frame(self.tab_stats, bg=self.get_card_bg(), padx=20, pady=15)
        summary.pack(fill="x", padx=15, pady=(15, 5))

        # بطاقات الإحصائيات
        stats = [
            ("📊 اليوم", "0", self.colors["success"]),
            ("📈 الإجمالي", "0", self.colors["info"]),
            ("🔥 المتتالية", "0", self.colors["primary"]),
            ("📅 آخر 7 أيام", "0", self.colors["gold"]),
        ]
        self.stat_cards = []
        for title, val, color in stats:
            card = tk.Frame(summary, bg=self.get_bg(), padx=20, pady=12,
                           highlightbackground=color, highlightthickness=2)
            card.pack(side="right", padx=8, expand=True, fill="both")
            tk.Label(card, text=title, font=("Segoe UI", 11, "bold"),
                    bg=self.get_bg(), fg=self.get_secondary_text()).pack()
            lbl = tk.Label(card, text=val, font=("Segoe UI", 22, "bold"),
                          bg=self.get_bg(), fg=color)
            lbl.pack()
            self.stat_cards.append(lbl)

        # الرسم البياني
        chart_frame = tk.Frame(self.tab_stats, bg=self.get_card_bg(), padx=15, pady=10)
        chart_frame.pack(fill="both", expand=True, padx=15, pady=10)

        tk.Label(chart_frame, text="📊 نشاط آخر 14 يوم", font=("Segoe UI", 14, "bold"),
                bg=self.get_card_bg(), fg=self.get_primary()).pack(anchor="e", pady=(0, 10))

        self.chart_canvas = tk.Canvas(chart_frame, bg=self.get_card_bg(), highlightthickness=0, height=250)
        self.chart_canvas.pack(fill="both", expand=True)

        # أزرار التصدير
        export_frame = tk.Frame(self.tab_stats, bg=self.get_bg(), padx=15, pady=10)
        export_frame.pack(fill="x", padx=15)

        tk.Button(export_frame, text="📄 تصدير JSON", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["success"], fg="white", bd=0, padx=15, pady=8,
                 command=lambda: self.export_stats("json"), cursor="hand2").pack(side="right", padx=5)

        tk.Button(export_frame, text="📊 تصدير CSV", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["info"], fg="white", bd=0, padx=15, pady=8,
                 command=lambda: self.export_stats("csv"), cursor="hand2").pack(side="right", padx=5)

        tk.Button(export_frame, text="⚠️ تصفير الإحصائيات", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["primary"], fg="white", bd=0, padx=15, pady=8,
                 command=self.reset_stats, cursor="hand2").pack(side="left", padx=5)

        self.draw_chart()
        self.update_stats_display()

    def draw_chart(self):
        """رسم بياني شريطي لآخر 14 يوم"""
        self.chart_canvas.delete("all")

        width = self.chart_canvas.winfo_width()
        height = self.chart_canvas.winfo_height()
        if width < 100:
            width = 800
        if height < 100:
            height = 250

        # جمع بيانات 14 يوم
        days = []
        values = []
        max_val = 1

        for i in range(13, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_name = (datetime.now() - timedelta(days=i)).strftime("%d/%m")
            val = self.stats['daily'].get(d, {}).get('total', 0)
            days.append(day_name)
            values.append(val)
            if val > max_val:
                max_val = val

        # هامش
        margin_left = 50
        margin_bottom = 40
        margin_top = 20
        chart_w = width - margin_left - 20
        chart_h = height - margin_bottom - margin_top

        # رسم خطوط الخلفية
        for i in range(5):
            y = margin_top + (chart_h / 4) * i
            self.chart_canvas.create_line(margin_left, y, width - 20, y,
                                         fill="#0f3460", width=1)
            val_label = int(max_val - (max_val / 4) * i)
            self.chart_canvas.create_text(margin_left - 25, y, text=str(val_label),
                                         font=("Segoe UI", 8), fill=self.get_secondary_text(),
                                         anchor="e")

        # رسم الأعمدة
        bar_count = len(values)
        bar_w = (chart_w / bar_count) * 0.6
        gap = (chart_w / bar_count) * 0.4

        today_str = datetime.now().strftime("%d/%m")

        for i, (day, val) in enumerate(zip(days, values)):
            x = margin_left + gap/2 + i * (bar_w + gap)
            bar_h = (val / max_val) * chart_h if max_val > 0 else 0
            y1 = margin_top + chart_h - bar_h
            y2 = margin_top + chart_h

            # لون مختلف لليوم الحالي
            color = self.colors["primary"] if day == today_str else self.colors["info"]
            if val > 0:
                self.chart_canvas.create_rectangle(x, y1, x + bar_w, y2,
                                                  fill=color, outline="", width=0)
                # القيمة فوق العمود
                self.chart_canvas.create_text(x + bar_w/2, y1 - 10, text=str(val),
                                             font=("Segoe UI", 8, "bold"), fill=color)

            # اسم اليوم
            self.chart_canvas.create_text(x + bar_w/2, y2 + 15, text=day,
                                         font=("Segoe UI", 8), fill=self.get_secondary_text())

        # عنوان
        self.chart_canvas.create_text(width/2, 10, text="نشاط التسبيح اليومي",
                                     font=("Segoe UI", 10, "bold"), fill=self.get_secondary_text())

    def update_stats_display(self):
        """تحديث عرض الإحصائيات"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_total = self.stats['daily'].get(today, {}).get('total', 0)

        last_7 = 0
        for i in range(7):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            last_7 += self.stats['daily'].get(d, {}).get('total', 0)

        streak = self.stats.get('streak_days', 0)

        # تحديث البطاقات
        if hasattr(self, 'stat_cards') and len(self.stat_cards) >= 4:
            self.stat_cards[0].config(text=str(today_total))
            self.stat_cards[1].config(text=str(self.stats['total_ever']))
            self.stat_cards[2].config(text=str(streak))
            self.stat_cards[3].config(text=str(last_7))

        # تحديث شاشة البداية
        if hasattr(self, 'start_today_label'):
            self.start_today_label.config(text=f"اليوم: {today_total}")
            self.start_total_label.config(text=f"الإجمالي: {self.stats['total_ever']}")
            self.start_streak_label.config(text=f"الأيام المتتالية: {streak}")

        # تحديث العداد الجزئي
        if hasattr(self, 'label_sub_count'):
            self.update_sub_counter()

    # ===================== دوال التصدير =====================
    def export_stats(self, fmt="json"):
        """تصدير الإحصائيات"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if fmt == "json":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    initialfile=f"tasbih_stats_{timestamp}.json",
                    filetypes=[("JSON files", "*.json")],
                    title="حفظ الإحصائيات"
                )
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.stats, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("تم التصدير", "✅ تم حفظ الإحصائيات بنجاح")

            elif fmt == "csv":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    initialfile=f"tasbih_stats_{timestamp}.csv",
                    filetypes=[("CSV files", "*.csv")],
                    title="حفظ الإحصائيات"
                )
                if filename:
                    with open(filename, 'w', encoding='utf-8-sig') as f:
                        f.write("التاريخ,العدد,الأذكار\n")
                        for date, data in sorted(self.stats['daily'].items()):
                            azkar_summary = "; ".join([f"{k}: {v}" for k, v in data.get('azkar', {}).items()])
                            f.write(f"{date},{data['total']},\"{azkar_summary}\"\n")
                    messagebox.showinfo("تم التصدير", "✅ تم تصدير الإحصائيات بصيغة CSV")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التصدير: {e}")

    def reset_stats(self):
        """تصفير الإحصائيات"""
        if messagebox.askyesno("تأكيد", "⚠️ هل أنت متأكد من تصفير جميع الإحصائيات؟ لا يمكن التراجع."):
            self.stats = self.init_stats()
            self.save_stats()
            self.update_stats_display()
            self.draw_chart()
            messagebox.showinfo("تم", "✅ تم تصفير الإحصائيات")


    # ===================== الوظائف الأساسية =====================
    def set_quick_target(self, val):
        """تعيين هدف سريع"""
        self.entry_target.delete(0, tk.END)
        self.entry_target.insert(0, str(val))
        # تأثير بصري
        self.entry_target.config(bg=self.colors["primary"])
        self.root.after(200, lambda: self.entry_target.config(
            bg="#0f3460" if self.dark_mode else "white"))

    def toggle_theme(self):
        """تبديل الوضع الداكن/الفاتح"""
        self.dark_mode = not self.dark_mode
        self.save_settings()
        self.apply_theme()
        self.populate_hadith_list()
        self.draw_chart()

    def apply_theme(self):
        """تطبيق السمة الحالية على جميع العناصر"""
        bg = self.get_bg()
        card_bg = self.get_card_bg()
        accent = self.get_accent()
        fg = self.get_fg()

        # تحديث الأزرار
        theme_text = "☀️ وضع فاتح" if self.dark_mode else "🌙 وضع داكن"
        self.btn_theme.config(text=theme_text, bg=self.colors["secondary"])

        # تحديث الإطارات الرئيسية
        for frame in [self.root, self.tab_main, self.tab_hadith, self.tab_stats,
                      self.start_frame, self.tasbih_frame]:
            if frame:
                frame.config(bg=bg)

        # تحديث Canvas الخرز
        if hasattr(self, 'anim_canvas'):
            self.anim_canvas.config(bg=bg)
            # تحديث ألوان الظلال
            shadow_color = "#1a1a3e" if self.dark_mode else "#d5dbdb"
            for shadow in self.beads_shadow:
                self.anim_canvas.itemconfig(shadow, fill=shadow_color)

        # تحديث Canvas الأحاديث
        if hasattr(self, 'hadith_canvas'):
            self.hadith_canvas.config(bg=bg)

        # تحديث Canvas الرسم البياني
        if hasattr(self, 'chart_canvas'):
            self.chart_canvas.config(bg=card_bg)

        # تحديث entry_target
        if hasattr(self, 'entry_target'):
            self.entry_target.config(
                bg="#0f3460" if self.dark_mode else "white",
                fg="white" if self.dark_mode else self.colors["light_text"],
                insertbackground="white" if self.dark_mode else "black"
            )

        # تحديث Combobox
        if hasattr(self, 'zekr_combo'):
            self.zekr_combo.config(foreground=fg if not self.dark_mode else "black")

    def toggle_sound(self):
        """تبديل الصوت"""
        if not SOUND_ENABLED:
            messagebox.showwarning("الصوت", "⚠️ لا يوجد backend صوت متاح على هذا النظام.\n\nلتفعيل الصوت:\n- Windows: مفعل تلقائياً\n- Linux/macOS: ثبت pygame (pip install pygame) أو simpleaudio (pip install simpleaudio)")
            return
        self.sound_on = not self.sound_on
        self.btn_sound.config(text="🔊 صوت مفعل" if self.sound_on else "🔇 صوت mute")
        self.save_settings()

    def toggle_focus_mode(self):
        """تبديل وضع التركيز"""
        self.focus_mode = not self.focus_mode
        self.save_settings()
        self.btn_focus.config(text="🧘 وضع التركيز: ON" if self.focus_mode else "🧘 وضع التركيز: OFF",
                            bg=self.colors["success"] if self.focus_mode else self.colors["warning"])

    def play_sound(self, sound_type="bead"):
        """تشغيل الصوت"""
        if not self.sound_on or not SOUND_ENABLED:
            return
        if sound_type == "bead":
            threading.Thread(target=play_beep, args=(1200, 40), daemon=True).start()
        elif sound_type == "complete":
            def play_completion():
                play_beep(1500, 150)
                import time as _time
                _time.sleep(0.15)
                play_beep(2000, 200)
                _time.sleep(0.15)
                play_beep(2500, 300)
            threading.Thread(target=play_completion, daemon=True).start()

    def start_app(self, event=None):
        """بدء التسبيح"""
        try:
            val = self.entry_target.get().strip()
            self.target = int(val) if val else 100
            if self.target <= 0:
                raise ValueError("الهدف يجب أن يكون أكبر من صفر")

            self.total_x = 0
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.label_total.config(text="0")
            self.update_sub_counter()
            self.label_info.config(text=f"📿 متبقي: {self.target} تسبيحة")
            self.progress_bar["maximum"] = self.target
            self.progress_bar["value"] = 0
            self.reset_cycle_visuals()
            self.show_frame(self.tasbih_frame, "tasbih")
            self.session_start_time = time.time()
            self.save_settings()
        except ValueError:
            messagebox.showerror("خطأ", "يرجى إدخال رقم صحيح موجب")

    def on_zekr_change(self, event=None):
        """عند تغيير الذكر المختار"""
        self.update_sub_counter()

    def update_sub_counter(self):
        """تحديث العداد الجزئي للذكر المختار"""
        selected = self.zekr_combo.get()
        if selected in self.azkar_data:
            count = self.azkar_data[selected]["count"]
            self.label_sub_count.config(text=f"📊 تكرار هذا الذكر: {count}")

    def show_hadith_popup(self):
        """عرض نافذة الحديث للذكر المختار"""
        selected = self.zekr_combo.get()
        if selected in self.azkar_data:
            self.show_hadith_popup_for_zekr(selected, self.azkar_data[selected])

    def show_hadith_popup_for_zekr(self, zekr_name, data):
        """عرض نافذة الحديث المنبثقة"""
        win = tk.Toplevel(self.root)
        win.title(f"حديث: {zekr_name[:40]}...")
        win.geometry("750x650")
        win.configure(bg=self.get_bg())
        win.transient(self.root)
        win.grab_set()

        # العنوان
        title_frame = tk.Frame(win, bg=self.colors["primary"], height=60)
        title_frame.pack(fill="x", pady=(0, 15))
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📜 الحديث النبوي الشريف",
                font=("Segoe UI", 18, "bold"), bg=self.colors["primary"],
                fg="white").pack(expand=True)

        # اسم الذكر
        tk.Label(win, text=zekr_name, font=("Segoe UI", 14, "bold"),
                bg=self.get_bg(), fg=self.colors["gold"]).pack(pady=8, padx=20)

        # نص الحديث
        text_frame = tk.Frame(win, bg=self.get_card_bg(), highlightbackground="#0f3460",
                             highlightthickness=1, padx=15, pady=15)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        hadith_text = tk.Text(text_frame, font=("Segoe UI", 14), wrap="word",
                             bg=self.get_card_bg(), fg=self.get_fg(),
                             padx=15, pady=15, relief="flat", spacing2=6,
                             height=1)
        hadith_text.pack(fill="both", expand=True)
        hadith_text.tag_configure("right", justify="right")
        hadith_text.insert("1.0", data.get("hadith", "-"))
        hadith_text.tag_add("right", "1.0", "end")
        hadith_text.config(state="disabled")

        # الفضل
        if data.get("fadl"):
            tk.Label(win, text=f"✨ الفضل: {data['fadl']}",
                    font=("Segoe UI", 12, "bold"), bg=self.get_bg(),
                    fg=self.colors["success"]).pack(pady=5, padx=20)

        # المعلومات
        info_frame = tk.Frame(win, bg=self.get_bg())
        info_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(info_frame, text=f"⭐ الدرجة: {data.get('grade', '-')}",
                font=("Segoe UI", 11, "bold"), bg=self.get_bg(),
                fg=self.colors["success"]).pack(side="right", padx=10)
        tk.Label(info_frame, text=f"📚 المصدر: {data.get('source', '-')}",
                font=("Segoe UI", 11, "bold"), bg=self.get_bg(),
                fg=self.colors["info"]).pack(side="right", padx=10)

        # الأزرار
        btn_frame = tk.Frame(win, bg=self.get_bg())
        btn_frame.pack(fill="x", padx=20, pady=15)
        tk.Button(btn_frame, text="📋 نسخ الحديث", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["info"], fg="white", bd=0, padx=20, pady=8,
                 command=lambda: self.copy_hadith(data.get("hadith", ""), zekr_name,
                                                 data.get("grade", ""), data.get("source", ""),
                                                 data.get("fadl", "")),
                 cursor="hand2").pack(side="right", padx=10)
        tk.Button(btn_frame, text="إغلاق", font=("Segoe UI", 11, "bold"),
                 bg=self.colors["primary"], fg="white", bd=0, padx=20, pady=8,
                 command=win.destroy, cursor="hand2").pack(side="right", padx=10)

    def copy_hadith(self, hadith, zekr, grade, source, fadl=""):
        """نسخ الحديث للحافظة"""
        text = f"📿 الذكر: {zekr}\n\n📜 الحديث: {hadith}"
        if fadl:
            text += f"\n\n✨ الفضل: {fadl}"
        text += f"\n\n⭐ الدرجة: {grade}\n📚 المصدر: {source}"
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("تم النسخ", "✅ تم نسخ الحديث إلى الحافظة")

    def quick_tasbih(self, zekr_name):
        """الانتقال السريع للتسبيح بذكر معين"""
        self.zekr_combo.set(zekr_name)
        self.notebook.select(0)
        self.show_frame(self.tasbih_frame, "tasbih")
        self.update_sub_counter()

    def show_welcome(self):
        """رسالة ترحيبية"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_total = self.stats['daily'].get(today, {}).get('total', 0)
        if today_total == 0:
            # أول مرة اليوم - عرض رسالة تحفيزية
            streak = self.stats.get('streak_days', 0)
            if streak > 1:
                messagebox.showinfo("بسم الله", f"🌟 أهلاً بك!\n\nسلسلة التسبيح المتتالية: {streak} أيام\n\nبارك الله فيك وأكثر من حسناتك.")

    # ===================== دوال التسبيح الأساسية =====================
    def get_count_in_cycle(self):
        """حساب عدد التسابيح في الدورة الحالية (1-33)"""
        if self.total_x <= 0:
            return 0
        return ((self.total_x - 1) % 33) + 1

    def count_up(self, event=None):
        """زيادة العداد"""
        now = time.time() * 1000
        if now - self.last_click_time < self.debounce_ms:
            return
        self.last_click_time = now

        # التحقق من الشاشة الحالية
        if self.current_screen != "tasbih":
            return

        # في وضع التركيز، نمنع الضوضاء
        if self.focus_mode and self._animation_in_progress:
            return

        self.total_x += 1

        # حفظ في undo stack
        self.undo_stack.append({
            'total': self.total_x,
            'zekr': self.zekr_combo.get()
        })
        self.redo_stack.clear()

        # تحديث العرض
        self.label_total.config(text=str(self.total_x))
        self.progress_bar["value"] = min(self.total_x, self.target)

        # تحديث الذكر المختار
        selected = self.zekr_combo.get()
        if selected in self.azkar_data:
            self.azkar_data[selected]["count"] += 1

        self.update_today_stats(selected)
        self.update_sub_counter()

        # حساب موضع الخرزة
        current_index = (self.total_x - 1) % 33
        count_in_cycle = self.get_count_in_cycle()

        self.anim_canvas.itemconfig(self.cycle_text, text=f"{count_in_cycle} / 33")

        # إعادة تعيين الدورة عند الاكتمال
        if count_in_cycle == 1 and self.total_x > 1:
            self.reset_cycle_visuals_partial()

        # تحريك الخرزة
        self.animate_bead(current_index)

        # تحديث قوس التقدم
        self.update_circular_progress(count_in_cycle)

        # تأثير الزر
        self.btn_tasbih.config(bg="#c0392b")
        self.root.after(100, lambda: self.btn_tasbih.config(bg=self.colors["primary"]))

        # التحقق من اكتمال الهدف
        if self.total_x >= self.target:
            self.play_sound("complete")
            self.label_info.config(text="🎉 مبروك! أكملت هدفك!")
            # حساب وقت الجلسة
            session_time = ""
            if self.session_start_time:
                elapsed = time.time() - self.session_start_time
                mins = int(elapsed // 60)
                secs = int(elapsed % 60)
                session_time = f"\n⏱️ وقت الجلسة: {mins} دقيقة و {secs} ثانية"
            
            self.root.after(500, lambda: messagebox.showinfo("تم بحمد الله",
                f"🎉 أكملت {self.target} تسبيحة بنجاح!{session_time}\n\nبارك الله فيك وزادك من فضله."))
            self.root.after(200, self.reset_counter)
        else:
            remaining = self.target - self.total_x
            self.label_info.config(text=f"📿 متبقي: {remaining} تسبيحة")

    def undo_last(self):
        """تراجع عن آخر تسبيحة"""
        if not self.undo_stack:
            return

        last_action = self.undo_stack.pop()
        self.redo_stack.append(last_action)

        self.total_x = max(0, self.total_x - 1)
        self.label_total.config(text=str(self.total_x))
        self.progress_bar["value"] = min(self.total_x, self.target)

        # تراجع عن إحصائيات الذكر
        zekr = last_action['zekr']
        if zekr in self.azkar_data and self.azkar_data[zekr]["count"] > 0:
            self.azkar_data[zekr]["count"] -= 1

        # تحديث الإحصائيات
        today = datetime.now().strftime("%Y-%m-%d")
        if today in self.stats['daily'] and self.stats['daily'][today]['total'] > 0:
            self.stats['daily'][today]['total'] -= 1
            if zekr in self.stats['daily'][today]['azkar']:
                self.stats['daily'][today]['azkar'][zekr] -= 1
                if self.stats['daily'][today]['azkar'][zekr] <= 0:
                    del self.stats['daily'][today]['azkar'][zekr]
            if self.stats['total_ever'] > 0:
                self.stats['total_ever'] -= 1

        self.save_stats()
        self.update_stats_display()
        self.update_sub_counter()

        # تحديث الخرز
        count_in_cycle = self.get_count_in_cycle()
        self.anim_canvas.itemconfig(self.cycle_text, text=f"{count_in_cycle} / 33")
        self.update_circular_progress(count_in_cycle)
        
        # إعادة تعيين الخرز السابقة
        if self.total_x > 0:
            prev_index = (self.total_x - 1) % 33
            bx, by = self.bead_centers[prev_index]
            self.anim_canvas.itemconfig(self.beads_main[prev_index], fill=self.colors["success"],
                                       outline="#27ae60", width=1)
            self.anim_canvas.coords(self.beads_main[prev_index], bx-7, by-7, bx+7, by+7)
            self.anim_canvas.coords(self.beads_shadow[prev_index], bx-9, by-9, bx+9, by+9)

        remaining = self.target - self.total_x
        self.label_info.config(text=f"📿 متبقي: {remaining} تسبيحة (تراجع)")

    def redo_last(self):
        """إعادة التسبيحة المتراجعة"""
        if not self.redo_stack:
            return
        action = self.redo_stack.pop()
        
        # إعادة دقيقة - نضيف واحدة ونحسب الإحصائيات
        self.total_x += 1
        
        self.label_total.config(text=str(self.total_x))
        self.progress_bar["value"] = min(self.total_x, self.target)
        
        zekr = action['zekr']
        if zekr in self.azkar_data:
            self.azkar_data[zekr]["count"] += 1
        
        self.update_today_stats(zekr)
        self.update_sub_counter()
        
        # تحديث الخرز
        current_index = (self.total_x - 1) % 33
        count_in_cycle = self.get_count_in_cycle()
        
        self.anim_canvas.itemconfig(self.cycle_text, text=f"{count_in_cycle} / 33")
        
        if count_in_cycle == 1 and self.total_x > 1:
            self.reset_cycle_visuals_partial()
        
        self.animate_bead(current_index)
        self.update_circular_progress(count_in_cycle)
        
        remaining = self.target - self.total_x
        self.label_info.config(text=f"📿 متبقي: {remaining} تسبيحة (إعادة)")

    def animate_bead(self, index, step=0):
        """تحريك الخرزة بتأثير بصري"""
        if index >= len(self.bead_centers):
            return
        
        self._animation_in_progress = True
        bx, by = self.bead_centers[index]

        if step == 0:
            # تكبير الخرزة وتغيير لونها
            self.anim_canvas.itemconfig(self.beads_main[index],
                                       fill=self.colors["gold"],
                                       outline=self.colors["primary"], width=2)
            self.anim_canvas.coords(self.beads_main[index], bx-10, by-10, bx+10, by+10)
            self.anim_canvas.coords(self.beads_shadow[index], bx-12, by-12, bx+12, by+12)
            self.play_sound("bead")
            self.root.after(80, lambda: self.animate_bead(index, 1))
        else:
            # إرجاع الحجم الطبيعي مع لون مضيء
            self.anim_canvas.itemconfig(self.beads_main[index],
                                       fill=self.colors["success"],
                                       outline="#27ae60", width=1)
            self.anim_canvas.coords(self.beads_main[index], bx-7, by-7, bx+7, by+7)
            self.anim_canvas.coords(self.beads_shadow[index], bx-9, by-9, bx+9, by+9)

            # وميض سريع
            flash = self.anim_canvas.create_oval(bx-3, by-3, bx+3, by+3,
                                                fill="white", outline="")
            self.root.after(100, lambda: self.anim_canvas.delete(flash))
            self._animation_in_progress = False

    def update_circular_progress(self, count_in_cycle):
        """تحديث قوس التقدم الدائري - تم تعطيله لإخفاء الخط"""
        # جعلنا القوس دائماً صفر وغير مرئي
        extent = 0
        self.anim_canvas.itemconfig(self.progress_arc, extent=0, outline="")

    def reset_cycle_visuals(self):
        """إعادة تعيين جميع الخرز"""
        for i, (bx, by) in enumerate(self.bead_centers):
            self.anim_canvas.itemconfig(self.beads_main[i], fill="#34495e",
                                       outline="#2c3e50", width=1)
            self.anim_canvas.coords(self.beads_main[i], bx-7, by-7, bx+7, by+7)
            shadow_color = "#1a1a3e" if self.dark_mode else "#d5dbdb"
            self.anim_canvas.itemconfig(self.beads_shadow[i], fill=shadow_color)
            self.anim_canvas.coords(self.beads_shadow[i], bx-9, by-9, bx+9, by+9)

        self.anim_canvas.itemconfig(self.progress_arc, extent=0, outline="")
        self.anim_canvas.itemconfig(self.progress_arc, extent=0)

    def reset_cycle_visuals_partial(self):
        """إعادة تعيين الخرز بدون مسح القوس بالكامل - للدورات الجديدة"""
        for i, (bx, by) in enumerate(self.bead_centers):
            self.anim_canvas.itemconfig(self.beads_main[i], fill="#34495e",
                                       outline="#2c3e50", width=1)
            self.anim_canvas.coords(self.beads_main[i], bx-7, by-7, bx+7, by+7)
            shadow_color = "#1a1a3e" if self.dark_mode else "#d5dbdb"
            self.anim_canvas.itemconfig(self.beads_shadow[i], fill=shadow_color)
            self.anim_canvas.coords(self.beads_shadow[i], bx-9, by-9, bx+9, by+9)

    def reset_counter(self):
        """تصفير العداد - لا يصفّر الإحصائيات التراكمية"""
        self.total_x = 0
        self.undo_stack.clear()
        self.redo_stack.clear()
        # ملاحظة: لا نصفّر azkar_data counts لأنها إحصائيات تراكمية
        self.label_total.config(text="0")
        self.update_sub_counter()
        self.label_info.config(text=f"📿 متبقي: {self.target} تسبيحة")
        self.progress_bar["value"] = 0
        self.session_start_time = time.time()
        self.reset_cycle_visuals()

    def go_back(self):
        """العودة لشاشة البداية"""
        self.show_frame(self.start_frame, "start")
        self.update_stats_display()
        self.draw_chart()

    def show_frame(self, frame, screen_name):
        """عرض شاشة معينة"""
        self.current_screen = screen_name
        frame.tkraise()
        self.root.focus_set()

    def bind_events(self):
        """ربط اختصارات لوحة المفاتيح"""
        self.entry_target.bind('<Return>', self.start_app)
        self.root.bind('<Return>', self.count_up)
        self.root.bind('<KeyRelease-Return>', self.reset_press)
        self.root.bind('<BackSpace>', lambda e: self.undo_last())
        self.root.bind('<Control-z>', lambda e: self.undo_last())
        self.root.bind('<Control-y>', lambda e: self.redo_last())
        self.root.bind('<Escape>', lambda e: self.reset_counter() if self.current_screen == "tasbih" else None)

    def reset_press(self, event):
        """إعادة تعيين حالة الضغط"""
        self.is_pressed = False

# ========================== تشغيل التطبيق ==========================
if __name__ == "__main__":
    root = tk.Tk()

    # محاولة تفعيل DPI awareness على Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass

    app = SmartTasbihApp(root)
    root.mainloop()
