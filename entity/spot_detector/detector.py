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
    @staticmethod
    def _to_bool(val) -> bool:
        """Convert 0/1, numeric, boolean or common string representations to bool."""
        try:
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return bool(int(val))
            if isinstance(val, str):
                v = val.strip().lower()
                if v in {"1", "true", "t", "yes", "y"}:
                    return True
                if v in {"0", "false", "f", "no", "n"}:
                    return False
            return False
        except Exception as e:
            return False

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
                                         adjust_bin_thresh=SpotDetector._to_bool(self.parameters['adjust_bin_thresh']),
                                         contour_area_threshold=int(self.parameters['min_spot_area']),
                                         wing_height_percentage_threshold=float(self.parameters['wing_height_percent']),
                                         left_most_point_adjustment=int(self.parameters['left_most_point_adjustment']),
                                         centroid_adjustment=int(self.parameters['centroid_adjustment']),
                                         scale_by=float(self.parameters['adjust_rate']),
                                         cut_right_half=True)
        return spot_contour