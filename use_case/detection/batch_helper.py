from entity.bg_remover.engine import U2NetBGRemover
from entity.image_resizing.resizer import ImageResizer
from entity.shape_predictor.predictor import ShapePredictor
from entity.spot_detector.detector import SpotDetector
from entity.wing_detector.detector import WingDetector

from PIL import Image
import os
from os import listdir
from os.path import isfile, join
import numpy as np
import cv2
import pandas as pd
from typing import Optional

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

def image_resize_helper(resizer: ImageResizer, image_path: str, image_id: str, output_dir: str, format: str = "png") -> tuple[str, str]:
    """
    Resize a single image using the provided ImageResizer.
    Returns the output path of the resized image.
    """
    # read image by PIL
    img = Image.open(image_path)
    resized_image = resizer.resize(img)
    output_path = os.path.join(output_dir, f"{image_id}.{format}")
    resized_image.save(output_path)
    return (output_path, image_id)

def binary_alpha(image: Image.Image, alpha_threshold: int = 0) -> Image.Image:
    """Convert a 4-channel RGBA image to a binary 1-channel image based on alpha channel.

    Pixels with alpha > alpha_threshold are set to 255, and pixels with alpha <= alpha_threshold are set to 0.

    Args:
        image (PIL.Image.Image): Input RGBA image.
        alpha_threshold (int): Alpha threshold for binarization.

    Returns:
        PIL.Image.Image: Output binary image.
    """
    if image.mode != 'RGBA':
        raise ValueError("Input image must be in 'RGBA' mode.")
    
    # Convert image to numpy array
    img_array = np.array(image)
    
    # Create a binary mask based on the alpha channel
    alpha_channel = img_array[:, :, 3]
    binary_mask = np.where(alpha_channel > alpha_threshold, 255, 0).astype(np.uint8)

    # Convert back to PIL Image
    binary_image = Image.fromarray(binary_mask, mode='L')

    return binary_image

def bg_removal_helper(bg_remover: U2NetBGRemover, image_path: str, image_id: str, output_dir: str, format: str = "png") -> tuple[str, str]:
    """
    Remove background from a single image using the provided U2NetBGRemover.
    Returns the output path of the background-removed image.
    """
    img = Image.open(image_path)
    bg_removed_image = bg_remover.remove_bg(img)
    result_image = binary_alpha(bg_removed_image, alpha_threshold=200)
    output_path = os.path.join(output_dir, f"{image_id}.{format}")
    result_image.save(output_path)
    return (output_path, image_id)

def shape_predictor_helper(predictor: ShapePredictor, image_dir: str, output_xml_file: str, n_jobs: int) -> pd.DataFrame:
    """
    Predict landmarks for images in a given directory using the provided ShapePredictor.
    Returns a DataFrame with image IDs and their corresponding landmarks.
    """
    return predictor.predict(image_dir, output_xml_file, n_jobs=n_jobs)

def final_detection_helper(wing_detector: WingDetector, spot_detector: SpotDetector, wing_image_path: str, spot_image_path: str, image_id: str, landmark1: tuple[int, int], landmark2: tuple[int, int], output_dir: str, format: str = "png") -> dict[str, str]:
    """
    Detect wing contour from a single image using the provided WingDetector.
    Returns a dictionary with detection results and the output path.
    """
    # read in with openCV to get np.ndarray
    wing_image = cv2.imread(wing_image_path)
    spot_image = cv2.imread(spot_image_path)
    wing_contour = wing_detector.detect(wing_image, landmark1, landmark2)
    spot_contour = spot_detector.detect(spot_image, wing_contour)

    # draw the contours on spot_image for visualization
    output_image = spot_image.copy()
    cv2.drawContours(output_image, [wing_contour], -1, (255, 0, 0), 2)  # draw wing contour in blue
    if spot_contour is not None:
        cv2.drawContours(output_image, [spot_contour], -1, (0, 0, 255), 2)  # draw spot contour in red

    output_path = os.path.join(output_dir, f"{image_id}.{format}")
    cv2.imwrite(output_path, output_image)

    # return area of wing and spot as ints along with the output path
    wing_area = cv2.contourArea(wing_contour) if wing_contour is not None else 0
    spot_area = cv2.contourArea(spot_contour) if spot_contour is not None else 0
    return {
        "image_id": image_id,
        "wing_area": str(int(wing_area)),
        "spot_area": str(int(spot_area)),
        "spot_ratio": str(float(spot_area / wing_area)) if wing_area > 0 else "0.0"
    }