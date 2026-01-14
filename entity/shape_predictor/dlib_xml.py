import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import numpy as np 
import pandas as pd
import cv2
import dlib
from .tools import images_from_path
from .tools import find_contour
from joblib import Parallel, delayed
# dlib xml tools
# Tools for predicting objects and shapes in new images

def predictions_to_xml(detector_name: str, predictor_name: str, dir='pred', upsample=0, threshold=0, ignore=None, out_file='output_prediction.xml', n_jobs=-1):
    """
    Generates a dlib format xml file for model predictions using multi-threading.

    Parameters:
        detector_name (str): object detector filename
        predictor_name (str): shape predictor filename
        dir (str): (optional) name of the directory containing images to be predicted
        upsample (int): (optional) number of times that an image should be upsampled (max=2 times)
        threshold (float): (optional) confidence threshold. Objects detected with lower confidence than 
                          the threshold are not output
        ignore (list): list of landmarks that should be ignored (based on landmark numeric id)
        out_file (str): name of the output file (xml format)
        n_jobs (int): Number of parallel jobs to run (-1 uses all available cores)

    Returns:
        None (out_file written to disk)
    """
    predictor = dlib.shape_predictor(predictor_name)
    detector = dlib.fhog_object_detector(detector_name)

    root = ET.Element('dataset')
    root.append(ET.Element('name'))
    root.append(ET.Element('comment'))
    images_e = ET.Element('images')
    root.append(images_e)

    def process_image(image_path):
        path, file = os.path.split(image_path)
        img = cv2.imread(image_path)
        image_e = ET.Element('image')
        image_e.set('file', str(image_path))
        [boxes, confidences, detector_idxs] = dlib.fhog_object_detector.run(
            detector, img, upsample_num_times=upsample, adjust_threshold=threshold)
        for k, d in enumerate(boxes):
            shape = predictor(img, d)
            box = ET.Element('box')
            box.set('top', str(int(d.top())))
            box.set('left', str(int(d.left())))
            box.set('width', str(int(d.right() - d.left())))
            box.set('height', str(int(d.bottom() - d.top())))
            for i in range(0, shape.num_parts):
                if ignore is not None:
                    if i not in ignore:
                        part = ET.Element('part')
                        part.set('name', str(int(i)))
                        part.set('x', str(int(shape.part(i).x)))
                        part.set('y', str(int(shape.part(i).y)))
                        box.append(part)
                else:
                    part = ET.Element('part')
                    part.set('name', str(int(i)))
                    part.set('x', str(int(shape.part(i).x)))
                    part.set('y', str(int(shape.part(i).y)))
                    box.append(part)

            image_e.append(box)
        return image_e

    # Retrieve image paths using images_from_path
    image_paths = images_from_path(dir, full_path=True)

    # check for none
    if image_paths is None:
        raise ValueError(f"No images found in directory: {dir}")

    # Process images in parallel
    processed_images = Parallel(n_jobs=n_jobs, backend='threading')(delayed(process_image)(image_path[0]) for image_path in image_paths)

    # Append processed images to the XML structure
    for image_e in processed_images:
        images_e.append(image_e) # type: ignore

    # Write XML to file
    et = ET.ElementTree(root)
    xmlstr = minidom.parseString(ET.tostring(et.getroot())).toprettyxml(indent="   ") # type: ignore
    with open(out_file, "w") as f:
        f.write(xmlstr)

def predictions_to_xml_with_contour(predictor_name: str, images: str, out_file: str, n_jobs: int):
    """
    Generates a dlib format xml file for model predictions using contours and bounding boxes.

    Parameters:
        predictor_name (str): shape predictor filename
        images (str): (optional) name of the directory containing images to be predicted
        ignore (list): list of landmarks that should be ignored (based on landmark numeric id)
        out_file (str): name of the output file (xml format)
        n_jobs (int): Number of parallel jobs to run (-1 uses all available cores)

    Returns:
        None (out_file written to disk)
    """
    predictor = dlib.shape_predictor(predictor_name)

    root = ET.Element('dataset')
    root.append(ET.Element('name'))
    root.append(ET.Element('comment'))
    images_e = ET.Element('images')
    root.append(images_e)

    def process_image(image_path):
        img = cv2.imread(image_path)
        image_e = ET.Element('image')
        image_e.set('file', str(image_path))

        # Find the largest contour
        contour = find_contour(img)
        if contour is not None:
            x, y, w, h = cv2.boundingRect(contour)  # Get bounding box from contour
            rect = dlib.rectangle(x, y, x + w, y + h)
            shape = predictor(img, rect)

            box = ET.Element('box')
            box.set('top', str(y))
            box.set('left', str(x))
            box.set('width', str(w))
            box.set('height', str(h))

            for i in range(0, shape.num_parts):
                part = ET.Element('part')
                part.set('name', str(i))
                part.set('x', str(int(shape.part(i).x)))
                part.set('y', str(int(shape.part(i).y)))
                box.append(part)

            image_e.append(box)
        return image_e

    # Retrieve image paths using images_from_path
    image_paths = images_from_path(images, full_path=True)

    # check for none
    if image_paths is None:
        raise ValueError(f"No images found in directory: {images}")
    # Process images in parallel
    processed_images = Parallel(n_jobs=n_jobs, backend='threading')(delayed(process_image)(image_path) for image_path, _ in image_paths)

    # Append processed images to the XML structure
    for image_e in processed_images:
        images_e.append(image_e)  # type: ignore

    # Write XML to file
    et = ET.ElementTree(root)
    xmlstr = minidom.parseString(ET.tostring(et.getroot())).toprettyxml(indent="   ")  # type: ignore
    with open(out_file, "w") as f:
        f.write(xmlstr)

