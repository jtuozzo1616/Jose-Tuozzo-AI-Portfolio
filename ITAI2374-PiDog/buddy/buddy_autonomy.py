#!/usr/bin/env python3
"""Buddy Autonomy v2 - offline-friendly PiDog voice control and bounded autonomy.

Dependencies on Pi only: existing buddy_repeat.py, SunFounder pidog/robot_hat,
local Ollama if chat is enabled. The parser and simulator use Python stdlib.

This is supervised obstacle-aware roaming, NOT SLAM, cliff sensing, or safe
unsupervised navigation. Movements must be tested in a controlled flat area.
"""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import json
import math
from pathlib import Path
import queue
import random
import re
import runpy
import statistics
import threading
import time
from typing import Optional

VERSION = '2.0.0'

# One action is a short preset action or one locomotion cycle, not a meter.
ACTION_LIMITS = {
    'push up': 10, 'forward': 8, 'backward': 3, 'trot': 5,
    'turn left': 4, 'turn right': 4, 'wag tail': 10,
    'shake head': 6, 'nod': 6, 'bark': 5, 'pant': 3,
    'howling': 2, 'handshake': 3, 'high five': 3,
}
DEFAULT_COUNTS = {'forward': 3, 'backward': 2, 'trot': 3}
MAX_SEQUENCE = 22
# This is a whitelist based on an observed installed version of ActionFlow.
# At runtime, it is intersected with the installed operation names.
ACTION_ALIASES = [
    (r'\b(?:push\s*ups?|pushups?|press\s*ups?)\b', 'push up'),
    (r'\b(?:high\s*fives?|give (?:me|us) (?:a )?high five)\b', 'high five'),
    (r'\b(?:shake (?:my|your) hand|give (?:me|us) (?:your|a) paw|shake paws?|handshake)\b', 'handshake'),
    (r'\b(?:turn|rotate)\s+(?:to the )?left\b', 'turn left'),
    (r'\b(?:turn|rotate)\s+(?:to the )?right\b', 'turn right'),
    (r'\b(?:walk|move|go|step)\s+(?:back|backwards?)\b|\breverse\b', 'backward'),
    (r'\b(?:trot|jog)\b', 'trot'),
    (r'\b(?:walk|move|go|step)\s+(?:forward|ahead)\b|\bwalk\b|\bforward\b', 'forward'),
    (r'\bwag\b.*\btail\b|\btail\b.*\bwag\b', 'wag tail'),
    (r'\bshake\b.*\bhead\b', 'shake head'),
    (r'\b(?:tilt|tilting)\b.*\bhead\b', 'tilting head'),
    (r'\b(?:look|head)\s+down\b', 'head down'),
    (r'\b(?:barks?|woof)\b', 'bark'),
    (r'\b(?:howl|howling)\b', 'howling'),
    (r'\b(?:pant|panting)\b', 'pant'),
    (r'\b(?:stretch|stretching)\b', 'stretch'),
    (r'\b(?:twist|twisting)\b.*\bbody\b', 'twist body'),
    (r'\b(?:lick|lick my hand)\b', 'lick hand'),
    (r'\b(?:nod|nodding)\b', 'nod'),
    (r'\b(?:lie|lay)\s+down\b|\blie\b|\bplay dead\b', 'lie'),
    (r'\b(?:sit|sit down)\b', 'sit'),
    (r'\b(?:stand|stand up|get up)\b', 'stand'),
]
ALIASES = [(re.compile(pattern, re.I), action) for pattern, action in ACTION_ALIASES]
SPLIT = re.compile(r'\s*(?:,|;|\b(?:and then|then|after that|afterwards|next)\b)\s*', re.I)
WORDS = {w: i for i, w in enumerate(('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty').split())}
WORDS.update({'once': 1, 'twice': 2, 'thrice': 3})
NUMBER_RE = re.compile(r'\b(?:\d{1,3}|' + '|'.join(WORDS) + r')\b', re.I)
NOISE = re.compile(r'\b(?:uh|um|please|could you|can you|would you|will you|buddy)\b', re.I)
NEGATION = re.compile(r"\b(?:don't|dont|do not|never|not)\b", re.I)
STOP = re.compile(r'^(?:stop|stop now|stop right now|stop moving|halt|freeze|cancel|cancel that|emergency stop|abort|quiet)$')
COMMAND_START = re.compile(
    r'^(?:do|perform|make|show|give|walk|move|go|step|turn|rotate|reverse|trot|jog|push|pushups|wag|shake|stand|sit|lie|lay|play dead|high five|bark|woof|howl|howling|pant|stretch|twist|lick|nod|look down|head down|tilt|forward|backward|\d+|one|two|three|four|five|six|seven|eight|nine|ten|i want you to|i need you to)\b'
)
# Allows friendly corrections only for sufficiently similar *simple* phrases.
FUZZY_PHRASES = {
    'wag your tail': 'wag tail', 'do push ups': 'push up',
    'walk forward': 'forward', 'walk backward': 'backward',
    'turn left': 'turn left', 'turn right': 'turn right',
    'sit down': 'sit', 'stand up': 'stand',
    'shake your head': 'shake head', 'give me a high five': 'high five',
}


