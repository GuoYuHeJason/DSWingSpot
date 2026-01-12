import cv2
import numpy as np
from PIL import Image

from .tools import find_contour, crop_contour

class WingDetector:
    def detect(self, image: np.ndarray | Image.Image, landmark1: tuple[int, int], landmark2: tuple[int, int]) -> np.ndarray:
        """Returns the contour of a wing in the given image"""
        contour = find_contour(image)
        if contour is None:
            raise ValueError("No contour found in the image.")
        
        split_contours = crop_contour(contour, landmark1, landmark2)
        # if len(split_contours) != 2:
        #     raise ValueError("The contour could not be split into two parts.")
        
        # Return the larger contour as the wing
        wing_contour = max(split_contours, key=cv2.contourArea)
        return wing_contour
