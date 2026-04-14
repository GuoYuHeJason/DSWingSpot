# spot_contour

import cv2
import numpy as np
def image_preprocessing(
    image: np.ndarray,
    median_kernel_size: int = 5,
    unsharp_mask_kernel_size: int = 15,
    unsharp_mask_amount: float = 1.5) -> np.ndarray:
    """
    Preprocesses the input image by converting it to grayscale, applying median blur, and sharpening it using unsharp masking.
    Parameters:
        image (np.ndarray): The input image in BGR format.
        median_kernel_size (int): The size of the kernel for median blur. Must be an odd integer.
        unsharp_mask_kernel_size (int): The size of the kernel for unsharp masking. Must be an odd integer.
        unsharp_mask_amount (float): The amount of sharpening to apply.
    Returns:
        np.ndarray: The preprocessed grayscale image after median blur and sharpening.
    Raises:
        ValueError: If the kernel sizes are not odd integers.
    """
    # Image processing 
    # convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    # do median blur
    gray = cv2.medianBlur(gray, median_kernel_size)

    return gray
def shrink_hull(
    contour: np.ndarray,
    shrink_factor: float = 0.95
) -> np.ndarray:
    """
    Shrinks the contour by a specified factor using the convex hull.

    Parameters:
        contour (np.ndarray): Input contour to be shrunk. Should be a NumPy array of shape (N, 1, 2) or (N, 2).
        shrink_factor (float, optional): Factor by which to shrink the contour (0 < shrink_factor < 1). Default is 0.95.

    Returns:
        np.ndarray: Shrunk contour as a NumPy array of the same shape as the input.

    Raises:
        TypeError: If contour is not a np.ndarray.
        ValueError: If shrink_factor is not between 0 and 1.
    """

    hull = cv2.convexHull(contour)
    M = cv2.moments(hull)
    
    if M['m00'] == 0:
        return hull
    
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    
    shrunk_hull = []
    
    for point in hull:
        x, y = point[0]
        new_x = int(cx + (x - cx) * shrink_factor)
        new_y = int(cy + (y - cy) * shrink_factor)
        shrunk_hull.append([new_x, new_y])
    
    return np.array(shrunk_hull, dtype=np.int32)
def get_morphological_kernels(operation: str,
) -> tuple[np.ndarray, np.ndarray]:
    
    """
    Generates morphological operation kernels for closing and opening operations using OpenCV.
    Parameters:
        operation (str): The type of operation to perform. Options are 'wing' or 'spot'.
            - 'wing': Uses a rectangle kernel for closing and a larger rectangle kernel for opening.
            - 'spot': Uses an ellipse kernel for both closing and opening.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the closing kernel and the opening kernel as NumPy arrays.
    Raises:
        ValueError: If an invalid kernel shape is provided for either closing or opening.
    """
    if operation == 'wing':
        close_kernel_shape = 'ellipse'
        close_kernel_size = (15, 15)
        open_kernel_shape = 'ellipse'
        open_kernel_size = (25, 25)
    elif operation == 'spot':
        close_kernel_shape = 'ellipse'
        close_kernel_size = (7, 7)
        open_kernel_shape = 'ellipse'
        open_kernel_size = (15, 3)
    elif operation == 'final':
        close_kernel_shape = 'ellipse'
        close_kernel_size = (9, 9)
        open_kernel_shape = 'ellipse'
        open_kernel_size = (7, 7)
    else:
        raise ValueError("Invalid operation. Use 'wing' or 'spot'.")

    # get morphological operation kernels
    if close_kernel_shape == 'rectangle':
        close_kernel_shape = cv2.MORPH_RECT
    elif close_kernel_shape == 'ellipse':
        close_kernel_shape = cv2.MORPH_ELLIPSE
    elif close_kernel_shape == 'cross':
        close_kernel_shape = cv2.MORPH_CROSS
    else:
        raise ValueError("Invalid close kernel shape. Use 'rectangle', 'ellipse', or 'cross'.")
    
    if open_kernel_shape == 'rectangle':
        open_kernel_shape = cv2.MORPH_RECT
    elif open_kernel_shape == 'ellipse':    
        open_kernel_shape = cv2.MORPH_ELLIPSE
    elif open_kernel_shape == 'cross':
        open_kernel_shape = cv2.MORPH_CROSS
    else:
        raise ValueError("Invalid open kernel shape. Use 'rectangle', 'ellipse', or 'cross'.")

    close_kernel = cv2.getStructuringElement(close_kernel_shape, close_kernel_size)
    open_kernel = cv2.getStructuringElement(open_kernel_shape, open_kernel_size)

    return close_kernel, open_kernel
