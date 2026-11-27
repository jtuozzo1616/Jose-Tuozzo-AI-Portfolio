#!/usr/bin/env python3
"""Non-destructive voice vision layer on top of Buddy Final.

Existing motion, patrol/scout, sound recall, voice fixes and safety remain
in buddy_final.py. Uses the already installed buddy_vision_directo.py for
object recognition and color segmentation. No motors activated here.
"""
import re
import sys
import time
import glob
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

try:
    import buddy_final as final
    import buddy_vision_directo as vision
    from picamera2 import Picamera2
    import cv2
    import numpy as np
except ImportError as exc:
    raise SystemExit(f'[SETUP ERROR] Missing dependency: {exc}')

core = final.core
old_handle = core.BuddyRuntime.handle  # includes final's sound-recall gating
model = None

TRANSLATE = {
    'persona':'person', 'botella':'bottle', 'perro':'dog',
    'gato':'cat', 'silla':'chair', 'carro':'car',
    'bicicleta':'bicycle', 'avion':'airplane',
    'ave':'bird', 'barco':'boat', 'autobus':'bus',
    'vaca':'cow', 'mesa':'dining table', 'caballo':'horse',
    'moto':'motorcycle', 'planta':'plant', 'oveja':'sheep',
    'tren':'train', 'televisor':'television',
    'rojo':'red', 'naranja':'orange', 'amarillo':'yellow',
    'verde':'green', 'cian':'cyan', 'azul':'blue',
    'morado':'purple', 'blanco':'white', 'negro':'black',
    'izquierda':'left','centro':'center','derecha':'right',
    'mixto':'mixed','desconocido':'unknown'
}
def en(value):
    return TRANSLATE.get(value, value)

COLOR_NAMES = {en(k): k for k in vision.COLORS}
SUPPORTED = {en(n) for n in vision.NAMES[1:]}
ALIASES = {'human':'person', 'people':'person', 'humans':'person',
           'bottles':'bottle', 'cars':'car', 'chairs':'chair',
           'dogs':'dog', 'cats':'cat', 'tv':'television',
           'motorbike':'motorcycle'}

VISION_COMMAND = re.compile(
    r'\b(?:what (?:do|can) you see|what(?: is|\'s) (?:in front|there)|'
    r'what(?: is|\'s) that|look (?:for|at)|find (?:a|an|the|something)|'
    r'(?:can|do) you see|where is (?:a|an|the)|what colou?r|'
    r'identify (?:an?|the|objects|colors)|describe (?:what|the|this)|'
    r'scan (?:the|your|around)|take (?:a )?(?:photo|picture)|'
    r'how many (?:people|persons|bottles|cars|chairs)|'
    r'(?:is|are) there (?:a|an|any)|can you recognize|'
    r'how far (?:away )?is)\b', re.I
)

def is_vision_command(text):
    t = core.normalize(str(text))
    if hasattr(final, 'is_recall') and final.is_recall(t):
        return False
    return bool(VISION_COMMAND.search(t))

def capture_bgr():
    cam = Picamera2()
    started = False
    try:
        cam.configure(cam.create_still_configuration(
            main={'size': (1280,720), 'format':'RGB888'}
        ))
        cam.start()
        started = True
        time.sleep(0.8)
        return cam.capture_array('main')  # Picamera2 RGB888 is BGR byte order
    finally:
        if started:
            cam.stop()
        cam.close()

def colors_in_scene(frame):
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    result = []
    for english, key in COLOR_NAMES.items():
        binary = vision.mask(hsv, key)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
                                  np.ones((5,5), dtype=np.uint8))
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:2]:
            area = cv2.contourArea(contour)
            if area < max(800, 0.0015*w*h):
                continue
            x,y,cw,ch = cv2.boundingRect(contour)
            result.append((english, en(vision.side(x+cw/2,w)), area))
    return sorted(result, key=lambda item: item[2], reverse=True)

def faces_in_scene(frame):
    locations = glob.glob('/usr/share/opencv*/haarcascades/haarcascade_frontalface_default.xml')
    locations += glob.glob('/usr/local/lib/python*/dist-packages/cv2/data/haarcascade_frontalface_default.xml')
    for path in locations:
        detector = cv2.CascadeClassifier(path)
        if not detector.empty():
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return list(detector.detectMultiScale(gray,1.1,4,minSize=(32,32)))
    print('[VISION] Face detector XML unavailable; skipping face recognition.', flush=True)
    return []

