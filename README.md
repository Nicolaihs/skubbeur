# Clockface

A fullscreen pygame analog clock. In the last hour before `end_time` (set in
`config.yaml`), the clock face turns red and the red area shrinks by one
sixtieth each minute; in the last 5 minutes it blinks. During that same hour,
images for configured `slots` are shown outside the clock face at the angle
of each slot's midpoint time. Press **Space** to play the sound of whichever
slot is currently active, or the `fallback_sound` if none is. For 5 minutes
after `end_time`, the whole screen flashes and the `siren_sound` repeats at
random 5-20s intervals. Press **Esc** or close the window to quit.

## Run

```sh
uv sync
uv run clockface [path/to/config.yaml]   # defaults to ./config.yaml
```

## Configuration

Edit `config.yaml`:

```yaml
end_time: "17:00"
fallback_sound: "assets/sounds/fallback.wav"  # optional, played when no slot is active
siren_sound: "assets/sounds/siren.wav"        # optional, played during the 5 min after end_time
slots:
  - start: 50   # minutes before end_time (50 = 16:10 if end_time is 17:00)
    end: 40     # minutes before end_time
    image: "https://example.com/image.png"  # downloaded and cached in .cache/
    sound: "assets/sounds/slot1.wav"        # local file path
```

`start`/`end` must fall within 0-60 minutes before `end_time` to be visible.
