from os import listdir
from os.path import isfile, join
from typing import Optional
import cv2
import numpy as np
from PIL import Image

def images_from_path(path: str, full_path: bool = False, formats: Optional[list[str]] = ['.jpg', '.png', '.jpeg', '.bmp', '.tif', '.tiff']) -> Optional[list[str]]:
    """
    This function retrieves all image file paths from a given directory.

    Parameters:
        path (str): The directory path containing images.

    Returns:
        List[str]: A list of image file paths.
        file name includes the extension.
        List[tuple[str, str]]: A list of tuples containing the (full path, file name), if full_path is True.

    """
    onlyimages = [f for f in listdir(path) if isfile(join(path, f)) and any(f.lower().endswith(ext.lower()) for ext in formats)] # type: ignore
    return [(join(path, f), f) for f in onlyimages] if full_path else onlyimages # type: ignore

def find_contour(image: Optional[np.ndarray]) -> Optional[np.ndarray]:
    """Finds the largest contour in a given image.
    work on both PIL and cv2 images.
    Args:
        image (Optional[np.ndarray]): The input image in which to find contours.

    Returns:
        Optional[np.ndarray]: The largest contour found in the image, or None if no contours are found. In the format (N, 1, 2).
    """
    if isinstance(image, Image.Image):
        image = np.array(image)

    # check if image is None
    if image is None:
        return None
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # find contours
    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea) if contours else None
    return contour