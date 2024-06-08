import numpy as np

import search_utils


# Config
SEARCH_DIAGONALS = True
SEARCH_TRICK_KANJI = True  # Based on known trickery, but not comprehensive
INPUT_FILENAME = "data/bad_chars.txt"
# u"\u3040" might be useful as an invalid sentinel in the hiragana block

# Hardcoded beam lookup
BASE_PATTERN = ["うウuU", "いイiI1|", "ビびbB", "ーいイiI1|_-/\\~〜", "ムむmM"]
KANJI_PATTERN = ["噂", "一今仏", "美", "一今仏", "仏難"]  # Sourced from clips


# Helper functions
def direction_match(data: list[str], pattern: list[str], r: int, c: int, r_step: int, c_step: int) -> list[tuple[int, int]]:
    """
    Search for the pattern char set using int steppers.
    TODO: Consider arg validation
    """
    running_match = []

    for m in range(len(pattern)):
        next_r = r_step * m + r
        next_c = c_step * m + c

        # Check if coord is valid and pattern matches
        if 0 <= next_r < len(data) and 0 <= next_c < len(data[next_r]) and data[next_r][next_c] in pattern[m]:
            running_match.append((next_r, next_c))
        else:
            return []  # Match failed

    return running_match  # Match successful


if __name__ == "__main__":
    # Read and filter bad characters/newlines
    raw_data = open(INPUT_FILENAME, "r", encoding="utf-8").read()
    data = search_utils.sanitise_japanese(raw_data)
    print("Sanitised data:")
    print(data)

    # Convert to variable-length "2D"
    data = data.split("\n")
    # Could have converted to padded Numpy from the beginning then use a
    # convolution-like approach, but:
    # - Unicode stuff in Numpy has been a pain so far.
    # - Eager matching is maaaaybe slower on average without vectorisation?
    # TODO: On second thoughts, will absolutely change to use utils interface

    # Begin radial search
    total_matches = 0
    matches = set()  # NOTE: Set is more useful for now, but might use hashed dict keys in the future for order
    for r in range(len(data)):
        for c in range(len(data[r])):
            # Prepare cardinal steppers (N, E, S, W)
            direction_steppers = [(-1, 0), (0, 1), (1, 0),(0, -1)]
            if SEARCH_DIAGONALS:
                # Prepare ordinal steppers (NE, SE, Sw, NW)
                direction_steppers += [(-1, 1), (1, 1), (1, -1), (-1, -1)]

            # Prepare configured patterns
            pattern = BASE_PATTERN
            if SEARCH_TRICK_KANJI:
                pattern = [s1 + s2 for s1, s2 in zip(BASE_PATTERN, KANJI_PATTERN)]

            # Now, match each direction
            for r_step, c_step in direction_steppers:
                result = direction_match(data, pattern, r, c, r_step, c_step)
                matches.update(result)

                if len(result) > 0:
                    total_matches += 1

    # Print stats
    print("Matched cells:")
    print(matches)
    print("Total matches:", total_matches)

    # Coerce and plot with (binary) highlighting
    # Convert to padded Numpy array of single unicodes
    longest_line = max(len(s) for s in data)
    nested_data = [[*s.ljust(longest_line)] for s in data]
    labels = np.array(nested_data, dtype="<U1")
    # TODO: Can remove this stuff after redesign

    # Highlight matched cells
    match_matrix = np.zeros(labels.shape)
    match_matrix[*zip(*matches)] = 1  # Apparently np expects it in zipped form

    search_utils.visualise_paragraph_heat(labels, match_matrix)
