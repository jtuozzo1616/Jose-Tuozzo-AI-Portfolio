#!/usr/bin/env python3
"""Lab 10 - Autonomous Navigation and Multi-Sensor Fusion (SunFounder PiDog).

Fuses: ultrasonic obstacle ranging, Vilib green-marker vision,
dual-touch commands, and sound-source bearing.

IMPORTANT: Run supervised on a flat, enclosed course. Never rely on this
experimental program for collision-free operation near people or stairs.

Reference: https://docs.sunfounder.com/projects/pidog/en/latest/
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
import time
from pathlib import Path
from typing import Optional

# Safety and geometric heuristics, in centimeters / pixels.
STOP_CM = 30.0        # Stop forward motion when anything is inside this radius.
SIDE_CLEAR_CM = 38.0 # Required free ultrasonic distance to select a turn.
HARD_STOP_CM = 12.0  # Emergency cutoff during an already commanded turn.
GOAL_MIN_AREA = 15000
GOAL_MAX_DISTANCE = 65.0
MIN_MARKER_AREA = 300
FRAME_CENTER = 160
FRAME_DEADBAND = 48
LEFT_SCAN_YAW = 40  # Default convention; validate on your PiDog.
RIGHT_SCAN_YAW = -40
SOUND_VALID_FOR_S = 5.0
SENSOR_POLL_S = 0.12
MAX_MOTION_TIME_S = 7.0
CSV_FIELDS = [
    'time', 'state', 'front_cm', 'left_cm', 'right_cm', 'touch',
    'sound_deg', 'marker_x', 'marker_area', 'command', 'notes'
]


def clean_distance(value: object) -> Optional[float]:
    """PiDog returns -1 on an ultrasonic fault; invalid distances are unsafe."""
    try:
        d = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(d) or d < 2.0 or d > 400.0:
        return None
    return d


def marker_side(x: Optional[int], area: int) -> Optional[str]:
    """Use Vilib's image coordinate system: 0..320, left to right."""
    if x is None or area < MIN_MARKER_AREA:
        return None
    if x < FRAME_CENTER - FRAME_DEADBAND:
        return 'left'
    if x > FRAME_CENTER + FRAME_DEADBAND:
        return 'right'
    return 'center'


def sound_side(degrees: Optional[float]) -> Optional[str]:
    """SunFounder: 0=front, 90=right, 270=left."""
    if degrees is None:
        return None
    angle = float(degrees) % 360
    if 45 <= angle <= 135:
        return 'right'
    if 225 <= angle <= 315:
        return 'left'
    return None


def choose_avoidance(left: Optional[float], right: Optional[float],
                     marker: Optional[str], sound: Optional[str]) -> Optional[str]:
    """Clearance is mandatory; vision & audio only bias *already-safe* routes."""
    options = {}
    if left is not None and left >= SIDE_CLEAR_CM:
        options['left'] = float(left)
    if right is not None and right >= SIDE_CLEAR_CM:
        options['right'] = float(right)
    if not options:
        return None
    for side in options:
        if marker == side:
            options[side] += 15.0
        elif marker is None and sound == side:
            options[side] += 7.0
    return max(options, key=options.get)


