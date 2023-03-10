import numpy as np
from PIL import Image

############### ---------- Basic Image Processing ------ ##############

# TODO 1: Read an Image and convert it into a floating point array with values between 0 and 1. You can assume a color image


def imread(filename):
    img = Image.open(filename)
    ans = np.array(img, dtype=np.float32) / 255.0
    return ans

# TODO 2: Convolve an image (m x n x 3 or m x n) with a filter(l x k). Perform "same" filtering. Apply the filter to each channel if there are more than 1 channels


def convolve(img, filt):
    matrix = np.zeros(img.shape)
    if img.ndim == 3:
        output = matrix
        for i in range(img.shape[2]):
            output[:, :, i] = convolve(img[:, :, i], filt)
        return output

    m = img.shape[0]
    n = img.shape[1]

    kernel = np.flip(filt)
    l = kernel.shape[0]
    k = kernel.shape[1]
    padding_x = l // 2
    padding_y = k // 2

    padded_img = np.zeros((m + padding_x * 2, n + padding_y * 2))
    padded_img[padding_x:m + padding_x, padding_y:n + padding_y] = img
    output = np.zeros((m, n))

    for i in range(m):
        for j in range(n):
            convol_img = padded_img[i:i+l, j:j+k]
            output[i, j] = np.sum(kernel * convol_img)

    return output

# TODO 3: Create a gaussian filter of size k x k and with standard deviation sigma


def gaussian_filter(k, sigma):
    center = k // 2
    x, y = np.mgrid[0:k, 0:k]

    # shift the coordinates of the arrays so that the center of the filter is at (0, 0)
    x = x - center
    y = y - center
    g = (1 / (2 * np.pi * sigma ** 2)) * \
        np.exp(-(x ** 2 + y ** 2) / (2 * sigma ** 2))
    ans = g / np.sum(g)
    return ans

# TODO 4: Compute the image gradient.
# First convert the image to grayscale by using the formula:
# Intensity = Y = 0.2125 R + 0.7154 G + 0.0721 B
# Then convolve with a 5x5 Gaussian with standard deviation 1 to smooth out noise.
# Convolve with [0.5, 0, -0.5] to get the X derivative on each channel
# convolve with [[0.5],[0],[-0.5]] to get the Y derivative on each channel
# Return the gradient magnitude and the gradient orientation (use arctan2)


def gradient(img):
    # convert to grayscale
    grayimg = 0.2125*img[:, :, 0] + 0.7154*img[:, :, 1] + 0.0721*img[:, :, 2]
    k = 5
    sigma = 1
    kernel = gaussian_filter(k, sigma)
    grayimg = convolve(grayimg, kernel)
    x_deriv = convolve(grayimg, [[0.5, 0, -0.5]])
    y_deriv = convolve(grayimg, [[0.5], [0], [-0.5]])
    return np.sqrt(x_deriv**2 + y_deriv**2), np.arctan2(y_deriv, x_deriv)


# ----------------Line detection----------------

# TODO 5: Write a function to check the distance of a set of pixels from a line parametrized by theta and c. The equation of the line is:
# x cos(theta) + y sin(theta) + c = 0
# The input x and y are numpy arrays of the same shape, representing the x and y coordinates of each pixel
# Return a boolean array that indicates True for pixels whose distance is less than the threshold


def check_distance_from_line(x, y, theta, c, thresh):
    num = np.abs(x * np.cos(theta) + y * np.sin(theta) + c)
    den = np.sqrt(np.cos(theta) ** 2 + np.sin(theta) ** 2)
    return (num/den) < thresh

# TODO 6: Write a function to draw a set of lines on the image.
# The `img` input is a numpy array of shape (m x n x 3).
# The `lines` input is a list of (theta, c) pairs.
# Mark the pixels that are less than `thresh` units away from the line with red color,
# and return a copy of the `img` with lines.


def draw_lines(img, lines, thresh):
    copy = np.copy(img)
    m, n, _ = img.shape
    for (theta, c) in lines:
        for i in range(m):
            for j in range(n):
                if check_distance_from_line(j, i, theta, c, thresh):
                    copy[i, j, 0] = 1
                    copy[i, j, 1] = 0
                    copy[i, j, 2] = 0
    return copy


# TODO 7: Do Hough voting. You get as input the gradient magnitude (m x n) and the gradient orientation (m x n),
# as well as a set of possible theta values and a set of possible c values.
# If there are T entries in thetas and C entries in cs, the output should be a T x C array.
# Each pixel in the image should vote for (theta, c) if:
# (a) Its gradient magnitude is greater than thresh1, **and**
# (b) Its distance from the (theta, c) line is less than thresh2, **and**
# (c) The difference between theta and the pixel's gradient orientation is less than thresh3


def hough_voting(gradmag, gradori, thetas, cs, thresh1, thresh2, thresh3):

    max_y, max_x = gradmag.shape
    y, x = np.where(gradmag > thresh1)
    y = np.clip(y, 0, max_y-1)
    x = np.clip(x, 0, max_x-1)
    tc_array = np.zeros((len(thetas), len(cs)))

    for ind_t, theta in enumerate(thetas):
        cond_c = (np.abs(gradori[y, x] - theta) < thresh3)
        for ind_c, c in enumerate(cs):
            cond_b = check_distance_from_line(x, y, theta, c, thresh2)
            tc_array[ind_t, ind_c] = np.sum(cond_b & cond_c, axis=0)

    return tc_array


# TODO 8: Find local maxima in the array of votes. A (theta, c) pair counts as a local maxima if:
# (a) Its votes are greater than thresh, **and**
# (b) Its value is the maximum in a nbhd x nbhd beighborhood in the votes array.
# The input `nbhd` is an odd integer, and the nbhd x nbhd neighborhood is defined with the
# coordinate of the potential local maxima placing at the center.
# Return a list of (theta, c) pairs.


def localmax(votes, thetas, cs, thresh, nbhd):
    max_list = []
    for ind_t, theta in enumerate(thetas):
        for ind_c, c in enumerate(cs):
            if votes[ind_t, ind_c] > thresh:
                vals = votes[max(0, ind_t - nbhd//2): min(len(thetas), ind_t + nbhd//2 + 1),
                             max(0, ind_c - nbhd//2): min(len(cs), ind_c + nbhd//2 + 1)]
                if votes[ind_t, ind_c] == np.max(vals):
                    max_list.append((theta, c))
    return max_list


# Final product: Identify lines using the Hough transform


def do_hough_lines(filename):

    # Read image in
    img = imread(filename)

    # Compute gradient
    gradmag, gradori = gradient(img)

    # Possible theta and c values
    thetas = np.arange(-np.pi-np.pi/40, np.pi+np.pi/40, np.pi/40)
    imgdiagonal = np.sqrt(img.shape[0]**2 + img.shape[1]**2)
    cs = np.arange(-imgdiagonal, imgdiagonal, 0.5)

    # Perform Hough voting
    votes = hough_voting(gradmag, gradori, thetas, cs, 0.1, 0.5, np.pi/40)

    # Identify local maxima to get lines
    lines = localmax(votes, thetas, cs, 20, 11)

    # Visualize: draw lines on image
    result_img = draw_lines(img, lines, 0.5)

    # Return visualization and lines
    return result_img, lines
