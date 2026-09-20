import os
import pytest

from use_case.detection.temp_folder_DAO import TempFolderDAO


def test_create_subdirectory_requires_temp_folder():
    dao = TempFolderDAO()
    with pytest.raises(ValueError, match="has not been created"):
        dao.create_subdirectory("resized")


def test_temp_folder_lifecycle():
    dao = TempFolderDAO()
    temp_dir = dao.create_temp_folder()
    sub = dao.create_subdirectory("resized")

    assert os.path.isdir(temp_dir)
    assert os.path.isdir(sub)

    dao.cleanup()

    assert not os.path.exists(temp_dir)
    assert dao.temp_dir is None
