#!/usr/bin/env python3
"""
ITAI 2374 - Lab 1: Robotics Hardware and Software Introduction
Student: Jose Miguel Tuozzo Izaguirre

Target hardware:
    SunFounder PiDog + Raspberry Pi + Robot HAT

Run this file ON THE RASPBERRY PI connected to the PiDog.
It is not intended for Google Colab.

This lab test:
1. Confirms Raspberry Pi/Linux environment information.
2. Checks that pidog and robot_hat can be imported.
3. Checks whether the Raspberry Pi I2C device interface is available.
4. Initializes the physical PiDog through the official Pidog class.
5. Runs a conservative wake/sit/tail sequence using the PiDog API.

IMPORTANT:
- Place PiDog on a clear, stable surface before running.
- Keep hands away from the joints while servos are powered.
- Servo calibration should already be completed according to SunFounder documentation.
"""

import os
import sys
import time
import platform
from pathlib import Path
import subprocess


def section(title):
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def check_environment():
    section("1. RASPBERRY PI / OPERATING SYSTEM CHECK")
    print("System:", platform.system())
    print("Machine:", platform.machine())
    print("Python:", platform.python_version())
    print("Hostname:", platform.node())

    try:
        model = Path("/proc/device-tree/model").read_text(errors="ignore").replace("\x00", "").strip()
        print("Board:", model)
    except Exception:
        print("Board: Could not read /proc/device-tree/model")

    print("User:", os.environ.get("USER", "unknown"))


def check_libraries():
    section("2. PIDOG / ROBOT-HAT LIBRARY CHECK")

    status = {"pidog": False, "robot_hat": False}

    try:
        import pidog
        status["pidog"] = True
        print("PASS: pidog library imported successfully.")
    except Exception as e:
        print("FAIL: pidog import:", e)

    try:
        import robot_hat
        status["robot_hat"] = True
        print("PASS: robot_hat library imported successfully.")
    except Exception as e:
        print("FAIL: robot_hat import:", e)

    return status


def check_i2c():
    section("3. I2C CHECK")
    devices = sorted(Path("/dev").glob("i2c-*"))
    if devices:
        print("PASS: I2C device interface detected:")
        for d in devices:
            print(" -", d)
    else:
        print("WARNING: No /dev/i2c-* interface was detected.")

    if shutil_which("i2cdetect"):
        print("\nI2C bus scan (bus 1):")
        try:
            subprocess.run(["i2cdetect", "-y", "1"], check=False)
        except Exception as e:
            print("Could not run i2cdetect:", e)
    else:
        print("INFO: i2cdetect is not installed; skipping address scan.")


def shutil_which(command):
    from shutil import which
    return which(command)


def run_physical_demo():
    section("4. PHYSICAL PIDOG INITIALIZATION")

    from pidog import Pidog

    print("Initializing PiDog...")
    dog = Pidog()
    print("PASS: Physical PiDog object initialized.")

    try:
        section("5. PHYSICAL WAKE-UP / SIT / TAIL TEST")
        print("The robot may move now. Keep the area around PiDog clear.")

        # Use the high-level PiDog action API.
        # These are intentionally simple movements for Lab 1.
        print("Action 1: Wake / stand posture")
        try:
            dog.do_action("stand", speed=60)
            time.sleep(1)
        except Exception as e:
            print("Stand action unavailable or failed:", e)

        print("Action 2: Sit")
        dog.do_action("sit", speed=60)
        time.sleep(1)

        print("Action 3: Wag tail")
        # Tail API differs slightly across PiDog package revisions.
        # Prefer the official high-level action when available.
        try:
            dog.do_action("wag_tail", speed=70)
        except Exception:
            try:
                dog.tail_move([[0], [30], [-30], [30], [-30], [0]], immediately=True, speed=70)
            except Exception as e:
                print("Tail action could not be executed:", e)
                raise

        time.sleep(2)
        print("\nPASS: Physical movement commands completed.")
        print("Observed sequence requested: stand/wake -> sit -> wag tail.")

    finally:
        section("6. SAFE SHUTDOWN")
        try:
            dog.close()
            print("PiDog resources closed safely.")
        except Exception as e:
            print("Close warning:", e)


def main():
    section("ITAI 2374 - LAB 1 PHYSICAL PIDOG TEST")
    print("SunFounder PiDog + Raspberry Pi + Robot HAT")

    check_environment()
    status = check_libraries()
    check_i2c()

    if not status["pidog"]:
        print("\nSTOP: pidog is not installed correctly.")
        print("Install the official SunFounder PiDog software before continuing.")
        sys.exit(1)

    print("\nHardware movement test is ready.")
    answer = input("Type YES to initialize and move the physical PiDog: ").strip().upper()

    if answer != "YES":
        print("Physical movement test cancelled. No movement command was sent.")
        return

    try:
        run_physical_demo()
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print("\nPHYSICAL TEST ERROR:", repr(e))
        print("Check PiDog assembly, servo calibration, Robot HAT power, and SunFounder setup.")


if __name__ == "__main__":
    main()
