import cv2
import numpy as np
from PIL import Image

def find_contour(image: np.ndarray | Image.Image) -> np.ndarray | None:
    """Finds the largest contour in a given image.
    work on both PIL and cv2 images.
    Args:
        image (np.ndarray | Image.Image): The input image in which to find contours.

    Returns:
        np.ndarray | None: The largest contour found in the image, or None if no contours are found. In the format (N, 1, 2).
    """
    if isinstance(image, Image.Image):
        image = np.array(image)

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # find contours
    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = max(contours, key=cv2.contourArea) if contours else None
    return contour

def crop_contour(contour: np.ndarray, point1: tuple[int, int], point2: tuple[int, int]) -> list[np.ndarray]:
    """
    If the straight line defined by point1 and point2 intersects the contour,
    return 2 contours split by the line. Else, return the original contour.

    Parameters:
        contour (np.ndarray): The input contour to be split.
        point1 (tuple[int, int]): The first point defining the line.
        point2 (tuple[int, int]): The second point defining the line.
    Returns:
        list[np.ndarray]: A list containing the split contours or the original contour.
    """
    # Convert points to numpy arrays
    p1 = np.array(point1, dtype=np.float32)
    p2 = np.array(point2, dtype=np.float32)

    # Create a large mask covering the contour
    x, y, w, h = cv2.boundingRect(contour)
    mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    shifted_contour = contour - (x, y)
    cv2.drawContours(mask, [shifted_contour], -1, color=255, thickness=-1)

    # shift p1 and p2
    p1 = p1 - np.array([x, y])
    p2 = p2 - np.array([x, y])

    # Create a mask for one side of the line
    yy, xx = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]
    # Equation of the line: (y2-y1)x - (x2-x1)y + (x2-x1)y1 - (y2-y1)x1 = 0
    side = (p2[1] - p1[1]) * xx - (p2[0] - p1[0]) * yy + (p2[0] - p1[0]) * p1[1] - (p2[1] - p1[1]) * p1[0]
    mask1 = (side > 0).astype(np.uint8) * mask
    mask2 = (side < 0).astype(np.uint8) * mask

    # Find contours on both sides
    contour1 = find_contour(mask1)
    contour2 = find_contour(mask2)

    # Only return split if both sides have a contour
    if contour1 is not None and contour2 is not None:
        # Shift contours back to original coordinates
        contour1 = contour1 + (x, y)
        contour2 = contour2 + (x, y)
        return [contour1, contour2]
    else:
        return [contour]