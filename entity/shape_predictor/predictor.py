from .dlib_xml import predictions_to_xml_with_contour, dlib_xml_to_pandas
import pandas as pd

class ShapePredictor:
    def __init__(self, model_path: str):
        self.model_path = model_path

    def predict(self, image_dir: str, output_xml_file: str, n_jobs: int) -> pd.DataFrame:
        """
        Predicts shape landmarks for images in the given directory and saves the results to an XML file.
        
        Args:
            image_dir (str): Directory containing images to predict.
            output_xml_file (str): Path to save the output XML file.
        
        Returns:
            pd.DataFrame: DataFrame containing the prediction results.
        """
        predictions_to_xml_with_contour(
            predictor_name=self.model_path,
            images=image_dir,
            out_file=output_xml_file,
            n_jobs=n_jobs
        )
        results_df = dlib_xml_to_pandas(output_xml_file)
        return results_df
