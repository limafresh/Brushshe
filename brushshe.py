from customtkinter import *
from CTkMenuBar import CTkMenuBar, CustomDropdownMenu
from CTkColorPicker import AskColor
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageDraw, ImageTk, ImageGrab
from tkinter import PhotoImage, font, Listbox
from os import listdir
from uuid import uuid4
from gc import disable as garbage_collector_disable

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
        file_dropdown = CustomDropdownMenu(widget=file_menu)
        file_dropdown.add_option(option="Відкрити з файлу", command=self.open_image)
        file_dropdown.add_option(option="Експортувати на ПК", command=self.export)

        bg_menu = menu.add_cascade("Колір тла")
        bg_dropdown = CustomDropdownMenu(widget=bg_menu)
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
            bg_dropdown.add_option(option=ukr_name, command=lambda c=color: self.change_bg(c))
        bg_dropdown.add_separator()
        bg_dropdown.add_option(option="Інший колір", command=self.other_bg_color)

        # ширина і висота всіх зображень стікерів - 88 px
        stickers_names = [
            "smile", "flower", "heart", "okay", "cheese", "face2", "cat", "alien", "like",
            "unicorn", "pineapple", "grass", "rain", "brucklin", "brushshe", "strawberry",
            "butterfly", "flower2"
        ]
        self.stickers = [Image.open(f"stickers/{name}.png") for name in stickers_names]
        
        add_menu = menu.add_cascade("Додати")
        add_dropdown = CustomDropdownMenu(widget=add_menu)
        smile_icon = CTkImage(light_image=Image.open("icons/smile.png"), size=(50, 50))
        add_dropdown.add_option(option="Наліпки", image=smile_icon, command=self.show_stickers_choice)
        text_icon = CTkImage(light_image=Image.open("icons/text.png"), size=(50, 50))
        text_submenu = add_dropdown.add_submenu("Текст", image=text_icon)
        text_submenu.add_option(option="Додати текст на малюнок", command=self.add_text_window_show)
        text_submenu.add_option(option="Налаштувати текст для вставлення", command=self.text_settings)
        frame_icon = CTkImage(light_image=Image.open("icons/frame.png"), size=(50, 50))
        add_dropdown.add_option(option="Рамки", image=frame_icon, command=self.show_frame_choice)
        
        shapes_menu = menu.add_cascade("Фігури")
        shapes_dropdown = CustomDropdownMenu(widget=shapes_menu)
        shapes_dropdown.add_option(option="Прямокутник", command=lambda: self.create_shape("rectangle"))
        shapes_dropdown.add_option(option="Овал", command=lambda: self.create_shape("oval"))
        shapes_dropdown.add_option(option="Лінія", command=lambda: self.create_shape("line"))
        shapes_dropdown.add_option(option="Заповнений прямокутник", command=lambda: self.create_shape("fill rectangle"))
        shapes_dropdown.add_option(option="Заповнений овал", command=lambda: self.create_shape("fill oval"))
        
        gallery_menu = menu.add_cascade("Моя галерея", command=self.show_gallery)

        other_menu = menu.add_cascade("Інше")
        other_dropdown = CustomDropdownMenu(widget=other_menu)
        theme_submenu = other_dropdown.add_submenu("Тема")
        theme_submenu.add_option(option="Системна", command=lambda: self.change_theme("system"))
        theme_submenu.add_option(option="Світла", command=lambda: self.change_theme("light"))
        theme_submenu.add_option(option="Темна", command=lambda: self.change_theme("dark"))
        other_dropdown.add_option(option="Про програму", command=self.about_program)
        
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
        size_slider.pack(side=LEFT, padx=1)

        self.brush_size_label = CTkLabel(tools_frame, text="2")
        self.brush_size_label.pack(side=LEFT, padx=1)

        save_button = CTkButton(tools_frame, text="Зберегти в галерею", width=70, command=self.save_image)
        save_button.pack(side=RIGHT, padx=1)

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

        garbage_collector_disable() # бо ввімкнений gc думає що додані наліпки і текст - це сміття

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

        self.canvas.configure(cursor="pencil")
        self.current_tool = None

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
        sticker_choose.geometry("350x420")
        sticker_choose.title("Оберіть наліпку")
                
        tabview = CTkTabview(sticker_choose, command=update_btn)
        tabview.add("Обрати наліпку")
        tabview.add("Розмір наліпок")
        tabview.set("Обрати наліпку")
        tabview.pack(fill=BOTH, expand=True)

        stickers_frame = CTkScrollableFrame(tabview.tab("Обрати наліпку"))
        stickers_frame.pack(fill=BOTH, expand=True)

        self.st_size_label = CTkLabel(tabview.tab("Розмір наліпок"), text=self.size_a)
        self.st_size_label.pack(padx=10, pady=10)
        self.st_slider = CTkSlider(tabview.tab("Розмір наліпок"), from_=10, to=175, command=self.change_sticker_size)
        self.st_slider.set(self.size_a)
        self.st_slider.pack(padx=10, pady=10)
        set_default = CTkButton(tabview.tab("Розмір наліпок"), text="Повернути як було", command=self.set_default_stickers_size)
        set_default.pack(padx=10, pady=10)

        update_btn()

    def set_current_sticker(self, image): # Обрати наліпку
        self.current_sticker = image
        if self.current_sticker:
            self.canvas.bind("<Button-1>", self.add_sticker)
            self.canvas.configure(cursor="")

    def add_sticker(self, event): # Додати наліпку
        self.canvas.create_image(event.x, event.y, anchor='center', image=self.current_sticker)
        self.canvas.unbind("<Button-1>")
        self.canvas.configure(cursor="pencil")

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
            self.canvas.configure(cursor="")

    def add_text(self, event, text): # Додати текст
        self.tk_font = CTkFont(family=self.tk_font["family"], size=self.font_size)
        self.canvas.create_text(event.x, event.y, text=text, fill=self.color, font=self.tk_font)
        self.canvas.unbind("<Button-1>")
        self.canvas.configure(cursor="pencil")

    def text_settings(self):
        def change_text_size(size):
            self.font_size = int(size)
            self.tx_size_label.configure(text=self.font_size)

        def listbox_callback(event):
            selected_font = fonts_listbox.get(fonts_listbox.curselection())
            self.tk_font = CTkFont(family=selected_font, size=self.font_size)
            
        text_settings = CTkToplevel(app)
        text_settings.title("Налаштувати текст")
        
        self.tx_size_label = CTkLabel(text_settings, text=self.font_size)
        self.tx_size_label.pack(padx=10, pady=10)
        tx_size_slider = CTkSlider(text_settings, from_=11, to=96, command=change_text_size)
        tx_size_slider.set(self.font_size)
        tx_size_slider.pack(padx=10, pady=10)

        fonts_label = CTkLabel(text_settings, text="Шрифти з системи:")
        fonts_label.pack(padx=10, pady=10)
        fonts = list(font.families())
        fonts_listbox = Listbox(text_settings)
        fonts_listbox.pack(padx=10, pady=10)
        for f in fonts:
            fonts_listbox.insert(END, f)
        fonts_listbox.bind("<<ListboxSelect>>", listbox_callback)

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
            CTkImage(light_image=Image.open(f"frames_preview/{name}.png"), size=(100, 100))
            for name in frames_names
        ]

        frames = [
            Image.open(f"frames/{name}.png")
            for name in frames_names
        ]

        row = 0
        column = 0
        
        for i, image in enumerate(frames_thumbnails):
            frames_btn = CTkButton(frames_win, text=None, image=image, command=lambda i=i: on_frames_click(i))
            frames_btn.grid(column=column, row=row, padx=10, pady=10)
            
            column += 1
            if column == 2:
                column = 0
                row +=1

    # Функції створення фігур
    def create_shape(self, shape):
        def start_shape(event):
            self.shape_start_x = event.x
            self.shape_start_y = event.y
            if self.shape == "rectangle":
                self.shape_id = self.canvas.create_rectangle(self.shape_start_x, self.shape_start_y, self.shape_start_x,
                                                             self.shape_start_y, width=self.brush_size, outline=self.color)
            elif self.shape == "oval":
                self.shape_id = self.canvas.create_oval(self.shape_start_x, self.shape_start_y, self.shape_start_x,
                                                        self.shape_start_y, width=self.brush_size, outline=self.color)
            elif self.shape == "line":
                self.shape_id = self.canvas.create_line(self.shape_start_x, self.shape_start_y, self.shape_start_x,
                                                        self.shape_start_y, width=self.brush_size, fill=self.color, capstyle=ROUND)
            elif self.shape == "fill rectangle":
                self.shape_id = self.canvas.create_rectangle(self.shape_start_x, self.shape_start_y, self.shape_start_x,
                                                        self.shape_start_y, width=self.brush_size, outline=self.color, fill=self.color)
            elif self.shape == "fill oval":
                self.shape_id = self.canvas.create_oval(self.shape_start_x, self.shape_start_y, self.shape_start_x,
                                                        self.shape_start_y, width=self.brush_size, outline=self.color, fill=self.color)

        def draw_shape(event):
            self.canvas.coords(self.shape_id, self.shape_start_x, self.shape_start_y, event.x, event.y)

        def end_shape(event):
            self.canvas.unbind("<ButtonPress-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")

            self.canvas.bind("<B1-Motion>", self.paint)
            self.canvas.bind("<ButtonRelease-1>", self.stop_paint)

            self.canvas.configure(cursor="pencil")
        
        self.shape = shape
        self.canvas.bind("<ButtonPress-1>", start_shape)
        self.canvas.bind("<B1-Motion>", draw_shape)
        self.canvas.bind("<ButtonRelease-1>", end_shape)

        self.canvas.configure(cursor="crosshair")
        
        self.after(100) # Невелика затримка, бо інакше не працює
        
    def show_gallery(self): # Галерея
        my_gallery = CTkToplevel(app)
        my_gallery.title("Галерея Brushshe")
        my_gallery.geometry("650x580")

        gallery_frame = CTkScrollableFrame(my_gallery, label_text="Моя галерея")
        gallery_frame.pack(fill=BOTH, expand=True)

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

        is_image_found = False
            
        for filename in os.listdir("gallery"):
            if filename.endswith(".png"):
                is_image_found = True
                img_path = os.path.join("gallery", filename)
                img = Image.open(img_path)

                button_image = CTkImage(img, size=(250, 250))
                image_button = CTkButton(gallery_frame, image=button_image, text=None, command=lambda img_path=img_path: open_from_gallery(img_path))
                image_button.grid(row=row, column=column, padx=10, pady=10)
                
                column += 1
                if column == 2:
                    column = 0
                    row +=1

        if is_image_found == False:
            gallery_frame.configure(label_text="Моя галерея (пусто)")
            
    def change_theme(self, theme):
        set_appearance_mode(theme)
        
    def about_program(self):
        about_text = '''
Brushshe (Брашше) - програма для малювання, в якій можна створювати те, що Вам подобається.

Орел на ім'я Brucklin (Браклін) - її талісман.

https://github.com/l1mafresh/Brushshe

v0.7
        '''
        about_msg = CTkMessagebox(title="Про програму", message=about_text,
                                  icon="icons/brucklin.png", icon_size=(150,191), option_1="ОК", height=400)

    def clean_all(self):
        self.canvas.delete("all")

    def change_brush_size(self, size):
        self.brush_size = int(size)
        self.brush_size_label.configure(text=self.brush_size)

    def eraser(self):
        self.color = self.canvas.cget('bg')
        self.tool_label.configure(text="Ластик:")
        self.canvas.configure(cursor="crosshair")
        self.current_tool = "eraser"
        
    def save_image(self):
        # позиції канви
        x0 = self.canvas.winfo_rootx()
        y0 = self.canvas.winfo_rooty()
        x1 = x0 + self.canvas.winfo_width()
        y1 = y0 + self.canvas.winfo_height()

        # вміст канви
        canvas_img = ImageGrab.grab(bbox=(x0, y0, x1, y1))

        image_name = f"gallery/{uuid4()}.png"

        saved = CTkMessagebox(title="Збережено",
                              message='Малюнок успішно збережено в галерею ("Моя галерея" в меню вгорі)!',
                              icon="icons/saved.png", icon_size=(100,100))

        canvas_img.save(image_name)

    def change_color(self, new_color):
        self.color = new_color
        self.tool_label.configure(text="Пензль:")
        if self.current_tool == "eraser":
            self.canvas.configure(cursor="pencil")
            self.current_tool = None

    def other_color_choise(self):
        try:
            pick_color = AskColor(title = "Оберіть інший колір пензля")
            self.getcolor = pick_color.get()
            if self.getcolor:
                self.color = self.getcolor
                self.other_color_btn.pack(side=RIGHT, padx=1)
                self.other_color_btn.configure(fg_color=self.getcolor)
                self.tool_label.configure(text="Пензль:")
                if self.current_tool == "eraser":
                    self.canvas.configure(cursor="pencil")
                    self.current_tool = None
        except:
            pass
        
    def select_other_color_btn(self):
        self.color = self.getcolor
        self.tool_label.configure(text="Пензль:")
        if self.current_tool == "eraser":
            self.canvas.configure(cursor="pencil")
            self.current_tool = None
        
app = Brushshe()
app.mainloop()
