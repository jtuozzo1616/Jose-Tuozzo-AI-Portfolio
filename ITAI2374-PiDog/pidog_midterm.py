#!/usr/bin/env python3
"""PiDog midterm: motion, custom inspection, sensor response, SSH terminal control.

Run on PiDog's Raspberry Pi (not on a normal laptop):
    sudo python3 pidog_midterm.py --mode menu

Author: Jose Tuozzo | ITAI 2374 | 2026-11-02
The software includes new integrated routines. Confirm them on the hardware
before describing their behavior as tested. Original tested routine is in
recorded_inspection.py.
"""

import argparse
import math
import time
from typing import Optional


DEFAULT_THRESHOLD_CM = 18.0
SENSOR_MAX_CM = 400.0


def valid_distance(value):
    """Return True only for plausible measurements; invalid values are ignored."""
    try:
        distance = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(distance) and 2.0 <= distance <= SENSOR_MAX_CM


def distance_state(value, threshold_cm=DEFAULT_THRESHOLD_CM):
    """Pure decision logic: UNKNOWN / NEAR / CLEAR, independent of PiDog.

    Note: this is a software state, not a guarantee of physical clearance.
    """
    if not valid_distance(value):
        return "UNKNOWN"
    return "NEAR" if float(value) <= threshold_cm else "CLEAR"


