<a id="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/GuoYuHeJason/wing_spot_detection">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">DSwingSpot</h3>

  <p align="center">
    A tool for detecting and analyzing wing spots in Drosophila suzukii.
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
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

This program estimates the area of the wing and wing spot of Drosophila suzukii. It processes images to detect wing contours, predict landmarks, and analyze wing spots. The results are saved in JSON and CSV formats, and the program supports configurable parameters for landmarks and scale bar detection.

### Key Features:
- **Image Preprocessing**: Resize images based on a scale bar and remove backgrounds.
- **Landmark Prediction**: Predict landmarks using a shape predictor.
- **Wing and Spot Detection**: Detect wing contours and wing spots using advanced algorithms.
- **Parallel Processing**: Speed up processing using multi-threading.
- **Configurable Parameters**: Customize detection parameters for landmarks and scale bar length.
- **Generalization Support**: Train dlib models with manually labeled landmarks to measure general wing-like structures.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Prerequisites

- Python 3.10+
- Required Python packages:
  ```sh
  pip install -r requirements.txt
  ```

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/GuoYuHeJason/wing_spot_detection.git
   ```
2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage


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

- [PyQt5](https://riverbankcomputing.com/software/pyqt/intro)
- [OpenCV](https://opencv.org/)
- [NumPy](https://numpy.org/)
- [Pandas](https://pandas.pydata.org/)
- [Dlib](http://dlib.net/)
- [PyTorch](https://pytorch.org/)
- [Pillow](https://python-pillow.org/)
- [Joblib](https://joblib.readthedocs.io/)
- [U-2-Net] (https://github.com/xuebinqin/U-2-Net)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