@dataclass(frozen=True)
class Plan:
    kind: str
    steps: tuple[str, ...] = ()
    say: str = ''
    proposal: str = ''


def normalize(text: str) -> str:
    """Normalize Vosk's text while preserving meaningful commands and counts."""
    t = (text or '').lower().replace('-', ' ')
    t = re.sub(r"[^a-z0-9,;!?\s']", ' ', t)
    t = re.sub(r'\b(?:okay|ok|hey)\s+(?:buddy|body|budi)\b', ' ', t)
    t = re.sub(r'\bpush\s+up\s+s\b', 'push ups', t)
    t = re.sub(r'\bpushups\b', 'push ups', t)
    t = re.sub(r'\b(?:your|the)\s+tail\b', 'tail', t)
    t = re.sub(r'\s+', ' ', t).strip(' .!?')
    return t


def _canonical_segment(seg: str) -> str:
    seg = NOISE.sub(' ', seg)
    return re.sub(r'\s+', ' ', seg).strip(' .!?')


def _get_count(seg: str, matched, action: str) -> int:
    # Exclude action itself so "high five" is never interpreted as 5 repetitions.
    remainder = seg[:matched.start()] + ' ' + seg[matched.end():]
    hits = list(NUMBER_RE.finditer(remainder))
    value = (int(hits[0].group()) if hits[0].group().isdigit()
             else WORDS[hits[0].group()]) if hits else DEFAULT_COUNTS.get(action, 1)
    value = min(max(1, value), ACTION_LIMITS.get(action, 6))
    return value


def _parse_segment(seg: str, available: set[str]) -> tuple[Optional[tuple[str, ...]], str]:
    if re.search(r'\b(?:seconds?|minutes?|meters?|feet|degrees?)\b', seg):
        return None, 'Please use steps or repetitions, not time or distance units.'
    if not COMMAND_START.match(seg):
        return None, ''
    for pattern, action in ALIASES:
        m = pattern.search(seg)
        if m:
            if action not in available:
                return None, f'{action} is not available on this PiDog.'
            leftover = seg[:m.start()] + ' ' + seg[m.end():]
            numbers = list(NUMBER_RE.finditer(leftover))
            if len(numbers) > 1:
                return None, 'I heard more than one number. Please repeat the command.'
            residue = NUMBER_RE.sub(' ', leftover)
            residue = re.sub(
                r'\b(?:do|perform|make|show|me|your|my|the|a|an|up|down|times?|steps?|reps?|repetitions?|please|i|want|you|to|need|of|give|take)\b',
                ' ', residue,
            )
            if residue.strip():
                # Avoid treating bad transcripts such as 'do tin push ups'
                # as an order for a single repetition.
                return None, 'I heard an unclear word in that command. Please say it again.'
            repetitions = _get_count(seg, m, action)
            return tuple([action] * repetitions), ''
    return None, ''


