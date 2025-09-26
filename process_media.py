import os
import cv2 as cv
import filters as flt
import ffmpeg

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

    print("Processing...")

    video_in = ffmpeg.input(
        'pipe:',
        format='rawvideo',
        pix_fmt='bgr24',
        s=f'{w}x{h}',
        r=fps
    )

    #audio_in = ffmpeg.input(vid_input_path).audio

    output = ffmpeg.output(
        video_in,
        vid_output_path,
        vcodec='libx264',
        crf=18, # lower val -> higher quality -> uses more memory
        preset='slow', # slower -> more efficient -> uses less memory (longer process time)
        pix_fmt='yuv420p',
        maxrate='12M', # higher val -> more detail -> uses more memory
        bufsize='24M' # higher val -> higher quality -> possibly uses more memory
    )

    process = output.overwrite_output().run_async(pipe_stdin=True)

    while vid_input.isOpened():
        ret, frame = vid_input.read()
        if not ret: 
            break
        if filter_type == "Sketch":
            filter_frame = flt.get_sketch_frame(frame, bg_color, for_video=True)
        else:
            filter_frame = flt.get_cartoon_frame(frame, for_video=True)

        process.stdin.write(filter_frame.astype('uint8').tobytes())
    
    vid_input.release()
    process.stdin.close()
    process.wait()

    print("Video saved to ", vid_output_path)

def get_output_path(input_path, output_dir, filter_type, bg_color=""):
    filename = os.path.basename(input_path)
    output_base, output_ext = os.path.splitext(filename)
    if bg_color != "":
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + f"_{bg_color}" + output_ext
    else:
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + output_ext
    return output_path