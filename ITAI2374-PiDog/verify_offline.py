"""Run hardware-independent checks only. No robot libraries are imported."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
commands = [
    [sys.executable, "-m", "unittest", "-v", "test_lab10_logic.py"],
    [sys.executable, "buddy/buddy_autonomy.py", "--self-test"],
    [sys.executable, "buddy/buddy_explore_bottle_v9.py", "--self-test"],
    [sys.executable, "-m", "py_compile", "pidog_midterm.py", "lab10_multisensor.py",
     "lab01/Jose_Tuozzo_Lab1_PiDog_RaspberryPi.py", "buddy/buddy_autonomy.py",
     "buddy/buddy_ultra.py", "buddy/buddy_vision_all.py", "buddy/buddy_explore_bottle_v9.py"],
]
for command in commands:
    subprocess.run(command, cwd=ROOT, check=True)
print("All offline robotics checks passed; no physical hardware tested.")
