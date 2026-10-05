from typing import Optional

class DetectionOutputData:
    """
    The output data class for the detection use case.
    """
    results: list[dict[str, str]]  # one row per successfully measured image
    errors: dict[str, str]  # image_id -> reason the image could not be measured
    output_path: str
    cancelled: bool

    def __init__(
        self,
        results: Optional[list[dict[str, str]]] = None,
        errors: Optional[dict[str, str]] = None,
        output_path: str = "",
        cancelled: bool = False,
    ) -> None:
        self.results = results if results is not None else []
        self.errors = errors if errors is not None else {}
        self.output_path = output_path
        self.cancelled = cancelled

    @property
    def success(self) -> list[str]:
        """image_ids that were measured successfully"""
        return [row["image_id"] for row in self.results]