def binary_spot(image, bin_thresh: int) -> np.ndarray:
    #std image passed in
    gray = image_preprocessing(image)

    # get binary veins using adjustable binary threshold
    _, binary = cv2.threshold(gray, bin_thresh, 255, cv2.THRESH_BINARY)

    # invert the color
    binary = cv2.bitwise_not(binary)
    # """remember: background is black, object is white"""

    # erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    # eroded = cv2.erode(binary, erode_kernel, iterations=2)
    # # show the eroded image
    # cv2.imshow('eroded', eroded)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


    # do morphological operations to reduce noise
    open_kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, open_kernel, iterations=3)
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, open_kernel, iterations=2)
    # show the opened image

    # invert the color
    binary = cv2.bitwise_not(binary)

    # 
    return binary
# works, hard to change, doc may be wrong
def get_width_of_black_region(col, first):
    """
    Finds the width of the continuous black region in a given column of a binary image.

    Args:
        col (np.ndarray): A single column of the binary image with only black pixels
        first (int): The y-coordinate of the first black pixel in the column.

    Returns:
        int: Width of the continuous black region, or 0 if no black pixels are found.
        last (int): The y-coordinate of the last black pixel in the continuous region.
    """
    last = first
    for i in range(1, len(col)):
        if col[i] == last + 1: # if continuous, increment last
            last = col[i]
        else:
            break
    width = last - first
    return width, last

