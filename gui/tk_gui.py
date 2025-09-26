import tkinter as tk
from tkinter import filedialog
import os
from mediafilter import process_media as pm

class Gui:
    def __init__(self, root):
        self.root = root
        self.media_type = None
        self.filter_type = None
        self.image_button = None
        self.video_button = None
        self.sketch_button = None
        self.cartoon_button = None
        self.upload_button = None
        self.dload_button = None
        self.condown_button = None

        self.upload_path = None
        self.download_dir = None

        root.title("Media Filtering")
        root.geometry("600x400")

        ### MEDIA ###
        media_frame = tk.Frame(root)
        media_frame.pack(pady=20)

        tk.Label(media_frame, text="Choose Media:", font=("Helvetica", 18, "bold")).pack(side="left", padx=10)

        self.image_button = tk.Button(media_frame, text="Image", width=8, command=lambda: self.select_media(self.image_button))
        self.image_button.pack(side="left", padx=5)

        self.video_button = tk.Button(media_frame, text="Video", width=8, command=lambda: self.select_media(self.video_button))
        self.video_button.pack(side="left", padx=5)

        ### FILTER ###
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=20)

        tk.Label(filter_frame, text="Choose Filter:", font=("Helvetica", 18, "bold")).pack(side="left", padx=10)

        self.sketch_button = tk.Button(filter_frame, text="Sketch", width=8, command=lambda: self.select_filter(self.sketch_button))
        self.sketch_button.pack(side="left", padx=5)

        self.cartoon_button = tk.Button(filter_frame, text="Cartoon", width=8, command=lambda: self.select_filter(self.cartoon_button))
        self.cartoon_button.pack(side="left", padx=5)

        ### BOTTOM ###
        bottom_frame = tk.Frame(root)
        bottom_frame.pack(pady=30)

        self.upload_button = tk.Button(bottom_frame, text="❌ Upload File ❌", width=16, command=self.choose_upload_path)
        self.upload_button.pack(side="left", padx=10)

        self.dload_button = tk.Button(bottom_frame, text="❌ Download Location ❌", width=20, command=self.choose_download_dir)
        self.dload_button.pack(side="left", padx=10)

        self.condown_button = tk.Button(root, text="Convert and Download", width=20, command=self.condown)
        self.condown_button.pack(pady=20)

        #root.mainloop()

    def select_media(self, choice_button):
        self.image_button.config(font=("Helvetica", 14), fg="black")
        self.video_button.config(font=("Helvetica", 14), fg="black")
        choice_button.config(font=("Helvetica", 14, "bold"), fg="green")
        self.media_type = choice_button.cget("text")
    
    def select_filter(self, choice_button):
        self.sketch_button.config(font=("Helvetica", 14), fg="black")
        self.cartoon_button.config(font=("Helvetica", 14), fg="black")
        choice_button.config(font=("Helvetica", 14, "bold"), fg="green")
        self.filter_type = choice_button.cget("text")
    
    def choose_upload_path(self):
        file_path = filedialog.askopenfilename(title="Select a Media File", filetypes=[("Images", "*.png *.jpg"), ("Videos", "*.mp4")])
        if file_path:
            self.upload_path = file_path
            self.upload_button.config(text="✅ Upload File ✅")
    
    def choose_download_dir(self):
        dir_path = filedialog.askdirectory(title="Select a Download Location")
        if dir_path:
            self.download_dir = dir_path
            self.dload_button.config(text="✅ Download Location ✅")

    def condown(self):
        input_path_ext = os.path.splitext(self.upload_path)[1]
        if self.media_type == None or self.filter_type == None or self.upload_path == None or self.download_dir == None:
            print("Please ensure all selections are valid")
        elif (self.media_type == "Image" and input_path_ext == ".mp4") or (self.media_type == "Video" and not input_path_ext == ".mp4"):
            print("Please ensure all selections are valid")
        else:
            if self.media_type == "Image":
                if self.filter_type == "Sketch":
                    pm.process_img(self.upload_path, self.download_dir, self.filter_type, "white")
                    pm.process_img(self.upload_path, self.download_dir, self.filter_type, "black")
                else:
                    pm.process_img(self.upload_path, self.download_dir, self.filter_type, "")
            else:
                if self.filter_type == "Sketch":
                    pm.process_vid(self.upload_path, self.download_dir, self.filter_type, "white")
                    pm.process_vid(self.upload_path, self.download_dir, self.filter_type, "black")
                else:
                    pm.process_vid(self.upload_path, self.download_dir, self.filter_type, "")
root = tk.Tk()
app = Gui(root)
root.mainloop()