class Interpreter:
    def __init__(self, available: set[str]):
        self.available = available
        self.last: tuple[str, ...] = ()
        self.pending: Optional[Plan] = None

    def interpret(self, original: str) -> Plan:
        t = normalize(original)
        if not t or t.startswith('<<<'):
            return Plan('ignore')
        if self.pending:
            proposal = self.pending
            self.pending = None
            if re.fullmatch(r'(yes|yes please|correct|confirm|do it|okay|ok|yeah|sure)', t):
                return Plan('actions', proposal.steps, f'Confirmed. {len(proposal.steps)} movements.')
            if re.fullmatch(r'(no|nope|cancel|nevermind|never mind)', t):
                return Plan('say', say='Cancelled. Please say the command again.')
            # If user gave a new command, evaluate it instead of guessing yes.
        if STOP.fullmatch(_canonical_segment(t)):
            return Plan('stop', say='Stopping the current routine.')
        if NEGATION.search(t):
            return Plan('say', say='Okay. I will not perform that command.')
        if re.fullmatch(r'(repeat|repeat that|do it again|again|same thing again)', t):
            if self.last:
                return Plan('actions', self.last, 'Repeating your previous routine.')
            return Plan('say', say='There is no previous routine.')
        if re.search(r'\b(?:how far|distance|how close)\b', t):
            return Plan('distance')
        if re.search(r'\b(?:sound direction|where is the sound|where did that sound|where is that noise)\b', t):
            return Plan('sound')
        if re.search(r'\b(?:tilt sensor|imu|am i level|are you level|how tilted|are you tilted)\b', t):
            return Plan('imu')
        if re.search(r'\b(?:your status|what are you doing|status report|robot status)\b', t):
            return Plan('status')
        if re.search(r'\b(?:what can you do|list commands|help|your commands)\b', t):
            return Plan('help', say='I can walk, turn, do exercises, look around, explore, and guard.')
        if re.fullmatch(r'(?:look around|scan|scan the room|check surroundings|look for obstacles)', t):
            return Plan('scan', say='I will scan three directions.')
        if re.fullmatch(r'(?:turn your head toward the sound|look toward the sound|face the sound)', t):
            return Plan('listen_direction', say='I will orient my head toward the detected sound.')
        if re.fullmatch(r'(?:explore|explore the room|roam|explore around|go exploring)', t):
            return Plan('explore', say='I will explore a small supervised area.')
        if re.fullmatch(r'(?:patrol|start patrol|patrol the area)', t):
            return Plan('explore', say='Starting a short supervised patrol.')
        if re.fullmatch(r'(?:guard|guard mode|start guarding|watch the room)', t):
            return Plan('guard', say='I will watch the front sensor for one minute.')
        if re.fullmatch(r'(?:stop guarding|stop exploring|stop patrol|stop patrolling)', _canonical_segment(t)):
            return Plan('stop', say='Stopping autonomous mode.')
        if re.fullmatch(r'(?:dance|show me a trick|do a trick)', t):
            seq = tuple(a for a in ('sit', 'wag tail', 'nod', 'wag tail', 'sit') if a in self.available)
            return self._action_plan(seq)
        if re.fullmatch(r'(?:workout|exercise|exercise routine|do your exercise routine)', t):
            seq = tuple(a for a in (['stand'] + ['push up'] * 5 + ['wag tail', 'sit']) if a in self.available)
            return self._action_plan(seq)
        if re.search(r'\b(follow me|find me|navigate to|go to the kitchen|recognize my face)\b', t):
            return Plan('say', say='I cannot reliably follow people or navigate to rooms without additional sensing.')
        if re.match(r'^(what|why|who|when|where|how|explain|describe|tell me about|tell me how|what is|can you explain)\b', t):
            return Plan('chat')

        # If there are several commands separated by 'and', split only if both sides
        # contain clear action phrases. Never split "shake head and tail" guessing.
        parts = [p for p in SPLIT.split(t) if p.strip()]
        if len(parts) == 1 and ' and ' in t:
            candidates = [p.strip() for p in t.split(' and ')]
            if len(candidates) <= 6:
                recognized = [_parse_segment(_canonical_segment(p), self.available)[0] for p in candidates]
                if all(recognized):
                    parts = candidates
                elif any(recognized):
                    # Do not silently perform only the first half of a sentence.
                    return Plan('say', say='I understood only part of that sequence. Please repeat it more clearly.')
        if len(parts) > 8:
            return Plan('say', say='Please give me eight instructions or fewer at a time.')
        steps: list[str] = []
        for raw in parts:
            part = _canonical_segment(raw)
            found, error = _parse_segment(part, self.available)
            if error:
                return Plan('say', say=error)
            if not found:
                if len(parts) == 1:
                    correction = self._fuzzy(part)
                    if correction:
                        intended = (correction,)
                        pending = Plan('actions', intended)
                        self.pending = pending
                        return Plan('confirm', say=f'Did you mean {correction}? Say yes or no.', proposal=correction)
                if any(x in part for x in ('walk', 'push', 'turn', 'step', 'bark', 'wag', 'stand', 'sit', 'run')):
                    return Plan('say', say='I could not understand that movement. Please repeat more clearly.')
                return Plan('chat') if len(parts) == 1 else Plan('say', say='Please repeat the full movement sequence.')
            steps.extend(found)
        if len(steps) > MAX_SEQUENCE:
            return Plan('say', say=f'Too many movements. The maximum is {MAX_SEQUENCE}.')
        return self._action_plan(tuple(steps))

    def _fuzzy(self, part: str) -> Optional[str]:
        # High threshold + confirmation; acoustic confidence is not available.
        options = [(SequenceMatcher(None, part, k).ratio(), action)
                   for k, action in FUZZY_PHRASES.items() if action in self.available]
        if not options:
            return None
        score, action = max(options)
        return action if score >= 0.82 else None

    def _action_plan(self, steps: tuple[str, ...]) -> Plan:
        if not steps:
            return Plan('say', say='That movement is not installed.')
        self.last = steps
        noun = 'movement' if len(steps) == 1 else 'movements'
        return Plan('actions', steps, f'Okay. {len(steps)} {noun}.')


