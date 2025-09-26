import numpy as np
import cv2 as cv

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
    grad_x = cv.Sobel(img, cv.CV_64F, 1, 0, ksize=1)
    grad_y = cv.Sobel(img, cv.CV_64F, 0, 1, ksize=1)
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
    blur = 3
    edges = get_edges(gray, blur, lower_th, upper_th, sigma)

    if bg_color == "White":
        sketch_frame = np.full_like(frame, 255)
    else:
        sketch_frame = np.full_like(frame, 0)
    sketch_frame[edges != 0] = frame[edges != 0]

    return sketch_frame

def get_cartoon_frame(frame, for_video=False):
    if for_video == False:
        frame = normalize_size(frame, max_side=1024)

    smooth = cv.bilateralFilter(frame, d=9, sigmaColor=150, sigmaSpace=75) 

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    lower_th, upper_th = get_canny_threshs(gray)
    sigma = get_sigma(gray)
    edges = get_edges(gray, 3, lower_th, upper_th, sigma)

    edges = cv.dilate(edges, np.ones((2,2), np.uint8), iterations=1)
    edges_inv = cv.bitwise_not(edges)

    cartoon_frame = cv.bitwise_and(smooth, smooth, mask=edges_inv)

    return cartoon_frame