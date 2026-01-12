from .scale_based_resizing import scale_PIL_adapter
from PIL import Image

class ImageResizer:
    def __init__(self, scale_bar_template: Image.Image, bar_length: float, target_scale: float):
        self.scale_bar_template = scale_bar_template
        self.bar_length = bar_length
        self.target_scale = target_scale

    def resize(self, image: Image.Image) -> Image.Image:
        return scale_PIL_adapter(
            input_image=image,
            template=self.scale_bar_template,
            bar_length=self.bar_length,
            target_scale=self.target_scale
        )
