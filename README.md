# ui-beam-finder

Experimental scripts for Ui Beams detection and visualisation. Might also be
useful for constructing new Ui Beams from existing text...

The number one goal is to avoid fancy AI stuff, keeping it alll classical where
possible. Of course, this does compromise effectiveness and flexibility.

## Exact Search
The simplest and least flexible of the two. Scans 8-way beams of Beams on an
aligned kana matrix with a small, hardcoded set of stand-ins.

### Limitations
As a simple 5 char search of monospace chars, this does not support:
- Half or variable-width char alignments
- Spaced, hyphenated, or off-axis Beams
- The really pesky context-specific kanji (to be addressed in next searcher)
- Beams that rely on text wrapping
- Koyo Beams

There are also no plans yet to:
- Restore pruned lines visually on display

## Candidate Heatmap
Highlights candidates by character probability to simplify human detection of
Kanji trickery, (some) funky Unicode, and paragraphs misaligned with
variable-width chars.

Contains a configurable wobbly line detector.

### Candidate Metric
The `candidates/` folder currently contains the following score mappings:
- Main set: Hand-crafted weights, including the actual Ui Beam.
- Known trick set: Based on kanji used in past Beam pranks, but may source from
other notable wordplay in the future.
- Jouyou set: Every jouyou kanji as of 2020, filtered only to those with
Beam-applicable readings.

Loose guidelines for weight tuning may include whether it is applicable in all
directions, whether it is visual or a reading, whether it is a common reading,
if it is used a ton for these pranks (none qualify so far), and whether it is
a full-width character on most fonts.

Currently, visualisation only uses a single score, so the max weight is taken
after merging all datasets.

### Limitations
- Cannot infer actual reading(s), so applying a light default weight
is the best I can do for now.
- The jouyou kanji set is inherently missing several common kanji, and probably
lacks some kanji common to niche sub-communities.

### Possible Work
Although this project is pretty much concluded, good-to-have features include:
- Variable-width display and heatmap, with configurable fonts.
- Matplotlib widgets or proper GUI for toggling search type/configs.
- Package it for laughs.
