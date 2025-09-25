import os
import cv2 as cv
import filters as flt

def process_img(img_input_path, img_output_dir, filter_type, bg_color=""):
    img_input = cv.imread(img_input_path)
    if filter_type == "Sketch":
        img_output = flt.get_sketch_frame(img_input, bg_color, for_video=False)
    else:
        img_output = flt.get_cartoon_frame(img_input, for_video=False)
    
    img_output_path = get_output_path(img_input_path, img_output_dir, filter_type, bg_color)
    cv.imwrite(img_output_path, img_output)
    print("Image saved to ", img_output_path)


def process_vid(vid_input_path, vid_output_dir, filter_type, bg_color=""):
    vid_input = cv.VideoCapture(vid_input_path)
    w = int(vid_input.get(cv.CAP_PROP_FRAME_WIDTH))
    h = int(vid_input.get(cv.CAP_PROP_FRAME_HEIGHT))
    fps = vid_input.get(cv.CAP_PROP_FPS) or 30.0

    vid_output_path = get_output_path(vid_input_path, vid_output_dir, filter_type, bg_color)
    
    fourcc = cv.VideoWriter_fourcc(*'mp4v')
    vid_output = cv.VideoWriter(vid_output_path, fourcc, fps, (w, h))

    print("Processing...")

    while vid_input.isOpened():
        ret, frame = vid_input.read()
        if not ret: 
            break
        if filter_type == "Sketch":
            filter_frame = flt.get_sketch_frame(frame, bg_color, for_video=True)
        else:
            filter_frame = flt.get_cartoon_frame(frame, for_video=True)
        vid_output.write(filter_frame)
    
    print("Video saved to ", vid_output_path)
    vid_input.release()
    vid_output.release()

def get_output_path(input_path, output_dir, filter_type, bg_color=""):
    filename = os.path.basename(input_path)
    output_base, output_ext = os.path.splitext(filename)
    if bg_color != "":
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + f"_{bg_color}" + output_ext
    else:
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + output_ext
    return output_path