@dataclass
class Config:
    clearance_cm: float = 30.0
    side_clearance_cm: float = 45.0
    explore_steps: int = 9
    explore_timeout_sec: float = 55.0
    guard_timeout_sec: float = 60.0
    min_valid_cm: float = 2.0
    max_valid_cm: float = 400.0
    speak: bool = True
    imu_guard: bool = False
    imu_max_tilt_degrees: float = 45.0


class SensorAdapter:
    def __init__(self, dog, cfg: Config):
        self.dog, self.cfg = dog, cfg

    def distance(self, samples=3) -> Optional[float]:
        fn = getattr(getattr(self.dog, 'ultrasonic', None), 'read_distance', None)
        if not callable(fn):
            fn = getattr(self.dog, 'read_distance', None)
        if not callable(fn):
            return None
        numbers = []
        for _ in range(samples):
            try:
                val = float(fn())
            except Exception:
                return None
            if not (math.isfinite(val) and self.cfg.min_valid_cm <= val <= self.cfg.max_valid_cm):
                return None  # fail closed, never treat an invalid reading as clear
            numbers.append(val)
            time.sleep(0.04)
        return round(statistics.median(numbers), 1)

    def tilt(self) -> Optional[float]:
        # PiDog documentation: acceleration is predominantly X-axis at rest.
        try:
            x, y, z = [float(a) for a in self.dog.accData]
            mag = math.sqrt(x*x + y*y + z*z)
            if not (8000 <= mag <= 25000):
                return None
            return round(math.degrees(math.acos(min(1.0, abs(x)/mag))), 1)
        except Exception:
            return None

    def sound_direction(self) -> Optional[float]:
        try:
            if not self.dog.ears.isdetected():
                return None
            angle = float(self.dog.ears.read())
            return angle if math.isfinite(angle) and 0 <= angle < 360 else None
        except Exception:
            return None

    def scan(self, flow, stop: threading.Event) -> dict[str, Optional[float]]:
        # Head yaw sweeps, not a depth map. The robot stays in place.
        readings = {'left': None, 'front': None, 'right': None}
        pitch_comp = getattr(flow, 'head_pitch_init', -35)
        try:
            for side, angle in (('left', 35), ('front', 0), ('right', -35)):
                if stop.is_set():
                    break
                self.dog.head_move([[angle, 0, 0]], pitch_comp=pitch_comp, speed=45)
                self.dog.wait_head_done()
                time.sleep(0.18)
                readings[side] = self.distance()
        except Exception as exc:
            print(f'[SENSOR] Scan failure: {exc}', flush=True)
        finally:
            try:
                self.dog.head_move([[0, 0, 0]], pitch_comp=pitch_comp, speed=45)
                self.dog.wait_head_done()
            except Exception:
                pass
        return readings


@dataclass
class Job:
    plan: Plan
    generation: int = 0
    submitted: float = field(default_factory=time.monotonic)


