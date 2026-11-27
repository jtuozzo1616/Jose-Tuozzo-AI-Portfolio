#!/usr/bin/env python3
"""Buddy Ultra 3.0: add-on for Buddy Autonomy 2.0 + calibrated head scratch.

Run beside buddy_autonomy.py, buddy_head_scratch.py, buddy_repeat.py.
Uses only built-in sound effects, optional PiCamera2/OpenCV and opt-in local
Ollama multimodal vision; never identifies a person by name.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import pwd
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import wave
from array import array

# The scratch module retains its calibration gate and any locally tuned speed.
import buddy_head_scratch as scratch
import buddy_autonomy as core

VERSION = '3.0.0'
VISION_MODEL = ''
VISION_URL = 'http://127.0.0.1:11434/api/generate'
BASE_DIR = Path(__file__).resolve().parent
FX = {
    'growl': 'growl_1', 'growl harder': 'growl_2',
    'snarl': 'growl_2', 'howl': 'howling',
    'bark': 'single_bark_1', 'bark loud': 'single_bark_2',
    'pant': 'pant', 'snore': 'snoring',
    'angry': 'angry', 'happy': 'woohoo',
    'confused': 'confused_1', 'surprised': 'confused_2',
    'sad': 'confused_3',
}

NUMBER = dict(core.WORDS)


def _quantity(txt, maximum=5):
    found = core.NUMBER_RE.search(txt)
    n = 1 if not found else (int(found.group()) if found.group().isdigit() else NUMBER[found.group()])
    return max(1, min(maximum, n))


def extra_plan(text):
    """Strict full-phrase interpretation, avoiding triggering on conversation."""
    t = core.normalize(text)
    if not t or core.NEGATION.search(t) or core.STOP.fullmatch(t):
        return None
    # No identification: we can describe observable appearances, not names.
    if re.fullmatch(r'(?:who is (?:that|there|in front of you)|do you know who (?:that|this) is|identify (?:that|the) person)', t):
        return core.Plan('say', say='I cannot identify a person by their face. I can describe visible clothing if local vision is available.')
    if re.fullmatch(r'(?:greet (?:the|a) person you see|greet whoever you see|say hi to the person you see)', t):
        return core.Plan('vision_greet', say='I will look for a face and greet the visitor.')
    if re.fullmatch(r'(?:look at (?:me|the person)|track (?:my|a|the) face|follow (?:my|the) face with your head|face tracking)', t):
        return core.Plan('vision_track', say='I will look toward a detected face, without moving my legs.')
    if re.fullmatch(r'(?:do you see (?:me|anyone|a person)|how many people (?:do you see|are there)|find (?:a|the) (?:person|face)|detect faces|look for people)', t):
        return core.Plan('vision_faces', say='I will look for visible faces.')
    if re.fullmatch(r'(?:describe (?:the|that|a) person|describe (?:what|who) you see|what is (?:the|that) person wearing|describe their clothes)', t):
        return core.Plan('vision_person', say='I will check for visible people and their clothing.')
    if re.fullmatch(r'(?:what (?:do|can) you see|describe (?:the room|the scene|your surroundings)|what objects (?:do you see|are in front of you)|identify objects|recognize objects|look at the camera)', t):
        return core.Plan('vision_scene', say='I will examine the camera image.')
    if re.fullmatch(r'(?:take (?:a|one) (?:photo|picture)|take a snapshot|save a picture|capture an image)', t):
        return core.Plan('vision_photo', say='I will save one photo locally.')
    if re.fullmatch(r'(?:what colors (?:do you see|are there)|name the colors|look for colors|scan colors)', t):
        return core.Plan('vision_colors', say='I will check for prominent colors.')
    if re.fullmatch(r'(?:look at (?:the|a) red ball|track (?:the|a) red ball with your head|watch (?:the|a) red ball)', t):
        return core.Plan('vision_ball_track', say='I will look toward a red round object without walking.')
    if re.fullmatch(r'(?:find (?:the|a) red ball|where is (?:the|a) red ball|spot (?:the|a) red ball|look for (?:the|a) red ball|find the red object)', t):
        return core.Plan('vision_ball', say='I will look for a red round object.')
    if re.fullmatch(r'(?:explore and attack|explore and growl|explore and defend|scout and growl|scout mode)', t):
        return core.Plan('vision_scout', say='I will scout briefly and make pretend warning sounds. I will not touch anyone.')
    if re.fullmatch(r'(?:chase (?:the|a) red ball|follow (?:the|a) red ball|play fetch|fetch the ball|chase (?:the|a) ball)', t):
        return core.Plan('vision_chase', say='I will follow a red round target for a few supervised steps.')
    if re.fullmatch(r'(?:what did you see|what was your last observation|repeat your last observation)', t):
        return core.Plan('vision_memory')
    if re.fullmatch(r'(?:sing|sing a song|sing your song|play a song|play music|play a melody|make music|sing something|sing me a song|play an original song)', t):
        return core.Plan('actions', ('melody happy',), 'Playing my original instrumental tune.')
    if re.fullmatch(r'(?:sing (?:a )?lullaby|play (?:a )?lullaby|sleepy music|good night song)', t):
        return core.Plan('actions', ('melody lullaby',), 'Playing my original lullaby.')
    if re.fullmatch(r'(?:celebrate|victory dance|party mode|birthday party|be happy|act happy|cheer up)', t):
        return core.Plan('actions', ('sound woohoo', 'wag tail', 'nod', 'sound single_bark_1', 'wag tail'), 'Party time!')
    if re.fullmatch(r'(?:play fight|pretend to fight|fight mode|act tough|act fierce|battle mode|attack|attack mode|pretend attack|protect me|defend me)', t):
        return core.Plan('actions', ('stand', 'sound growl_1', 'sound growl_2', 'sound single_bark_2', 'wag tail'), 'Pretend battle only. No contact.')
    if re.fullmatch(r'(?:play dead|pretend to sleep|go to sleep|sleep mode|be sleepy|take a nap)', t):
        return core.Plan('actions', ('lie', 'sound snoring'), 'Nap time.')
    if re.fullmatch(r'(?:greet me|say hello|welcome me|greet the guests|be friendly)', t):
        return core.Plan('actions', ('sound woohoo', 'wag tail', 'handshake'), 'Hello, friend!')
    if re.fullmatch(r'(?:be dramatic|dramatic mode|do a drama scene|act like a movie star)', t):
        return core.Plan('actions', ('sound confused_2', 'tilting head', 'sound growl_1', 'nod', 'sound woohoo'), 'My dramatic performance starts now.')
    if re.fullmatch(r'(?:do a funny routine|make me laugh|be silly|goof around)', t):
        return core.Plan('actions', ('sound confused_1', 'shake head', 'wag tail', 'sound woohoo'), 'Here is my silly routine.')
    if re.fullmatch(r'(?:do a morning routine|wake up routine|good morning buddy)', t):
        return core.Plan('actions', ('stretch', 'sit', 'wag tail', 'sound woohoo'), 'Good morning!')
    if re.fullmatch(r'(?:act scared|be afraid|pretend you are scared)', t):
        return core.Plan('actions', ('sound confused_2', 'backward', 'sit'), 'Oh! That startled me.')
    if re.fullmatch(r'(?:act confused|be confused|what was that)', t):
        return core.Plan('actions', ('sound confused_1', 'tilting head'), 'Hmm, interesting.')
    if re.fullmatch(r'(?:show all sounds|list your sounds|what sounds can you make)', t):
        return core.Plan('say', say='I can bark, howl, growl, pant, snore, sound happy, angry, surprised or confused.')
    # Explicit sound commands only. No fuzzy coercion of unrelated speech.
    sound_patterns = [
        (r'(?:growl harder|growl loudly|deep growl|big growl)', 'growl_2'),
        (r'(?:growl|grrr|snarl|grumble)', 'growl_1'),
        (r'(?:howl|howling|howl like a wolf|howl at the moon)', 'howling'),
        (r'(?:bark loudly|bark harder|loud bark|big bark)', 'single_bark_2'),
        (r'(?:bark|woof|woof woof)', 'single_bark_1'),
        (r'(?:pant|panting)', 'pant'),
        (r'(?:snore|snoring)', 'snoring'),
        (r'(?:sound angry|act angry|angry sound)', 'angry'),
        (r'(?:make a happy sound|happy sound|woohoo)', 'woohoo'),
        (r'(?:make a confused sound|confused sound)', 'confused_1'),
    ]
    for phrase, sound in sound_patterns:
        m = re.fullmatch(r'(?:please )?(?:make a |make the |do a |do |can you |please )?(?:'+phrase+r')(?: (\d+|one|two|three|four|five|once|twice|thrice)\s*(?:times?)?)?', t)
        if m:
            count = _quantity(m.group(1) or '', 4)
            return core.Plan('actions', tuple(['sound '+sound] * count), f'Okay, {count} sound effects.')
    return None


class Camera:
    def __init__(self, vad):
        self.vad = vad
        self.camera = None
        self.owns_camera = False
        self.cv2 = None
        self.detector = None
        self.last_observation = 'I have not taken a camera observation yet.'
        self.last_shot = None

    def _open(self):
        if self.camera:
            return
        try:
            import cv2
            self.cv2 = cv2
        except ImportError as exc:
            raise RuntimeError('OpenCV is missing: sudo apt install python3-opencv') from exc
        # Reuse the legacy assistant camera if it already owns the camera device.
        existing = getattr(self.vad, 'picam2', None)
        if existing is not None:
            self.camera = existing
            self.owns_camera = False
        else:
            try:
                from picamera2 import Picamera2
                camera = Picamera2()
                camera.configure(camera.create_preview_configuration(main={'size': (640, 480), 'format': 'RGB888'}))
                camera.start()
                time.sleep(1.0)
                self.camera = camera
                self.owns_camera = True
            except Exception as exc:
                raise RuntimeError('Camera unavailable. Check ribbon cable, driver and other camera apps.') from exc
        locations = [
            Path(getattr(getattr(cv2, 'data', None), 'haarcascades', '/unlikely')) / 'haarcascade_frontalface_default.xml',
            Path('/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'),
            Path('/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml'),
        ]
        for cascade in locations:
            if cascade.is_file():
                model = cv2.CascadeClassifier(str(cascade))
                if not model.empty():
                    self.detector = model
                    break

    def capture(self):
        self._open()
        frame = self.camera.capture_array()
        fmt = ''
        try:
            fmt = self.camera.camera_configuration().get('main', {}).get('format', '')
        except Exception:
            pass
        # Standardize to 3-channel BGR for all OpenCV operations.
        if len(frame.shape) != 3 or frame.shape[2] not in (3,4):
            raise RuntimeError('Unsupported camera frame format.')
        if frame.shape[2] == 4:
            if fmt == 'XBGR8888':  # channel order RGBA
                return self.cv2.cvtColor(frame, self.cv2.COLOR_RGBA2BGR)
            return frame[:, :, :3].copy()  # XRGB8888 is BGRA
        if fmt == 'BGR888':  # PiCamera2 calls the RGB byte order BGR888
            return self.cv2.cvtColor(frame, self.cv2.COLOR_RGB2BGR)
        return frame

    def faces(self, frame):
        if self.detector is None:
            raise RuntimeError('OpenCV Haar face classifier is not installed.')
        # RGB888 in Picamera2 yields BGR byte ordering in the numpy array.
        gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
        gray = self.cv2.equalizeHist(gray)
        return self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(45, 45))

    def red_round(self, frame):
        cv2 = self.cv2
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        low = cv2.inRange(hsv, (0, 100, 75), (10, 255, 255))
        high = cv2.inRange(hsv, (170, 100, 75), (179, 255, 255))
        mask = cv2.bitwise_or(low, high)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5)))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        region = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(region)
        perimeter = cv2.arcLength(region, True)
        if area < 230 or perimeter <= 0:
            return None
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        x, y, w, h = cv2.boundingRect(region)
        if circularity < .57 or not (.55 <= w / max(h,1) <= 1.65):
            return None
        if w > frame.shape[1] * 0.65:  # oversized red surfaces are not ball targets
            return None
        return {'cx': x + w/2, 'cy': y + h/2, 'width': w, 'area': round(area), 'roundness': round(circularity,2)}

    def colors(self, frame):
        hsv = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2HSV)
        h, w = hsv.shape[:2]
        # Ignore greys/white/black; this is a rough color summary, not object ID.
        pixels = hsv[::8, ::8].reshape(-1,3)
        histogram = dict(red=0, orange=0, yellow=0, green=0, cyan=0, blue=0, purple=0)
        for hue, sat, val in pixels:
            if sat < 75 or val < 55: continue
            if hue < 10 or hue >= 170: name='red'
            elif hue < 20: name='orange'
            elif hue < 36: name='yellow'
            elif hue < 86: name='green'
            elif hue < 100: name='cyan'
            elif hue < 135: name='blue'
            else: name='purple'
            histogram[name] += 1
        return [k for k,v in sorted(histogram.items(), key=lambda item: -item[1]) if v >= 10][:3]

    def snapshot(self):
        frame = self.capture()
        sudo_name = os.environ.get('SUDO_USER')
        owner = pwd.getpwnam(sudo_name) if sudo_name and sudo_name != 'root' else None
        home = Path(owner.pw_dir) if owner else Path.home()
        folder = home/'pidog'/'captures'
        folder.mkdir(parents=True, exist_ok=True)
        filepath = folder / ('buddy_' + time.strftime('%Y%m%d_%H%M%S') + '.jpg')
        if not self.cv2.imwrite(str(filepath), frame):
            raise RuntimeError('Could not save camera image.')
        if owner:
            os.chown(folder, owner.pw_uid, owner.pw_gid)
            os.chown(filepath, owner.pw_uid, owner.pw_gid)
        self.last_shot = filepath
        return filepath

    def describe(self, frame, question):
        if not VISION_MODEL:
            return ''
        jpeg_ok, image = self.cv2.imencode('.jpg', frame, [int(self.cv2.IMWRITE_JPEG_QUALITY), 75])
        if not jpeg_ok:
            raise RuntimeError('Image encoding failed.')
        prompt = (
            'Describe only directly visible objects, positions, clothing, colors, and actions. '
            'Do not identify real people, guess names, identity, age, ethnicity, gender, health, emotions, or other personal traits. '
            'If uncertain, say so. Use two short sentences, plain English. '
            + question
        )
        payload = json.dumps({'model': VISION_MODEL, 'prompt': prompt, 'images': [base64.b64encode(image.tobytes()).decode()], 'stream': False, 'options': {'temperature':0.1, 'num_predict':90}}).encode()
        request = urllib.request.Request(VISION_URL, data=payload, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request, timeout=35) as resp:
            result = json.loads(resp.read(200000))
        return str(result.get('response', '')).strip()[:440]

    def close(self):
        if self.owns_camera and self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except Exception as exc:
                print('[CAMERA] Closing error:', exc, flush=True)
        self.camera = None


def original_melody(style):
    """Original composed tune, generated as a WAV. No copyrighted recordings."""
    sequences = {
        'happy': [(523, .28), (659, .28), (784, .28), (659, .28), (587, .28), (698, .28), (880, .55), (784, .40), (523, .60)],
        'lullaby': [(392, .55), (440, .55), (523, .75), (440, .55), (392, .65), (349, .65), (330, .8), (392, 1.0)],
    }
    seq = sequences.get(style, sequences['happy'])
    sample_rate = 22050
    data = array('h')
    for hz, length in seq:
        ns = int(sample_rate * length)
        for i in range(ns):
            t = i/sample_rate
            envelope = min(1.0, i/250, (ns-i)/600)
            sample = (math.sin(2*math.pi*hz*t) + .18*math.sin(2*math.pi*2*hz*t)) * envelope * 3600
            data.append(int(sample))
        data.extend([0] * int(.05 * sample_rate))
    if not shutil.which('aplay'):
        print('[MUSIC] ALSA aplay is not installed; try: sudo apt install alsa-utils')
        return
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp:
            temp_path = Path(temp.name)
        with wave.open(str(temp_path), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(data.tobytes())
        subprocess.run(['aplay', '-q', str(temp_path)], timeout=16, check=True)
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


def install_actions(vad):
    operations = dict(vad.action_flow.OPERATIONS)
    for sound in ('angry', 'confused_1','confused_2','confused_3','growl_1','growl_2','howling','pant','single_bark_1','single_bark_2','snoring','woohoo'):
        def fn(flow, filename=sound):
            print('[SOUND]', filename, flush=True)
            flow.dog_obj.speak(filename, volume=65)
            time.sleep(.5)
        operations['sound ' + sound] = {'function': fn}
    for style in ('happy','lullaby'):
        def fn(flow, kind=style):
            print('[MUSIC] Original composition:', kind, flush=True)
            original_melody(kind)
        operations['melody ' + style] = {'function': fn}
    vad.action_flow.OPERATIONS = operations
    return vad


_original_load = core.load_existing_vad

def load_plus(path):
    return install_actions(_original_load(path))

core.load_existing_vad = load_plus

_original_init = core.BuddyRuntime.__init__

def init_plus(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    self.ultra_camera = Camera(self.vad)
    self.controller.ultra_runtime = self
    self.ultra_speak_lock = threading.RLock()

core.BuddyRuntime.__init__ = init_plus

_original_speak = core.BuddyRuntime.speak

def speak_plus(self, message):
    with self.ultra_speak_lock:
        return _original_speak(self, message)

core.BuddyRuntime.speak = speak_plus

_original_handle = core.BuddyRuntime.handle

def handle_plus(self, text):
    t = core.normalize(text)
    if not t or core.NEGATION.search(t) or core.STOP.fullmatch(t):
        return _original_handle(self, text)
    if time.monotonic() - self.last_said_at < 2.5 and t == core.normalize(self.last_said):
        print('[ULTRA] Ignoring exact speaker echo.', flush=True)
        return
    if self.require_wake and not re.search(r'\b(?:hey|okay)\s+(?:buddy|body|budi)\b', text.lower()):
        return _original_handle(self, text)
    special = extra_plan(t)
    if special is None:
        return _original_handle(self, text)
    # Reject echo and avoid a new command while a safety routine is underway.
    print('[ULTRA]', special.kind, list(special.steps), flush=True)
    if special.kind == 'say':
        self.speak(special.say)
    elif special.kind == 'vision_memory':
        self.speak(self.ultra_camera.last_observation)
    elif special.kind == 'actions':
        if any(s not in self.controller.flow.OPERATIONS for s in special.steps):
            self.speak('One of the actions is not installed on this PiDog.')
        else:
            self.speak(special.say)
            self.parser.last = special.steps
            self.controller.submit(special)
    else:
        self.speak(special.say)
        self.controller.submit(special)

core.BuddyRuntime.handle = handle_plus

_original_execute = core.MotionController._execute


def execute_plus(self, plan):
    if not plan.kind.startswith('vision_'):
        return _original_execute(self, plan)
    runtime = self.ultra_runtime
    camera = runtime.ultra_camera
    try:
        if self.cancel.is_set():
            return
        if plan.kind == 'vision_memory':
            runtime.speak(camera.last_observation)
            return
        frame = camera.capture()
        if plan.kind == 'vision_photo':
            path = camera.snapshot()
            runtime.speak('Photo saved locally. I printed its full path on the terminal.')
            print('[PHOTO]', path, flush=True)
        elif plan.kind == 'vision_colors':
            names = camera.colors(frame)
            response = 'Prominent colors: ' + ', '.join(names) + '.' if names else 'No reliable prominent saturated colors detected.'
            camera.last_observation = response
            runtime.speak(response)
        elif plan.kind in ('vision_faces','vision_track','vision_person','vision_scene','vision_greet'):
            boxes = list(camera.faces(frame)) if camera.detector is not None else []
            count = len(boxes)
            width = frame.shape[1]
            if plan.kind == 'vision_greet':
                if count:
                    self._do('wag tail')
                    if not self.cancel.is_set():
                        self._do('sound woohoo')
                    runtime.speak('Hello, visitor! I can see a face, but I do not identify people.')
                else:
                    runtime.speak('No reliable frontal face detected to greet.')
            elif plan.kind == 'vision_track':
                if not boxes:
                    runtime.speak('I do not see a reliable frontal face.')
                else:
                    face = max(boxes, key=lambda box: box[2] * box[3])
                    x = face[0] + face[2] / 2
                    yaw = max(-28, min(28, (width/2-x)/(width/2)*28))
                    self.dog.head_move([[yaw, 0, 0]], pitch_comp=getattr(self.flow, 'head_pitch_init', -35), speed=28)
                    self.dog.wait_head_done()
                    runtime.speak('I adjusted my head toward a detected face.')
            elif plan.kind == 'vision_faces':
                statement = ('No frontal faces reliably detected.' if not count else
                             f'I detected {count} visible frontal face' + ('s.' if count != 1 else '.'))
                camera.last_observation = statement
                runtime.speak(statement)
            else:
                question = ('Describe the visible clothing and position of any people.' if plan.kind=='vision_person' else 'Describe the visible objects and scene.')
                response = camera.describe(frame, question)
                if not response:
                    blob = camera.red_round(frame)
                    response = (f'I detected {count} frontal faces. ' if camera.detector else 'Face detector unavailable. ')
                    response += ('I also see a red rounded region, but cannot confirm the object type.' if blob else 'I cannot reliably identify other objects without a local vision model.')
                camera.last_observation = response
                runtime.speak(response)
        elif plan.kind == 'vision_scout':
            # Pretend warning only. Never pursue a person or make physical contact.
            for i in range(3):
                if self.cancel.is_set(): break
                img = camera.capture()
                human = bool(len(camera.faces(img))) if camera.detector is not None else True
                red = camera.red_round(img)
                if human or red:
                    print('[SCOUT] Visible target found. Holding position.', flush=True)
                    self._do('sound growl_1')
                    if not self.cancel.is_set(): self._do('sound single_bark_1')
                    break
                if not self._do('forward'): break
            runtime.speak('Scout finished. No contact or chasing people.')
        elif plan.kind in ('vision_ball', 'vision_chase', 'vision_ball_track'):
            if plan.kind == 'vision_ball':
                blob = camera.red_round(frame)
                response = ('I see a red rounded region in the image.' if blob else 'I cannot see a reliable red round object.')
                camera.last_observation = response
                runtime.speak(response)
            elif plan.kind == 'vision_ball_track':
                blob = camera.red_round(frame)
                if blob is None:
                    runtime.speak('No reliable red rounded object to track.')
                else:
                    offset = blob['cx'] - frame.shape[1]/2
                    yaw = max(-25, min(25, -offset/(frame.shape[1]/2)*25))
                    self.dog.head_move([[yaw,0,0]], pitch_comp=getattr(self.flow, 'head_pitch_init', -35), speed=25)
                    self.dog.wait_head_done()
                    runtime.speak('I am looking toward the red rounded object.')
            else:
                # No human chasing, no cliff protection; robot must be supervised.
                if camera.detector is None:
                    runtime.speak('Face safety check unavailable; I will not chase the ball.')
                    return
                deadline = time.monotonic() + 25
                movements = 0
                while not self.cancel.is_set() and movements < 6 and time.monotonic() < deadline:
                    img = camera.capture()
                    if len(camera.faces(img)) > 0:
                        runtime.speak('Person visible. I will not chase a target toward anyone.')
                        break
                    candidate = camera.red_round(img)
                    if not candidate:
                        print('[CHASE] Lost visual target. Stopping.', flush=True)
                        break
                    # Require consecutive confirmations before moving.
                    time.sleep(.12)
                    candidate2 = camera.red_round(camera.capture())
                    if not candidate2 or abs(candidate2['cx'] - candidate['cx']) > 75:
                        print('[CHASE] Unstable target. Stopping.', flush=True)
                        break
                    d = self.sensors.distance()
                    if d is None or d < max(45, self.cfg.clearance_cm):
                        print('[CHASE] Insufficient verified clearance:', d, flush=True)
                        break
                    center = img.shape[1] / 2
                    offset = candidate['cx'] - center
                    action = 'turn right' if offset > 85 else ('turn left' if offset < -85 else 'forward')
                    if not self._do(action):
                        break
                    movements += 1
                runtime.speak(f'I finished the supervised ball game after {movements} movement cycles.')
    except Exception as exc:
        print('[VISION ERROR]', repr(exc), flush=True)
        runtime.speak('Camera or vision feature unavailable. Check the camera and optional packages.')

core.MotionController._execute = execute_plus

_original_close = core.BuddyRuntime.close

def close_plus(self):
    _original_close(self)
    if not self.controller.worker.is_alive():
        self.ultra_camera.close()

core.BuddyRuntime.close = close_plus


def self_test():
    assert extra_plan('growl three times').steps == tuple(['sound growl_1'] * 3)
    assert extra_plan('play fight').steps[0] == 'stand'
    assert extra_plan('chase the red ball').kind == 'vision_chase'
    assert extra_plan('describe the person').kind == 'vision_person'
    assert extra_plan('what colors do you see').kind == 'vision_colors'
    assert extra_plan('greet the person you see').kind == 'vision_greet'
    assert extra_plan('track the red ball with your head').kind == 'vision_ball_track'
    assert extra_plan('explore and attack').kind == 'vision_scout'
    assert extra_plan('sing a song').steps == ('melody happy',)
    assert extra_plan('do not chase the ball') is None
    assert extra_plan('who is that').kind == 'say'
    assert extra_plan('what if you attacked someone') is None
    assert extra_plan('should you chase someone') is None
    assert extra_plan('who is the president') is None
    assert extra_plan('stop') is None
    assert extra_plan('scratch yourself') is None  # delegated to calibrated scratch code
    assert not extra_plan('can you explain what a growl is')
    print('[TEST] Buddy Ultra: 17 extra parser tests PASSED (no hardware).')
    core.self_test()


def camera_check():
    class Dummy: pass
    c = Camera(Dummy())
    try:
        frame = c.capture()
        print('[CAMERA] Resolution:', tuple(frame.shape))
        print('[CAMERA] Face classifier available:', c.detector is not None)
        print('[CAMERA] Camera tests completed; no motors were activated.')
    finally:
        c.close()

def main():
    global VISION_MODEL, VISION_URL
    # Remove only addon-specific CLI args, leaving the original Buddy 2 args intact.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--camera-check', action='store_true')
    parser.add_argument('--vision-model', default='')
    parser.add_argument('--vision-url', default='http://127.0.0.1:11434/api/generate')
    mine, remaining = parser.parse_known_args(sys.argv[1:])
    sys.argv = [sys.argv[0]] + remaining
    VISION_MODEL = mine.vision_model.strip()
    VISION_URL = mine.vision_url.strip()
    if VISION_MODEL:
        from urllib.parse import urlparse
        import ipaddress
        u = urlparse(VISION_URL)
        try:
            host = u.hostname or ''
            allowed = (host == 'localhost' or ipaddress.ip_address(host).is_private or ipaddress.ip_address(host).is_loopback)
        except ValueError:
            allowed = False
        if not allowed or u.scheme != 'http' or not u.path.endswith('/api/generate'):
            raise SystemExit('Vision server must be a localhost/private-LAN HTTP Ollama /api/generate URL.')
    if mine.camera_check:
        camera_check()
        return
    if '--calibrate-scratch' in sys.argv or scratch.CALIBRATE:
        scratch.calibrate()
        return
    if '--self-test' in sys.argv:
        self_test()
        return
    core.main()


if __name__ == '__main__':
    main()
