from abc import ABC, abstractmethod
import numpy as np

from .tools import find_spot_contour

class SpotDetector(ABC):
    def __init__(self, parameters: dict[str, float]) -> None:
        self.parameters = parameters

    @abstractmethod
    def detect(self, image: np.ndarray, wing_contour: np.ndarray) -> np.ndarray | None:
        """Abstract method to detect contours of spots in the given image."""
        pass

class AlgSpotDetector(SpotDetector):
    def detect(self, image: np.ndarray, wing_contour: np.ndarray) -> np.ndarray | None:
        """Returns the contours of spots in the given image."""
        spot_contour = find_spot_contour(image, wing_contour, 
                                         bin_thresh=int(self.parameters['bin_thresh']), 
                                         min_black_pixels=int(self.parameters['min_black_pixels']), 
                                         min_black_width=int(self.parameters['min_black_width']), 
                                         median_blur_ksize=int(self.parameters['median_blur_ksize']), 
                                         close_kernel_hori=int(self.parameters['close_kernel_hori']), 
                                         close_kernel_vert=int(self.parameters['close_kernel_vert']), 
                                         open_kernel_hori=int(self.parameters['open_kernel_hori']), 
                                         open_kernel_vert=int(self.parameters['open_kernel_vert']),
                                         cut_right_half=False)
        return spot_contour