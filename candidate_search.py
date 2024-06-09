import pandas as pd
import numpy as np

import os

import search_utils


# Config
INPUT_FILENAME = "data/steep_beam.txt"
CANDIDATE_FOLDER = "candidates"


def angle_search(
    indices_lookup: dict[tuple[int, int], list[int]],
    running_match: list[tuple[int, int]],
    max_index: int,
    search_radius: int,
    search_angle: float,
    mean_angle: float | None,
) -> list[list[tuple[int, int]]]:
    """
    Approximate line detection of ascending sequences, returning all matched
    lines, and (r, c) coords of each line. The angle is incrementally averaged
    to build a total angle estimate, while the search radius/angle is limited
    to permit only slight deviations.

    As an approximate solution, the search angle cannot be too small to
    accommadate initial average errors on the first few points.
    """
    # Possibly subject to minor precision errors

    # Base cases
    current_index = len(running_match) - 1
    if current_index == max_index:
        return [running_match]  # Solution found
    elif current_index > max_index:
        raise ValueError("running_match length cannot exceed max_index.")
    elif current_index < 0:
        raise ValueError("running_match must at least contain initial coords.")

    # Compute next cells and their relative angle
    r, c = running_match[-1]

    next_cells = [
        (next_r, next_c, np.rad2deg(np.arctan2(next_r - r, next_c - c)))
        for next_r in range(r - search_radius, r + search_radius + 1)  # BBox
        for next_c in range(c - search_radius, c + search_radius + 1)
        if next_r != r or next_c != c  # Ignore centre
        if current_index + 1
        in indices_lookup.get((next_r, next_c), [])  # Next cell in order
    ]
    # NOTE: Angle is clockwise from East, while radius is square

    matches = []
    if mean_angle is None:
        # No average: Continue search regardless of direction
        for next_r, next_c, next_mean_angle in next_cells:
            matches.extend(
                angle_search(
                    indices_lookup,
                    [*running_match, (next_r, next_c)],
                    max_index,
                    search_radius,
                    search_angle,
                    next_mean_angle,
                )
            )

    else:
        # Average exists: Filter to only similar angled, while enhancing average
        for next_r, next_c, current_angle in next_cells:
            angle_diff = (current_angle - mean_angle + 180) % 360 - 180
            if np.abs(angle_diff) <= search_angle:
                # Within threshold, so increment average
                next_mean_angle = mean_angle + (
                    (current_angle - mean_angle) / current_index
                )

                matches.extend(
                    angle_search(
                        indices_lookup,
                        [*running_match, (next_r, next_c)],
                        max_index,
                        search_radius,
                        search_angle,
                        next_mean_angle,
                    )
                )

    # Collect up all sub-case matches
    return matches


if __name__ == "__main__":
    # Read and filter bad characters/newlines
    raw_data = open(INPUT_FILENAME, "r", encoding="utf-8").read()
    data = search_utils.sanitise_japanese(raw_data)
    print("Sanitised data:")
    print(data)

    # Convert to variable-length "2D"
    data = data.split("\n")

    # Read in candidate lookups and merge by max score
    dfs = []
    for filename in os.listdir(CANDIDATE_FOLDER):
        if filename.endswith(".csv"):
            dfs.append(
                pd.read_csv(
                    os.path.join(CANDIDATE_FOLDER, filename),
                    usecols=["char", "beam_index", "score"],
                    skip_blank_lines=True,
                )
            )
    candidate_df = pd.concat(dfs).groupby(["char", "beam_index"]).max().reset_index()

    # Part 1: Visualise as char-only heatmap
    # Set up labels as Numpy 2D
    labels = search_utils.to_unicode_paragraph(data)

    # Map data into corresponding scores
    scores_map = candidate_df.groupby(["char"])["score"].max()
    scores: np.ndarray = np.vectorize(lambda c: scores_map.get(c, default=0))(labels)

    # Display heatmap
    search_utils.visualise_paragraph_heat(labels, scores)

    # Part 2: Visualise thresholded approx lines
    # Motivation is to find lines in text which may be slightly curved by sharp
    # angles or variable-width characters. Whether or not a "horse move" jump
    # is actually an acceptable line... Well let's leave it to the user.
    score_thresh = 0.15
    search_angle = 50  # Max degrees change from average per step
    search_radius = 2  # Square kernel to search
    beam_length = 5

    # Each character may have multiple indices, so a {coords: indices list} mapping
    # is a bit easier than 3D Numpy for sparse data
    beam_indices = dict()
    for r in range(len(data)):
        for c in range(len(data[r])):
            # Filter to matching char of sufficent weight
            viable_indices = candidate_df[
                (candidate_df["char"] == data[r][c])
                & (candidate_df["beam_index"] >= 0)
                & (candidate_df["beam_index"] < beam_length)
                & (candidate_df["score"] >= score_thresh)
            ]["beam_index"].to_list()

            if len(viable_indices) > 0:
                beam_indices[(r, c)] = viable_indices

    # Begin beam search from index 0
    # Hoping that square radius search keeps runtime lower than other options
    matches = []
    for coord in beam_indices:
        if 0 in beam_indices[coord]:
            # First match detected, begin recursion
            matches.extend(
                angle_search(
                    beam_indices,
                    [coord],
                    beam_length - 1,
                    search_radius,
                    search_angle,
                    None,
                )
            )

    print(matches)

    # TODO: visualise
    # Might wanna visual also with kerning, perhaps now without heatmap
    # convert to 2D again
    # draw lines
