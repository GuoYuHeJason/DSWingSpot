from use_case.detection.detection_input_boundary import DetectionInputBoundary
from use_case.detection.detection_input_data import DetectionInputData
from use_case.detection.detection_output_boundary import DetectionOutputBoundary
from use_case.detection.detection_output_data import DetectionOutputData
from .temp_folder_DAO import TempFolderDAO

from .tools import *
from .batch_helper import *
import os
import threading
import pandas as pd
from joblib import Parallel, delayed
import traceback
from typing import Any, Callable, Iterable

# stage names reported to the output boundary, in pipeline order
STAGE_RESIZE = "Calibrating scale and resizing"
STAGE_BG_REMOVAL = "Removing background"
STAGE_LANDMARKS = "Predicting landmarks"
STAGE_DETECTION = "Detecting wings and spots"
STAGE_SAVING = "Saving results"
STAGES = [STAGE_RESIZE, STAGE_BG_REMOVAL, STAGE_LANDMARKS, STAGE_DETECTION, STAGE_SAVING]


class DetectionInteractor(DetectionInputBoundary):
    """
    The interactor class for the detection use case.
    Implements the DetectionInputBoundary interface.
    """
    # image name is the file name
    _data: dict[str, list[str]]
    _output_boundary: DetectionOutputBoundary
    _temp_folder_dao: TempFolderDAO
    _errors: dict[str, str]  # image_id -> error message
    _cancel_event: threading.Event

    def _create_empty_data(self) -> dict[str, list[str]]:
        return {
            "image_id": [],
            "wing_area": [],
            "spot_area": [],
            "spot_ratio": [],
        }

    def __init__(self, output_boundary: DetectionOutputBoundary):
        self._data = self._create_empty_data()
        self._errors = {}
        self._output_boundary = output_boundary
        self._temp_folder_dao = TempFolderDAO()
        self._cancel_event = threading.Event()

    # may be having it as a separate function is better for preparing data access
    def reset_data(self) -> None:
        self._data = self._create_empty_data()
        self._errors = {}
        # clear temp folder
        self._temp_folder_dao.cleanup()

    def cancel(self) -> None:
        self._cancel_event.set()

    def _run_stage(self, stage: str, items: list[tuple[str, Any]], func: Callable[[Any], Any], n_jobs: int) -> dict[str, Any]:
        """
        Runs func on every (image_id, item) pair in parallel.
        Failures are recorded per image in self._errors so one bad image does not stop the batch.
        Returns {image_id: result} for the images that succeeded.
        """
        total = len(items)
        completed = 0
        lock = threading.Lock()
        self._output_boundary.prepare_progress_view(stage, 0, total)

        def run_one(image_id: str, item: Any) -> tuple[str, Any]:
            nonlocal completed
            if self._cancel_event.is_set():
                return image_id, None
            try:
                result = func(item)
            except Exception as e:
                self._errors[image_id] = f"{stage}: {str(e) or type(e).__name__}"
                result = None
            with lock:
                completed += 1
                self._output_boundary.prepare_progress_view(stage, completed, total)
            return image_id, result

        results: Iterable[tuple[str, Any]] = Parallel(n_jobs=n_jobs, backend='threading')(
            delayed(run_one)(image_id, item) for image_id, item in items
        ) # type: ignore
        return {image_id: result for image_id, result in results if result is not None}

    def _prepare_cancelled_view(self, input: DetectionInputData) -> None:
        self._output_boundary.prepare_success_view(DetectionOutputData(
            output_path=input.output_path, cancelled=True
        ))

    def execute(self, input: DetectionInputData, n_jobs: int = -1) -> None:
        """
        Executes the detection use case.
        """
        # the cancel flag is cleared when a run finishes, so a cancel requested while models load still applies
        try:
            # Create a temporary folder
            temp_dir = self._temp_folder_dao.create_temp_folder()
            resized_dir = self._temp_folder_dao.create_subdirectory("resized")
            bg_removed_dir = self._temp_folder_dao.create_subdirectory("bg_removed")

            # Retrieve image paths from the input directory
            images = list(images_from_path(input.input_path, full_path=True)) # type: ignore
            if not images:
                raise ValueError(f"No images found in {input.input_path}")

            # Convert img_name to image_id
            images = [(img_path, img_name.split('.')[0]) for img_path, img_name in images]
            os.makedirs(input.output_path, exist_ok=True)

            # Resize images in parallel
            resized = self._run_stage(
                STAGE_RESIZE,
                [(image_id, (img_path, image_id)) for img_path, image_id in images],
                lambda item: image_resize_helper(input.image_resizer, item[0], item[1], resized_dir)[0],
                n_jobs,
            )
            if self._cancel_event.is_set():
                return self._prepare_cancelled_view(input)

            # Remove background in parallel
            bg_removed = self._run_stage(
                STAGE_BG_REMOVAL,
                [(image_id, (resized_path, image_id)) for image_id, resized_path in resized.items()],
                lambda item: bg_removal_helper(input.bg_removal_model, item[0], item[1], bg_removed_dir)[0],
                n_jobs,
            )
            if self._cancel_event.is_set():
                return self._prepare_cancelled_view(input)

            # now predict landmarks, no per image progress available
            if bg_removed:
                self._output_boundary.prepare_progress_view(STAGE_LANDMARKS, 0, 0)
                landmarks_df = shape_predictor_helper(
                    input.shape_predictor, bg_removed_dir,
                    os.path.join(temp_dir, "landmarks.xml"),
                    n_jobs=n_jobs
                )
                # set id as index
                landmarks_df.set_index('id', inplace=True)

                # save landmarks for debugging
                landmarks_df.to_csv(os.path.join(input.output_path, "landmarks_debug.csv"))
            else:
                landmarks_df = pd.DataFrame()
            self._output_boundary.prepare_progress_view(STAGE_LANDMARKS, 1, 1)
            if self._cancel_event.is_set():
                return self._prepare_cancelled_view(input)

            def detect(item: tuple[str, str, str]) -> dict[str, str]:
                resized_path, bg_removed_path, image_id = item
                if image_id not in landmarks_df.index:
                    raise ValueError("no landmarks were predicted")
                row = landmarks_df.loc[image_id]
                landmark1 = (int(row[input.landmark1_x]), int(row[input.landmark1_y]))
                landmark2 = (int(row[input.landmark2_x]), int(row[input.landmark2_y]))
                return final_detection_helper(
                    input.wing_detector, input.spot_detector,
                    bg_removed_path, resized_path,
                    image_id, landmark1, landmark2, input.output_path
                )

            # Perform final detection in parallel
            area_results = self._run_stage(
                STAGE_DETECTION,
                [(image_id, (resized[image_id], bg_path, image_id)) for image_id, bg_path in bg_removed.items()],
                detect,
                n_jobs,
            )
            if self._cancel_event.is_set():
                return self._prepare_cancelled_view(input)

            # keep rows in the same order as the input images
            self._output_boundary.prepare_progress_view(STAGE_SAVING, 0, 1)
            rows = [area_results[image_id] for _, image_id in images if image_id in area_results]
            for result in rows:
                if set(result.keys()) == set(self._data.keys()):
                    for key, value in result.items():
                        self._data[key].append(value)

            # Save results as CSV and JSON
            save_results(input.output_path, self._data, filename="wing_spot_results")
            self._output_boundary.prepare_progress_view(STAGE_SAVING, 1, 1)

            # images that never produced a row but have no recorded error
            errors = dict(self._errors)
            for _, image_id in images:
                if image_id not in area_results and image_id not in errors:
                    errors[image_id] = "Unknown error"

            # call output boundary to prepare success view
            self._output_boundary.prepare_success_view(DetectionOutputData(
                results=rows,
                errors=errors,
                output_path=input.output_path,
            ))

        except Exception as e:
            error_message = traceback.format_exc()
            self._output_boundary.prepare_fail_view(error_message)
        finally:
            # Reset data and clean up temporary folder
            self.reset_data()
            self._cancel_event.clear()
