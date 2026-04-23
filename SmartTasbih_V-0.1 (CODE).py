import tkinter as tk
from tkinter import messagebox, ttk, font
import math
import json
import os
from datetime import datetime, timedelta
import time

# محاولة إضافة الصوت (لنظام Windows فقط)
try:
    import winsound
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False

# ========================== كلاس التطبيق الرئيسي ==========================
class SmartTasbihApp:
    def __init__(self, root):
        self.root = root
        self.root.title("السبحة الذكية - الأحاديث النبوية")
        self.root.geometry("900x1050") 
        self.root.minsize(750, 900)
        self.root.configure(bg="#f4f7f6")
        
        # متغيرات الحالة
        self.total_x = 0
        self.target = 100
        self.is_pressed = False
        self.current_screen = "start"
        self.dark_mode = False
        self.sound_on = True
        self.last_click_time = 0
        self.debounce_ms = 100
        
        # تحميل الإعدادات والإحصائيات
        self.stats_file = "azkar_stats.json"
        self.settings_file = "settings.json"
        self.load_settings()
        self.load_stats()
        
        # بيانات الأذكار مع الأحاديث الكاملة
        self.azkar_data = {
            "لا إله إلا الله وخده لا شريك له له الملك وله الحمد وهو على كل شيئ قدير": {
                "hadith": "حديث أبي هريرة رضي الله عنه أن النبي صلى الله عليه وسلم قال: من قال لا إله إلا الله وحده لا شريك له له الملك وله الحمد وهو على كل شيء قدير في يوم مائة مرة كانت له عدل عشر رقاب، وكتبت له مائة حسنة، ومحيت عنه مائة سيئة، وكانت له حرزاً من الشيطان يومه ذلك حتى يمسي، ولم يأت أحد بأفضل مما جاء به إلا أحد عمل أكثر من ذلك.» (رواه البخاري ومسلم).",
                "count": 0,
                "grade": "صحيح",
                "source": "البخاري ومسلم"
            },
            "سبحان الله وبحمده، سبحان الله العظيم": {
                "hadith": "عن أبي هريرة ـ رضي الله عنه ـ قال: قال النبي صلى الله عليه وسلم: كلمتان حبيبتان إلى الرحمن، خفيفتان على اللسان، ثقيلتان في الميزان: سبحان الله وبحمده، سبحان الله العظيم. (رواه البخاري ومسلم).",
                "count": 0,
                "grade": "صحيح",
                "source": "البخاري ومسلم"
            },
        }
        self.azkar_list = list(self.azkar_data.keys())
        
        # بناء الواجهة
        self.setup_ui()
        self.apply_theme()
        self.update_stats_display()
        
        # ربط الأحداث
        self.bind_events()
        
        # بدء التشغيل
        self.show_frame(self.start_frame, "start")
    
    # --------------------- دوال الإعدادات والإحصائيات ---------------------
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.dark_mode = settings.get('dark_mode', False)
                    self.sound_on = settings.get('sound_on', True)
                    self.target = settings.get('target', 100)
            except:
                pass
    
    def save_settings(self):
        settings = {
            'dark_mode': self.dark_mode,
            'sound_on': self.sound_on,
            'target': self.target
        }
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    
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
            'last_reset': datetime.now().strftime("%Y-%m-%d")
        }
    
    def save_stats(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def update_today_stats(self, zekr_name):
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.stats['daily']:
            self.stats['daily'][today] = {'total': 0, 'azkar': {}}
        self.stats['daily'][today]['total'] += 1
        self.stats['daily'][today]['azkar'][zekr_name] = self.stats['daily'][today]['azkar'].get(zekr_name, 0) + 1
        self.stats['total_ever'] += 1
        self.save_stats()
        self.update_stats_display()
    
    def update_stats_display(self):
        today = datetime.now().strftime("%Y-%m-%d")
        today_total = self.stats['daily'].get(today, {}).get('total', 0)
        self.label_today_total.config(text=f"اليوم: {today_total} تسبيحة")
        self.label_total_ever.config(text=f"الإجمالي: {self.stats['total_ever']}")
        
        last_7 = []
        for i in range(7):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            last_7.append(self.stats['daily'].get(d, {}).get('total', 0))
        self.label_last_7.config(text=f"آخر 7 أيام: {sum(last_7)}")
    
    # --------------------- بناء الواجهة ---------------------
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        self.tab_main = tk.Frame(self.notebook, bg="#f4f7f6")
        self.notebook.add(self.tab_main, text="📿 التسبيح")
        self.tab_main.grid_rowconfigure(0, weight=1)
        self.tab_main.grid_columnconfigure(0, weight=1)
        
        self.tab_hadith = tk.Frame(self.notebook, bg="#f4f7f6")
        self.notebook.add(self.tab_hadith, text="📖 الأحاديث النبوية")
        self.setup_hadith_tab()
        
        self.tab_stats = tk.Frame(self.notebook, bg="#f4f7f6")
        self.notebook.add(self.tab_stats, text="📊 الإحصائيات")
        self.setup_stats_tab()
        
        # --- شاشة البداية ---
        self.start_frame = tk.Frame(self.tab_main, bg="#f4f7f6")
        self.start_frame.grid(row=0, column=0, sticky="nsew")
        
        tk.Label(self.start_frame, text="🕌", font=("Tahoma", 90), bg="#f4f7f6", fg="#2ecc71").pack(pady=(50, 10))
        tk.Label(self.start_frame, text="السبحة الذكية", font=("Tahoma", 32, "bold"), bg="#f4f7f6", fg="#2c3e50").pack(pady=5)
        tk.Label(self.start_frame, text="تتبع تسبيحك مع الأحاديث النبوية الصحيحة", font=("Tahoma", 12), bg="#f4f7f6", fg="#7f8c8d").pack(pady=(0, 20))
        
        quick_frame = tk.Frame(self.start_frame, bg="#f4f7f6")
        quick_frame.pack(pady=10)
        for val in [100, 500, 1000, 5000]:
            btn = tk.Button(quick_frame, text=str(val), font=("Tahoma", 10, "bold"),
                           bg="#ecf0f1", fg="#2c3e50", bd=0, padx=12, pady=4,
                           command=lambda v=val: self.set_quick_target(v))
            btn.pack(side="left", padx=5)
        
        input_container = tk.Frame(self.start_frame, bg="white", highlightbackground="#bdc3c7", highlightthickness=1)
        input_container.pack(pady=20, padx=40, ipadx=10, ipady=5)
        tk.Label(input_container, text="الهدف الكلي:", font=("Tahoma", 12), bg="white", fg="#34495e").pack(side="right", padx=10)
        self.entry_target = tk.Entry(input_container, font=("Tahoma", 20, "bold"), justify="center", bd=0, bg="white", width=6)
        self.entry_target.insert(0, str(self.target))
        self.entry_target.pack(side="right", padx=10, pady=5)
        
        settings_frame = tk.Frame(self.start_frame, bg="#f4f7f6")
        settings_frame.pack(pady=10)
        self.btn_theme = tk.Button(settings_frame, text="🌙 وضع داكن", font=("Tahoma", 10, "bold"),
                                  bg="#34495e", fg="white", bd=0, padx=10, pady=4,
                                  command=self.toggle_theme)
        self.btn_theme.pack(side="left", padx=5)
        self.btn_sound = tk.Button(settings_frame, text="🔊 صوت", font=("Tahoma", 10, "bold"),
                                  bg="#34495e", fg="white", bd=0, padx=10, pady=4,
                                  command=self.toggle_sound)
        self.btn_sound.pack(side="left", padx=5)
        
        self.btn_start = tk.Button(self.start_frame, text="✨ ابدأ التسبيح ✨", font=("Tahoma", 16, "bold"),
                                  bg="#2ecc71", fg="white", bd=0, padx=20, pady=10,
                                  command=self.start_app, activebackground="#27ae60")
        self.btn_start.pack(pady=20)
        
        # --- شاشة التسبيح الرئيسية ---
        self.tasbih_frame = tk.Frame(self.tab_main, bg="#f4f7f6")
        self.tasbih_frame.grid(row=0, column=0, sticky="nsew")
        
        zekr_control = tk.Frame(self.tasbih_frame, bg="#f4f7f6")
        zekr_control.pack(pady=(20, 5), fill="x", padx=20)
        self.zekr_combo = ttk.Combobox(zekr_control, values=self.azkar_list, state="readonly",
                                      font=("Tahoma", 12), justify="center", width=30)
        self.zekr_combo.set(self.azkar_list[0])
        self.zekr_combo.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.btn_hadith = tk.Button(zekr_control, text="📖 الحديث", font=("Tahoma", 10, "bold"),
                                   bg="#3498db", fg="white", bd=0, padx=8, pady=4,
                                   command=self.show_hadith_popup)
        self.btn_hadith.pack(side="right")
        
        self.label_sub_count = tk.Label(self.tasbih_frame, text="📖 تكرار هذا الذكر: 0",
                                       font=("Tahoma", 12, "bold"), bg="#f4f7f6", fg="#e67e22")
        self.label_sub_count.pack()
        
        self.setup_bead_canvas()
        
        self.counter_frame = tk.Frame(self.tasbih_frame, bg="white", highlightbackground="#2ecc71", highlightthickness=2)
        self.counter_frame.pack(pady=10)
        self.label_total = tk.Label(self.counter_frame, text="0", font=("Tahoma", 64, "bold"), bg="white", fg="#2ecc71", width=4)
        self.label_total.pack(padx=20, pady=10)
        
        self.progress_bar = ttk.Progressbar(self.tasbih_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(pady=5)
        
        self.label_info = tk.Label(self.tasbih_frame, text="", font=("Tahoma", 12), bg="#f4f7f6", fg="#7f8c8d")
        self.label_info.pack(pady=5)
        
        self.btn_tasbih = tk.Button(self.tasbih_frame, text="📿 سَبِّح (Enter) 📿", font=("Tahoma", 18, "bold"),
                                   bg="#2ecc71", fg="white", bd=0, padx=20, pady=12,
                                   command=self.count_up, activebackground="#27ae60")
        self.btn_tasbih.pack(pady=15)
        
        controls_frame = tk.Frame(self.tasbih_frame, bg="#f4f7f6")
        controls_frame.pack(pady=10)
        tk.Button(controls_frame, text="🔄 تصفير الكل", font=("Tahoma", 11, "bold"),
                 bg="#e67e22", fg="white", bd=0, padx=15, pady=5,
                 command=self.reset_counter).pack(side="left", padx=10)
        tk.Button(controls_frame, text="🔙 رجوع", font=("Tahoma", 11, "bold"),
                 bg="#95a5a6", fg="white", bd=0, padx=15, pady=5,
                 command=self.go_back).pack(side="left", padx=10)
    
    # ===================== شاشة الأحاديث (التصميم الرأسي المنظم) =====================
    def setup_hadith_tab(self):
        # --- الشريط العلوي (البحث وحجم الخط) ---
        top_frame = tk.Frame(self.tab_hadith, bg="#f4f7f6", pady=10)
        top_frame.pack(fill="x", padx=10)
        
        search_frame = tk.Frame(top_frame, bg="#f4f7f6")
        search_frame.pack(fill="x", pady=5)
        
        tk.Label(search_frame, text="🔍 بحث:", font=("Tahoma", 11, "bold"),
                bg="#f4f7f6", fg="#2c3e50").pack(side="right", padx=5)
        
        self.search_entry = tk.Entry(search_frame, font=("Tahoma", 12), width=35, bd=1, relief="solid")
        self.search_entry.pack(side="right", padx=5, ipady=3)
        self.search_entry.bind("<KeyRelease>", self.search_hadith)
        
        clear_btn = tk.Button(search_frame, text="✖ مسح", font=("Tahoma", 9),
                              bg="#e74c3c", fg="white", bd=0, padx=8, pady=2,
                              command=self.clear_search)
        clear_btn.pack(side="right", padx=2)
        
        font_frame = tk.Frame(top_frame, bg="#f4f7f6")
        font_frame.pack(fill="x", pady=5)
        
        tk.Label(font_frame, text="📏 حجم الخط:", font=("Tahoma", 10), bg="#f4f7f6", fg="#2c3e50").pack(side="right", padx=5)
        
        self.font_size = 16 
        self.btn_font_up = tk.Button(font_frame, text="▲ تكبير", font=("Tahoma", 9, "bold"), width=8,
                                     bg="#2ecc71", fg="white", bd=0, padx=5, pady=2,
                                     command=lambda: self.change_hadith_font(2))
        self.btn_font_up.pack(side="right", padx=2)
        
        self.btn_font_down = tk.Button(font_frame, text="▼ تصغير", font=("Tahoma", 9, "bold"), width=8,
                                       bg="#e67e22", fg="white", bd=0, padx=5, pady=2,
                                       command=lambda: self.change_hadith_font(-2))
        self.btn_font_down.pack(side="right", padx=2)

        self.status_label = tk.Label(top_frame, text=f"📚 عدد الأحاديث: {len(self.azkar_data)}",
                                     font=("Tahoma", 10, "bold"), bg="#f4f7f6", fg="#7f8c8d")
        self.status_label.pack(side="left")

        # --- منطقة التمرير للأحاديث (Scrollable Area) ---
        self.container_frame = tk.Frame(self.tab_hadith, bg="#f4f7f6")
        self.container_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(self.container_frame, bg="#f4f7f6", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f4f7f6")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_canvas(event):
            # تحديث عرض الإطار الداخلي ليتناسب مع الشاشة
            self.canvas.itemconfig(self.canvas_window, width=event.width)
            # تحديث التفاف النص (Wraplength) ليتناسب مع العرض الجديد
            if hasattr(self, 'hadith_labels'):
                wrap_width = event.width - 60 
                for lbl in self.hadith_labels:
                    lbl.config(wraplength=max(wrap_width, 300))

        self.canvas.bind("<Configure>", configure_canvas)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # ربط عجلة الماوس
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.hadith_labels = []
        self.populate_hadith_list()

    def populate_hadith_list(self, search_text=""):
        # مسح المحتوى القديم
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.hadith_labels.clear()

        # ألوان بناءً على الوضع الداكن والفاتح
        bg_color = "#2f3640" if self.dark_mode else "white"
        fg_color = "#ecf0f1" if self.dark_mode else "#2c3e50"
        text_fg = "#bdc3c7" if self.dark_mode else "#34495e"
        frame_bg = "#1e272e" if self.dark_mode else "#f4f7f6"

        self.scrollable_frame.config(bg=frame_bg)
        self.canvas.config(bg=frame_bg)

        count = 0
        for zekr, data in self.azkar_data.items():
            if search_text and search_text not in zekr and search_text not in data['hadith']:
                continue
            
            count += 1

            # إطار لكل حديث وذكر
            item_frame = tk.Frame(self.scrollable_frame, bg=bg_color, highlightbackground="#bdc3c7", highlightthickness=1, pady=15, padx=15)
            item_frame.pack(fill="x", pady=10, padx=10)

            # عنوان الذكر
            title_lbl = tk.Label(item_frame, text=zekr, font=("Tahoma", 15, "bold"), bg=bg_color, fg=fg_color, justify="right")
            title_lbl.pack(anchor="e", pady=(0, 10))
            self.hadith_labels.append(title_lbl)

            # نص الحديث
            hadith_lbl = tk.Label(item_frame, text=data['hadith'], font=("Tahoma", self.font_size), bg=bg_color, fg=text_fg, justify="right")
            hadith_lbl.pack(anchor="e", pady=(0, 10))
            self.hadith_labels.append(hadith_lbl)

            # إطار التفاصيل والنسخ
            info_frame = tk.Frame(item_frame, bg=bg_color)
            info_frame.pack(fill="x", pady=5)

            tk.Label(info_frame, text=f"⭐ الدرجة: {data.get('grade', 'حسن')}", font=("Tahoma", 11, "bold"), bg=bg_color, fg="#27ae60").pack(side="right", padx=10)
            tk.Label(info_frame, text=f"📚 المصدر: {data.get('source', '-')}", font=("Tahoma", 11, "bold"), bg=bg_color, fg="#3498db").pack(side="right", padx=10)

            copy_btn = tk.Button(info_frame, text="📋 نسخ", font=("Tahoma", 10, "bold"),
                                 bg="#3498db", fg="white", bd=0, padx=15, pady=5,
                                 command=lambda h=data['hadith'], z=zekr, g=data.get('grade', ''), s=data.get('source', ''): self.copy_hadith_to_clipboard(h, z, g, s))
            copy_btn.pack(side="left", padx=5)

        if search_text:
            self.status_label.config(text=f"🔍 نتائج البحث: {count} حديث")
        else:
            self.status_label.config(text=f"📚 عدد الأحاديث: {count}")

        # تحديث حجم التفاف النص فوراً
        self.root.update_idletasks()
        wrap_width = self.canvas.winfo_width() - 60
        if wrap_width > 0:
            for lbl in self.hadith_labels:
                lbl.config(wraplength=wrap_width)

    def search_hadith(self, event=None):
        search_text = self.search_entry.get().strip()
        self.populate_hadith_list(search_text)
    
    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.populate_hadith_list()
    
    def change_hadith_font(self, delta):
        self.font_size += delta
        self.font_size = max(12, min(28, self.font_size))
        # إعادة رسم الأحاديث لتطبيق الحجم الجديد
        self.populate_hadith_list(self.search_entry.get().strip())
    
    # ===================== شاشة قراءة الحديث المنبثقة (تصميم صارم) =====================
    def show_hadith_popup_for_zekr(self, zekr_name, data):
        hadith = data["hadith"]
        grade = data.get('grade', 'حسن')
        source = data.get('source', '-')
        
        win = tk.Toplevel(self.root)
        win.title(f"حديث: {zekr_name[:40]}...")
        win.geometry("700x600")
        win.configure(bg="#f4f7f6")
        win.transient(self.root)
        win.grab_set()
        
        main_frame = tk.Frame(win, bg="#f4f7f6")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_frame, bg="#2ecc71", height=60)
        title_frame.pack(fill="x", pady=(0, 15))
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📜 الحديث النبوي الشريف", font=("Tahoma", 18, "bold"),
                bg="#2ecc71", fg="white").pack(expand=True)
        
        tk.Label(main_frame, text=zekr_name, font=("Tahoma", 14, "italic"),
                bg="#f4f7f6", fg="#e67e22").pack(pady=5)
        
        # استخدام Grid هنا لضمان عدم خروج النص عن الشاشة المنبثقة
        text_frame = tk.Frame(main_frame, bg="white", highlightbackground="#bdc3c7", highlightthickness=1)
        text_frame.pack(fill="both", expand=True, pady=10)
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(1, weight=1)
        
        text_scroll = tk.Scrollbar(text_frame)
        text_scroll.grid(row=0, column=0, sticky="ns")
        
        hadith_text = tk.Text(text_frame, font=("Tahoma", 16), wrap="word",
                             bg="white", fg="#2c3e50", yscrollcommand=text_scroll.set,
                             padx=20, pady=20, relief="flat", spacing2=8,
                             width=1, height=1) # ضروري لمنع التمدد الخاطئ
        hadith_text.grid(row=0, column=1, sticky="nsew")
        text_scroll.config(command=hadith_text.yview)
        
        hadith_text.tag_configure("right_align", justify="right")
        hadith_text.insert("1.0", hadith)
        hadith_text.tag_add("right_align", "1.0", "end")
        hadith_text.config(state="disabled")
        
        info_frame = tk.Frame(main_frame, bg="#f4f7f6")
        info_frame.pack(fill="x", pady=5)
        tk.Label(info_frame, text=f"⭐ الدرجة: {grade}", font=("Tahoma", 11, "bold"),
                bg="#f4f7f6", fg="#27ae60").pack(side="right", padx=15)
        tk.Label(info_frame, text=f"📚 المصدر: {source}", font=("Tahoma", 11, "bold"),
                bg="#f4f7f6", fg="#3498db").pack(side="right", padx=15)
        
        btn_frame = tk.Frame(main_frame, bg="#f4f7f6")
        btn_frame.pack(fill="x", pady=15)
        tk.Button(btn_frame, text="📋 نسخ الحديث", font=("Tahoma", 11, "bold"),
                 bg="#3498db", fg="white", bd=0, padx=20, pady=8,
                 command=lambda: self.copy_hadith_to_clipboard(hadith, zekr_name, grade, source)).pack(side="right", padx=10)
        tk.Button(btn_frame, text="إغلاق", font=("Tahoma", 11, "bold"),
                 bg="#e74c3c", fg="white", bd=0, padx=20, pady=8,
                 command=win.destroy).pack(side="right", padx=10)

    # --------------------- باقي الدوال ---------------------
    def setup_stats_tab(self):
        self.stats_canvas = tk.Frame(self.tab_stats, bg="#f4f7f6")
        self.stats_canvas.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.label_today_total = tk.Label(self.stats_canvas, text="اليوم: 0", font=("Tahoma", 14, "bold"), bg="#f4f7f6", fg="#2c3e50")
        self.label_today_total.pack(pady=5)
        self.label_total_ever = tk.Label(self.stats_canvas, text="الإجمالي: 0", font=("Tahoma", 12), bg="#f4f7f6", fg="#7f8c8d")
        self.label_total_ever.pack()
        self.label_last_7 = tk.Label(self.stats_canvas, text="آخر 7 أيام: 0", font=("Tahoma", 12), bg="#f4f7f6", fg="#7f8c8d")
        self.label_last_7.pack(pady=5)
        
        tk.Button(self.stats_canvas, text="تصدير الإحصائيات", font=("Tahoma", 10),
                 bg="#2ecc71", fg="white", bd=0, padx=10, pady=5,
                 command=self.export_stats).pack(pady=10)
        tk.Button(self.stats_canvas, text="إعادة تعيين الإحصائيات", font=("Tahoma", 10),
                 bg="#e74c3c", fg="white", bd=0, padx=10, pady=5,
                 command=self.reset_stats).pack(pady=5)
    
    def setup_bead_canvas(self):
        self.anim_canvas = tk.Canvas(self.tasbih_frame, width=320, height=320, bg="#f4f7f6", highlightthickness=0)
        self.anim_canvas.pack(pady=10)
        
        self.beads_main = []
        self.beads_shadow = []
        self.bead_centers = []
        cx, cy = 160, 160
        r = 120
        
        for i in range(33):
            angle = -math.pi/2 + (i * 2 * math.pi / 33)
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            self.bead_centers.append((x, y))
            shadow = self.anim_canvas.create_oval(x-8, y-8, x+8, y+8, fill="#d5dbdb", outline="")
            bead = self.anim_canvas.create_oval(x-6, y-6, x+6, y+6, fill="#bdc3c7", outline="#95a5a6", width=1)
            self.beads_shadow.append(shadow)
            self.beads_main.append(bead)
        
        self.cycle_text = self.anim_canvas.create_text(cx, cy, text="0 / 33", font=("Tahoma", 22, "bold"), fill="#2c3e50")
        self.progress_arc = None
    
    # --------------------- الوظائف الأساسية ---------------------
    def set_quick_target(self, val):
        self.entry_target.delete(0, tk.END)
        self.entry_target.insert(0, str(val))
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.save_settings()
    
    def apply_theme(self):
        if self.dark_mode:
            bg_color = "#1e272e"
            entry_bg = "#2c3e50"
            self.btn_theme.config(text="☀️ وضع فاتح", bg="#f39c12")
        else:
            bg_color = "#f4f7f6"
            entry_bg = "white"
            self.btn_theme.config(text="🌙 وضع داكن", bg="#34495e")
        
        # تغيير خلفيات الإطارات الأساسية
        for frame in [self.root, self.start_frame, self.tasbih_frame, self.tab_main, self.tab_stats, self.stats_canvas, self.tab_hadith]:
            frame.config(bg=bg_color)
            
        for label in [self.label_sub_count, self.label_info]:
            label.config(bg=bg_color)
            
        self.anim_canvas.config(bg=bg_color)
        self.counter_frame.config(bg=entry_bg)
        self.label_total.config(bg=entry_bg)
        
        for shadow in self.beads_shadow:
            self.anim_canvas.itemconfig(shadow, fill="#2c3e50" if self.dark_mode else "#d5dbdb")

        # تحديث ألوان شاشة الأحاديث الجديدة
        if hasattr(self, 'populate_hadith_list'):
            if hasattr(self, 'status_label'):
                self.status_label.config(bg=bg_color)
            search_txt = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
            self.populate_hadith_list(search_txt)
    
    def toggle_sound(self):
        self.sound_on = not self.sound_on
        self.btn_sound.config(text="🔇 صوت" if not self.sound_on else "🔊 صوت")
        self.save_settings()
    
    def play_sound(self, sound_type="bead"):
        if not self.sound_on or not SOUND_ENABLED:
            return
        if sound_type == "bead":
            winsound.Beep(1200, 30)
        elif sound_type == "complete":
            winsound.Beep(2000, 200)
            winsound.Beep(2500, 200)
    
    def start_app(self, event=None):
        if self.notebook.index(self.notebook.select()) != 0:
            return
        try:
            val = self.entry_target.get()
            self.target = int(val) if val else 100
            if self.target <= 0:
                raise ValueError
            self.total_x = 0
            self.label_total.config(text="0")
            self.update_sub_counter()
            self.label_info.config(text=f"📿 متبقي لك {self.target} تسبيحة")
            self.progress_bar["maximum"] = self.target
            self.progress_bar["value"] = 0
            self.reset_cycle_visuals()
            self.show_frame(self.tasbih_frame, "tasbih")
        except ValueError:
            messagebox.showerror("خطأ", "برجاء إدخال رقم صحيح موجب")
    
    def update_sub_counter(self, event=None):
        selected = self.zekr_combo.get()
        current_count = self.azkar_data[selected]["count"]
        self.label_sub_count.config(text=f"📖 تكرار هذا الذكر: {current_count}")
    
    def show_hadith_popup(self):
        selected = self.zekr_combo.get()
        data = self.azkar_data[selected]
        self.show_hadith_popup_for_zekr(selected, data)
    
    def copy_hadith_to_clipboard(self, hadith, zekr, grade, source):
        text = f"📿 الذكر: {zekr}\n\n📜 الحديث: {hadith}\n\n⭐ الدرجة: {grade}\n📚 المصدر: {source}"
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("تم النسخ", "✅ تم نسخ الحديث إلى الحافظة")
    
    def animate_bead(self, index, step=0):
        bx, by = self.bead_centers[index]
        if step == 0:
            self.anim_canvas.itemconfig(self.beads_main[index], fill="#f1c40f", outline="#e67e22", width=2)
            self.anim_canvas.coords(self.beads_main[index], bx-9, by-9, bx+9, by+9)
            self.anim_canvas.coords(self.beads_shadow[index], bx-11, by-11, bx+11, by+11)
            self.play_sound("bead")
            self.root.after(70, lambda: self.animate_bead(index, 1))
        else:
            self.anim_canvas.itemconfig(self.beads_main[index], fill="#2ecc71", outline="#27ae60", width=1)
            self.anim_canvas.coords(self.beads_main[index], bx-6, by-6, bx+6, by+6)
            self.anim_canvas.coords(self.beads_shadow[index], bx-8, by-8, bx+8, by+8)
            highlight = self.anim_canvas.create_oval(bx-2, by-2, bx+2, by+2, fill="white", outline="")
            self.root.after(100, lambda: self.anim_canvas.delete(highlight))
    
    def reset_cycle_visuals(self):
        for i, (bx, by) in enumerate(self.bead_centers):
            self.anim_canvas.itemconfig(self.beads_main[i], fill="#bdc3c7", outline="#95a5a6", width=1)
            self.anim_canvas.coords(self.beads_main[i], bx-6, by-6, bx+6, by+6)
            self.anim_canvas.coords(self.beads_shadow[i], bx-8, by-8, bx+8, by+8)
        self.anim_canvas.itemconfig(self.cycle_text, text="0 / 33", fill="#2c3e50")
        self.reset_circular_progress()
    
    def reset_circular_progress(self):
        pass
    
    def update_circular_progress(self, count_in_cycle):
        pass
    
    def count_up(self, event=None):
        now = time.time() * 1000
        if now - self.last_click_time < self.debounce_ms:
            return
        self.last_click_time = now
        
        if self.notebook.index(self.notebook.select()) != 0 or self.current_screen != "tasbih":
            return
        if event and self.is_pressed:
            return
        if event:
            self.is_pressed = True
        
        self.total_x += 1
        self.label_total.config(text=str(self.total_x))
        self.progress_bar["value"] = self.total_x
        
        selected = self.zekr_combo.get()
        self.azkar_data[selected]["count"] += 1
        self.update_today_stats(selected)
        self.update_sub_counter()
        
        current_index = (self.total_x - 1) % 33
        count_in_cycle = self.total_x % 33
        if count_in_cycle == 0:
            count_in_cycle = 33
        
        self.anim_canvas.itemconfig(self.cycle_text, text=f"{count_in_cycle} / 33")
        self.update_circular_progress(count_in_cycle)
        
        if current_index == 0 and self.total_x > 1:
            for i in range(33):
                self.anim_canvas.itemconfig(self.beads_main[i], fill="#bdc3c7", outline="#95a5a6", width=1)
                self.anim_canvas.coords(self.beads_main[i], self.bead_centers[i][0]-6, self.bead_centers[i][1]-6,
                                       self.bead_centers[i][0]+6, self.bead_centers[i][1]+6)
                self.anim_canvas.coords(self.beads_shadow[i], self.bead_centers[i][0]-8, self.bead_centers[i][1]-8,
                                       self.bead_centers[i][0]+8, self.bead_centers[i][1]+8)
        
        self.animate_bead(current_index)
        
        self.btn_tasbih.config(relief="sunken", bg="#27ae60")
        self.root.after(100, lambda: self.btn_tasbih.config(relief="raised", bg="#2ecc71"))
        
        if self.total_x >= self.target:
            self.play_sound("complete")
            messagebox.showinfo("تم بحمد الله", f"🎉 أكملت {self.target} تسبيحة بنجاح!")
            self.reset_counter()
        else:
            remaining = self.target - self.total_x
            self.label_info.config(text=f"📿 متبقي لك {remaining} تسبيحة")
    
    def reset_counter(self):
        self.total_x = 0
        for z in self.azkar_data:
            self.azkar_data[z]["count"] = 0
        self.label_total.config(text="0")
        self.update_sub_counter()
        self.label_info.config(text=f"📿 متبقي لك {self.target} تسبيحة")
        self.progress_bar["value"] = 0
        self.reset_cycle_visuals()
    
    def go_back(self):
        self.show_frame(self.start_frame, "start")
    
    def show_frame(self, frame, screen_name):
        self.current_screen = screen_name
        frame.tkraise()
        self.root.focus_set()
    
    def export_stats(self):
        try:
            filename = f"stats_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("تم التصدير", f"✅ تم حفظ الإحصائيات في ملف {filename}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {e}")
    
    def reset_stats(self):
        if messagebox.askyesno("تأكيد", "⚠️ هل أنت متأكد من إعادة تعيين جميع الإحصائيات؟ لا يمكن التراجع."):
            self.stats = self.init_stats()
            self.save_stats()
            self.update_stats_display()
            messagebox.showinfo("تم", "✅ تم إعادة تعيين الإحصائيات")
    
    def bind_events(self):
        self.entry_target.bind('<Return>', self.start_app)
        self.root.bind('<Return>', self.count_up)
        self.root.bind('<KeyRelease-Return>', self.reset_press)
        self.zekr_combo.bind("<<ComboboxSelected>>", self.update_sub_counter)
    
    def reset_press(self, event):
        self.is_pressed = False

# ========================== تشغيل التطبيق ==========================
if __name__ == "__main__":
    root = tk.Tk()
    app = SmartTasbihApp(root)
    root.mainloop()