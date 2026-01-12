# original scale resizing, and then compress the img as needed.

# the parameter passed in as # um per pixel.

import cv2
import numpy as np
from typing import Optional
from PIL import Image

def scale_bar(
    image: np.ndarray,
    template: np.ndarray,
    match_thresh: float=0.5,
    bin_thresh: float=15,
    bar_length: float=500,
    padding: int=30
) -> Optional[float]:
    """
    Detects a scale bar in the image using template matching.
    Since the magnification level varies between images, we measured the scale bar on the image and resize the image to 1 pixel per 1 micrometer. We assume that the scale bar is on the bottom right of the image and of high contrast between the image background. We find the scale bar using template matching algorithms through a sliding window cross-correlation operation and the assumption that the. The point on the response surface with response over the threshold and lowest x coordinate is deemed to be the leftmost point of the scale bar. We then crop the image accordingly and measure the contour of the scale bar.
    
    :param image: Input image where the scale bar is to be detected.
    :param template: Template image of the scale bar. (This should be a cropped, binary image of the scale bar.)
    :param match_thresh: Threshold for template matching.
    :param bar_length: Length of the scale bar in micrometers.
    :param padding: Padding around the detected template match.
    :return: Scale factor in micrometers per pixel, or None if not found.
    """
    # Convert images to grayscale

    # debug log: some images are loaded in empty (place holder image?)
    if image is None or image.size == 0:
        raise ValueError("Empty image")

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    # binarize the image
    _, gray_image = cv2.threshold(gray_image, bin_thresh, 255, cv2.THRESH_BINARY)
    _, gray_template = cv2.threshold(gray_template, bin_thresh, 255, cv2.THRESH_BINARY)

    # debugging:
    show_img = image.copy()

    # template matching
    res = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= match_thresh)
    # if match, crop to the scale bar
    if not (len(loc[0]) == 0 or len(loc[1]) == 0):
        # get the first location with the lowest x coordinate
        min_x_index = np.argmin(loc[1])
        pt = (loc[1][min_x_index], loc[0][min_x_index])
        # crop the image from the location of the template match with some padding
        gray_image = gray_image[pt[1] - padding:, pt[0] - padding:]
        # debugging:
        # crop the original image to the same area as the gray image
        show_img = show_img[pt[1] - padding:, pt[0] - padding:]
    else:
        # position filter: scale bar must be in the 4th quadrant
        # crop
        gray_image = gray_image[-show_img.shape[0] // 2:, -show_img.shape[1] // 2:]
        # debugging:
        show_img = show_img[-show_img.shape[0] // 2:, -show_img.shape[1] // 2:]

    # invert color
    gray_image = cv2.bitwise_not(gray_image)
    # find contours in the gray image
    contours, _ = cv2.findContours(gray_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # area filter: scale bar can't be too big, make the upper threshold 5000 pixels^2
    contours = [cnt for cnt in contours if cv2.contourArea(cnt) < 5000]

    if not contours:
        print("No scale bar found in the image.")
        return None

    # find the largest contour, which should be the scale bar
    largest_contour = max(contours, key=cv2.contourArea)
    # print(f"largest contour a aaaaaaaaaaaaaaaaaaaaaaaa aaa  a   aaa   area: {cv2.contourArea(largest_contour)}")
    # get the bounding rectangle of the largest contour
    x, y, w, h = cv2.boundingRect(largest_contour)

    # # debugging: draw contours on the original image
    # cv2.drawContours(show_img, [largest_contour], -1, (0, 255, 0), 3)
    # # draw the bounding rectangle on the original image
    # cv2.rectangle(show_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
    # # show the image with contours
    # cv2.imshow('Contours', show_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


    return bar_length / w if w > 0 else None  # scale factor in micrometers per pixel

def resize_image_based_on_scale(
    image: np.ndarray,
    scale_factor: float,
    target_scale: float=1.0
) -> np.ndarray:
    """
    Resizes the image based on the detected scale factor to achieve the target scale.
    
    :param image: Input image to be resized.
    :param scale_factor: Detected scale factor in micrometers per pixel.
    :param target_scale: Desired scale in micrometers per pixel.
    :return: Resized image.
    """
    if scale_factor is None:
        raise ValueError("Scale factor is None, cannot resize image.")

    resize_ratio = scale_factor / target_scale
    new_width = int(image.shape[1] * resize_ratio)
    new_height = int(image.shape[0] * resize_ratio)
    resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized_image

def scale_based_resizing(
    image: np.ndarray,
    template: np.ndarray,
    bar_length: float,
    target_scale: float,
    match_thresh: float=0.5,
    bin_thresh: float=15,
    padding: int=30
) -> np.ndarray:
    """
    Combines scale bar detection and image resizing based on the detected scale.
    
    :param image: Input image to be resized.
    :param template: Template image of the scale bar.
    :param match_thresh: Threshold for template matching.
    :param bar_length: Length of the scale bar in micrometers.
    :param padding: Padding around the detected template match.
    :param target_scale: Desired scale in micrometers per pixel.
    :return: Resized image.
    """
    scale_factor = scale_bar(
        image,
        template,
        match_thresh,
        bin_thresh,
        bar_length,
        padding
    )
    if scale_factor is None:
        raise ValueError("Scale bar could not be detected in the image.")
    
    resized_image = resize_image_based_on_scale(
        image,
        scale_factor,
        target_scale
    )
    return resized_image

def scale_PIL_adapter(
    input_image: Image.Image,
    template: Image.Image,
    bar_length: float,
    target_scale: float
) -> Image.Image:
    """
    Adapts the scale-based resizing function to work with PIL Image objects.
    
    :param input_image: Input PIL Image to be resized.
    :param template: Template image of the scale bar as a numpy array.
    :param match_thresh: Threshold for template matching.
    :param bar_length: Length of the scale bar in micrometers.
    :param padding: Padding around the detected template match.
    :param target_scale: Desired scale in micrometers per pixel.
    :return: Resized PIL Image.
    """
    # Convert PIL Image to numpy array
    image_np = np.array(input_image)
    template_np = np.array(template)

    # Perform scale-based resizing
    resized_image_np = scale_based_resizing(
        image_np,
        template_np,
        bar_length,
        target_scale
    )

    # Convert back to PIL Image
    resized_image_pil = Image.fromarray(resized_image_np)
    return resized_image_pil