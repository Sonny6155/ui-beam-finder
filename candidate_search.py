import pandas as pd
import numpy as np

import os

import search_utils


# Config
INPUT_FILENAME = "data/bad_chars.txt"
CANDIDATE_FOLDER = "candidates"


if __name__ == "__main__":
    # Read and filter bad characters/newlines
    raw_data = open(INPUT_FILENAME, "r", encoding="utf-8").read()
    data = search_utils.sanitise_japanese(raw_data)
    print("Sanitised data:")
    print(data)

    # Convert to Numpy 2D
    data = search_utils.to_unicode_paragraph(data)
    # NOTE: Trying early numpy conversion approach this time

    # Merge candidate mappings by max
    scores_map = pd.Series()
    for filename in [f for f in os.listdir(CANDIDATE_FOLDER) if f.endswith(".csv")]:
        candidate_df = pd.read_csv(
            os.path.join(CANDIDATE_FOLDER, filename),
            usecols=["char", "score"],
            skip_blank_lines=True,
        )
        scores_map = scores_map.combine(
            candidate_df.groupby("char")["score"].max(),
            max,
            fill_value=0,  # Prevent max choosing NaN
        )

    # Map data into corresponding scores
    scores: np.ndarray = np.vectorize(lambda c: scores_map.get(c, default=0))(data)

    # Display heatmap
    search_utils.visualise_paragraph_heat(data, scores)