def find_spot_contour(
    image: np.ndarray,
    wing_contour: np.ndarray,
    bin_thresh: int,
    min_black_pixels: int,
    min_black_width: int,
    median_blur_ksize: int,
    close_kernel_hori: int,
    close_kernel_vert: int,
    open_kernel_hori: int,
    open_kernel_vert: int,
    median_blur_iterations: int = 5,
    contour_area_threshold: float = 10000,
    cut_right_half: bool = False,
    ostu_threshold: bool = True,
    adjust_bin_thresh: bool = False,
    upper_bound: int = 120000,
    softer_upper_bound: int = 90000,
    hard_upper_bound: int = 200000,
    scale_by: float = 0.9,
    iterations: int = 0,
) -> np.ndarray | None:
    """
    Finds the largest contour in a thresholded grayscale image, 
    which is the spot outline.

    Args:
        image (np.ndarray): Input BGR or grayscale image.
        wing_contour (np.ndarray): The contour of the wing to be used for further processing.
        bin_thresh (int): Threshold value for binarization.
        min_black_pixels (int): Minimum number of black pixels in a column to keep it.
        min_black_width (int): Minimum width of continuous black region to keep it.
        median_blur_iterations (int): Number of times to apply median blur.
        median_blur_ksize (int): Kernel size for median blur.
        contour_area_threshold (float): Minimum area for a valid contour.
        cut_right_half (bool): Whether to cut the right half of the image.
        contour_draw_color (tuple): Color to draw the contour.
        contour_draw_thickness (int): Thickness to draw the contour.
        harder_upper_bound (int): Area threshold above which the contour is considered too large to be valid, considered no spot or software error.
        upper_bound (int): Area threshold above which the contour is considered to be larger than expected, but may still be valid, return the contour if already tired long enough
        softer_upper_bound (int): Area threshold below which the contour is considered to be expected and acceptable, return the contour immediately.

    Returns:
        tuple: (contour, image)
            contour: The largest contour found.
            image: The original image with the contour drawn on it.
    """

    if ostu_threshold:
        # Apply Otsu's thresholding
        gray = image_preprocessing(image)
        _, bin_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    thresh = binary_spot(image, bin_thresh)

    # show_img = thresh.copy()
    # cv2.imshow('t',show_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # median blur the image to remove noise and close gaps in the spot
    for _ in range(median_blur_iterations):
        thresh = cv2.medianBlur(thresh, median_blur_ksize)
    
    # print the shape of the thresholded image
    # print(f"Thresholded image shape: {thresh.shape}")

    # for each x coordinate, find the number of continuous black pixels (value 0)
    for x in range(thresh.shape[1]):
        black_pixel_indices = np.nonzero(thresh[:, x] == 0)[0]
        if black_pixel_indices.size < min_black_pixels:
            thresh[:, x] = 255
        else:
            last = black_pixel_indices[0]
            final_black = black_pixel_indices[-1]
            while last < final_black:
                last_index = np.where(black_pixel_indices == last)[0][0]
                first_index = last_index + 1
                if first_index >= len(black_pixel_indices):
                    break
                first = black_pixel_indices[first_index]
                width, last = get_width_of_black_region(black_pixel_indices[first_index:], first)
                if width < min_black_width:
                    thresh[first - 1:last + 1, x] = 255
    
    # # for each y coordinate, find the number of continuous black pixels (value 0)
    # for y in range(thresh.shape[0]):
    #     black_pixel_indices = np.nonzero(thresh[y, :] == 0)[0]
    #     if black_pixel_indices.size < min_black_pixels:
    #         thresh[y, :] = 255
    #     else:
    #         last = black_pixel_indices[0]
    #         final_black = black_pixel_indices[-1]
    #         while last < final_black:
    #             last_index = np.where(black_pixel_indices == last)[0][0]
    #             first_index = last_index + 1
    #             if first_index >= len(black_pixel_indices):
    #                 break
    #             first = black_pixel_indices[first_index]
    #             width, last = get_width_of_black_region(black_pixel_indices[first_index:], first)
    #             if width < min_black_width:
    #                 thresh[y, first - 1:last + 1] = 255

    if cut_right_half:
        thresh = thresh[:, :thresh.shape[1] // 2]  # cut the right half of the image
    
    thresh = cv2.bitwise_not(thresh) # black to white, white to black, as findContours expects white regions on a black background

    # show_img = thresh.copy()
    # cv2.imshow('erase veins',show_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # mask the image (a round thinner than the wing contour, shrink the wing contour to the centroid)to remove the wing hairs.
    shrunk_hull = shrink_hull(wing_contour)
    mask = np.zeros_like(thresh)
    cv2.fillPoly(mask, [shrunk_hull], 255)  # fill the hull with white
    thresh = cv2.bitwise_and(thresh, mask)  # keep only the area inside the hull

    # close the gaps in the spot using morphological operations
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel_hori, close_kernel_vert))
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_kernel_hori, open_kernel_vert))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)
    opened = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, open_kernel)

    # show_img = opened.copy()
    # cv2.imshow('morph',show_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # find contours
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea) if contours else None

    # assess the contour area
    if contour is None or cv2.contourArea(contour) < contour_area_threshold:
        return None # original image with no contour found
    # if the contour is good, return it
    if not adjust_bin_thresh:
        return contour
    
    area = cv2.contourArea(contour)
    if area < softer_upper_bound or softer_upper_bound <= 0:
        return contour
    # if too long, return
    if iterations >= 10:
        if area < hard_upper_bound or hard_upper_bound <= 0:
            return contour
        else:
            return None
    if iterations >= 3:
        if area < upper_bound or upper_bound <= 0:
            return contour
        
    return find_spot_contour(image = image,
                    wing_contour = wing_contour,
                    bin_thresh = int(bin_thresh * scale_by),
                    min_black_pixels = min_black_pixels,
                    min_black_width = min_black_width,
                    median_blur_ksize = median_blur_ksize,
                    close_kernel_hori = close_kernel_hori,
                    close_kernel_vert = close_kernel_vert,
                    open_kernel_hori = open_kernel_hori,
                    open_kernel_vert = open_kernel_vert,
                    median_blur_iterations = median_blur_iterations,
                    contour_area_threshold = contour_area_threshold,
                    cut_right_half = cut_right_half,
                    upper_bound = upper_bound,
                    softer_upper_bound = softer_upper_bound,
                    hard_upper_bound = hard_upper_bound,
                    scale_by = scale_by,
                    iterations = iterations + 1)
        # iterate
        # find the spot on cut thresholded image, but draw the contour on the original image

    """uncomment the following lines to visualize the intermediate steps"""
    # cv2.drawContours(image, [contour], -1, contour_draw_color, contour_draw_thickness)
    # cv2.imshow('t',thresh)
    # cv2.waitKey(0)
    # cv2.imshow('final',image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

# if __name__ == "__main__":
    # # Test the functions here
    # from tools.cv_tools.images_from_path import images_from_path
    # from tools.cv_tools.contour import find_contour
    # input_path = "/Users/heguoyu/Desktop/wings/Maggie_Block_1"
    # image_paths = images_from_path(input_path, full_path=True)
    # for img_path, img_name in image_paths:
    #     image = cv2.imread(img_path)
    #     # Call your functions here
    #     contour = find_contour(image)
    #     if contour is not None:
    #         # Process the contour as needed
    #         spot_contour, _ = find_spot_contour(image, contour)
    #         if spot_contour is not None:
    #             # Do something with the spot contour
    #             # show
    #             output_image = image.copy()
    #             cv2.drawContours(output_image, [spot_contour], -1, (0, 255, 0), 3)
    #             cv2.imshow('Spot Contour', output_image)
    #             cv2.waitKey(0)
    #             cv2.destroyAllWindows()