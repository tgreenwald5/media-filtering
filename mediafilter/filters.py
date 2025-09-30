import numpy as np
import cv2 as cv
from sklearn.cluster import MiniBatchKMeans
from collections import deque

def normalize_size(img, max_side=1024):
    h, w = img.shape[:2]
    if max(h, w) <= max_side:
        return img
    scale = max_side / max(h, w)
    norm_w = max(1, int(w * scale))
    norm_h = max(1, int(h * scale))
    norm_img = cv.resize(img, (norm_w, norm_h), interpolation=cv.INTER_AREA)
    return norm_img

def get_canny_threshs(img):
    grad_x = cv.Sobel(img, cv.CV_64F, 1, 0, ksize=3)
    grad_y = cv.Sobel(img, cv.CV_64F, 0, 1, ksize=3)
    grad_mag = cv.magnitude(grad_x, grad_y)
    med = float(np.median(grad_mag))
    lower = int(max(0, min(0.66 * med, 255)))
    upper = int(max(0, min(1.33 * med, 255)))
    if upper <= lower:
        upper = min(lower + 20, 255)
    return lower, upper

def get_sigma(img):
    sharpness = cv.Laplacian(img, cv.CV_64F).var()
    base_sigma = 1.5
    if sharpness > 500:    
        return base_sigma * 2.5
    elif sharpness > 200:
        return base_sigma * 1.5
    else:
        return base_sigma

def get_edges(img, k_size, lower_th, upper_th, sigma):
    k_size = max(3, k_size | 1)
    blur_img = cv.GaussianBlur(img, (k_size, k_size), sigma)
    edges = cv.Canny(blur_img, lower_th, upper_th)
    return edges

def get_sketch_frame(frame, bg_color, for_video=False):
    if for_video == False:
        frame = normalize_size(frame, max_side=1024)
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_th, upper_th = get_canny_threshs(gray)
    sigma = get_sigma(gray)
    blur = 5
    edges = get_edges(gray, blur, lower_th, upper_th, sigma)

    if bg_color == "White":
        sketch_frame = np.full_like(frame, 255)
    else:
        sketch_frame = np.full_like(frame, 0)
    sketch_frame[edges != 0] = frame[edges != 0]

    return sketch_frame

# fit new kmeans with new color centroids
def get_kmeans(pix_colors, num_clusts):
    new_kmeans = MiniBatchKMeans(n_clusters=num_clusts, random_state=0, batch_size=3000)
    new_kmeans.fit(pix_colors)
    return new_kmeans

# reduce edge flickering in video
edge_buffer = deque(maxlen=10)
def smooth_edges(curr_edges, blend_weight=0.3):
    global edge_buffer
    edge_buffer.append(curr_edges.astype(np.float32))
    if len(edge_buffer) == 1:
        return curr_edges
    
    smoothed = blend_weight * edge_buffer[-1]
    remaining_weight = (1 - blend_weight) / (len(edge_buffer) - 1)
    for i in range(len(edge_buffer) - 1):
        smoothed += remaining_weight * edge_buffer[i]
    
    return (smoothed > 127).astype(np.uint8) * 255

kmeans = None
def get_cartoon_frame(frame, frame_idx, for_video=False):
    global kmeans
    if for_video == False:
        frame = normalize_size(frame, max_side=1280)

    smooth = cv.bilateralFilter(frame, d=6, sigmaColor=150, sigmaSpace=75)
    pixel_colors = smooth.reshape((-1, 3)) 

    rt_every_frame = 30 # retrain and update color centroids every n frames
    if kmeans == None or frame_idx % rt_every_frame == 0: # if kmeans not created or time for new fitting
        if for_video == True:
            sample = pixel_colors[np.random.choice(len(pixel_colors), size=5000, replace=False)]
            elbow_k = get_k_elbow(sample, k_min=24, k_max=64, step=4)
            kmeans = get_kmeans(pixel_colors, num_clusts=elbow_k) # get new centroids (video)
        else:
            sample = pixel_colors[np.random.choice(len(pixel_colors), size=200000, replace=False)]
            elbow_k = get_k_elbow(sample, k_min=24, k_max=64, step=4)
            kmeans = get_kmeans(pixel_colors, num_clusts=elbow_k) # get new centroids (img)

    labels = kmeans.predict(pixel_colors) # pixels to color clusters
    quantized = kmeans.cluster_centers_[labels].astype('uint8')
    quantized = quantized.reshape(smooth.shape)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_th, upper_th = get_canny_threshs(gray)
    sigma = get_sigma(gray)
    edges = get_edges(gray, 5, lower_th * 1.5, upper_th * 1.5, sigma)
    edges = cv.dilate(edges, np.ones((2,2), np.uint8), iterations=1)

    if for_video == True:
        edges = smooth_edges(edges)

    cartoon_frame = quantized.copy()
    df = 0.5  # larger value -> lighter edges 
    cartoon_frame[edges != 0] = (cartoon_frame[edges != 0] * df).astype(np.uint8)

    return cartoon_frame

# calc number of clusters to use for kmeans
def get_k_elbow(pix_colors, k_min, k_max, step):
    inertias = []
    ks = range(k_min, k_max + 1, step)
    for k in ks:
        kmeans = MiniBatchKMeans(n_clusters=k, random_state=0, batch_size=10000)
        kmeans.fit(pix_colors)
        inertias.append(kmeans.inertia_)
    diffs = np.diff(inertias)
    elbow_idx = np.argmin(diffs)
    return ks[elbow_idx]