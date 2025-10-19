import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import gradio as gr
from mediafilter import process_media as pm
import tempfile
import random

from pexelsapi.pexels import Pexels
PEXELS_KEY = "fIeN1AtM0fclJrWeahHn83w12N9ebHgMqiFjZm0VTQXkrGlAmFI6U3ZG"
pexel = Pexels(PEXELS_KEY)

# img processing
def process_image(upload, filter_type, bg_color):
    output_dir = tempfile.mkdtemp()
    return pm.process_img(upload, output_dir, filter_type, bg_color)

# vid processing
def process_video(upload, filter_type, bg_color):
    output_dir = tempfile.mkdtemp()
    return pm.process_vid(upload, output_dir, filter_type, bg_color)

# set bg
def update_bg_options(filter_choice):
        if filter_choice == "Sketch":
            return gr.update(choices=["White", "Black"], value="White", interactive=True, visible=True)
        else:
            return gr.update(choices=[], value=None, interactive=False, visible=False)

# get random pic from pexels
def get_random_pic():
    page = random.randint(1, 100)
    res = pexel.search_photos(query="nature", per_page=50, page=page)
    if "photos" not in res or not res["photos"]:
        raise gr.Error("Could not fetch image.")
    photo = random.choice(res["photos"])
    return photo["src"]["large2x"]

# ui
with gr.Blocks(css=".progress-text {display: none !important;}") as demo:
    gr.Markdown("Media Filtering")
    with gr.Tabs():
        # img tab
        with gr.Tab("Image Filtering"):
            with gr.Row():
                with gr.Column():
                    img_input = gr.Image(type="filepath", label="Upload Image")
                    random_button = gr.Button("Click To Use Random Image Instead")
                img_output = gr.Image(label="Processed Image")
            
            random_button.click(get_random_pic, outputs=img_input)
            
            img_filter = gr.Radio(["Sketch", "Cartoon"], label="Filter")
            img_bg = gr.Radio([], label="Sketch Background Color", value=None, interactive=False, visible=False)
            img_filter.change(update_bg_options, img_filter, img_bg)
            
            img_button = gr.Button("Apply Filter", variant="primary")
            img_button.click(process_image, [img_input, img_filter, img_bg], img_output)

        # vid tab
        with gr.Tab("Video Filtering"):
            with gr.Row():
                vid_input = gr.Video(label="Upload Video")
                vid_output = gr.Video(label="Processed Video", show_download_button=True)
            vid_filter = gr.Radio(["Sketch", "Cartoon"], label="Filter")
            vid_bg = gr.Radio([], label="Sketch Background Color", value=None, interactive=False, visible=False)
            vid_filter.change(update_bg_options, vid_filter, vid_bg)
            vid_button = gr.Button("Apply Filter")
            vid_button.click(process_video, [vid_input, vid_filter, vid_bg], vid_output)
demo.launch()
