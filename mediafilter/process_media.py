import os
import cv2 as cv
import mediafilter.filters as flt
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
    return img_output_path


def process_vid(vid_input_path, vid_output_dir, filter_type, bg_color=""):
    # open input video file
    cv_cap = cv.VideoCapture(vid_input_path)
    w = int(cv_cap.get(cv.CAP_PROP_FRAME_WIDTH))
    h = int(cv_cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    fps = cv_cap.get(cv.CAP_PROP_FPS) or 30.0

    # build output file (force output ext to .mp4)
    vid_output_path = get_output_path(vid_input_path, vid_output_dir, filter_type, bg_color)

    print("Processing...")

    # ffmpeg input stream from raw frames
    ffmpeg_input = ffmpeg.input(
        'pipe:',
        format='rawvideo',
        pix_fmt='bgr24',
        s=f'{w}x{h}',
        r=fps
    )
    
    # ffmpeg output stream - compressed into h.264 and put into .mp4
    ffmpeg_output = ffmpeg.output(
        ffmpeg_input,
        vid_output_path,
        vcodec='libx264',
        crf=18, # lower val -> higher quality -> uses more memory
        preset='fast', # slower -> more efficient -> uses less memory (longer process time)
        pix_fmt='yuv420p',
        maxrate='12M', # higher val -> more detail -> uses more memory
        bufsize='24M' # higher val -> higher quality -> possibly uses more memory
    )

    # start ffmpeg process async to receive raw frames
    ffmpeg_process = ffmpeg_output.overwrite_output().run_async(pipe_stdin=True)

    # read frames from input vivd with opencv
    while cv_cap.isOpened():
        ret, frame = cv_cap.read()
        if not ret: 
            break

        # apply filter to frame
        if filter_type == "Sketch":
            processed_frame = flt.get_sketch_frame(frame, bg_color, for_video=True)
        else:
            processed_frame = flt.get_cartoon_frame(frame, for_video=True)

        # send processed frame to ffmpeg compression
        ffmpeg_process.stdin.write(processed_frame.astype('uint8').tobytes())
    
    cv_cap.release()
    ffmpeg_process.stdin.close()
    ffmpeg_process.wait()

    print("Video saved to ", vid_output_path)
    return vid_output_path

def get_output_path(input_path, output_dir, filter_type, bg_color=""):
    filename = os.path.basename(input_path)
    output_base, _ = os.path.splitext(filename)
    output_ext = ".mp4"
    if bg_color != "":
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + f"_{bg_color}" + output_ext
    else:
        output_path = output_dir + "/" + output_base + f"_{filter_type.lower()}" + output_ext
    return output_path