import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os

import search_utils


# Config
INPUT_FILENAME = "data/steep_beam.txt"
CANDIDATE_FOLDER = "candidates"

# Probably move these to args if I ever implement a class
SEARCH_SCORE_THRESH = 0.15
SEARCH_ANGLE = 50  # Max degrees change from average per step
SEARCH_RADIUS = 2  # Square kernel to search

# Widgets are a pain, so just leave as config
DRAW_HEAT = True
DRAW_LINES = True


def recursive_angle_search(
    indices_lookup: dict[tuple[int, int], list[int]],
    running_match: list[tuple[int, int]],
    max_index: int,
    search_radius: int,
    search_angle: float,
    mean_angle: float | None,
) -> list[list[tuple[int, int]]]:
    """
    A line detector for approximately straight, ascending sequences.

    Uses incremental averaging to progressively build a total angle estimate,
    while continually searching in a limited "cone".
    
    Using a hashmap + local search hopefully keeps runtime lower than comparing
    every other data point matching data on dense data. The bbox can be reduced
    further if this is ever adapted to large search zones.

    When searching for approximate solutions, the search angle must be big
    enough to allow any expected early average errors. Additionally, while
    it can find some excellent diagonals, the square kernel also purposely
    keeps non-contiguous cardinal results which may subpar for aligned text.

    Parameters
    ----------
    indices_lookup : dict
        A mapping of (r, c) coords to sequence index. Acts as a sparse
        representation of the problem space.
    running_match : list of coords
        The accumulated coords for the current line match.
    max_index : int
        Maximum search depth, usually matching the pattern length.
    search_radius : int
        The radius of the square area to search in next, excluding centre.
    search_angle : float
        The angle to limit the search to, in degrees.
    mean_angle : float or None
        The running average angle of the line. If missing, search in all
        directions, then set for next recursion.

    Returns
    -------
    list of matches
        All matched lines, where each line is itself an ordered list of (r, c) coords.
    """
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
        if (
            current_index + 1 in indices_lookup.get((next_r, next_c), [])
        )  # Next cell in order
    ]
    # NOTE: Angle is clockwise from East, while radius is square

    matches = []
    if mean_angle is None:
        # No average: Continue search regardless of direction
        for next_r, next_c, next_mean_angle in next_cells:
            matches.extend(
                recursive_angle_search(
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
                    recursive_angle_search(
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


def beam_search(
    data: list[str],
    candidate_df: pd.DataFrame,
    search_score_thresh: float = 0,
    search_radius: int = 2,
    search_angle: float = 50,
) -> list[list[tuple[int, int]]]:
    """
    Wrapper to initiate recursive "wobbly" Ui Beam detection at any angle
    within the square radius.

    Uses incremental averaging to progressively build a total angle estimate,
    while continually searching in a limited "cone".

    Parameters
    ----------
    data : list of str
        The paragraph of Unicode text, split by line.
    candidate_df : DataFrame
        Lookup table of (char, beam_index, score) candidates, uniquely keyed by
        (char, beam_index).
    search_score_thresh : float, default=0
        Prunes candidates below a score threshold.
    search_radius : int, default=2
        The radius of the square area to search in next, excluding centre.
        Recommended to limit to 3 or less for semi-realistic results.
    search_angle : float, default=50
        The angle to limit the search to, in degrees. Recommended 50 to allow
        some wobble, and 10 to lock search into fixed hop patterns.

    Returns
    -------
    list of matches
        All matched lines, where each line is itself an ordered list of (r, c) coords.
    """
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
                & (candidate_df["score"] >= search_score_thresh)
            ]["beam_index"].to_list()

            if len(viable_indices) > 0:
                beam_indices[(r, c)] = viable_indices

    # Begin beam search from index 0
    matches = []
    for coord in beam_indices:
        if 0 in beam_indices[coord]:
            # First match detected, begin recursion
            matches.extend(
                recursive_angle_search(
                    beam_indices,
                    [coord],
                    beam_length - 1,
                    search_radius,
                    search_angle,
                    None,
                )
            )

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

    # Visualise as heatmap
    # Set up heatmap inputs
    labels = search_utils.to_unicode_paragraph(data)
    scores: np.ndarray

    if DRAW_HEAT:
        # Map data into corresponding scores
        scores_map = candidate_df.groupby(["char"])["score"].max()
        scores = np.vectorize(lambda c: scores_map.get(c, default=0), otypes="f")(
            labels
        )
        # Casting fixes a possible inference bug
    else:
        scores = np.zeros(labels.shape)

    search_utils.build_kana_heatmap(labels, scores)

    # Draw matches on top
    if DRAW_LINES:
        matches = beam_search(
            data,
            candidate_df,
            SEARCH_SCORE_THRESH,
            SEARCH_RADIUS,
            SEARCH_ANGLE,
        )
        print("Total matches:", len(matches))

        for line in matches:
            # Plot expects zipped and flipped form
            line_x = []
            line_y = []
            for r, c in line:
                line_x.append(c + 0.5)  # Grid offset
                line_y.append(r + 0.5)

            plt.plot(line_x, line_y, color="red", linewidth=1, alpha=0.5)

    plt.show()
