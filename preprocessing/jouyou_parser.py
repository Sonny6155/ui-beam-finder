import csv

# Pre-process full kanji data into candidates format
# Source: https://github.com/sph-mn/kanji/blob/master/download/jouyou-kanji.csv

# Define which kanji to select, and which Ui Beam char they correspond to
beam_index_map = {
    "u": [0],
    "i": [1, 3],
    "bi": [2],
    "be": [2],
    "m": [4],
}

new_csv_data = ["char,beam_index,score"]

# Parse out components
# NOTE: Currently in spaced "char ["]meaning["] reading1/reading2..." form
lines = open("jouyou-kanji.csv", "r", encoding="utf-8").readlines()
for split_line in csv.reader(
    lines, quotechar='"', delimiter=" ", quoting=csv.QUOTE_ALL, skipinitialspace=True
):  # Reader handles quoting
    if len(split_line) == 3:
        char, _, readings = split_line
        for reading in readings.split("/"):

            # Check if any reading starts with Beam-ish characters
            for prefix, to_update in beam_index_map.items():
                if reading.startswith(prefix):
                    for beam_index in to_update:
                        new_csv_data.append(f"{char},{beam_index},0.2")
    else:
        print("Ignored line:", split_line)

# Concat and output
open("jouyou_set.csv", "x", encoding="utf-8").write("\n".join(new_csv_data) + "\n")
