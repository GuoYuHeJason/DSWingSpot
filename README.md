<a id="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/GuoYuHeJason/wing_spot_detection">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">DSwingSpot</h3>

  <p align="center">
    A tool for detecting and analyzing wings and wing spots of Drosophila suzukii and other winged insects.
    <br />
    <a href="https://github.com/GuoYuHeJason/wing_spot_detection"><strong>Explore the docs »</strong></a>
    <br />
    <br />
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li>
      <a href="#inputs">Inputs</a>
      <ul>
        <li><a href="#required-files">Required Files</a></li>
        <li><a href="#parameters">Parameters</a></li>
      </ul>
    </li>
    <li><a href="#processing-pipeline">Processing Pipeline</a></li>
    <li><a href="#output">Output</a></li>
    <li><a href="#troubleshooting">Troubleshooting</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

DSwingSpot is a desktop application that estimates the area of wings and wing spots of *Drosophila suzukii* and other winged insects. It uses image processing and machine learning techniques to automatically detect wing contours, predict anatomical landmarks, and analyze wing spots from microscopy images.

### Key Features

- **Automatic Scale Calibration**: Detects scale bars in images and normalizes measurements to real-world units (micrometers).
- **Background Removal**: Uses U²-Net deep learning model to isolate wings from image backgrounds.
- **Landmark Prediction**: Predicts anatomical landmarks using dlib shape predictor models.
- **Wing and Spot Detection**: Detects wing contours and wing spots using computer vision algorithms.
- **Batch Processing**: Process multiple images at once with parallel multi-threading support.
- **Configurable Parameters**: Customize detection parameters for different specimen types or imaging conditions.
- **Extensibility**: Train custom dlib models with manually labeled landmarks to measure general wing-like structures.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Installation

#### From Source

##### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Recommended: A virtual environment (venv, conda, etc.)

1. Clone the repository:
   ```sh
   git clone https://github.com/GuoYuHeJason/wing_spot_detection.git
   cd wing_spot_detection
   ```

