import gradio as gr
from mediafilter import process_media as pm
import tempfile, os

# img processing
def process_image(upload, filter_type, bg_color):
    output_dir = tempfile.mkdtemp()
    return pm.process_img(upload, output_dir, filter_type, bg_color)

# vid processing
def process_video(upload, filter_type, bg_color):
    output_dir = tempfile.mkdtemp()
    return pm.process_vid(upload, output_dir, filter_type, bg_color)

def update_bg_options(filter_choice):
        if filter_choice == "Sketch":
            return gr.update(choices=["White", "Black"], value="White", interactive=True, visible=True)
        else:
            return gr.update(choices=[], value=None, interactive=False, visible=False)

# ui
with gr.Blocks() as demo:
    gr.Markdown("Media Filtering")
    
    with gr.Tabs():
        # img tab
        with gr.Tab("Image Filtering"):
            with gr.Row():
                img_input = gr.Image(type="filepath", label="Upload Image", webcam_options=None)
                img_output = gr.Image(label="Processed Image")
            img_filter = gr.Radio(["Sketch", "Cartoon"], label="Filter")
            img_bg = gr.Radio([], label="Sketch Background Color", value=None, interactive=False, visible=False)
            img_filter.change(update_bg_options, img_filter, img_bg)
            img_button = gr.Button("Apply Filter")
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
