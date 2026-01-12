import os
import tempfile
import shutil

class TempFolderDAO:
    # not very separated, can be refactored so interactor knows less,
    # but is much easier to just do everything, and keep track of everything in detection_interactor
    def __init__(self):
        self.temp_dir = None

    def create_temp_folder(self):
        """Creates a temporary folder and returns its path."""
        self.temp_dir = tempfile.mkdtemp()
        print(f"Temporary directory created at: {self.temp_dir}")
        return self.temp_dir

    def create_subdirectory(self, sub_dir_name: str) -> str:
        """Creates a subdirectory within the temp folder."""
        if not self.temp_dir:
            raise ValueError("Temporary folder has not been created.")
        sub_dir_path = os.path.join(self.temp_dir, sub_dir_name)
        os.makedirs(sub_dir_path, exist_ok=True)
        print(f"Subdirectory created at: {sub_dir_path}")
        return sub_dir_path

    def cleanup(self):
        """Deletes the temporary folder and its contents."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"Temporary directory {self.temp_dir} deleted.")
            self.temp_dir = None