class MotionController:
    """Exactly one thread commands the motors. Voice remains on the main thread."""
    def __init__(self, dog, flow, cfg: Config):
        self.dog, self.flow, self.cfg = dog, flow, cfg
        self.sensors = SensorAdapter(dog, cfg)
        self.q: queue.Queue[Job] = queue.Queue(maxsize=1)
        self.cancel = threading.Event()
        self.generation = 0
        self.generation_lock = threading.Lock()
        self.shutdown = threading.Event()
        self.busy = threading.Event()
        self.worker = threading.Thread(target=self._loop, name='buddy-motion', daemon=True)
        self.history = deque(maxlen=40)

    def start(self):
        self.worker.start()

    def stop(self):
        with self.generation_lock:
            self.generation += 1
            self.cancel.set()
        while True:
            try:
                self.q.get_nowait()
                self.q.task_done()
            except queue.Empty:
                break
        print('[STOP] Cancel requested; a running servo cycle may need to finish.', flush=True)

    def submit(self, plan: Plan):
        self.stop()
        with self.generation_lock:
            generation = self.generation
            self.q.put_nowait(Job(plan, generation))
        print(f'[PLAN] {plan.kind}: {list(plan.steps)}', flush=True)

    def close(self):
        self.stop()
        self.shutdown.set()
        self.worker.join(timeout=4.0)
        if self.worker.is_alive():
            print('[WARNING] Motion worker is still active; use physical power-off if unsafe.', flush=True)
        else:
            try:
                self.flow.run('sit')
            except Exception as exc:
                print('[WARNING] Cannot sit:', exc, flush=True)

    def _loop(self):
        while not self.shutdown.is_set():
            try:
                job = self.q.get(timeout=0.15)
            except queue.Empty:
                continue
            with self.generation_lock:
                if job.generation != self.generation or self.shutdown.is_set():
                    self.q.task_done()
                    continue
                self.cancel.clear()
                self.busy.set()
            try:
                self._execute(job.plan)
            except Exception as exc:
                print('[ERROR] Routine stopped:', repr(exc), flush=True)
            finally:
                self.busy.clear()
                self.q.task_done()
                print('[MOTION] Routine ended; voice remains active.', flush=True)

    def _do(self, action: str) -> bool:
        if self.cancel.is_set() or self.shutdown.is_set():
            return False
        if self.cfg.imu_guard and action in ('forward', 'trot', 'turn left', 'turn right'):
            tilt = self.sensors.tilt()
            if tilt is None or tilt > self.cfg.imu_max_tilt_degrees:
                print(f'[SAFETY] IMU tilt abnormal or unavailable: {tilt}', flush=True)
                self.cancel.set()
                return False
        if action in ('forward', 'trot'):
            d = self.sensors.distance()
            if d is None or d < self.cfg.clearance_cm:
                print(f'[SAFETY] Cannot {action}; front range={d} cm.', flush=True)
                self.cancel.set()
                return False
        print(f'[ACTION] {action}', flush=True)
        self.flow.run(action)
        # The action flow catches its own errors; wait so commands do not overlap.
        self.dog.wait_all_done()
        self.history.append(action)
        return not self.cancel.is_set()

    def _execute(self, plan: Plan):
        if plan.kind == 'actions':
            for action in plan.steps:
                if not self._do(action):
                    break
        elif plan.kind == 'scan':
            print('[SCAN] ' + json.dumps(self.sensors.scan(self.flow, self.cancel)), flush=True)
        elif plan.kind == 'listen_direction':
            bearing = self.sensors.sound_direction()
            if bearing is None:
                print('[EARS] No reliable sound direction available.', flush=True)
            else:
                yaw = -bearing if bearing <= 180 else (360 - bearing)
                yaw = max(-65, min(65, yaw))
                pitch_comp = getattr(self.flow, 'head_pitch_init', -35)
                self.dog.head_move([[yaw, 0, 0]], pitch_comp=pitch_comp, speed=45)
                self.dog.wait_head_done()
                print(f'[EARS] Sound at {bearing} degrees; head yaw {yaw}', flush=True)
        elif plan.kind == 'explore':
            self._explore()
        elif plan.kind == 'guard':
            self._guard()

    def _explore(self):
        deadline = time.monotonic() + self.cfg.explore_timeout_sec
        steps = 0
        avoid_attempts = 0
        while not self.cancel.is_set() and time.monotonic() < deadline and steps < self.cfg.explore_steps:
            d = self.sensors.distance()
            if d is None:
                print('[EXPLORE] Sensor unavailable; stopping.', flush=True)
                break
            if d >= self.cfg.clearance_cm:
                if not self._do('forward'):
                    break
                steps += 1
                avoid_attempts = 0
                continue
            print(f'[EXPLORE] Obstacle {d} cm; scanning alternatives.', flush=True)
            scan = self.sensors.scan(self.flow, self.cancel)
            options = [(key, scan[key]) for key in ('left', 'right')
                       if scan[key] is not None and scan[key] >= self.cfg.side_clearance_cm]
            if not options:
                print('[EXPLORE] No verified turn direction; stopping.', flush=True)
                break
            side, _ = max(options, key=lambda x: x[1])
            # Turning in place still needs a level, unobstructed floor.
            if not self._do('turn left' if side == 'left' else 'turn right'):
                break
            avoid_attempts += 1
            if avoid_attempts >= 3:
                print('[EXPLORE] Too many avoidance attempts; stopping.', flush=True)
                break
        print(f'[EXPLORE] Completed {steps} forward cycles (not measured meters).', flush=True)

    def _guard(self):
        deadline = time.monotonic() + self.cfg.guard_timeout_sec
        last_alert = 0.0
        failed = 0
        while not self.cancel.is_set() and time.monotonic() < deadline:
            d = self.sensors.distance()
            if d is None:
                failed += 1
                if failed >= 3:
                    print('[GUARD] Sensor failed repeatedly. Exiting guard mode.', flush=True)
                    break
            else:
                failed = 0
                if d < self.cfg.clearance_cm and time.monotonic() - last_alert > 12:
                    print(f'[GUARD] New nearby obstacle: {d} cm', flush=True)
                    last_alert = time.monotonic()
                    self._do('bark')
            # Avoid long sleeps so cancellation is observed quickly.
            self.cancel.wait(0.5)
        print('[GUARD] Watch period ended.', flush=True)


