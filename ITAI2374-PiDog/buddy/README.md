# Buddy — Human-Robot Interaction and Vision Experiments

This is a recovered archive of actual course-development Python files, not a claim that the latest robot image was recovered. The terminal transcript contains later incomplete/corrupted pasted versions; those are not distributed as runnable software.

| File | Scope | Verification |
|---|---|---|
| [buddy_autonomy.py](buddy_autonomy.py) | Strict natural-language command parsing, action sequencing, cancellation and simulated roaming | Original offline self-test passed in portfolio review |
| [buddy_ultra.py](buddy_ultra.py) | Expressive sound, face/scene/color vision, optional local Ollama vision | Syntax checked; requires original runtime modules |
| [buddy_vision_all.py](buddy_vision_all.py) | Voice-command routing to object/color detection | Syntax checked; requires prior Buddy Final/vision modules |
| [buddy_explore_bottle_v9.py](buddy_explore_bottle_v9.py) | Robust range filtering and supervised bottle search/orbit prototype | Eight built-in offline assertions passed; physical orbit completion not evidenced |

## Reproduce the offline experiments

From this directory with Python 3.10+:

```bash
python buddy_autonomy.py --self-test
python buddy_explore_bottle_v9.py --self-test
python -m py_compile buddy_autonomy.py buddy_ultra.py buddy_vision_all.py buddy_explore_bottle_v9.py
```

No robot, microphone, camera, network, model download or paid API is required for these two self-tests. The simulator tests action queues and command decisions, not real-world motion. The V9 test verifies valid/invalid range scenarios and turn selection only.

## Hardware environment

These are extensions developed for the original PiDog installation. Use the vendor's OS-specific PiDog, Robot HAT and Vilib setup. Camera extensions use Picamera2, OpenCV and NumPy; optional local vision uses Ollama. The original `buddy_repeat.py`, `buddy_head_scratch.py`, `buddy_final.py`, `buddy_vision_directo.py` and `buddy_orbit_motion_v6.py` dependency chain was not recovered in full. Do not run these historical extensions as a standalone hardware release. The [midterm and Lab 10 source](../README.md) are the supported hardware examples in this portfolio.

No external training dataset is bundled; images/audio originate from live sensors. Optional model inference depends on locally installed model weights. No credentials or private host paths are published; the recovered V9 hardcoded home directory was replaced with its script directory.

## Results and lessons

Historical [terminal observations](../evidence/TERMINAL_OBSERVATIONS.md) show speech recognition, action dispatch, routine completion and camera detections, alongside misrecognition, unreliable range and failed face acquisition. The logs do not establish distance accuracy, person identification, verified arrival at a speaker or continuous orbit success. Natural-language command execution is rule-based; optional LLM chat/vision is a separate experimental integration. Next steps: restore the missing hardware dependencies from the original Pi, test each component independently, then record supervised closed-loop trials.
