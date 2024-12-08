import os
import json
import tkinter as tk
from tkinter import filedialog, simpledialog
from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence


class ImageManagerApp:
    CONFIG_FILE = "config.json"

    def __init__(self, root):
        self.root = root
        self.root.title("圖片管理工具")
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))
        self.root.bind("<Control-z>", lambda e: self.undo_last_action())
        self.root.bind("<Control-f>", lambda e: self.search_button())
        self.root.bind("<Control-t>", lambda e: self.add_button())

        self.image_folder = ""
        self.target_folder = ""
        self.image_files = []
        self.current_image_index = 0
        self.buttons = []
        self.gif_frames = None
        self.gif_index = 0
        self.gif_animation = None
        self.last_moved_image = None

        self.load_config()

        # 主框架設置
        self.main_frame = tk.Frame(self.root, bg="#2e2e2e")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側設置：1/3
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=2)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # 左側圖片框架
        self.image_frame = tk.Frame(self.main_frame, bg="#2e2e2e")
        self.image_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.image_label = tk.Label(self.image_frame, bg="#2e2e2e")
        self.image_label.pack(fill=tk.BOTH, expand=True)

        self.image_info = tk.Label(self.image_frame, bg="#2e2e2e", fg="white", font=("Arial", 14))
        self.image_info.pack(pady=10)

        # 左側下方按鈕區域
        self.button_bar = tk.Frame(self.image_frame, bg="#2e2e2e")
        self.button_bar.pack(side=tk.BOTTOM, pady=10)

        self.undo_button = tk.Button(self.button_bar, text="上一步", command=self.undo_last_action, bg="#4f4f4f", fg="white", font=("Arial", 12), width=10)
        self.undo_button.grid(row=0, column=0, padx=5)

        self.current_folder_button = tk.Button(self.button_bar, text="當前資料夾", command=self.select_image_folder, bg="#4f4f4f", fg="white", font=("Arial", 12), width=12)
        self.current_folder_button.grid(row=0, column=1, padx=5)

        self.target_folder_button = tk.Button(self.button_bar, text="目標資料夾", command=self.select_target_folder, bg="#4f4f4f", fg="white", font=("Arial", 12), width=12)
        self.target_folder_button.grid(row=0, column=2, padx=5)

        # 右側：按鈕區域
        self.button_frame = tk.Frame(self.main_frame, bg="#2e2e2e")
        self.button_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.canvas = tk.Canvas(self.button_frame, bg="#2e2e2e", highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self.button_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#2e2e2e")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.root.bind("<MouseWheel>", self.scroll_canvas)

        if self.image_folder:
            self.load_image_files()
            self.load_image()

        if self.target_folder:
            self.load_target_buttons()

    def scroll_canvas(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def select_image_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder = folder
            self.save_config()
            self.load_image_files()
            self.load_image()

    def select_target_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.target_folder = folder
            self.save_config()
            self.load_target_buttons()

    def search_button(self):
        keyword = simpledialog.askstring("搜尋按鈕", "請輸入按鈕名稱：")
        if keyword:
            for button in self.buttons:
                if keyword.lower() in button.cget("text").lower():
                    button.grid()  # 顯示符合條件的按鈕
                else:
                    button.grid_remove()  # 隱藏不符合條件的按鈕

        # 加入 'X' 按鈕以恢復顯示所有按鈕
            self.add_reset_button()

    def add_reset_button(self):
        """新增恢復顯示所有按鈕的功能。"""
        reset_button = tk.Button(
            self.scrollable_frame,
            text="X",
            command=self.reset_buttons,
            bg="#4f4f4f",
            fg="white",
            font=("Arial", 12),
            width=4,
        )
        reset_button.grid(row=0, column=0, padx=5, pady=5)
        self.buttons.append(reset_button)  # 將 'X' 按鈕加入按鈕列表以方便管理

    def reset_buttons(self):
        """恢復顯示所有按鈕並移除高亮，隱藏'X'按鈕。"""
        for button in self.buttons:
            if button.cget("text") != "X":  # 排除'X'按鈕
                button.grid()  # 顯示所有按鈕

        # 隱藏 'X' 按鈕
        self.buttons[-1].grid_remove()

    def add_button(self):
        folder_name = simpledialog.askstring("新增按鈕", "請輸入按鈕名稱：")
        if folder_name:
            folder_path = os.path.join(self.target_folder, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            self.load_target_buttons()

    def load_image_files(self):
        self.image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
        self.current_image_index = 0

    def load_image(self):
        if not self.image_files:
            return
        image_path = os.path.join(self.image_folder, self.image_files[self.current_image_index])

        if image_path.lower().endswith(".gif"):
            self.load_gif(image_path)
        else:
            self.display_image(image_path)

    def load_gif(self, image_path):
        image = Image.open(image_path)
        self.gif_frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(image)]
        self.gif_index = 0
        self.animate_gif()
        self.image_info.config(text=f"顯示GIF: {os.path.basename(image_path)}")

    def animate_gif(self):
        if self.gif_frames:
            self.image_label.config(image=self.gif_frames[self.gif_index])
            self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
            self.gif_animation = self.image_label.after(100, self.animate_gif)

    def display_image(self, image_path):
        if self.gif_animation:
            self.image_label.after_cancel(self.gif_animation)
            self.gif_animation = None

        image = Image.open(image_path)
        image.thumbnail((600, 600))
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.image_info.config(text=f"顯示圖片: {os.path.basename(image_path)}")

    def load_target_buttons(self):
        # 清除舊按鈕
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.buttons = []

        # 生成目標資料夾按鈕
        if not self.target_folder:
            return

        target_folders = [
            f for f in os.listdir(self.target_folder) if os.path.isdir(os.path.join(self.target_folder, f))
        ]
        if "其他" in target_folders:
            target_folders.remove("其他")
            target_folders.append("其他")

        for i, folder in enumerate(target_folders):
            folder_path = os.path.join(self.target_folder, folder)

            # 嘗試加載該資料夾的第一張圖片作為按鈕背景
            image_files = [
                f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", "gif"))
            ]
            if image_files:
                first_image_path = os.path.join(folder_path, image_files[0])
                image = Image.open(first_image_path)
                image.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(image)
            else:
                photo = None

            button = tk.Button(
                self.scrollable_frame,
                text=folder,
                image=photo,
                compound=tk.TOP,
                command=lambda p=folder_path: self.move_image(p),
                font=("Arial", 10),
                bg="#4f4f4f", fg="white"
            )
            button.photo = photo  # 保存引用避免被垃圾回收
            button.grid(row=i // 4, column=i % 4, padx=10, pady=10)
            self.buttons.append(button)

    def move_image(self, target_path):
        if not self.image_files:
            return
        current_image_path = os.path.join(self.image_folder, self.image_files[self.current_image_index])
        new_path = os.path.join(target_path, os.path.basename(current_image_path))
        os.rename(current_image_path, new_path)
        self.last_moved_image = (current_image_path, new_path)
        del self.image_files[self.current_image_index]
        if self.image_files:
            self.load_image()
        else:
            self.image_label.config(image="")
            self.image_info.config(text="無圖片顯示")

    def undo_last_action(self):
        if self.last_moved_image:
            old_path, new_path = self.last_moved_image
            os.rename(new_path, old_path)
            self.image_files.insert(self.current_image_index, os.path.basename(old_path))
            self.load_image()
            self.last_moved_image = None
            self.image_info.config(text="上一步操作已還原")

    def save_config(self):
        config = {"image_folder": self.image_folder, "target_folder": self.target_folder}
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=4)

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    self.image_folder = config.get("image_folder", "")
                    self.target_folder = config.get("target_folder", "")
            except (json.JSONDecodeError, FileNotFoundError):
                self.reset_config()
        else:
            self.reset_config()

    def reset_config(self):
        self.image_folder = ""
        self.target_folder = ""
        self.save_config()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageManagerApp(root)
    root.mainloop()
