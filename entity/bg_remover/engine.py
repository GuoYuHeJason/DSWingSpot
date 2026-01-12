import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from .u2net import utils, model

class U2NetBGRemover:
    def __init__(self, model_path):
        self.model_pred = model.U2NET(3, 1)
        self.model_pred.load_state_dict(torch.load(model_path, map_location="cpu"))
        self.model_pred.eval()

    def _norm_pred(self, d):
        ma = torch.max(d)
        mi = torch.min(d)
        dn = (d - mi) / (ma - mi)
        return dn

    def _preprocess(self, image):
        label_3 = np.zeros(image.shape)
        label = np.zeros(label_3.shape[0:2])

        if 3 == len(label_3.shape):
            label = label_3[:, :, 0]
        elif 2 == len(label_3.shape):
            label = label_3

        if 3 == len(image.shape) and 2 == len(label.shape):
            label = label[:, :, np.newaxis]
        elif 2 == len(image.shape) and 2 == len(label.shape):
            image = image[:, :, np.newaxis]
            label = label[:, :, np.newaxis]

        transform = transforms.Compose([utils.RescaleT(320), utils.ToTensorLab(flag=0)])
        sample = transform({"imidx": np.array([0]), "image": image, "label": label})

        return sample

    def _remove(self, image):
        sample = self._preprocess(np.array(image))
        with torch.no_grad():
            inputs_test = torch.FloatTensor(sample["image"].unsqueeze(0).float())
            d1, _, _, _, _, _, _ = self.model_pred(inputs_test)
            pred = d1[:, 0, :, :]
            predict = self._norm_pred(pred).squeeze().cpu().detach().numpy()
            img_out = Image.fromarray(predict * 255).convert("RGB")
            image = image.resize((img_out.size), resample=Image.BILINEAR)
            empty_img = Image.new("RGBA", (image.size), 0)
            img_out = Image.composite(image, empty_img, img_out.convert("L"))

        return img_out

    def _remove_bg_mult(self, image):
        img_out = image.copy()
        for _ in range(4):
            img_out = self._remove(img_out)

        img_out = img_out.resize((image.size), resample=Image.BILINEAR)
        empty_img = Image.new("RGBA", (image.size), 0)
        img_out = Image.composite(image, empty_img, img_out)
        return img_out
    
    def remove_bg(self, image: Image.Image) -> Image.Image:
        """Removes the background from the input image using U-2-Net model.
        Wrapper function.
        Args:
            image (Image.Image): The input PIL Image from which to remove the background.
        Returns:
            Image.Image: The PIL Image with the background removed, max 4 channels."""
        return self._remove_bg_mult(image)