class FakeDog:
    """No motors; representative mock of only the APIs we call."""
    def __init__(self, distances=None):
        self.distances = deque(distances or [90] * 200)
        self.ultrasonic = self
        self.log = []
    def read_distance(self):
        d = self.distances.popleft() if self.distances else 90
        return d
    def head_move(self, *args, **kwargs):
        self.log.append('head')
    def wait_head_done(self):
        pass
    def wait_all_done(self):
        pass


class FakeFlow:
    head_pitch_init = -35
    def __init__(self, dog):
        self.dog, self.log = dog, []
    def run(self, action):
        self.log.append(action)


class BuddyRuntime:
    def __init__(self, vad, cfg: Config, require_wake: bool, enable_chat: bool):
        self.vad = vad
        self.cfg = cfg
        self.controller = MotionController(vad.dog, vad.action_flow, cfg)
        self.controller.start()
        self.parser = Interpreter(set(vad.action_flow.OPERATIONS))
        self.require_wake = require_wake
        self.enable_chat = enable_chat
        self.last_said = ''
        self.last_said_at = 0.0

    def speak(self, message: str):
        if not message:
            return
        message = message[:240]
        print('[BUDDY] ' + message, flush=True)
        if self.cfg.speak:
            try:
                self.vad.tts.say(message)
            except Exception as exc:
                print('[AUDIO] TTS failure:', exc, flush=True)
        self.last_said, self.last_said_at = message.lower(), time.monotonic()
        time.sleep(0.3)  # avoid speaker audio leaking into the next command

    def handle(self, text: str):
        print('[STT RAW]', repr(text), flush=True)
        t = normalize(text)
        print('[STT NORMALIZED]', repr(t), flush=True)
        if not t:
            return
        # Quiet echo rejection is heuristic, not full acoustic echo cancellation.
        if time.monotonic() - self.last_said_at < 2 and t == normalize(self.last_said):
            print('[AUDIO] Echo ignored.', flush=True)
            return
        if self.require_wake:
            # Stop is always accepted without a wake word.
            if not STOP.fullmatch(t) and not re.search(r'\b(?:hey|okay)\s+(?:buddy|body|budi)\b', text.lower()):
                print('[VOICE] Wake word required for this command.', flush=True)
                return
        plan = self.parser.interpret(t)
        if plan.kind == 'ignore':
            return
        if plan.kind == 'stop':
            self.controller.stop()
            self.speak(plan.say)
        elif plan.kind in ('actions', 'explore', 'scan', 'guard', 'listen_direction'):
            self.speak(plan.say)
            self.controller.submit(plan)
        elif plan.kind == 'status':
            self.speak('I am completing a routine.' if self.controller.busy.is_set() else 'I am idle and listening.')
        elif plan.kind == 'imu':
            tilt = self.controller.sensors.tilt()
            self.speak('The IMU reading is unavailable.' if tilt is None else f'My approximate tilt is {tilt} degrees. This is not a cliff detector.')
        elif plan.kind == 'sound':
            bearing = self.controller.sensors.sound_direction()
            self.speak('I cannot detect a current sound direction.' if bearing is None else f'The detected sound is at {bearing} degrees relative to my front.')
        elif plan.kind == 'distance':
            if self.controller.busy.is_set():
                self.speak('I am moving. Please stop or wait before checking distance.')
                return
            d = self.controller.sensors.distance()
            self.speak(f'The front sensor reads {d} centimeters.' if d is not None else 'The distance sensor is not giving a valid reading.')
        elif plan.kind in ('say', 'confirm', 'help'):
            self.speak(plan.say)
        elif plan.kind == 'chat':
            if not self.enable_chat:
                self.speak('Please give me a movement command. Conversation is disabled.')
            else:
                try:
                    # Chat output is NEVER parsed as motor commands.
                    answer = self.vad.think(t, disable_image=True)
                    answer = re.split(r'\bACTIONS\s*:', answer, maxsplit=1, flags=re.I)[0].strip()
                    self.speak(answer or 'Please try asking that again.')
                except Exception as exc:
                    print('[CHAT] Ollama issue:', repr(exc), flush=True)
                    self.speak('My offline conversation model is unavailable right now.')

    def listen_loop(self):
        self.speak('Buddy autonomy ready. Give me a command.')
        try:
            while True:
                print('[VOICE] Listening. Say stop to cancel at the next safe step.', flush=True)
                final = ''
                try:
                    # Uses the STT already configured by the proven base program.
                    # Vosk final segments are more reliable than streaming partials.
                    for result in self.vad.stt.listen(stream=True):
                        if result.get('done'):
                            final = (result.get('final') or '').strip()
                        elif result.get('partial'):
                            print('[STT PARTIAL]', result['partial'], end='\r', flush=True)
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    print('[VOICE] Microphone issue:', repr(exc), flush=True)
                    time.sleep(1)
                    continue
                if final:
                    print('', flush=True)
                    self.handle(final)
        except KeyboardInterrupt:
            print('\n[EXIT] Ctrl+C received.', flush=True)
        finally:
            self.close()

    def text_loop(self):
        self.speak('Buddy keyboard input enabled.')
        try:
            while True:
                phrase = input('Buddy> ').strip()
                if phrase.lower() in ('quit', 'exit'):
                    break
                self.handle(phrase)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            self.close()

    def close(self):
        self.controller.close()
        try:
            self.vad.stt.close()
        except Exception:
            pass
        # Refuse to close motor hardware while worker is still active.
        if not self.controller.worker.is_alive():
            try:
                if getattr(self.vad, 'with_image', False):
                    self.vad.close_camera()
            except Exception:
                pass
            try:
                self.vad.dog.close()
            except Exception:
                pass
        print('[EXIT] Buddy stopped.', flush=True)


