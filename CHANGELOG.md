# Changelog

All notable changes to this project will be documented in this file.

## [2026-04-29]

### Added
- Initial changelog.

### Changed
- spot detection patch to reduce spot overdetection error
1. adjust bin threshould based on height of wing and height of spot. 
2. option to start with set threshold or ostu threshold

### How to use new feature
- Set `ostu_threshold=True` if you want `find_spot_contour` to start from an Otsu-based threshold instead of the manual `bin_thresh` value.
- Set `adjust_bin_thresh=True` to let the detector retry with a lower threshold when the spot is overdetected
- Choose one reference method for the retry logic:
	- `wing_height_percentage_threshold` to compare spot height against a percentage of the wing height. spot height higher than this  percentage of the wing height is overdetected.
	- `left_most_point_adjustment` to compare lowest point of the spot against the y position of the left-most wing point plus an offset (moving up is negative adjustment, moving down is positive adjustment), spot lower than this position is overdetected.
	- `centroid_adjustment` to compare lowest point of the spot against the y position of the wing contour centroid plus an offset (moving up is negative adjustment, moving down is positive adjustment), spot lower than this position is overdetected.
- Tune `scale_by` to control how much the threshold is reduced on each retry.
- Leave the adjustment parameters at `0` for the other reference methods, default reference method is wing_height > left_most_point > centroid


### Fixed
- fixed reset data bug so you could run things again without restarting application or deleting files from output directory now!
