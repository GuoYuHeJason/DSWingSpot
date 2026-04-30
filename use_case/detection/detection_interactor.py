from use_case.detection.detection_input_boundary import DetectionInputBoundary
from use_case.detection.detection_input_data import DetectionInputData
from use_case.detection.detection_output_boundary import DetectionOutputBoundary
from use_case.detection.detection_output_data import DetectionOutputData
from .temp_folder_DAO import TempFolderDAO

from .tools import *
from .batch_helper import *
import os
import pandas as pd
from joblib import Parallel, delayed
import traceback

class DetectionInteractor(DetectionInputBoundary):
    """
    The interactor class for the detection use case.
    Implements the DetectionInputBoundary interface.
    """
    # image name is the file name
    _data: dict[str, list[str]]
    _output_boundary: DetectionOutputBoundary
    _temp_folder_dao: TempFolderDAO

    def _create_empty_data(self) -> dict[str, list[str]]:
        return {
            "image_id": [],
            "wing_area": [],
            "spot_area": [],
            "spot_ratio": [],
        }

    def __init__(self, output_boundary: DetectionOutputBoundary):
        self._data = self._create_empty_data()
        self._output_boundary = output_boundary
        self._temp_folder_dao = TempFolderDAO()

    # may be having it as a separate function is better for preparing data access
    def reset_data(self) -> None:
        self._data = self._create_empty_data()
        # clear temp folder
        self._temp_folder_dao.cleanup()

    def execute(self, input: DetectionInputData, n_jobs: int = -1) -> None:
        """
        Executes the detection use case.
        """
        try:
            # Create a temporary folder
            temp_dir = self._temp_folder_dao.create_temp_folder()
            resized_dir = self._temp_folder_dao.create_subdirectory("resized")
            bg_removed_dir = self._temp_folder_dao.create_subdirectory("bg_removed")

            # Retrieve image paths from the input directory
            images = list(images_from_path(input.input_path, full_path=True)) # type: ignore

            # Convert img_name to image_id
            images = [(img_path, img_name.split('.')[0]) for img_path, img_name in images]

            # Resize images in parallel
            resized_results = Parallel(n_jobs=n_jobs, backend='threading', verbose=10)(
                delayed(image_resize_helper)(
                    input.image_resizer, img_path, image_id, resized_dir
                ) for img_path, image_id in images
            ) # type: ignore

            # Remove background in parallel
            bg_removed_results = Parallel(n_jobs=n_jobs, backend='threading', verbose=10)(
                delayed(bg_removal_helper)(
                    input.bg_removal_model, resized_path, image_id, bg_removed_dir
                ) for resized_path, image_id in resized_results # type: ignore
            )

            resized_results: list[tuple[str, str]] # type: ignore
            bg_removed_results: list[tuple[str, str]] # type: ignore

            # Merge resized_results and bg_removed_results into a list of tuples
            merged_results = [
                (resized_path, bg_removed_path, image_id)
                for (resized_path, image_id) in resized_results
                for (bg_removed_path, bg_image_id) in bg_removed_results
                if image_id == bg_image_id
            ]

            # # check merged_results length
            # if len(merged_results) != len(images):
            #     raise ValueError("Mismatch in number of processed images after merging resized and background removed results.")
            
            # now predict landmarks###############################
            landmarks_df = shape_predictor_helper(
                input.shape_predictor, bg_removed_dir,
                os.path.join(temp_dir, "landmarks.xml"),
                n_jobs=n_jobs
            )
            # set id as index
            landmarks_df.set_index('id', inplace=True)

            # save landmarks for debugging
            landmarks_df.to_csv(os.path.join(input.output_path, "landmarks_debug.csv"))

            # Perform final detection in parallel
            area_results = Parallel(n_jobs=n_jobs, backend='threading', verbose=10)(
                delayed(final_detection_helper)(
                    input.wing_detector, input.spot_detector,
                    bg_removed_path, resized_path,
                    image_id,
                    (int(landmarks_df.loc[image_id][input.landmark1_x]), int(landmarks_df.loc[image_id][input.landmark1_y])), # type: ignore
                    (int(landmarks_df.loc[image_id][input.landmark2_x]), int(landmarks_df.loc[image_id][input.landmark2_y])), input.output_path # type: ignore
                ) for resized_path, bg_removed_path, image_id in merged_results
            ) # type: ignore

            # Ensure area_results is not None
            if area_results is None:
                raise ValueError("area_results is None. Cannot aggregate results.")
            area_results: list[dict[str, str]] # type: ignore

            # Convert area_results to a single dictionary with lists of values
            # can be vectorized later, but for now keep it simple
            for result in area_results:
                if result is not None and isinstance(result, dict) and set(result.keys()) == set(self._data.keys()):
                    for key, value in result.items():
                        self._data[key].append(value)

            # Save results as CSV and JSON
            save_results(input.output_path, self._data, filename="wing_spot_results")

            # call output boundary to prepare success view
            self._output_boundary.prepare_success_view(DetectionOutputData(
                # errors are image_ids in images but not in self._data["image_id"]
                errors=[image_id for (image_path, image_id) in images if image_id not in self._data.get("image_id", [])],
                success=self._data.get("image_id", [])
            ))

        except Exception as e:
            error_message = traceback.format_exc()
            self._output_boundary.prepare_fail_view(error_message)
        finally:
            # Reset data and clean up temporary folder
            self.reset_data()


