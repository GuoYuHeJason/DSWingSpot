<a id="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/GuoYuHeJason/spotSize">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">DSwingSpot</h3>

  <p align="center">
    project_description
    <br />
    <a href="https://github.com/GuoYuHeJason/spotSize"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/GuoYuHeJason/spotSize">View Demo</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
      </ul>
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

This program estimates the area of the wing and wing spot of drosophilla suzukii
For each image in the input folder,
the image is resized based on the scale bar on the image (req: shape, color and position of scale bar (param: scale bar length in micrometers)/ opt: input img_id: scale json file)
Then the program find an initial wing contour using ostu thresholding, canny contour detection and morphological operations
Using positional information from the initial wing contour and ostu thresholding, morphological operations, findContour, and original vein erasing alg: find contour and area of spot of the wing. (req: 2nd quadrant of the wing contour must be accurate)
using the initial wing contour, the program orient the wings to be in the same position (req: landmark 3 must be in the leftmost point on the estimated contour, the 2nd quadrant of the wing contour must be accurate)
Using correct positions (training points) of landmark 5 and landmark 12, the program estimates the position of landmark 5 and landmark 12 of each oriented wing (req: wing correctly oriented, correct training points, correct gender detection: males must have spots) (param: minimal |slope| of the line from landmark 5 to landmark 12)
The program draws a line between est landmark 5 and landmark 12 that is then corrected by minimal |slope|
The program cuts the initial contour based on the line between landmark 5 and landmark 12
The wing contour is then adjusted through an iterative process until it is approximately within the metrics range of the training contours.
The results are outputed into a json/txt/ file.
Can change some parameters and choose to skip male or female or a label if have a wing_documentation json file
(opt: the wing images with the final wing and wing spot contours drawn)

Training process (opt: use the default training points)
mannually measure the x, y positions of landmark 5 and landmark 12 for some images (around 20 - 30), convert the data to the approiate format (see default training landmarks, GitHub Copilot (or any LLM) does well in converting formats).
Or use the default landmarks.
Then from the input folder, the program random select (input number) of all images for you to check if well detected, press y to save contour to training data.
The program goes through the same detection procedure, without adjusting or smoothing.

In any detection procedure, if there is no wing_doc.json file in resources folder, the program generates one with gender information.
Before any detection procedure, you should ensure that the wing_doc.json file has all the wings you want to detect and is in the correct format; or there is no wing_doc.json file.



<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Prerequisites

* numpy
  ```sh
  pip install numpy
  ```

### Installation

2. Clone the repo
   ```sh
   git clone https://github.com/GuoYuHeJason/spotSize.git
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

### Top contributors:

<a href="https://github.com/GuoYuHeJason/spotSize/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=GuoYuHeJason/spotSize" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Project Link: [https://github.com/GuoYuHeJason/spotSize](https://github.com/GuoYuHeJason/spotSize)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>
