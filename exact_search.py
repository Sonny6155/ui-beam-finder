# import unicodedata
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
# also need some sort of monospace display
# also need a standard module for detecting/filtering non printables and invisible characters etc

# Limitations
# - Assumes full-width monospace characters
# - Assumes simple 5 char beams, hence doesn't support english or spaced beams
# - Can't handle Koyo Beams
# - No feature (yet) to use standard marshmallow size wrapping (is there a standard size even?)
# - No feature (yet) to restore pruned lines visually on display
# - Can't really detect kanji unless hardcoded (planned to be addressed in a candidate highlighter later)


# Expected features
# ability to toggle unusual char search
# ability to toggle punctuation filtering
# ability to toggle invisible char filtering
# pad half width chars visually, or display using a utf-8 monospace font


# Config
search_diagonals = True
unusual_chars = True  # Based on known trickery, but not comprehensive
# input_filename = "data/6kaSnEtmUMg.txt"
# input_filename = "data/trivial.txt"
input_filename = "data/bad_chars.txt"


# Helper functions
def sanitise_japanese(raw_data: str, preferred_width: str = "half", strip_bad: bool = True, strip_space: bool = False, prune_empty_lines: bool = True) -> list[str]:
    working_data = raw_data

    # Define relevant Unicode ranges
    # NOTE: These blocks may actually include a few non-assigned points
    # Source: https://stackoverflow.com/questions/19899554/unicode-range-for-japanese
    valid_ranges = [
        r"\u000a",  # Avoid losing newline too early...
        r"\u0020-\u007e",  # ASCII printables
        r"\u3000-\u303f",  # CJK punctuation
        r"\u3040-\u309f",  # Hiragana
        r"\u30a0-\u30ff",  # Katakana
        r"\uff00-\uffef",  # Full-width roman and half-width katakana
        r"\u4e00-\u9faf",  # CJK unified
    ]

    # Transpose Latin depending preferred width setting
    # NFKC normalisation risks side effects and is one-way, so do it manually
    if preferred_width == "half":
        mapping = dict((i + 0xFEE0, i) for i in range(0x21, 0x7F))
        mapping[0x3000] = 0x20  # CJK space is actually part of the punc block
        working_data = str(working_data).translate(mapping)
    elif preferred_width == "full":
        mapping = dict((i, i + 0xFEE0) for i in range(0x21, 0x7F))
        mapping[0x20] = 0x3000
        working_data = str(working_data).translate(mapping)
    elif preferred_width != "keep":
        raise ValueError("preferred_width arg must be half/full/keep")
    # Derived from: https://stackoverflow.com/questions/2422177/python-how-can-i-replace-full-width-characters-with-half-width-characters

    # Transpose Kangxi radicals to CJK
    # TODO: Might need normalisation for this after all?

    # Strip bad chars, per config
    # NOTE: Stripping all bad chars may ruin some emoticons or advanced tricks
    # Also might not strip every bad char, due to block-based patterns
    if strip_bad:
        removal_pattern = f"[^{"".join(valid_ranges)}]"
        working_data = re.sub(removal_pattern, "", working_data, re.U)
        # TODO: Warn if any removed. use compile for this?

    if strip_space:
        removal_pattern = r"[\u0020\u3000]"
        working_data = re.sub(removal_pattern, "", working_data, re.U)

    # Finally, split into distinct rows, optionally pruning empty rows
    final_data = working_data.split("\n")
    if prune_empty_lines:
        final_data = [s for s in final_data if s != ""]
        print(final_data)

    return final_data

# Hardcoded beam lookup
base_pattern = ["うウuU", "いイiI1|", "ビびbB", "ーいイiI1|_-/\\~〜", "ムむmM"]
kanji_pattern = ["", "一", "", "一", ""]  # High probability trick chars
unusual_pattern = ["", "今仏", "美", "今仏", "仏難"]  # Lower chance, but used before
# TODO: Source more from well known clips


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


def display_text_array(data: list[str], matches: set[tuple[int, int]]) -> None:
    # Convert to padded Numpy array of single unicodes
    longest_line = max(len(s) for s in data)
    nested_data = [[*s.ljust(longest_line)] for s in data]
    labels = np.array(nested_data, dtype="<U1")

    # Highlight matched cells
    mat = np.zeros(labels.shape)
    mat[*zip(*matches)] = 1  # Apparently np expects it in zipped form

    # Display
    r, c = labels.shape
    plt.figure(figsize=(c/4, r/4))  # TODO: Make this more configurable or auto
    sns.heatmap(mat, cmap=sns.color_palette("light:lightblue", as_cmap=True), annot=labels, annot_kws={"fontfamily": "Meiryo"}, fmt='s', cbar=False, square=True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Read and filter bad characters/newlines
    raw_data = open(input_filename, "r", encoding="utf-8").read()
    data = sanitise_japanese(raw_data)
    # Could have converted to padded Numpy from the beginning then use a
    # convolution-like approach, but:
    # - Unicode stuff in Numpy has been a pain so far.
    # - Slightly less portable.
    # - It was easier to sanitise in native form.
    # - Eager matching is maaaaybe slower on average without vectorisation?

    print("Sanitised data:")
    print(data)

    # Begin radial search
    total_matches = 0  # TODO: Temp hijacking code, will refactor later maybe
    matches = set()  # NOTE: Set is more useful for now, but might use hashed dict keys in the future for order
    for r in range(len(data)):
        for c in range(len(data[r])):
            # Prepare cardinal steppers (N, E, S, W)
            direction_steppers = [(-1, 0), (0, 1), (1, 0),(0, -1)]
            if search_diagonals:
                # Prepare ordinal steppers (NE, SE, Sw, NW)
                direction_steppers += [(-1, 1), (1, 1), (1, -1), (-1, -1)]

            # Prepare configured patterns
            pattern = [s1 + s2 for s1, s2 in zip(base_pattern, kanji_pattern)]
            if unusual_chars:
                pattern = [s1 + s2 for s1, s2 in zip(pattern, unusual_pattern)]

            # Now, match each direction
            for r_step, c_step in direction_steppers:
                result = direction_match(data, pattern, r, c, r_step, c_step)
                matches.update(result)

                # TODO: Temp hijacking code, will refactor later maybe
                # Still debating whether to return cells or just start/angle data
                if len(result) > 0:
                    total_matches += 1

    # Print stats
    print("Matched cells:")
    print(matches)
    print("Total matches:", total_matches)

    # Plot with (binary) highlighting
    display_text_array(data, matches)
