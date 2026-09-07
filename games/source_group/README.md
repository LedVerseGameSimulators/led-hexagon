# Group / Corporate mode levels (LED Hexagon / Arena)

Corporate playlist (10 levels):

1. **BASIC** `source_group/-/{05,06,07,08,09}.led`
2. **Advance** `source_group/--/{YC01…YC05}.led`

Play order: 05 → 09, then YC01 → YC05 (`_TIERS_GROUP = ["-", "--"]`).

Copied from `games/source/`. Effects run on the shared marathon loop. (No
headless floor scaler in either single or group mode.)