class MidtermController:
    """SSH-operated, sequential PiDog demonstrations with safe cleanup."""

    def __init__(self, dog, sleeper=time.sleep, clock=time.monotonic, printer=print):
        self.dog = dog
        self.sleep = sleeper
        self.clock = clock
        self.print = printer

    def action(self, name, steps=1, speed=40):
        self.print(f"ACTION: {name} | steps={steps} | speed={speed}", flush=True)
        self.dog.do_action(name, step_count=steps, speed=speed)
        self.dog.wait_all_done()

    def stop(self):
        """Clear active motion buffers; Ctrl+C also invokes this in main()."""
        self.print("STOP: clearing leg, head, and tail queues", flush=True)
        self.dog.body_stop()

    def basic_motion_demo(self):
        """One short command at a time to avoid queuing a long uninterruptible run."""
        self.print("DEMO: Basic motion", flush=True)
        self.action("stand", speed=35)
        self.action("forward", steps=1, speed=45)
        self.action("backward", steps=1, speed=45)
        self.action("turn_left", steps=1, speed=42)
        self.action("turn_right", steps=1, speed=42)
        self.stop()
        self.action("sit", speed=35)
        self.print("BASIC MOTION COMPLETE", flush=True)

    def inspection_sequence(self):
        """Student-authored choreography derived from the successful terminal run.

        Built-in primitives are combined into a new ordered action; the head
        sweep is an explicitly programmed list of servo-angle keyframes.
        """
        self.print("CUSTOM ACTION: Multi-step inspection sequence", flush=True)
        self.action("stand", speed=35)
        self.dog.head_move(
            [[0, 0, 0], [25, 0, 0], [-25, 0, 0], [0, 0, 0]],
            speed=30,
        )
        self.dog.wait_all_done()
        self.action("tilting_head", steps=2, speed=30)
        self.sleep(1.0)
        self.action("sit", speed=35)
        self.print("CUSTOM INSPECTION COMPLETE", flush=True)

    def sensor_snapshot(self):
        distance = self.dog.ultrasonic.read_distance()
        touch = self.dog.dual_touch.read()
        self.print(
            f"SENSORS: distance={distance} cm | state={distance_state(distance)} "
            f"| touch={touch}",
            flush=True,
        )
        return distance, touch

    def respond_to_obstacle(self):
        """Visible reaction without autonomous walking into an unsafe area."""
        self.print("TRIGGER: nearby object -> pause + head recoil", flush=True)
        self.stop()
        self.dog.head_move([[0, 0, 0], [0, 0, -14], [0, 0, 0]], speed=30)
        self.dog.wait_all_done()
        self.action("wag_tail", steps=3, speed=45)

    def respond_to_touch(self, touch):
        """Touch sensor response distinct from the distance sensor response."""
        self.print(f"TRIGGER: touch={touch} -> head sweep + tail wag", flush=True)
        self.dog.head_move([[12, 0, 0], [-12, 0, 0], [0, 0, 0]], speed=30)
        self.dog.wait_all_done()
        self.action("wag_tail", steps=3, speed=45)

    def sensor_demo(self, duration=35.0, threshold_cm=DEFAULT_THRESHOLD_CM,
                    interval=0.25):
        """Limited-duration ultrasonic + touch behavior for a live demonstration.

        Distance alert triggers once per approach; it rearms after the object
        moves at least 10 cm beyond the threshold. Invalid measurements never
        trigger movement. Touch alerts require a fresh non-N state transition.
        """
        if duration <= 0 or threshold_cm < 5 or threshold_cm > 60:
            raise ValueError("Duration must be positive; threshold 5–60 cm")
        self.print(
            f"DEMO: Sensors | duration={duration:g}s | threshold={threshold_cm:g} cm",
            flush=True,
        )
        self.action("stand", speed=35)
        deadline = self.clock() + duration
        obstacle_latched = False
        last_touch = "N"
        next_touch_time = 0.0
        last_status_time = float("-inf")
        while self.clock() < deadline:
            current = self.clock()
            distance = self.dog.ultrasonic.read_distance()
            touch = self.dog.dual_touch.read()
            status = distance_state(distance, threshold_cm)

            if current - last_status_time >= 1.0:
                self.print(
                    f"READING: {distance} cm | {status} | touch={touch}",
                    flush=True,
                )
                last_status_time = current

            if status == "NEAR" and not obstacle_latched:
                obstacle_latched = True
                self.respond_to_obstacle()
            elif status == "CLEAR" and float(distance) > threshold_cm + 10:
                obstacle_latched = False

            if touch not in (None, "N") and touch != last_touch \
                    and self.clock() >= next_touch_time:
                self.respond_to_touch(touch)
                next_touch_time = self.clock() + 1.5
            last_touch = touch
            self.sleep(interval)
        self.action("sit", speed=35)
        self.print("SENSOR DEMONSTRATION COMPLETE", flush=True)

    def menu(self):
        """A plain SSH terminal is sufficient; no web server is required."""
        options = {
            "1": self.basic_motion_demo,
            "2": self.inspection_sequence,
            "3": self.sensor_demo,
            "4": self.sensor_snapshot,
            "5": self.stop,
        }
        while True:
            self.print(
                "\nPiDog MIDTERM | 1 Motion | 2 Custom | 3 Sensors "
                "| 4 Read sensors | 5 STOP | 0 Exit",
                flush=True,
            )
            command = input("Choose: ").strip()
            if command == "0":
                return
            if command not in options:
                self.print("Choose 0, 1, 2, 3, 4, or 5.", flush=True)
                continue
            options[command]()


def main(argv: Optional[list] = None):
    parser = argparse.ArgumentParser(description="PiDog ITAI 2374 midterm demos")
    parser.add_argument(
        "--mode", choices=("menu", "motion", "custom", "sensors", "read", "stop"),
        default="menu",
    )
    parser.add_argument("--duration", type=float, default=35)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_CM)
    args = parser.parse_args(argv)

    # Import inside main so pure logic can be tested on a non-Raspberry Pi host.
    from pidog import Pidog
    dog = None
    try:
        dog = Pidog()
        controller = MidtermController(dog)
        if args.mode == "menu":
            controller.menu()
        elif args.mode == "motion":
            controller.basic_motion_demo()
        elif args.mode == "custom":
            controller.inspection_sequence()
        elif args.mode == "sensors":
            controller.sensor_demo(duration=args.duration, threshold_cm=args.threshold)
        elif args.mode == "read":
            controller.sensor_snapshot()
        elif args.mode == "stop":
            controller.stop()
    except KeyboardInterrupt:
        print("Keyboard interruption: stopping commands", flush=True)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", flush=True)
        raise
    finally:
        if dog is not None:
            try:
                dog.body_stop()
            finally:
                dog.close()


if __name__ == "__main__":
    main()