def analyze(command):
    global model
    if re.search(r'\bhow far (?:away )?is\b', command):
        return ('My camera cannot measure an exact object distance. '
                'The ultrasonic sensor only checks the area directly ahead, '
                'and its readings must be valid before moving.')

    frame = capture_bgr()
    h,w = frame.shape[:2]
    overlay = frame.copy()
    found = []
    for cls, confidence, box in vision.objects(model, frame):
        if confidence < 0.53:
            continue
        x1,y1,x2,y2 = box
        name = en(vision.NAMES[cls]); location = en(vision.side((x1+x2)/2,w))
        color = en(vision.main_color(frame[y1:y2, x1:x2]))
        found.append((name,color,location,confidence,box))
        cv2.rectangle(overlay, (x1,y1),(x2,y2),(0,255,0),3)
        cv2.putText(overlay, f'{name}: {confidence:.0%}, {color}',
                    (x1,max(24,y1-8)), cv2.FONT_HERSHEY_SIMPLEX,.63,(0,255,0),2)

    color_regions = colors_in_scene(frame)
    faces = faces_in_scene(frame)
    for x,y,fw,fh in faces:
        cv2.rectangle(overlay,(x,y),(x+fw,y+fh),(255,255,0),2)
        cv2.putText(overlay,'face',(x,max(20,y-5)),
                    cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,0),2)
    path = BASE / 'buddy_last_voice_vision.jpg'
    cv2.imwrite(str(path), overlay)
    print('[VISION] Objects:', [(n,c,p,round(q,2)) for n,c,p,q,_ in found],flush=True)
    print('[VISION] Color regions:',color_regions[:5],flush=True)
    print('[VISION] Faces:',len(faces),'Photo:',str(path),flush=True)

    spoken = core.normalize(command)
    wanted_color = next((c for c in COLOR_NAMES if re.search(r'\b'+c+r'\b',spoken)),None)
    wanted_object = next((n for n in sorted(SUPPORTED,key=len,reverse=True)
                          if re.search(r'\b'+re.escape(n)+r's?\b',spoken)),None)
    if wanted_object is None:
        wanted_object = next((v for k,v in ALIASES.items()
                              if re.search(r'\b'+re.escape(k)+r'\b',spoken)),None)

    if re.search(r'\b(face|faces)\b',spoken):
        if faces:
            x,y,fw,fh = faces[0]
            return f'Yes. I can see {len(faces)} face' + ('s.' if len(faces)>1 else f' on the {en(vision.side(x+fw/2,w))}.')
        return 'I cannot clearly detect a face right now.'

    if re.search(r'\bhow many\b',spoken):
        target = wanted_object or ('person' if re.search(r'\b(people|persons)\b',spoken) else None)
        count = sum(n == target for n,_,_,_,_ in found) if target else len(found)
        category = ('people' if target == 'person' else (target + 's' if target else 'objects'))
        return f'I can identify {count} {category} in this image.'

    if wanted_object:
        matches = [item for item in found if item[0] == wanted_object]
        if wanted_color:
            matches = [item for item in matches if item[1] == wanted_color]
        if matches:
            n,c,p,q,box = matches[0]
            return f'Yes. I see a {c} {n} on the {p}.' if c not in ('mixed','unknown') else f'Yes. I see a {n} on the {p}.'
        if model is None:
            return 'Object recognition is unavailable. I can still detect colors.'
        return f'I cannot confidently identify a {wanted_color+" " if wanted_color else ""}{wanted_object}.'

    if wanted_color:
        regions = [region for region in color_regions if region[0] == wanted_color]
        if regions:
            return f'I can see {wanted_color} on the {regions[0][1]}.'
        return f'I cannot clearly detect {wanted_color} right now.'

    if re.search(r'\b(photo|picture)\b',spoken):
        return 'I took a picture and saved it to buddy last voice vision dot jpg.'
    if found:
        descriptions=[]
        for n,c,p,_,_ in found:
            label=f'a {n} on the {p}'
            if label not in descriptions:
                descriptions.append(label)
        return 'I can see '+', '.join(descriptions[:3])+'.'
    if faces:
        return f'I can see {len(faces)} face' + ('s.' if len(faces)>1 else '.')
    if color_regions:
        return 'I can see '+', '.join(f'{c} on the {p}' for c,p,_ in color_regions[:3])+', but no clearly recognized objects.'
    if model is None:
        return 'My object detection model is unavailable, and I cannot detect a clear color region.'
    return 'I cannot confidently recognize an object. Try better lighting or move it closer.'

def enhanced_handle(self, text):
    if getattr(self, 'sound_recall_active', False) or not is_vision_command(text):
        return old_handle(self,text)
    print('[VISION COMMAND]',repr(text),flush=True)
    try:
        answer = analyze(str(text))
    except Exception as exc:
        print('[VISION ERROR]',repr(exc),flush=True)
        answer = 'I could not access my camera. Please make sure no other camera program is running.'
    print('[BUDDY]',answer,flush=True)
    self.speak(answer)  # existing offline voice; no motor commands triggered

core.BuddyRuntime.handle = enhanced_handle

if __name__ == '__main__':
    if '--vision-self-test' in sys.argv:
        assert is_vision_command('Buddy what do you see')
        assert is_vision_command('Can you see a bottle?')
        assert not is_vision_command('Come back')
        assert not is_vision_command('Dance')
        print('[TEST] Vision command routing passed. No motors or camera activated.')
        sys.exit(0)
    print('[BUDDY] Loading existing final motion and sound-recall system...')
    try:
        model = vision.get_model()
    except Exception as exc:
        print('[VISION] Model unavailable:',exc,flush=True)
    print('[BUDDY] Vision + voice active. Ask: What do you see?',flush=True)
    final.ultra.main()