def benchmark_voice(vad):
    samples = [
        'do ten push ups',
        'walk forward five steps',
        'turn left twice',
        'wag your tail three times',
        'stop',
    ]
    results = []
    print('[VOICE BENCHMARK] Say each displayed English phrase. Motors stay idle.', flush=True)
    try:
        for phrase in samples:
            print('\nSAY:', phrase, flush=True)
            heard = ''
            for result in vad.stt.listen(stream=True):
                if result.get('done'):
                    heard = (result.get('final') or '').strip()
            match = round(SequenceMatcher(None, normalize(phrase), normalize(heard)).ratio(), 3)
            results.append(match)
            print('HEARD:', repr(heard), 'TEXT MATCH:', match, flush=True)
        print('\n[VOICE BENCHMARK] Mean text match:', round(statistics.mean(results), 3))
        print('These are transcript similarities, NOT the recognizer\'s acoustic confidence.')
    finally:
        try:
            vad.stt.close()
        finally:
            vad.dog.close()


def load_existing_vad(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'Missing {path}; copy this script next to your working buddy_repeat.py')
    # Execution as non-__main__ builds vad without starting the original main loop.
    namespace = runpy.run_path(str(path.resolve()), run_name='buddy_autonomy_base')
    vad = namespace.get('vad')
    if vad is None or not all(hasattr(vad, attr) for attr in ('dog', 'action_flow', 'stt', 'tts')):
        raise RuntimeError('Base script did not provide the expected vad object.')
    return vad


