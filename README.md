# ui-beam-finder

An experimental script for Ui Beams detection and visualisation. Simply scans
8-way beams of Beams on an aligned kana matrix with a small, hardcoded set of
stand-ins.

## Limitations
As a simple 5 char search of monospace chars, this does not support:
- Half or variable-width char alignments
- Spaced, hyphenated, or off-axis Beams
- The really pesky context-specific kanji (to be addressed in next searcher)
- Beams that rely on text wrapping
- Koyo Beams

There are also no plans yet to:
- Restore pruned lines visually on display

## Pending Work
### Improvements for Current Version
- It would be good to clean up the current display method, if possible.
- Configurable text wrapping (check if Marshmallows come in standard size)
- Better JP sanitisation (well, use case research comes first)
- Write actual unit tests...

### Candidate Heatmap
Highlights and weights candidates to simplify human detection of
context-specific Kanji, funky Unicode, and non-trivially aligned paragraphs.
This can also be used in automated detector pipeline. In terms of additional
line visualisation helpers:
- Highly generic auto line detection seems hard, but maybe a *very* loose form
of Hough transform could work on aligned matrices?
- Maybe a tiered connect-the-dots-like approach could work depending on
candidate density.

The plan:
1. Read and sanitise text data.
2. Apply character probability mapping, configurable as an external file.
3. (Optional) Compute approximated or exact line detection, based on cumulative
probability, angle, and connectivity.
4. Display on Seaborn heatmap for visualisation.

Loose candidate metric guidelines:
- Perfect matches should be max probability.
- Alt kana should only be slightly less than max.
- Half/full-width latin should be ranked lower than alt kana.
    - Partial like "b" or 4th "i" should be very low
    - Extra romanised characters ("e", "a", and similar shaped) should be even
    lower.
- Some kanji known to have been used before will be ranked higher.
- Kanji that are commonly used for similar wordplay be ranked higher.
    - This includes kanji like "一", but also blatant radical tricks like "仏".
    - Let's say for now that these shouldn't exceed 0.2?
- Kanji that are only distinctly similar like "be" or situational "bi" should
be lower.
- Other kanji with start with the same romanised letter should be extremely low.

The unknowns:
- Would colouring by line probablity or line index be more useful than by
individual char score?
    - Maybe add configs to test this?
- How do we best implement associated line index info (per mapping) on the
final array, and where will we use it?
- Could we throw in matplotlib widgets to allow the user to test various
configs easily?
