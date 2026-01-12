
class DetectionOutputData:
    """
    The output data class for the detection use case.
    """
    errors: list[str] = []  # error image_id
    success: list[str] = []  # list of successful image_ids

    def __init__(
        self,
        errors: list[str] = [],
        success: list[str] = []
    ) -> None:
        self.errors = errors
        self.success = success