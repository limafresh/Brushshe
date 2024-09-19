from customtkinter import *
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkColorPicker import AskColor
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageDraw, ImageTk, ImageGrab
from tkinter import PhotoImage, font
import gc, os, uuid

class Brushshe(CTk):
    def __init__(self):
        super().__init__()
        self.title("Brushshe")
        self.geometry("650x580")
        self.minsize(650, 580)
        self.iconphoto(True, PhotoImage(file="icons/icon.png"))
        set_default_color_theme("brushshe_theme.json")
        set_appearance_mode("system")
        self.protocol("WM_DELETE_WINDOW", self.when_closing)

        ''' Інтерфейс '''
        menu = CTkMenuBar(self)   # Меню
        
        file_menu = menu.add_cascade("Файл")
        dropdown1 = CustomDropdownMenu(widget=file_menu)
        dropdown1.add_option(option="Відкрити з файлу", command=self.open_image)
        dropdown1.add_option(option="Експортувати на ПК", command=self.export)

        bg_menu = menu.add_cascade("Колір тла")
        dropdown3 = CustomDropdownMenu(widget=bg_menu)
        ukr_colors = {
            "Білий": "white",
            "Червоний": "red",
            "Яскраво-зелений": "#2eff00",
            "Синій": "blue",
            "Жовтий": "yellow",
            "Фіолетовий": "purple",
            "Блакитний": "cyan",
            "Рожевий": "pink",
            "Помаранчевий": "orange",
            "Коричневий": "brown",
            "Сірий": "gray",
            "Чорний": "black"
        }
        for ukr_name, color in ukr_colors.items():
            dropdown3.add_option(option=ukr_name, command=lambda c=color: self.change_bg(c))
        dropdown3.add_separator()
        dropdown3.add_option(option="Інший колір", command=self.other_bg_color)

        # ширина і висота всіх зображень стікерів - 88 px
        stickers_names = [
            "smile", "flower", "heart", "okay", "cheese", "face2", "cat", "alien", "like",
            "unicorn", "pineapple", "grass", "rain", "brucklin", "brushshe", "strawberry",
            "butterfly", "flower2"
        ]
        self.stickers = [Image.open(f"stickers/{name}.png") for name in stickers_names]
        
        add_menu = menu.add_cascade("Додати")
        dropdown4 = CustomDropdownMenu(widget=add_menu)
        smile_icon = CTkImage(light_image=Image.open("icons/smile.png"), size=(50, 50))
        dropdown4.add_option(option="Наліпки", image=smile_icon, command=self.show_stickers_choice)
        text_icon = CTkImage(light_image=Image.open("icons/text.png"), size=(50, 50))
        text_submenu = dropdown4.add_submenu("Текст", image=text_icon)
        text_submenu.add_option(option="Додати текст на малюнок", command=self.add_text_window_show)
        text_submenu.add_option(option="Налаштувати текст для вставлення", command=self.text_settings)
        frame_icon = CTkImage(light_image=Image.open("icons/frame.png"), size=(50, 50))
        dropdown4.add_option(option="Рамки", image=frame_icon, command=self.show_frame_choice)

        gallery_menu = menu.add_cascade("Моя галерея", command=self.show_gallery)

        other_menu = menu.add_cascade("Інше")
        dropdown6 = CustomDropdownMenu(widget=other_menu)
        dropdown6.add_option(option="Інфо", command=self.about_program)
        
        tools_frame = CTkFrame(self)   # Панель інструментів
        tools_frame.pack(side=TOP, fill=X)

        clean_btn = CTkButton(tools_frame, text="Очистити все", width=50, command=self.clean_all)
        clean_btn.pack(side=LEFT, padx=1)
        
        eraser_icon = CTkImage(light_image=Image.open("icons/eraser.png"), size=(20, 20))
        eraser = CTkButton(tools_frame, text=None, width=35, image=eraser_icon, command=self.eraser)
        eraser.pack(side=LEFT, padx=1)

        self.tool_label = CTkLabel(tools_frame, text="Пензль:")
        self.tool_label.pack(side=LEFT, padx=1)

        size_slider = CTkSlider(tools_frame, from_=1, to=50, command=self.change_brush_size)
        self.brush_size = 2
        size_slider.set(self.brush_size)
        size_slider.pack(side=LEFT, padx=5)

        self.brush_size_label = CTkLabel(tools_frame, text="2")
        self.brush_size_label.pack(side=LEFT, padx=1)

        self.theme_switch_var = StringVar(value="off")
        theme_switch = CTkSwitch(tools_frame, text="Темний", width=50, command=self.change_theme,
                                 variable=self.theme_switch_var, onvalue="on", offvalue="off")
        theme_switch.pack(side=RIGHT, padx=5)

        save_button = CTkButton(tools_frame, text="Зберегти в галерею", width=70, command=self.save_image)
        save_button.pack(side=RIGHT, padx=5)

        self.canvas = CTkCanvas(self, bg="white")   # Канва
        self.canvas.pack(fill=BOTH, expand=True)

        self.palette = CTkFrame(self)   # Палітра
        self.palette.pack(side=BOTTOM, fill=X)

        self.colors = [
            "black", "red", "#2eff00", "blue", "yellow", "purple",
            "cyan", "pink", "orange", "brown", "gray", "white"
            ]
        for color in self.colors:
            color_btn = CTkButton(self.palette, fg_color=color, text=None, width=35,
                                  border_width=2, command=lambda c=color: self.change_color(c))
            color_btn.pack(side=LEFT, padx=1)

        choice_other_color = CTkButton(self.palette, text="Інший", width=70, command=self.other_color_choise)
        choice_other_color.pack(side=RIGHT, padx=1)

        self.other_color_btn = CTkButton(self.palette, text=None, width=35,
                                         border_width=2, command=self.select_other_color_btn)

        ''' Ініціалізація '''
        self.color = "black"

        self.image = Image.new("RGB", (800, 600), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.photo = None

        self.prev_x = None
        self.prev_y = None

        self.font_size = 24
        self.tk_font = CTkFont(size=self.font_size)
        self.size_a = 100

        gc.disable() # бо ввімкнений gc думає що додані наліпки і текст - це сміття

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

    ''' Функціонал '''
    def when_closing(self):
        closing_msg = CTkMessagebox(title = "Ви покидаєте Brushshe", message = "Зберегти малюнок?",
                                    option_1="Ні", option_2="Повернутися щоб зберегти",
                                    icon="icons/question.png", icon_size=(100,100), sound=True)
        response = closing_msg.get()
        if response == "Ні":
            app.destroy()
        else:
            pass

    def paint(self, cur):
        if self.prev_x and self.prev_y:
            self.canvas.create_line(self.prev_x, self.prev_y, cur.x, cur.y, width=self.brush_size, fill=self.color,
                               smooth=True, capstyle=ROUND)
        self.prev_x, self.prev_y = cur.x, cur.y

    def stop_paint(self, cur):
        self.prev_x, self.prev_y = (None, None)

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Зображення", "*.png;*.jpg;*.jpeg;*.gif"), ("Всі файли", "*.*")])
        if file_path:
            try:
                image = Image.open(file_path)
                self.image = image
                self.draw = ImageDraw.Draw(self.image)
                self.canvas.delete("all")
                self.canvas.configure(bg="white")
                self.photo = ImageTk.PhotoImage(self.image)
                self.canvas.create_image(0, 0, anchor=NW, image=self.photo)
            except Exception as e:
                open_error_msg = CTkMessagebox(title = "Ех, на жаль, це сталося",
                                               message = f"Помилка - неможливо відкрити файл: {e}",
                                               icon="icons/cry.png", icon_size=(100,100), sound=True)

    def export(self):
        # позиції канви
        x0 = self.canvas.winfo_rootx()
        y0 = self.canvas.winfo_rooty()
        x1 = x0 + self.canvas.winfo_width()
        y1 = y0 + self.canvas.winfo_height()

        # вміст канви
        canvas_img = ImageGrab.grab(bbox=(x0, y0, x1, y1))

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG файли", "*.png"), ("Всі файли", "*.*")])
        if file_path:
            canvas_img.save(file_path)

    def change_bg(self, new_color):
        self.canvas.configure(bg=new_color)
        if self.tool_label.cget('text') == "Ластик:":
            self.eraser()

    def other_bg_color(self):
        pick_color = AskColor(title="Оберіть інший колір тла")
        bg_getcolor = pick_color.get()
        if bg_getcolor:
            self.canvas.configure(bg=bg_getcolor)
        
    def show_stickers_choice(self):
        def update_btn():
            for widget in stickers_frame.winfo_children():
                widget.destroy()
            row = 0
            column = 0
            for image in self.stickers:
                resized_image = image.resize((self.size_a, self.size_a))
                image = ImageTk.PhotoImage(resized_image)
                sticker_btn = CTkButton(stickers_frame, text=None, image=image, command=lambda img=image: self.set_current_sticker(img))
                sticker_btn.grid(row=row, column=column, padx=10, pady=10)
                column += 1
                if column == 2:
                    column = 0
                    row +=1
                    
        sticker_choose = CTkToplevel(app)
        sticker_choose.geometry("320x420")
        sticker_choose.title("Оберіть наліпку")
                
        tabview = CTkTabview(sticker_choose, command=update_btn)
        tabview.add("Обрати наліпку")
        tabview.add("Розмір наліпок")
        tabview.set("Обрати наліпку")
        tabview.pack()

        stickers_frame = CTkScrollableFrame(tabview.tab("Обрати наліпку"), width=300, height=400)
        stickers_frame.pack()

        self.st_size_label = CTkLabel(tabview.tab("Розмір наліпок"), text=self.size_a)
        self.st_size_label.pack()
        self.st_slider = CTkSlider(tabview.tab("Розмір наліпок"), from_=10, to=175, command=self.change_sticker_size)
        self.st_slider.set(self.size_a)
        self.st_slider.pack()
        set_default = CTkButton(tabview.tab("Розмір наліпок"), text="Повернути як було", command=self.set_default_stickers_size)
        set_default.pack()

        update_btn()

    def set_current_sticker(self, image): # Обрати наліпку
        self.current_sticker = image
        if self.current_sticker:
            self.canvas.bind("<Button-1>", self.add_sticker)

    def add_sticker(self, event): # Додати наліпку
        self.canvas.create_image(event.x, event.y, anchor='center', image=self.current_sticker)
        self.canvas.unbind("<Button-1>")

    def change_sticker_size(self, value):
        self.size_a = int(self.st_slider.get())
        self.st_size_label.configure(text=self.size_a)

    def set_default_stickers_size(self):
        self.size_a = 100
        self.st_size_label.configure(text=self.size_a)
        self.st_slider.set(self.size_a)

    def add_text_window_show(self): # Обрати текст
        dialog = CTkInputDialog(title="Введіть текст,", text="а потім клацніть на потрібне місце на малюнку")
        text = dialog.get_input()
        if text:
            self.canvas.bind("<Button-1>", lambda event, t=text: self.add_text(event, text))

    def add_text(self, event, text): # Додати текст
        self.tk_font = CTkFont(family=self.tk_font['family'], size=self.font_size)
        self.canvas.create_text(event.x, event.y, text=text, fill=self.color, font=self.tk_font)
        self.canvas.unbind("<Button-1>")

    def text_settings(self):
        def change_text_size(size):
            self.font_size = int(size)
            self.tx_size_label.configure(text=self.font_size)

        def combobox_callback(value):
            self.tk_font = CTkFont(family=value, size=self.font_size)
            
        text_settings = CTkToplevel(app)
        text_settings.title("Налаштувати текст")
        self.tx_size_label = CTkLabel(text_settings, text=self.font_size)
        self.tx_size_label.pack()
        tx_size_slider = CTkSlider(text_settings, from_=11, to=96, command=change_text_size)
        tx_size_slider.set(self.font_size)
        tx_size_slider.pack()

        fonts_label = CTkLabel(text_settings, text="Шрифти з системи:")
        fonts_label.pack()
        fonts = list(font.families())
        fonts_combobox = CTkComboBox(text_settings, values=fonts, command=combobox_callback)
        fonts_combobox.set(self.tk_font['family'])
        fonts_combobox.pack()

    def show_frame_choice(self):
        def on_frames_click(index):
            selected_frame = frames[index]
            resized_image = selected_frame.resize((self.canvas.winfo_width(), self.canvas.winfo_height()))
            self.frame_image = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image(0, 0, anchor="nw", image=self.frame_image)
            
        frames_win = CTkToplevel(app)
        frames_win.title("Рамки")

        frames_names = ["frame1", "frame2", "frame3", "frame4", "frame5", "frame6", "frame7"]
        frames_thumbnails = [
            CTkImage(light_image=Image.open(f"frames_preview/{name}.png"), size=(70, 70))
            for name in frames_names
        ]

        frames = [
            Image.open(f"frames/{name}.png")
            for name in frames_names
        ]
        
        for i, image in enumerate(frames_thumbnails):
            frames_btn = CTkButton(frames_win, text=None, image=image, command=lambda i=i: on_frames_click(i))
            frames_btn.pack()
        
    def show_gallery(self):
        my_gallery = CTkToplevel(app)
        my_gallery.title("Галерея Brushshe")
        my_gallery.geometry("650x580")

        title_label = CTkLabel(my_gallery, text="Моя галерея")
        title_label.pack()

        gallery_frame = CTkScrollableFrame(my_gallery, width=650, height=560)
        gallery_frame.pack()

        row = 0
        column = 0

        def open_from_gallery(img_path):
            open_msg = CTkMessagebox(title = "Відкриття малюнку",
                                     message = "Малюнок, що Ви малюєте зараз, буде втрачено, якщо він не збережений і замінено на малюнок з галереї. Продовжити?",
                                     option_1="Так", option_2="Повернутися",
                                     icon="icons/question.png", icon_size=(100,100), sound=True)
            response = open_msg.get()
            if response == "Повернутися":
                pass
            else:
                image = Image.open(img_path)
                self.image = image
                self.draw = ImageDraw.Draw(self.image)
                self.canvas.delete("all")
                self.canvas.configure(bg="white")
                self.photo = ImageTk.PhotoImage(self.image)
                self.canvas.create_image(0, 0, anchor=NW, image=self.photo)
            
        for filename in os.listdir("gallery"):
            if filename.endswith(".png"):
                img_path = os.path.join("gallery", filename)
                img = Image.open(img_path)

                button_image = CTkImage(img, size=(250, 250))
                image_button = CTkButton(gallery_frame, image=button_image, text=None, command=lambda img_path=img_path: open_from_gallery(img_path))
                image_button.grid(row=row, column=column, padx=10, pady=10)
                
                column += 1
                if column == 2:
                    column = 0
                    row +=1
        
    def about_program(self):
        about_msg = CTkMessagebox(title="Про програму",
                                  message="Brushshe (Брашше) - програма для малювання, в якій можна створювати те, що Вам подобається.\n\nОрел на ім'я Brucklin (Браклін) - її талісман.\n\nhttps://github.com/l1mafresh/Brushshe\n\nv0.1.1",
                                  icon="icons/brucklin.png", icon_size=(150,191), option_1="ОК", height=400)

    def clean_all(self):
        self.canvas.delete("all")

    def change_brush_size(self, size):
        self.brush_size = int(size)
        self.brush_size_label.configure(text=self.brush_size)

    def eraser(self):
        self.color = self.canvas.cget('bg')
        self.tool_label.configure(text="Ластик:")
        
    def save_image(self):
        # позиції канви
        x0 = self.canvas.winfo_rootx()
        y0 = self.canvas.winfo_rooty()
        x1 = x0 + self.canvas.winfo_width()
        y1 = y0 + self.canvas.winfo_height()

        # вміст канви
        canvas_img = ImageGrab.grab(bbox=(x0, y0, x1, y1))

        image_name = f"gallery/{uuid.uuid4()}.png"

        saved = CTkMessagebox(title="Збережено",
                              message='Малюнок успішно збережено в галерею ("Моя галерея" в меню вгорі)!',
                              icon="icons/saved.png", icon_size=(100,100))

        canvas_img.save(image_name)

    def change_theme(self):
        if self.theme_switch_var.get() == "on":
            set_appearance_mode("dark")
        else:
            set_appearance_mode("light")

    def change_color(self, new_color):
        self.color = new_color
        self.tool_label.configure(text="Пензль:")

    def other_color_choise(self):
        try:
            pick_color = AskColor(title = "Оберіть інший колір пензля")
            self.getcolor = pick_color.get()
            if self.getcolor:
                self.color = self.getcolor
                self.other_color_btn.pack(side=RIGHT, padx=1)
                self.other_color_btn.configure(fg_color=self.getcolor)
                self.brush_size_label.configure(text="Пензль:")
        except:
            pass
        
    def select_other_color_btn(self):
        self.color = self.getcolor
        self.tool_label.configure(text="Пензль:")
        
app = Brushshe()
app.mainloop()