class Navigator:
    def __init__(self, dog, vision, args):
        self.dog = dog
        self.vision = vision
        self.args = args
        self.paused = False
        self.last_touch_time = 0.0
        self.last_sound_side = None
        self.last_sound_time = 0.0
        self.last_sound_deg = None
        self.goal_reached = False
        self.camera_started = False
        self.state = 'INITIALIZING'
        self.latest_touch = 'N'
        self.latest_marker_x = None
        self.latest_marker_area = 0
        self.latest_distance = None
        self.logfile = Path(args.log).open('w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.logfile, fieldnames=CSV_FIELDS)
        self.writer.writeheader()
        self.log('INITIALIZING', 'init', 'Initializing PiDog')

    def log(self, state: str, command: str, notes: str = '',
            front: Optional[float] = None, left: Optional[float] = None,
            right: Optional[float] = None):
        self.state = state
        data = dict(time=time.strftime('%Y-%m-%d %H:%M:%S'), state=state,
                    front_cm=round(front, 1) if front is not None else '',
                    left_cm=round(left, 1) if left is not None else '',
                    right_cm=round(right, 1) if right is not None else '',
                    touch=self.latest_touch,
                    sound_deg=self.last_sound_deg if self.last_sound_deg is not None else '',
                    marker_x=self.latest_marker_x if self.latest_marker_x is not None else '',
                    marker_area=self.latest_marker_area,
                    command=command, notes=notes)
        self.writer.writerow(data)
        self.logfile.flush()
        print(f"[{state:>15}] {command:<15} {notes}", flush=True)

    def distance(self, attempts=3) -> Optional[float]:
        samples = []
        for i in range(attempts):
            raw = self.dog.ultrasonic.read_distance()
            value = clean_distance(raw)
            if value is not None:
                samples.append(value)
            if i != attempts - 1:
                time.sleep(0.065)
        return statistics.median(samples) if len(samples) >= max(1, (attempts + 1) // 2) else None

    def sense_touch(self):
        status = self.dog.dual_touch.read()
        self.latest_touch = str(status).upper()
        now = time.monotonic()
        if self.latest_touch in ('L', 'LS') and now - self.last_touch_time > 1.0:
            self.paused = True
            self.last_touch_time = now
            self.dog.body_stop()
            self.log('PAUSED', 'stop', 'Front/left touch: manual pause')
        elif self.latest_touch in ('R', 'RS') and now - self.last_touch_time > 1.0:
            self.paused = False
            self.last_touch_time = now
            self.log('RESUMED', 'resume', 'Rear/right touch: continue')

    def sense_sound(self):
        # Speaker sounds have intentionally been omitted to avoid self-triggering.
        if self.dog.ears.isdetected():
            direction = self.dog.ears.read()
            if direction is not None:
                self.last_sound_deg = int(direction)
                new_side = sound_side(self.last_sound_deg)
                if new_side is not None:
                    self.last_sound_side = new_side
                    self.last_sound_time = time.monotonic()
                    self.log('SOUND', 'bearing', f'{direction} deg -> {new_side}')

    def active_sound_side(self):
        if time.monotonic() - self.last_sound_time < SOUND_VALID_FOR_S:
            return self.last_sound_side
        return None

    def sense_vision(self):
        if self.vision is None:
            self.latest_marker_x = None
            self.latest_marker_area = 0
            return None
        params = self.vision.detect_obj_parameter
        try:
            n = int(params['color_n'])
            w = int(params['color_w'])
            h = int(params['color_h'])
            x = int(params['color_x'])
        except (KeyError, ValueError, TypeError):
            n, w, h, x = 0, 0, 0, None
        area = max(0, w) * max(0, h) if n > 0 else 0
        self.latest_marker_area = area
        self.latest_marker_x = x if area >= MIN_MARKER_AREA else None
        return marker_side(self.latest_marker_x, area)

    def head(self, yaw):
        self.dog.head_move([[yaw, 0, 0]], immediately=True, speed=65)
        self.dog.wait_head_done()
        time.sleep(0.18)

    def scan_sides(self):
        """Rotate the *ultrasonic head*, not the body, to probe both directions."""
        try:
            self.head(-LEFT_SCAN_YAW if self.args.invert_scan else LEFT_SCAN_YAW)
            left = self.distance()
            self.head(-RIGHT_SCAN_YAW if self.args.invert_scan else RIGHT_SCAN_YAW)
            right = self.distance()
            return left, right
        finally:
            self.head(0)

    def move(self, action, speed=85, emergency_cm=STOP_CM) -> bool:
        """One gait step, checking the ultrasonic range DURING movement."""
        self.dog.do_action(action, step_count=1, speed=speed)
        started = time.monotonic()
        while not self.dog.is_legs_done():
            self.sense_touch()
            if self.paused:
                self.dog.body_stop()
                return False
            measured = self.distance(attempts=1)
            self.latest_distance = measured
            if measured is None or measured < emergency_cm:
                self.dog.body_stop()
                self.log('EMERGENCY_STOP', 'body_stop',
                         f'{action}: ultrasonic reading unsafe: {measured}', front=measured)
                return False
            if time.monotonic() - started > MAX_MOTION_TIME_S:
                self.dog.body_stop()
                raise RuntimeError(f'Action timed out: {action}')
            time.sleep(SENSOR_POLL_S)
        return True

    def avoid(self, front):
        self.dog.body_stop()
        self.log('OBSTACLE', 'stop_scan', f'Forward obstruction at {front:.1f} cm', front=front)
        left, right = self.scan_sides()
        # Vision may be stale during scanning; re-check after looking forward.
        time.sleep(0.18)
        visual = self.sense_vision()
        decision = choose_avoidance(left, right, visual, self.active_sound_side())
        self.log('FUSED_DECISION', decision or 'hold',
                 f'color={visual or "none"}; audio={self.active_sound_side() or "none"}',
                 front=front, left=left, right=right)
        if decision is None:
            # No reverse driving without a rear proximity sensor.
            self.dog.body_stop()
            self.log('BLOCKED', 'hold', 'Both scanned directions unsafe; retrying after pause')
            time.sleep(0.6)
            return
        self.move('turn_left' if decision == 'left' else 'turn_right',
                  speed=80, emergency_cm=HARD_STOP_CM)
        self.last_sound_time = 0.0

    def run(self):
        if self.vision is not None:
            self.vision.camera_start(vflip=self.args.vflip, hflip=self.args.hflip)
            self.camera_started = True
            self.vision.color_detect(color=self.args.color)
            time.sleep(2.0)  # Camera/detection initialization.
        self.dog.do_action('stand', speed=75)
        self.dog.wait_all_done()
        self.head(0)
        self.log('READY', 'stand', 'Initial calibration: head points forward')
        print('Controls: L / LS = PAUSE, R / RS = RESUME; Ctrl+C = EXIT.')
        print('Verify head scans left then right; use --invert-scan if reversed.')
        print('Robot begins navigating in 3 seconds. Keep hands and feet clear.')
        time.sleep(3)
        start = time.monotonic()
        while time.monotonic() - start < self.args.duration:
            self.sense_touch()
            if self.paused:
                time.sleep(0.2)
                continue
            self.sense_sound()
            visual = self.sense_vision()
            front = self.distance()
            self.latest_distance = front
            if front is None:
                self.dog.body_stop()
                self.log('SENSOR_FAULT', 'hold', 'Invalid ultrasonic readings, no motion')
                time.sleep(0.6)
                continue
            if visual == 'center' and self.latest_marker_area >= GOAL_MIN_AREA \
                    and STOP_CM <= front <= GOAL_MAX_DISTANCE:
                self.dog.body_stop()
                self.dog.do_action('sit', speed=60)
                self.dog.wait_legs_done()
                self.goal_reached = True
                self.log('GOAL', 'sit', 'Large centered color marker within goal range', front=front)
                break
            if front < STOP_CM:
                self.avoid(front)
                continue
            # Target bearing has priority over sound, but neither overrides sonar.
            desired = visual if visual in ('left', 'right') else None
            if desired is None and visual is None:
                desired = self.active_sound_side()
            if desired in ('left', 'right'):
                action = 'turn_left' if desired == 'left' else 'turn_right'
                self.log('STEERING', action, f'vision={visual}; sound={self.active_sound_side()}', front=front)
                self.move(action, speed=78, emergency_cm=HARD_STOP_CM)
                self.last_sound_time = 0.0  # One sound cue = one turn, not endless spinning.
            else:
                self.log('CLEAR', 'forward', f'vision={visual or "not found"}', front=front)
                self.move('forward', speed=85, emergency_cm=STOP_CM)
            time.sleep(0.08)
        if not self.goal_reached:
            self.log('FINISHED', 'stop', f'Time limit ({self.args.duration}s) reached')

    def close(self):
        try:
            try:
                self.dog.body_stop()
                if self.camera_started:
                    self.vision.camera_close()
            finally:
                self.dog.close()  # Always release servos, even if camera cleanup fails.
        finally:
            self.logfile.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', action='store_true', help='REQUIRED to enable motor operation')
    parser.add_argument('--duration', type=float, default=90, help='Max runtime in seconds (default 90)')
    parser.add_argument('--color', choices=['red', 'orange', 'yellow', 'green', 'blue', 'purple'],
                        default='green', help='Vision marker color (default green)')
    parser.add_argument('--no-camera', action='store_true',
                        help='Diagnostic only: disables vision, does NOT satisfy full Lab 10')
    parser.add_argument('--invert-scan', action='store_true', help='Use if +40 yaw points right instead of left')
    parser.add_argument('--hflip', action='store_true', help='Flip camera horizontally if required')
    parser.add_argument('--vflip', action='store_true', help='Flip camera vertically if required')
    parser.add_argument('--log', default='lab10_navigation_log.csv', help='CSV output path')
    args = parser.parse_args()
    if not args.arm:
        parser.error('Motors are DISARMED. Read the safety note, then add --arm to run.')
    if args.duration <= 0 or args.duration > 600:
        parser.error('--duration must be between 0 and 600 seconds')
    from pidog import Pidog
    from vilib import Vilib
    dog = None
    nav = None
    try:
        dog = Pidog()
        nav = Navigator(dog, None if args.no_camera else Vilib, args)
        nav.run()
    except KeyboardInterrupt:
        print('\nUser abort requested, stopping PiDog...')
    except Exception as exc:
        print(f'LAB10 ERROR: {exc}')
        raise
    finally:
        if nav is not None:
            nav.close()
        elif dog is not None:
            dog.close()


if __name__ == '__main__':
    main()
