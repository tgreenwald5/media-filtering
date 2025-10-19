import numpy as np
import cv2 as cv
from sklearn.cluster import MiniBatchKMeans
from collections import deque
from kneed import KneeLocator
from mediafilter.constants import *

def normalize_size(img):
    h, w = img.shape[:2]
    if max(h, w) <= IMAGE_MAX_SIDE:
        return img
    scale = IMAGE_MAX_SIDE / max(h, w)
    norm_w = max(1, int(w * scale))
    norm_h = max(1, int(h * scale))
    norm_img = cv.resize(img, (norm_w, norm_h), interpolation=cv.INTER_AREA)
    return norm_img

def get_canny_threshs(img): # thresholds for edge detection 
    grad_x = cv.Sobel(img, cv.CV_64F, 1, 0, ksize=3)
    grad_y = cv.Sobel(img, cv.CV_64F, 0, 1, ksize=3)
    grad_mag = cv.magnitude(grad_x, grad_y)
    med = float(np.median(grad_mag))
    lower = int(max(0, min(CANNY_LOWER_RATIO * med, 255)))
    upper = int(max(0, min(CANNY_UPPER_RATIO * med, 255)))
    if upper <= lower:
        upper = min(lower + CANNY_FALLBACK_INC, 255)
    return lower, upper

def get_sigma(img): # calculate how much blur to use for gaussianBlur
    sharpness = cv.Laplacian(img, cv.CV_64F).var()
    base_sigma = GAUS_BASE_SIGMA
    if sharpness > GAUS_SIGMA_THRESH_HIGH:    
        return base_sigma * GAUS_SIGMA_MULT_HIGH
    elif sharpness > GAUS_SIGMA_THRESH_MED:
        return base_sigma * GAUS_SIGMA_MULT_MED
    else:
        return base_sigma

def get_edges(img, k_size, lower_th, upper_th, sigma):
    k_size = max(MIN_BLUR_KERNEL, k_size | 1)
    blur_img = cv.GaussianBlur(img, (k_size, k_size), sigma)
    edges = cv.Canny(blur_img, lower_th, upper_th)
    return edges

def get_sketch_frame(frame, bg_color, for_video=False):
    if for_video == False:
        frame = normalize_size(frame)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_th, upper_th = get_canny_threshs(gray)
    sigma = get_sigma(gray)
    edges = get_edges(gray, SKETCH_BLUR, lower_th * SKETCH_THRESH_MULT, upper_th * SKETCH_THRESH_MULT, sigma)
    if for_video == True:
        edges = smooth_edges(edges)
        
    if bg_color == "White":
        sketch_frame = np.full_like(frame, 255)
    else:
        sketch_frame = np.full_like(frame, 0)
    sketch_frame[edges != 0] = frame[edges != 0]

    return sketch_frame

# fit new kmeans with new color centroids
def get_kmeans(pix_colors, num_clusts):
    new_kmeans = MiniBatchKMeans(n_clusters=num_clusts, random_state=0, batch_size=KMEANS_BATCH_FIT, n_init="auto")
    new_kmeans.fit(pix_colors)
    return new_kmeans

# reduce edge flickering in video
edge_buffer = deque(maxlen=EDGE_BUFFER_LEN)
def smooth_edges(curr_edges, min_weight=EDGE_MIN_WEIGHT, max_weight=EDGE_MAX_WEIGHT): # small weight -> more past frame influence
    global edge_buffer
    curr_edges = curr_edges.astype(np.float32)

    if len(edge_buffer) == 0:
        edge_buffer.append(curr_edges)
        return curr_edges.astype(np.uint8)
    
    prev_smoothed = edge_buffer[-1] # get last frame edges
    edge_diff = np.mean(cv.absdiff(curr_edges.astype(np.uint8), prev_smoothed.astype(np.uint8)))
    motion = edge_diff / 255.0

    blend_weight = min_weight + (max_weight - min_weight) * motion # more motion -> larger weight -> less past frame influence

    edge_buffer.append(curr_edges)

    smoothed = blend_weight * edge_buffer[-1]
    remaining_weight = (1 - blend_weight) / (len(edge_buffer) - 1)
    for i in range(len(edge_buffer) - 1):
        smoothed += remaining_weight * edge_buffer[i]
    smoothed = np.clip(smoothed, 0, 255).astype(np.uint8)
    return smoothed
    

kmeans = None
def get_cartoon_frame(frame, frame_idx, for_video=False):
    global kmeans
    if for_video == False:
        frame = normalize_size(frame)

    smooth = cv.bilateralFilter(frame, d=BILATERAL_D, sigmaColor=BILATERAL_SIGMA_COLOR, sigmaSpace=BILATERAL_SIGMA_SPACE)
    pixel_colors = smooth.reshape((-1, 3)) 

    if kmeans == None or frame_idx % KMEANS_RETRAIN_INTERVAL == 0: # if kmeans not created or time for new fitting
        if for_video == True:
            sample = pixel_colors[np.random.choice(len(pixel_colors), size=KMEANS_SAMPLE_SIZE, replace=False)]
            elbow_k = get_k_elbow(sample, k_min=KMEANS_K_MIN, k_max=KMEANS_K_MAX, step=4, for_vid=True)
            kmeans = get_kmeans(pixel_colors, num_clusts=elbow_k) # get new centroids (video)
        else:
            sample = pixel_colors[np.random.choice(len(pixel_colors), size=KMEANS_SAMPLE_SIZE, replace=False)]
            elbow_k = get_k_elbow(sample, k_min=KMEANS_K_MIN, k_max=KMEANS_K_MAX, step=4, for_vid=False)
            kmeans = get_kmeans(pixel_colors, num_clusts=elbow_k) # get new centroids (img)

    labels = kmeans.predict(pixel_colors) # pixels to color clusters
    quantized = kmeans.cluster_centers_[labels].astype('uint8')
    quantized = quantized.reshape(smooth.shape)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    lower_th, upper_th = get_canny_threshs(gray)
    sigma = get_sigma(gray)
    if  for_video == True:
        edges = get_edges(gray, CARTOON_EDGE_KERNEL_VID, lower_th * CARTOON_THRESH_MULT_VID, upper_th * CARTOON_THRESH_MULT_VID, sigma)
    else:
        edges = get_edges(gray, CARTOON_EDGE_KERNEL_IMG, lower_th, upper_th, sigma)

    if for_video == True:
        edges = smooth_edges(edges)

    cartoon_frame = quantized.copy()

    cartoon_frame[edges != 0] = (cartoon_frame[edges != 0] * DARK_FACTOR).astype(np.uint8)

    return cartoon_frame

# calc number of clusters to use for kmeans
def get_k_elbow(pix_colors, k_min, k_max, step, for_vid):
    inertias = []
    ks = range(k_min, k_max + 1, step)
    if for_vid == True:
        bs = KMEANS_BATCH_VID
    else:
        bs = KMEANS_BATCH_IMG
    for k in ks:
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=0, batch_size=bs, n_init="auto")
        kmeans.fit(pix_colors)
        inertias.append(kmeans.inertia_)

    kl = KneeLocator(ks, inertias, curve="convex", direction="decreasing")
    best_k = kl.knee
    if best_k == None:
        best_k = ks[len(ks) // 2]
    return best_k