def self_test():
    options = set(a for _, a in ACTION_ALIASES)
    options |= {'twist body'}
    samples = [
        ('do 10 push ups', 'push up', 10),
        ('please do ten push ups', 'push up', 10),
        ('hey buddy walk eight steps', 'forward', 8),
        ('walk backwards two steps', 'backward', 2),
        ('give me a high five', 'high five', 1),
        ('turn right 3 times', 'turn right', 3),
        ('stand up, wag your tail 5 times, then sit down', 'wag tail', 5),
    ]
    for phrase, expected, count in samples:
        parser = Interpreter(options)
        plan = parser.interpret(phrase)
        assert plan.kind == 'actions' and plan.steps.count(expected) == count, (phrase, plan)
    parser = Interpreter(options)
    assert parser.interpret('what are push ups').kind == 'chat'
    assert parser.interpret('do not walk forward').kind == 'say'
    assert parser.interpret('stop').kind == 'stop'
    assert parser.interpret('explore').kind == 'explore'
    assert parser.interpret('scan the room').kind == 'scan'
    assert parser.interpret('follow me').kind == 'say'
    # Unknown potential command must never cause random physical movement.
    assert parser.interpret('xyz nonsense').kind == 'chat'
    mock = FakeDog([90] * 200)
    controller = MotionController(mock, FakeFlow(mock), Config(explore_steps=3, explore_timeout_sec=10))
    controller.start()
    controller.submit(Plan('actions', ('forward', 'forward', 'sit')))
    controller.q.join()
    assert controller.flow.log == ['forward', 'forward', 'sit'], controller.flow.log
    controller.submit(Plan('explore'))
    controller.q.join()
    assert controller.flow.log.count('forward') == 5
    controller.close()
    print(f'[TEST] Buddy {VERSION}: parser, safety, and simulated rover checks PASSED.')


def main():
    arg = argparse.ArgumentParser(description='Buddy Autonomy: supervised voice-controlled PiDog.')
    arg.add_argument('--self-test', action='store_true', help='Run without PiDog hardware or microphone.')
    arg.add_argument('--text', action='store_true', help='Use typed input but real motors.')
    arg.add_argument('--diagnose-voice', action='store_true', help='Only print microphone transcripts, NEVER move motors or call LLM.')
    arg.add_argument('--voice-benchmark', action='store_true', help='Five spoken prompts with transcription comparisons; no motor motion.')
    arg.add_argument('--require-wake', action='store_true', help='Require Hey Buddy for non-stop commands.')
    arg.add_argument('--no-chat', action='store_true', help='Do not call the optional Ollama model.')
    arg.add_argument('--imu-guard', action='store_true', help='Opt-in tilt check before locomotion; calibrate IMU first.')
    arg.add_argument('--quiet', action='store_true', help='Disable synthesized spoken replies.')
    arg.add_argument('--base', type=Path, default=Path(__file__).with_name('buddy_repeat.py'))
    arg.add_argument('--clearance-cm', type=float, default=30, help='Front ultrasonic stop threshold.')
    args = arg.parse_args()
    if args.self_test:
        self_test()
        return
    if not (20 <= args.clearance_cm <= 80):
        arg.error('--clearance-cm must be between 20 and 80')
    vad = load_existing_vad(args.base)
    cfg = Config(clearance_cm=args.clearance_cm, speak=not args.quiet, imu_guard=args.imu_guard)
    if args.voice_benchmark:
        benchmark_voice(vad)
        return
    if args.diagnose_voice:
        print('[MICROPHONE DIAGNOSTICS] No motion worker; Ctrl+C to exit.', flush=True)
        try:
            while True:
                for result in vad.stt.listen(stream=True):
                    if result.get('done'):
                        raw = result.get('final', '')
                        print('[STT RAW]', repr(raw), '[NORMALIZED]', repr(normalize(raw)), flush=True)
        except KeyboardInterrupt:
            pass
        finally:
            try:
                vad.stt.close()
            finally:
                vad.dog.close()
        return
    runtime = BuddyRuntime(vad, cfg, args.require_wake, not args.no_chat)
    runtime.text_loop() if args.text else runtime.listen_loop()


if __name__ == '__main__':
    main()
