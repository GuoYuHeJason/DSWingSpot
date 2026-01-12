from os.path import join, exists
import json
import pandas as pd
import cv2
import numpy as np
from typing import Optional


def read_image(file_path: str):
    """Returns the image data.
    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file format is incorrect.
    """
    if not exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")
    return cv2.imread(file_path)

def write_image(image_id: str, image: np.ndarray, output_path: str, format="png"):
    """Writes the image data.
    Raises:
        IOError: If the file cannot be written.
    """
    cv2.imwrite(join(output_path, image_id + '.' + format), image)

def read_dictionary(file_path: str):
    """Reads a dictionary from a JSON file.
    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the file format is incorrect.
    """
    if not exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")
    with open(file_path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("File format is incorrect, expected a dictionary.")
    return data

def write_dictionary(file_path: str, dictionary: dict):
    """Writes a dictionary to a JSON file.
    Raises:
        IOError: If the file cannot be written.
    """
    with open(file_path, 'w') as f:
        json.dump(dictionary, f)

def write_csv(file_path: str, data: dict[str, list[str]]):
    """
    The input dictionary has numbers as strings
    Writes a dictionary to a CSV file. Using the keys as columns.
    Each row corresponds to an index in the lists.
    Raises:
        ValueError: If the lists in the dictionary are not the same length.
        IOError: If the file cannot be written.
    """
    # Check that all lists are the same length
    lengths = [len(v) for v in data.values()]
    if len(set(lengths)) > 1:
        raise ValueError("All lists in the dictionary must be the same length.")

    df = pd.DataFrame.from_dict(data, orient='index').transpose()
    df.to_csv(file_path, index=False, header=True)

def save_results(output_path: str, data: dict[str, list[str]], filename: str = "wing_spot_results"):
    """Saves the detection results as a CSV file and as a json file in the specified output path."""
    csv_path = join(output_path, filename + ".csv")
    write_csv(csv_path, data)

    # Save as JSON
    json_path = join(output_path, filename + ".json")
    write_dictionary(json_path, data)

