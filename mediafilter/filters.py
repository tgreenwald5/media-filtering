import numpy as np
import cv2 as cv
from mediafilter.constants import *
import mediafilter.filters_utils as fu

def get_sketch_frame(frame, bg_color, for_video=False):
    if for_video == False:
        frame = fu.normalize_size(frame)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_th, upper_th = fu.get_canny_threshs(gray)
    sigma = fu.get_sigma(gray)
    edges = fu.get_edges(gray, SKETCH_BLUR, lower_th * SKETCH_THRESH_MULT, upper_th * SKETCH_THRESH_MULT, sigma)
    if for_video == True:
        edges = fu.smooth_edges(edges)
        
    if bg_color == "White":
        sketch_frame = np.full_like(frame, 255)
    else:
        sketch_frame = np.full_like(frame, 0)
    sketch_frame[edges != 0] = frame[edges != 0]

    return sketch_frame

kmeans = None
def get_cartoon_frame(frame, frame_idx, for_video=False):
    global kmeans
    if for_video == False:
        frame = fu.normalize_size(frame)

    smooth = cv.bilateralFilter(frame, d=BILATERAL_D, sigmaColor=BILATERAL_SIGMA_COLOR, sigmaSpace=BILATERAL_SIGMA_SPACE)
    pixel_colors = smooth.reshape((-1, 3))
    if kmeans == None or frame_idx % KMEANS_RETRAIN_INTERVAL == 0: # if kmeans not created or time for new fitting
        k_min, k_max = fu.get_k_range(frame)
        if for_video == True:
            sample = pixel_colors[np.random.choice(len(pixel_colors), size=min(len(pixel_colors), KMEANS_SAMPLE_SIZE), replace=False)]
            elbow_k = fu.get_k_elbow(sample, k_min=k_min, k_max=k_max, step=KMEANS_STEP, for_vid=True)
            kmeans = fu.get_kmeans(pixel_colors, num_clusts=elbow_k) # get new centroids (video)
        else:
            sample = pixel_colors[np.random.choice(len(pixel_colors), size=min(len(pixel_colors), KMEANS_SAMPLE_SIZE), replace=False)]
            elbow_k = fu.get_k_elbow(sample, k_min=k_min, k_max=k_max, step=KMEANS_STEP, for_vid=False)
            kmeans = fu.get_kmeans(pixel_colors, num_clusts=elbow_k) # get new centroids (img)
    else:
        sample = pixel_colors[np.random.choice(len(pixel_colors), size=min(len(pixel_colors), KMEANS_SAMPLE_SIZE), replace=False)]
        kmeans.partial_fit(sample)

    labels = kmeans.predict(pixel_colors) # pixels to color clusters
    quantized = kmeans.cluster_centers_[labels].astype('uint8')
    quantized = quantized.reshape(smooth.shape)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    lower_th, upper_th = fu.get_canny_threshs(gray)
    sigma = fu.get_sigma(gray)
    if  for_video == True:
        edges = fu.get_edges(gray, CARTOON_EDGE_KERNEL_VID, lower_th * CARTOON_THRESH_MULT_VID, upper_th * CARTOON_THRESH_MULT_VID, sigma)
    else:
        edges = fu.get_edges(gray, CARTOON_EDGE_KERNEL_IMG, lower_th, upper_th, sigma)

    if for_video == True:
        edges = fu.smooth_edges(edges)

    cartoon_frame = quantized.copy()

    cartoon_frame[edges != 0] = (cartoon_frame[edges != 0] * DARK_FACTOR).astype(np.uint8)
    return cartoon_frame