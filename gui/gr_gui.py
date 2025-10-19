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
            return gr.update(choices=["Black", "White"], value="Black", interactive=True, visible=True)
        else:
            return gr.update(choices=[], value=None, interactive=False, visible=False)


# get random img from pexels
def get_random_img():
    page = random.randint(1, 100)
    res = pexel.search_photos(query="nature", per_page=80, page=page)
    if "photos" not in res or not res["photos"]:
        raise gr.Error("Could not fetch image.")
    photo = random.choice(res["photos"])
    return photo["src"]["medium"]


# get random vid from pexels
def get_random_vid():
    VID_MIN_DUR = 5
    VID_MAX_DUR = 20
    VID_TARGET_RES = 1280 * 720

    page = random.randint(1, 100)
    res = pexel.search_videos(query="nature", per_page=80, page=page)
    vid_pool = res.get("videos") or []

    # filter vids by time
    filt_by_dur = []
    for all_vid in vid_pool:
        if all_vid['duration'] >= VID_MIN_DUR and all_vid['duration'] <= VID_MAX_DUR:
            filt_by_dur.append(all_vid)
    vid_pool = filt_by_dur

    # filter vids by res
    filt_by_res = []
    for all_vid in vid_pool:
        for indiv_vid in all_vid["video_files"]:
            vid_res = indiv_vid["width"] * indiv_vid["height"]
            if vid_res == VID_TARGET_RES:
                filt_by_res.append(indiv_vid)
    vid_pool = filt_by_res

    print(len(vid_pool))
    best_vid = vid_pool[random.randint(0, len(vid_pool) - 1)]
    return best_vid["link"]


# ui
with gr.Blocks(css=".progress-text {display: none !important;}") as demo:
    gr.Markdown("## **Media Filtering**")
    with gr.Tabs():
        # img tab
        with gr.Tab("Image Filtering"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### **1. Upload Your Own Image Or Try a Random One**")
                    img_input = gr.Image(type="filepath", label="Upload Image")
                    random_img_button = gr.Button("Click For Random Image")
                img_output = gr.Image(label="Processed Image")
            
            random_img_button.click(get_random_img, outputs=img_input)

            gr.Markdown("### **2. Choose a Filter Style**")
            img_filter = gr.Radio(["Sketch", "Cartoon"], label="Filter Style")
            img_bg = gr.Radio([], label="Choose Sketch Background Color", value=None, interactive=False, visible=False)
            img_filter.change(update_bg_options, img_filter, img_bg)
            
            
            gr.Markdown("### **3. Apply the Filter**")
            img_button = gr.Button("Apply Filter", variant="primary")
            img_button.click(process_image, [img_input, img_filter, img_bg], img_output)

        # vid tab
        with gr.Tab("Video Filtering"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### **1. Upload Your Own Video Or Try a Random One**")
                    vid_input = gr.Video(label="Upload Video")
                    random_vid_button = gr.Button("Click For Random Video")
                vid_output = gr.Video(label="Processed Video", show_download_button=True)

            random_vid_button.click(get_random_vid, outputs=vid_input)

            gr.Markdown("### **2. Choose a Filter Style**")
            vid_filter = gr.Radio(["Sketch", "Cartoon"], label="Filter Style")
            vid_bg = gr.Radio([], label="Sketch Background Color", value=None, interactive=False, visible=False)
            vid_filter.change(update_bg_options, vid_filter, vid_bg)
            
            gr.Markdown("### **3. Apply the Filter**")
            vid_button = gr.Button("Apply Filter", variant="primary")
            vid_button.click(process_video, [vid_input, vid_filter, vid_bg], vid_output)

demo.launch()
