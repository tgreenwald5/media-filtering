---
title: Media Filtering
emoji: 📖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "5.47.1"
app_file: gui/gr_gui.py
pinned: false
---

# Adaptive Media Filter Engine
Transforms images and videos into sketch or cartoon styles using adaptive computer vision algorithms. Automatically optimizes processing parameters for each frame using gradient analysis, elbow method clustering, and temporal edge smoothing between frames to efficiently process video at up to 24 fps.

**Live Demo:** [Hugging Face Space](https://huggingface.co/spaces/greenwaldtaylor/media-filtering)


## Some Features
- **Filters**
    - Sketch Filter: Converts images and videos into their pencil sketch-like style (over a white or black background)
    - Cartoon Filter: Applies cartoon effect using color quantization and edge enhancement
- **Adaptive Processing**
    - Automatic frame resizing to improve efficiency
    - Adaptive edge detection based on frame characteristics
    - Processes video with temporal smoothing to reduce edge flickering across frames
    - Adaptive color clustering using K-means with elbow method
- **Multiple Interfaces**
    - Web interface using Gradio
    - Desktop GUI using Tkinter

## Examples


## Installation
1. **Clone the Repository**
    ```bash
    git clone https://github.com/tgreenwald5/media-filtering.git
    cd media-filtering
    ```
2. **Prerequisites**
    - Python 3.7+
    - FFmpeg (needed for video processing)
3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

    **Installing FFmpeg**
    - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
    - macOS:
        ```bash
        brew install ffmpeg
        ```
    - Linux:
        ```bash
        sudo apt-get install ffmpeg
        ```

## Usage
**Gradio Web Interface**

Launch the web interface:
```bash
python -m gui.gr_gui
```
The interface will open in your default browser. Upload an image or a video, select a filter type, and click "Apply Filter". Your uploaded media will then be filtered and previewed in the right window pane. Click the button on its top right if you would like to download it.

**Tkinter Desktop GUI**

Launch the desktop application:
```bash
python -m gui.tk_gui
```
1. Select media type (Image or Video)
2. Select filter type (Sketch or Cartoon)
3. Upload your file
4. Select download location
5. Click "Convert and Download"

## Technical Details
**Processing Pipeline**
- **Image Processing**
    1. Automatic resizing (1280px on longest side)
    2. Apply filter (sketch or cartoon)
    3. Output as PNG file  
- **Video Processing**
    1. Automatic resizing (1050px on longest side)
    2. FPS limiting to 24 fps
    3. Apply filter frame by frame
    4. Temporal smoothing in between frames to reduce edge flickering
    5. H.264 compression and MP4 output

**Filter Algorithms**
- **Sketch Filter**
    - Gaussian blur with sigma calculated from frame sharpness
    - Adaptive Canny edge detection with thresholds based on gradient magnitude
    - Keeps the original colors from the detected edges
    - A background color of white or black can be chosen
- **Cartoon Filter**
    - Bilateral filtering to smooth image while preserving edges
    - K-means color quantization (20-40 color clusters, exact number is dynamically found using the elbow method)
    - Edges are detected and darkened
    - K-means is retrained every 60 frames for videos

**Performance Optimizations**
- Chose to use MiniBatchKMeans instead of traditional KMeans for more efficient clustering
- Used a sample of 50,000 pixels for elbow calculations
- Adaptive frame sampling to balance processing speed and output quality
- H.264 compression with CRF 18 and ultrafast preset     

## Limitations
- Video processing can be a bit memory intensive if they are long and/or of high resolution
- Fast motion in videos may cause edge flickering
- Fully CPU-based so speed can be an issue for high resolution content
- Frames that contain many different colors may not be perfectly preserved in cartoon filter
- Frames with very low contrast can result in weak edge detection   