2. (Optional) Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Download the required assets (model files):
   - Download `assets.zip` from the [Releases](https://github.com/GuoYuHeJason/DSwingSpot/releases/tag/v1.0.0_wins) page
   - Extract the contents to a known location on your system

#### macOS

1. Download the binary release for macOS 
   - Download `DSwingSpot.zip` from the [Releases](https://github.com/GuoYuHeJason/DSwingSpot/releases/tag/v1.0.0_mac) page
   - Extract the contents to a known location on your system

4. Download the required assets (model files):
   - Download `assets.zip` from the [Releases](https://github.com/GuoYuHeJason/DSwingSpot/releases/tag/v1.0.0_mac) page
   - Extract the contents to a known location on your system

#### Windows

1. Download the binary release for Windows 
   - Download `DSwingSpot.zip` from the [Releases](https://github.com/GuoYuHeJason/DSwingSpot/releases/tag/v1.0.0_win) page
   - Extract the contents to a known location on your system

4. Download the required assets (model files):
   - Download `assets.zip` from the [Releases](https://github.com/GuoYuHeJason/DSwingSpot/releases/tag/v1.0.0_win) page
   - Extract the contents to a known location on your system

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### Running the Application

1. Start the application:
   ```sh
   python main.py
   ```
   or run the executable DSwingSpot.exe if you downloaded a binary release.

2. In the GUI, configure the following:

   **Paths:**
   - **Input Path**: Directory containing your wing images (supports common formats: PNG, JPG, TIFF)
   - **Output Path**: Directory where results will be saved

   **Asset Files:**
   - **Shape Predictor**: Path to the `.dat` model file
   - **Background Removal Model**: Path to the `.pth` model file
   - **Scale Bar Template**: Path to your scale bar template image

   **Parameters:**
   - Adjust parameters as needed for your specific images (see [Parameters](#parameters) section)

3. Click the **Detect** button to start processing.

4. Monitor progress in the application. Upon completion, results will be saved to the output directory.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- INPUTS -->
## Inputs

### Required Files

The application requires the following asset files to be provided:

| File | Description |
|------|-------------|
| **Shape Predictor Model** (`.dat`) | A dlib shape predictor model trained to detect anatomical landmarks on wings. Included in `assets.zip`. |
| **Background Removal Model** (`.pth`) | A U²-Net model for background segmentation. Included in `assets.zip`. |
| **Scale Bar Template** (image file) | A cropped, high-contrast image of the scale bar from your microscope. Used for template matching to detect scale bars in input images. |

### Parameters

The following parameters can be configured in the application:

#### Scale & Measurement Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `bar_length` | The real-world length of the scale bar in micrometers (μm) | `500` for a 500μm scale bar |
| `target_scale` | The target scale ratio for output measurements. Set to `1` to measure areas in μm² | `1` |

#### Landmark Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `landmark1` | Index of the first landmark used to split the wing contour | `3` |
| `landmark2` | Index of the second landmark used to split the wing contour | `8` |

#### Spot Detection Parameters

| Parameter | Description | Recommended Range |
|-----------|-------------|-------------------|
| `bin_thresh` | Binary threshold for spot detection. Lower values detect larger spots | `100` - `130` |
| `min_black_pixels` | Minimum number of dark pixels to qualify as a spot | Varies by image |
| `min_black_width` | Minimum width of dark region to qualify as a spot | Varies by image |
| `median_blur_ksize` | Kernel size for median blur preprocessing | Odd numbers (3, 5, 7) |
| `close_kernel_hori` | Horizontal kernel size for morphological closing | Varies by image |
| `close_kernel_vert` | Vertical kernel size for morphological closing | Varies by image |
| `open_kernel_hori` | Horizontal kernel size for morphological opening | Varies by image |
| `open_kernel_vert` | Vertical kernel size for morphological opening | Varies by image |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- PROCESSING PIPELINE -->
## Processing Pipeline

DSwingSpot processes images through the following stages:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HIGH-LEVEL PROCEDURE                            │
└─────────────────────────────────────────────────────────────────────────┘

1. IMAGE LOADING
   └── Load images from the input directory

2. SCALE CALIBRATION & RESIZING
   └── Detect scale bar using template matching
   └── Resize images to normalize pixel-to-micrometer ratio

3. BACKGROUND REMOVAL
   └── Apply U²-Net model to segment the wing from the background
   └── Output: transparent PNG with isolated wing

4. LANDMARK PREDICTION
   └── Run dlib shape predictor on background-removed images
   └── Identify anatomical landmarks on the wing

5. WING DETECTION
   └── Extract wing contour from the segmented image
   └── Split contour at landmark points to isolate the wing region

6. SPOT DETECTION
   └── Apply thresholding and morphological operations
   └── Detect dark spots within the wing region

7. AREA CALCULATION
   └── Calculate wing area from contour
   └── Calculate spot area from detected spots
   └── Compute spot-to-wing ratio

8. OUTPUT GENERATION
   └── Save results to CSV and JSON files
   └── Save debug images (landmarks, contours) to output directory
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- OUTPUT -->
## Output

The application generates the following output files:

| File | Description |
|------|-------------|
| `wing_spot_results.csv` | Tabular results with image ID, wing area, spot area, and spot ratio |
| `wing_spot_results.json` | Same results in JSON format |
| `landmarks_debug.csv` | Predicted landmark coordinates for each image (useful for debugging) |
| Debug images | Annotated images showing detected contours and landmarks (in output directory) |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- TROUBLESHOOTING -->
## Troubleshooting

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| **"No scale bar detected"** | Scale bar template doesn't match | Create a new scale bar template image cropped from one of your input images |
| **Poor background segmentation** | U²-Net model not suited for your images | Train a custom U²-Net model on your image type, or manually edit images |
| **Incorrect wing cropping** | Landmark prediction is inaccurate | Train a new dlib shape predictor model with manually labeled landmarks from your images |
| **Spots not detected / over-detected** | `bin_thresh` parameter needs adjustment | Increase `bin_thresh` (100-130) to detect fewer/smaller spots; decrease for more/larger spots |
| **Spots not detected / spot cropped in half** | Wing position/orientation issue | Tip of the wing needs to be on left side, remove excessive white space so that the wing is approximately centered|
| **Application crashes on start** | Missing dependencies | Ensure all packages in `requirements.txt` are installed correctly |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

Project Link: [https://github.com/GuoYuHeJason/wing_spot_detection](https://github.com/GuoYuHeJason/wing_spot_detection)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

- [PyQt5](https://riverbankcomputing.com/software/pyqt/intro) - GUI framework
- [OpenCV](https://opencv.org/) - Computer vision library
- [NumPy](https://numpy.org/) - Numerical computing
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [Dlib](http://dlib.net/) - Machine learning and shape prediction
- [PyTorch](https://pytorch.org/) - Deep learning framework
- [Pillow](https://python-pillow.org/) - Image processing
- [Joblib](https://joblib.readthedocs.io/) - Parallel processing
- [U²-Net](https://github.com/xuebinqin/U-2-Net) - Background removal model
- [scikit-image](https://scikit-image.org/) - Image processing algorithms

<p align="right">(<a href="#readme-top">back to top</a>)</p>
