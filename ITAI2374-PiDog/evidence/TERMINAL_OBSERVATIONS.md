# Historical robotics evidence — November 17–18, 2026

Selected verbatim lines from the student's saved PiDog terminal session. Private network details and unrelated speech were omitted. This is a curated excerpt, not a complete log, video, or independent physical trial.

## Speech and action dispatch

```text
[STT RAW] 'scratch your head'
[STT NORMALIZED] 'scratch your head'
[SCRATCH] Starting two slow head scratches.
[SCRATCH] Completed.
[MOTION] Routine ended; voice remains active.
```

## Camera observations

```text
[OBJECTS] person 97% / green / left
[COLORS] orange left; green right; green left
[BUDDY] Camera stopped.
```

The displayed percentage is a detector confidence, not measured accuracy.

## Failure handling and ranging

```text
[BUDDY] Looking for a face. I will move only if the path is clear.
[BUDDY] Ultrasonic distance is invalid or path is too close. I cannot move safely.
[BUDDY] I cannot see one clear face. I am staying here.
[BUDDY] I see a green bottle-like target ahead, but distance is uncertain.
[BUDDY] I see a green bottle-like target ahead. The ultrasonic echo in that direction is about 65 centimeters. The echo may be from another surface.
```

The evidence supports camera/color outputs and conservative behavior when sensor readings were uncertain. It does not establish that the echo corresponds to the bottle, that a full orbit succeeded or that the system reliably identifies the speaker.

## Offline review

The recovered Lab 10 test suite (8 tests), Buddy Autonomy self-test and V9 self-test (8 assertions) passed in the review environment. These are software checks, not physical results. No original photographs or videos of the hardware were available for inclusion during this review.
