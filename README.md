# ui-beam-finder

Experimental scripts for Ui Beams detection and visualisation. Might also be
useful for constructing new Ui Beams from existing text...

The number one goal is to avoid fancy AI stuff, keeping it alll classical where
possible. Of course, this does compromise effectiveness and flexibility.

## Exact Search
Simply scans 8-way beams of Beams on an aligned kana matrix with a small,
hardcoded set of stand-ins.

### Other Possible Approaches
The current method uses variable length rows which maintains O(nm) for n text
and m pattern regardless of 2D shape. Assuming the average is a relatively even
paragraph and matches for the first pattern character set are sparse, this is
closer to O(n) average.

Pre-loading into a Numpy padded array is unlikely to offer significant linear
speedups without being able to vectorise. Vectorised search would increase the
average to at least O(nm), and the worst case to O(n^2 m) on sufficiently large
and uneven text.

However, in the unusual case where the text is expected to be big but also even,
Scipy's FFT 2D convolve might be a interesting O(n log(n) m) array solution.
This method might be an cool line probability detector for candidate search, if
a bit fiddly...

### Limitations
As a simple 5 char search of monospace chars, this does not support:
- Half or variable-width char alignments
- Spaced, hyphenated, or off-axis Beams
- The really pesky context-specific kanji (to be addressed in next searcher)
- Beams that rely on text wrapping
- Koyo Beams

There are also no plans yet to:
- Restore pruned lines visually on display

### Pending Work
- Configurable text wrapping (check if Marshmallows come in standard size)
- Write actual unit tests...

## Candidate Heatmap
Highlights and weights candidates to simplify human detection of
context-specific Kanji, funky Unicode, and non-trivially aligned paragraphs.

There are plans for approximate line detection... eventually?

### Candidate Metric
The `candidates/` folder currently contains the following score mappings:
- Main set: Hand-crafted weights, including the actual Ui Beam.
- Known trick set: Based on kanji used in past Beam pranks, but may source from
other notable wordplay in the future.

Loose guidelines for weight tuning may include whether it is applicable in all
directions, whether it is visual or a reading, whether it is a common reading,
if it is used a ton for these pranks (none qualify so far), and whether it is
a full-width character on most fonts.

Currently, visualisation only uses a single score, so the max weight is taken
after merging all datasets.

### Limitations
- Cannot discern context-sensitive readings, so applying a light default weight
is the best I can do for now.
- Dynamic range and indistinctness of similar weights on continuous colour maps
both limit heatmap visualisation effectiveness.
- The jouyou kanji set is inherently missing several common kanji, and probably
lacks some kanji common to niche sub-communities.

### Pending Work
- Need to see if there is a good way to make use of `beam_index` metadata for
extended visualisation (gradient colour by index, approximate line detection,
interactive filters, etc)
    - Regarding line detection, it might be doable if a local radius, threshold
    angle search. This naturally handles limited curvatures and spaced lines.
- Add widgets to the plot for a simple GUI to edit configs
- Need to figure out a way to change text colour to a contrasting one, allowing
a larger dynamic range for the highlighting colour