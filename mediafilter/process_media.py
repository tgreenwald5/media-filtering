import os
import cv2 as cv
import mediafilter.filters as flt
import ffmpeg
from mediafilter.constants import *

def process_img(img_input_path, img_output_dir, filter_type, bg_color=""):
    img_input = cv.imread(img_input_path)
    if filter_type == "Sketch":
        img_output = flt.get_sketch_frame(img_input, bg_color, for_video=False)
    else:
        img_output = flt.get_cartoon_frame(img_input, frame_idx=0, for_video=False)
    
    img_output_path = get_output_path(img_input_path, img_output_dir, filter_type, bg_color)
    cv.imwrite(img_output_path, img_output)
    print("Image saved to ", img_output_path)
    return img_output_path

def process_vid(vid_input_path, vid_output_dir, filter_type, bg_color=""):
    # open input video file
    cv_cap = cv.VideoCapture(vid_input_path)
    orig_w = int(cv_cap.get(cv.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cv_cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    input_fps = cv_cap.get(cv.CAP_PROP_FPS) or MAX_FPS
    output_fps = min(input_fps, MAX_FPS)

    # reduce video dimensions if needed 
    if max(orig_h, orig_w) > VIDEO_MAX_SIDE:
        scale = VIDEO_MAX_SIDE / max(orig_h, orig_w)
        w = max(1, int(orig_w * scale))
        h = max(1, int(orig_h * scale))
        if w % 2 != 0:
            w = w -1
        if h % 2 != 0:
            h = h - 1
    else:
        w = orig_w
        h = orig_h

    # build output file (force output ext to .mp4)
    vid_output_path = get_output_path(vid_input_path, vid_output_dir, filter_type, bg_color)

    print("Processing...")

    # ffmpeg input stream from raw frames
    ffmpeg_input = ffmpeg.input(
        'pipe:',
        format='rawvideo',
        pix_fmt='bgr24',
        s=f'{w}x{h}',
        r=output_fps
    )
    
    # ffmpeg output stream - compressed into h.264 and put into .mp4
    ffmpeg_output = ffmpeg.output(
        ffmpeg_input,
        vid_output_path,
        vcodec=FFMPEG_VCODEC,
        crf=FFMPEG_CRF, # lower val -> higher quality -> uses more memory
        preset=FFMPEG_PRESET, # slower -> more efficient -> uses less memory (longer process time)
        pix_fmt=FFMPEG_PIX_FMT,
        maxrate=FFMPEG_MAXRATE, # higher val -> more detail -> uses more memory
        bufsize=FFMPEG_BUFSIZE # higher val -> higher quality -> possibly uses more memory
    )

    # start ffmpeg process async to receive raw frames
    ffmpeg_process = ffmpeg_output.overwrite_output().run_async(pipe_stdin=True)


    # read frames from input vivd with opencv
    frame_idx = 0
    processed_frame_idx = 0

    frame_interval = input_fps / output_fps
    next_frame_to_process = 0.0

    while cv_cap.isOpened():
        ret, frame = cv_cap.read()
        if not ret: 
            break
        
        if frame_idx >= next_frame_to_process:
            if (w != orig_w or h != orig_h):
                frame = cv.resize(frame, (w, h), interpolation=cv.INTER_AREA)

            # apply filter to frame
            if filter_type == "Sketch":
                processed_frame = flt.get_sketch_frame(frame, bg_color, for_video=True)
            else:
                processed_frame = flt.get_cartoon_frame(frame, frame_idx, for_video=True)

            # send processed frame to ffmpeg compression
            ffmpeg_process.stdin.write(processed_frame.astype('uint8').tobytes())

            processed_frame_idx += 1
            next_frame_to_process += frame_interval

        frame_idx += 1
    
    cv_cap.release()
    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()

    print("Video saved to ", vid_output_path)
    flt.kmeans = None
    flt.edge_buffer.clear()
    return vid_output_path

def get_output_path(input_path, output_dir, filter_type, bg_color=""):
    filename = os.path.basename(input_path)
    output_base, input_ext = os.path.splitext(filename)

    
    if input_ext.lower() in IMAGE_EXTENSIONS:
        output_ext = OUTPUT_IMAGE_EXT
    else:
        output_ext = OUTPUT_VIDEO_EXT

    if bg_color:
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + f"_{bg_color}" + output_ext
    else:
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + output_ext
        
    return output_path