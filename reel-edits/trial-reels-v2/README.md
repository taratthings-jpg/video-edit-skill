# Trial reels v2

50 trial reels for @taraphilipofficial: one on-screen line over one 7-second b-roll clip. Each one has its own trending track and its own caption.
Source: `BRIEF.md`, copied from the "Trial reels v2 · 7-second overlays" tab of the Content Waterfall doc on 10 Nov 2026.

## What's here
- `NN-slug/`: one project per reel, containing:
  - `overlay.png`: the text overlay
  - `caption.txt`: the caption
  - `project.json`: clip, audio and backup, keyword and posting settings
  - `EDIT.md`: the edit sheet, with the Edits app steps
- `clips/`: drop the b-roll here as `NN.mov` or `NN.mp4`. Clips are not committed.
- `reels.json`: all 50 reels as data.
- `overlays-sheet.jpg`: every overlay on one sheet, for review.
- `desk/`: the Trial Reels Desk page (https://claude.ai/artifact/LrDUx81fVNnhqEk5NJ57Ey).

## Make a reel
    python3 scripts/trial_reels.py render 07       # one reel
    python3 scripts/trial_reels.py render          # every reel with a clip in clips/
This writes `NN-slug/NN-slug.mp4`: 1080 x 1920, 7 seconds, overlay burned in, a silent audio track, H.264.
Open it in Edits and add the track from `EDIT.md`. Then add the export to the reel in the desk.

## Post
In the desk, open the reel and press **Post**. Posting walks through four steps:
1. Export the video.
2. Copy the caption.
3. Confirm that the audio is added, trial reel is on, and Share to Facebook and Share to Threads are off.

Only then does **Mark as posted** unlock. The desk records the post time, the settings and the audio used. Add views, follows and shares there afterwards.
