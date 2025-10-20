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

def get_k_range(frame):
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    h, w = hsv.shape[:2]
    sample_size = min(10000, h * w)
    idxs = np.random.choice(h * w, size=sample_size, replace=False)
    pixel_sample = hsv.reshape(-1, 3)[idxs]

    hue_var = np.var(pixel_sample[:, 0])
    avg_sat = np.mean(pixel_sample[:, 1])
    unique_colors = len(np.unique(pixel_sample[:, 0]))

    if avg_sat < 30:
        k_min = 4
        k_max = 8
    elif hue_var < 500 or unique_colors < 20:
        k_min = 6
        k_max = 10
    elif hue_var < 1500:
        k_min = 8
        k_max = 14
    else:
        k_min = 12
        k_max = 24
    
    return k_min, k_max