def dlib_xml_to_pandas(xml_file: str, parse=False):
    '''
    Efficiently imports dlib xml data into a pandas dataframe.
    '''
    tree = ET.parse(xml_file)
    root = tree.getroot()
    landmark_list = []

    # Flatten the XML structure using list comprehensions
    for image in root.findall("images/image"):
        image_file = image.attrib['file']
        box = image.findall("box")[0]
        box_top = float(box.attrib['top'])
        box_left = float(box.attrib['left'])
        box_width = float(box.attrib['width'])
        box_height = float(box.attrib['height'])

        parts = {}

        for part in box.findall("part"):
            part_name = part.attrib['name']
            part_x = float(part.attrib['x'])
            part_y = float(part.attrib['y'])
            parts[part_name] = (part_x, part_y)

        landmark_list.append({
            'file': image_file,
            'id': os.path.splitext(os.path.basename(image_file))[0],
            'box_top': box_top,
            'box_left': box_left,
            'box_width': box_width,
            'box_height': box_height,
            **{f'X{part_name}': part_x for part_name, (part_x, part_y) in parts.items()},
            **{f'Y{part_name}': part_y for part_name, (part_x, part_y) in parts.items()}
        })

    dataset = pd.DataFrame(landmark_list)
    return dataset

def pandas_to_dlib_xml(name_element_text: str, comment_element_text: str, df: pd.DataFrame, out_file: str, landmark_cols: list[tuple[str, str]], image_folder: str = '.', image_ext: str = '.jpg'):
    """
    Convert a pandas DataFrame of landmarks to dlib XML format.
    - df: DataFrame with columns ['id', 'landmarkx1', 'landmarky1', ...]
    - out_file: output XML file path
    - landmark_cols: A list of tuples specifying the column names for x and y coordinates of landmarks.
    - image_folder: folder where images are stored (for file path in XML)
    - image_ext: image file extension (default '.jpg')
    """
    # set up XML structure
    root = ET.Element('dataset')
    name_element = ET.Element('name')
    name_element.text = name_element_text
    root.append(name_element)
    comment_element = ET.Element('comment')
    comment_element.text = comment_element_text
    root.append(comment_element)
    images_element = ET.Element('images')
    root.append(images_element)

    # for each image/row in the dataframe
    for _, row in df.iterrows():
        # Get landmark coordinates
        lm_xy = []
        for i, (x_col, y_col) in enumerate(landmark_cols):
            # use ser.iloc[pos] if using index, but using names now
            x = row[x_col]
            y = row[y_col]
            if pd.notnull(x) and pd.notnull(y):
                lm_xy.append((int(x), int(y)))
        lm_xy = np.array(lm_xy)

        # Get box parameters (assuming they are in the dataframe)
        top, left, width, height = row['top'], row['left'], row['width'], row['height']

        # Compose image file path
        img_file = os.path.join(image_folder, str(row['id']) + image_ext)
        # if length of lm_xy is not as expected, meaning this row has more or less landmarks, skip this row 
        # if anything is None, skip
        if len(lm_xy) != len(landmark_cols) or np.any(np.isnan(lm_xy)) or pd.isnull(top) or pd.isnull(left) or pd.isnull(width) or pd.isnull(height):
            continue


        # Create XML elements
        image_element = ET.Element('image')
        image_element.set('file', img_file)

        box_element = ET.Element('box')
        box_element.set('top', str(int(top)))
        box_element.set('left', str(int(left)))
        box_element.set('width', str(int(width)))
        box_element.set('height', str(int(height)))

        for i, (x, y) in enumerate(lm_xy):
            part_element = ET.Element('part')
            part_element.set('name', str(i))
            part_element.set('x', str(int(x)))
            part_element.set('y', str(int(y)))
            box_element.append(part_element)

        image_element.append(box_element)
        images_element.append(image_element)

    # Write XML
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
    with open(out_file, "w") as f:
        f.write(xmlstr)

def pandas_split_for_dlib(df: pd.DataFrame, train_frac: float = 0.8, random_seed: int = 42):
    """
    Splits a pandas DataFrame into training and testing sets for dlib XML conversion.
    Note: Remember not to read the dataframe with index_col set, as we will drop it.
    - df: DataFrame with landmark data
    - train_frac: fraction of data to use for training
    - random_seed: seed for reproducibility
    Returns:
    - train_df: training DataFrame
    - test_df: testing DataFrame
    """
    np.random.seed(random_seed)
    shuffled_indices = np.random.permutation(len(df))
    train_size = int(len(df) * train_frac)
    train_indices = shuffled_indices[:train_size]
    test_indices = shuffled_indices[train_size:]
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    return train_df, test_df
# 1. permutation splitting of the input using pandas before converting to xml
# 2. have box be a part of the input, measured from cropped contour.
# 3. make getting landmarks from the df similar to pandas vis.
# 4. split, make xml, run trainer tommrrow 
# only show the 3 landmarks used and left most, optional cropping (defination of wing area.)

def merge_xml_files(input_files, output_file):
    """
    Merges multiple XML files into a single XML file.
    """
    # Create a root element for the merged XML
    merged_root = ET.Element('dataset')

    for xml_file in input_files:
        # Parse each XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Append the images from the current XML to the merged root
        for image in root.findall('images/image'):
            merged_root.append(image)

    # Write the merged XML to the output file
    merged_tree = ET.ElementTree(merged_root)
    merged_tree.write(output_file, encoding='utf-8', xml_declaration=True)