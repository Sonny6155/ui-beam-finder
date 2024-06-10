import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

import re


def sanitise_japanese(
    raw_data: str,
    preferred_width: str = "half",
    strip_bad: bool = True,
    strip_space: bool = False,
    prune_empty_lines: bool = True
) -> str:
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

    # NOTE: Would have also transposed Kangxi radicals, but that sounds like
    # hell without using normalisation, so I'll leave that to another day...

    # Strip bad chars and empty lines, per config
    # NOTE: Stripping all bad chars may ruin some emoticons or advanced tricks
    # Also might not strip every bad char, due to block-based patterns
    if strip_bad:
        removal_pattern = f"[^{"".join(valid_ranges)}]"
        working_data, changes = re.subn(removal_pattern, "", working_data)
        if changes > 0:
            print("Some non-Latin/Japanese characters were removed.")

    if strip_space:
        removal_pattern = r"[\u0020\u3000]"
        working_data, changes = re.subn(removal_pattern, "", working_data)
        if changes > 0:
            print("Some Latin/Japanese spaces were removed.")

    if prune_empty_lines:
        original_length = len(working_data)
        working_data = re.sub("\n\n", "\n", working_data.strip("\n"))
        changes = original_length - len(working_data)
        if changes > 0:
            print("Some empty lines removed.")

    return working_data


def to_unicode_paragraph(data: list[str], fill_char: str = " ") -> np.ndarray:
    """
    Convert text lines to a 2D array of Unicode chars.

    NOTE: Numpy's U1 is fixed-width 4 bytes, whereas latin and most kanji fit
    within 2 bytes in variable-width UTF-8. Also consider O(n^2) worst case
    padding for uneven line lengths on n text.
    """
    longest_line = max(len(s) for s in data)
    working_data = [[*s.ljust(longest_line, fill_char)] for s in data]
    unicode_array = np.array(working_data, dtype="<U1")
    
    return unicode_array


def build_kana_heatmap(labels: np.ndarray, weights: np.ndarray) -> plt.Axes:
    """
    Initialises a clean, fancy heatmap for 2D kana.
    """
    # Maximise plot size, but keep the window small
    r, c = labels.shape
    plt.figure(figsize=(c / 4, r / 4))

    # Customised for an actually white background
    cmap = LinearSegmentedColormap.from_list("", ["white", "darkturquoise"])

    ax = sns.heatmap(
        weights,
        vmin=0, 
        vmax=1,
        cmap=cmap,
        annot=labels,
        annot_kws={"fontfamily": "Meiryo"},
        fmt="s",
        cbar=False,
        xticklabels=False,
        yticklabels=False,
        square=True,
    )
    plt.tight_layout()

    return ax
