#!/usr/bin/env python3
"""Buddy V9: patrol forward -> acquire green bottle -> cautious orbit.
Standalone navigation module on top of the existing buddy_orbit_motion_v6.py.
No changes to existing files. All spoken responses are English.
"""
import sys
sys.dont_write_bytecode = True
import math, re, statistics, time, threading
from contextlib import suppress
from pathlib import Path

# Pure helpers: allow testing on a Mac without PiDog hardware.
def stable_front(samples, minimum):
    """Front range: majority must agree, ANY valid close echo is a veto."""
    v = clean_samples(samples)
    if len(v) < 5 or min(v) < minimum:
        return None
    cluster = sorted(max(groups(v), key=len))
    if len(cluster) < 5 or len(cluster) / len(v) < .67:
        return None
    if len(groups(v)) > 1 and sorted((len(x) for x in groups(v)), reverse=True)[1] >= 3:
        return None
    return round(statistics.median(cluster), 1)

def clean_samples(samples):
    out = []
    for item in samples:
        try:
            val = float(item)
            if math.isfinite(val) and 5 <= val <= 350:
                out.append(val)
        except (TypeError, ValueError, OverflowError):
            pass
    return sorted(out)

def groups(values):
    clusters = []
    for value in sorted(values):
        if not clusters or value-clusters[-1][-1] > max(7, value*.085):
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return clusters

def cautious_side(samples, minimum):
    """For side scans, take the NEAREST repeated echo, never the farthest.
    A directional echo is not full lateral obstacle coverage.
    """
    values = clean_samples(samples)
    if len(values) < 4 or min(values) < minimum:
        return None
    near = groups(values)[0]
    if len(near) < 3 or min(near) < minimum+5:
        return None
    return round(statistics.median(near), 1)

def choose_turn(offset, size, nearby, previous_forward):
    """offset: target angle on bottle's INSIDE, in degrees."""
    if nearby is not None and nearby < 50:
        return 'away'
    if offset < 30:
        return 'away'
    if offset > 67:
        return 'toward'
    if nearby is not None and nearby > 145:
        return 'toward'
    if previous_forward >= 4 and offset > 43:
        return 'toward'
    return 'forward'

def self_test():
    assert stable_front([100,100,100.1,99.9,100,100], 78) == 100.0
    assert stable_front([100,100,100,100,100,55], 78) is None
    assert stable_front([65,65,65,194,194,194], 60) is None
    assert cautious_side([84.7,86.4,85,174,167,211], 74) is not None
    assert cautious_side([84,86,66,200], 74) is None
    assert choose_turn(17,.25,90,0) == 'away'
    assert choose_turn(45,.25,90,2) == 'forward'
    assert choose_turn(74,.25,90,0) == 'toward'
    print('[TEST PASSED] Patrol, distance filter, and orbit control; no hardware started.')

if '--self-test' in sys.argv:
    self_test()
    raise SystemExit(0)

import cv2
from picamera2 import Picamera2
import buddy_orbit_motion_v6 as v6

core = v6.core
old_handle = core.BuddyRuntime.handle
lock = v6.lock
cancel = v6.cancel
MODEL = None
ROOT = Path(__file__).resolve().parent
RUN_ENABLED = '--supervised-search' in sys.argv
MAX_SESSION = 270.0  # No fixed move count, but 4.5-minute watchdog.
PATROL_FRONT = 105.0
ORBIT_FRONT = 75.0
TURN_FRONT = 70.0
SIDE_MIN = 74.0
BOTTLE_MIN = 43.0
last_head = {'dog': None, 'yaw': None}
active = {'dog': None, 'quiet': 0.0}

MISSION = re.compile(r'(?:explore|search|patrol|find|look for|go around|orbit|circle)', re.I)
TARGET_WORD = re.compile(r'\b(?:green|bottles?|object)\b', re.I)
HALT = re.compile(r'^(?:stop|cancel|halt|freeze)(?: now)?$', re.I)

def stopped():
    if cancel.is_set():
        raise InterruptedError('Stop requested')

def aim(dog, yaw):
    stopped()
    yaw = round(max(-43, min(43, yaw)))
    if dog is last_head['dog'] and last_head['yaw'] is not None and abs(yaw-last_head['yaw']) <= 1 and dog.is_head_done():
        return yaw
    dog.head_move([[yaw,0,0]], immediately=True, speed=30)
    deadline = time.monotonic()+4
    while not dog.is_head_done():
        stopped()
        if time.monotonic() > deadline:
            raise RuntimeError('Head timeout')
        time.sleep(.045)
    time.sleep(.15)
    last_head.update(dog=dog, yaw=yaw)
    return yaw

def sensor_read(sensor, attempts=18):
    if not callable(sensor):
        return []
    raw=[]
    for i in range(attempts):
        stopped()
        try:
            d=float(sensor())
            if math.isfinite(d) and 5 <= d <= 350:
                raw.append(d)
        except (TypeError, ValueError, OSError, RuntimeError, OverflowError):
            pass
        time.sleep(.058)
    return raw

def measure(dog, sensor, yaw, min_cm, label, side=False):
    aim(dog, yaw)
    vals=sensor_read(sensor)
    cm=(cautious_side(vals,min_cm) if side else stable_front(vals,min_cm))
    print(f'[RANGE] {label}: {cm} cm; samples={[round(x,1) for x in vals]}', flush=True)
    if cm is None:
        raise RuntimeError(f'Cannot verify {label} clearance')
    return cm

def green(frame):
    shapes = v6.base.green_candidates(frame)
    if shapes:
        return shapes[0]
    # MobileNet fallback when green segmentation did not find a target.
    if MODEL is not None:
        models=v6.base.model_bottle(frame)
        if models:
            return max(models, key=lambda x:x['confidence'])
    return None

def visible(cam):
    """Confirm green bottle-like object in at least 2 of 3 camera frames."""
    shots=[]
    for _ in range(3):
        stopped()
        frame=cam.capture_array('main')
        obj=green(frame)
        if obj:
            shots.append((obj,frame))
        time.sleep(.065)
    for i in range(len(shots)):
        for j in range(i+1,len(shots)):
            a,b=shots[i][0],shots[j][0]
            if abs(a['x']-b['x']) < .13 and abs(a['size']-b['size']) < .18:
                return shots[j]
    return None, None

def sight(cam,dog,angles=(0,),name='look'):
    """Small head scan. Prefer no head movement when target appears."""
    candidate=None
    for angle in dict.fromkeys(angles):
        yaw=aim(dog,angle)
        obj,frame=visible(cam)
        if obj is not None:
            candidate=(yaw,obj,frame)
            break
    if candidate is None:
        return None
    yaw,obj,frame=candidate
    # One correction only when target is notably off-center.
    if abs(obj['x']-.5) > .18:
        correction=round(max(-7,min(7,(.5-obj['x'])*30)))
        if abs(correction)>=3:
            yaw2=round(max(-43,min(43,yaw+correction)))
            aim(dog,yaw2)
            better,betterframe=visible(cam)
            if better is not None and abs(better['x']-.5)<abs(obj['x']-.5)+.02:
                yaw,obj,frame=yaw2,better,betterframe
            else:
                aim(dog,yaw)
    obj=dict(obj, yaw=yaw, bearing=yaw+(.5-obj['x'])*52)
    print('[FOUND]', obj['source'], 'bearing=',round(obj['bearing'],1),
          'height=',round(obj['size'],2),flush=True)
    if name in ('found','start'):
        img=frame.copy()
        x1,y1,x2,y2=obj['box']
        cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
        cv2.imwrite(str(ROOT/f'buddy_explore_{name}.jpg'),img)
    return obj

def move(dog,action):
    stopped()
    aim(dog,0)
    if not dog.is_legs_done():
        raise RuntimeError('Legs are busy')
    print('[MOVE]',action,flush=True)
    dog.do_action(action,step_count=1,speed=23)
    deadline=time.monotonic()+8
    time.sleep(.10)
    while not dog.is_legs_done():
        stopped()
        if time.monotonic()>deadline:
            raise RuntimeError('Motor action timeout')
        time.sleep(.05)
    time.sleep(.13)

def select_side(dog,sensor):
    options=[]
    for side,angle in (('left',30),('right',-30)):
        try:
            cm=measure(dog,sensor,angle,SIDE_MIN,side+' side',side=True)
            options.append((side,cm))
        except RuntimeError as err:
            print('[SIDE]',side,'unconfirmed:',err,flush=True)
    return max(options,key=lambda x:x[1])[0] if options else None

def run_mission(cam,dog,sensor):
    if not RUN_ENABLED:
        return 'Bottle exploration is not enabled.'
    if not callable(sensor):
        return 'My ultrasonic sensor is unavailable. I will not walk.'
    began=time.monotonic()
    count=0
    forwards=0
    turns_without_forward=0
    side=None
    try:
        print('[PHASE] EXPLORE -> SEARCH FOR GREEN BOTTLE',flush=True)
        # Search ahead before the first step: no blind walk toward an existing bottle.
        found=sight(cam,dog,(0,-23,23),'start')
        patrol_turns=0
        while found is None:
            stopped()
            if time.monotonic()-began>MAX_SESSION:
                return 'Exploration session ended. I could not find the green bottle.'
            try:
                measure(dog,sensor,0,PATROL_FRONT,'patrol front')
            except RuntimeError:
                side=select_side(dog,sensor)
                if side is None or patrol_turns>=3:
                    raise RuntimeError('Patrol path blocked or sensor inconclusive')
                measure(dog,sensor,0,TURN_FRONT,'patrol turning clearance')
                move(dog,'turn_left' if side=='left' else 'turn_right')
                count+=1
                patrol_turns+=1
            else:
                move(dog,'forward')
                count+=1
                forwards+=1
                patrol_turns=0
            # Look during the patrol, at most a small scan every third step.
            angles=(0,-22,22) if count%3==0 else (0,)
            found=sight(cam,dog,angles,'patrol')
            print('[EXPLORE] total=',count,'forward=',forwards,'target=',bool(found),flush=True)

        print('[PHASE] TARGET ACQUIRED -> APPROACH',flush=True)
        # Gently align the body, if target was off-axis.
        for _ in range(3):
            if abs(found['bearing']) <= 20:
                break
            direction=1 if found['bearing']>0 else -1
            measure(dog,sensor,0,TURN_FRONT,'alignment front')
            measure(dog,sensor,30*direction,SIDE_MIN,'alignment side',side=True)
            move(dog,'turn_left' if direction>0 else 'turn_right')
            count+=1
            found=sight(cam,dog,(0,-20,20),'found')
            if found is None:
                raise RuntimeError('Bottle lost during body alignment')
        if abs(found['bearing'])>25:
            raise RuntimeError('Bottle is too far to one side')

        # If bottle is already 74-100 cm ahead, do not approach into it.
        # Require measurable progress so a stuck gait cannot run repeatedly.
        approach_ranges=[]
        while time.monotonic()-began<MAX_SESSION:
            target_cm=measure(dog,sensor,round(found['yaw']),60,'bottle direction')
            approach_ranges.append(target_cm)
            if (len(approach_ranges)>=4 and
                    target_cm>approach_ranges[-4]-3):
                raise RuntimeError('No measured progress toward bottle')
            print('[BOTTLE] Forward ultrasonic echo approximately',target_cm,'cm',flush=True)
            if target_cm <= 120:
                break
            measure(dog,sensor,0,115,'approach front')
            move(dog,'forward')
            count+=1
            forwards+=1
            found=sight(cam,dog,(0,-20,20),'approach')
            if found is None or abs(found['bearing'])>28:
                raise RuntimeError('Bottle lost during approach')
        else:
            raise RuntimeError('Approach watchdog expired')

        print('[PHASE] SELECT ORBIT SIDE',flush=True)
        side=select_side(dog,sensor)
        if side is None:
            raise RuntimeError('Neither side provides enough credible clearance')
        sign=1 if side=='right' else -1
        inside=sign*32
        outside=-sign*30
        away='turn_right' if side=='right' else 'turn_left'
        toward='turn_left' if side=='right' else 'turn_right'
        # Turn to place the bottle on the inside of the circle.
        measure(dog,sensor,0,TURN_FRONT,'initial turn front')
        measure(dog,sensor,outside,SIDE_MIN,'initial outside',side=True)
        move(dog,away)
        count+=1
        print('[PHASE] ORBIT; keeping bottle', 'left' if sign>0 else 'right',flush=True)
        streak=0
        while time.monotonic()-began < MAX_SESSION:
            stopped()
            found=sight(cam,dog,(inside,inside+sign*9,0),'orbit')
            if found is None:
                raise RuntimeError('Lost green bottle; refusing blind movement')
            offset=found['bearing']*sign
            if not 5 <= offset <= 83:
                raise RuntimeError(f'Bottle outside tracking sector ({offset:.0f} degrees)')
            if found['size']>.65:
                raise RuntimeError('Bottle appears very close in camera')
            # Do not insist on a strong bottle echo, but reject any close return.
            aim(dog,found['yaw'])
            echo=sensor_read(sensor,12)
            if echo and min(echo) < BOTTLE_MIN:
                raise RuntimeError('Bottle side below safe clearance')
            action=choose_turn(offset,found['size'],min(echo) if echo else None,streak)
            # Always check the actual front before the next action.
            measure(dog,sensor,0,ORBIT_FRONT if action=='forward' else TURN_FRONT,
                    'orbit front')
            if action=='forward' or count%3==0:
                measure(dog,sensor,outside,SIDE_MIN,'orbit outside',side=True)
            if action=='away':
                real=away
                turns_without_forward+=1
                streak=0
            elif action=='toward':
                real=toward
                turns_without_forward+=1
                streak=0
            else:
                real='forward'
                turns_without_forward=0
                streak+=1
                forwards+=1
            if turns_without_forward>5:
                raise RuntimeError('Repeated turns without forward progress')
            move(dog,real)
            count+=1
            print('[ORBIT] actions=',count,'forwards=',forwards,
                  'angle=',round(offset,1),'elapsed=',round(time.monotonic()-began),flush=True)
        return (f'I completed {count} short actions, including {forwards} forward gaits. '
                'The safety session ended. A complete circle was not measured.')
    except (RuntimeError,TimeoutError,InterruptedError) as err:
        print('[MISSION STOP]',str(err),flush=True)
        return f'I stopped after {count} actions and {forwards} forward gaits. Reason: {err}.'
    finally:
        with suppress(Exception): dog.body_stop()
        with suppress(Exception): dog.head_move([[0,0,0]],immediately=True,speed=25)

def worker(runtime):
    cam=None
    dog=None
    try:
        dog,sensor=v6.get_parts(runtime)
        active['dog']=dog
        required=('head_move','is_head_done','do_action','is_legs_done','body_stop')
        if dog is None or any(not callable(getattr(dog,name,None)) for name in required):
            response='My motor controller is unavailable.'
        elif not dog.is_legs_done():
            response='My legs are busy.'
        else:
            cam=Picamera2()
            cam.configure(cam.create_video_configuration(main={'size':(1280,720),'format':'RGB888'}))
            cam.start()
            time.sleep(.7)
            response=run_mission(cam,dog,sensor)
    except Exception as exc:
        print('[MISSION ERROR]',repr(exc),flush=True)
        response='The exploration failed, so I stopped.'
    finally:
        if cam is not None:
            with suppress(Exception): cam.stop()
            with suppress(Exception): cam.close()
        if dog is not None:
            with suppress(Exception): dog.body_stop()
        active['dog']=None
        last_head.update(dog=None,yaw=None)
        lock.release()
    print('[BUDDY]',response,flush=True)
    active['quiet']=time.monotonic()+3
    with suppress(Exception): runtime.speak(response)
    active['quiet']=time.monotonic()+3

def handle(runtime,text):
    raw=core.normalize(str(text)).lower()
    query=' '.join(re.sub(r'\b(?:buddy|body|budi)\b',' ',raw).split())
    if HALT.fullmatch(query):
        cancel.set()
        if lock.locked():
            dog=active['dog']
            if dog is not None:
                with suppress(Exception): dog.body_stop()
            print('[BUDDY] STOP requested',flush=True)
            return
        return old_handle(runtime,text)
    if lock.locked() or time.monotonic()<active['quiet']:
        return
    if getattr(runtime,'sound_recall_active',False) or v6.base.base.previous.base.buddy.is_recall(query):
        return old_handle(runtime,text)
    mission=((MISSION.search(query) and TARGET_WORD.search(query))
             or query in ('explore','search bottle','bottle patrol','find bottle and orbit'))
    if mission and not core.NEGATION.search(query):
        if not RUN_ENABLED:
            runtime.speak('Supervised bottle patrol is disabled.')
            return
        if lock.acquire(blocking=False):
            cancel.clear()
            threading.Thread(target=worker,args=(runtime,),daemon=True).start()
        return
    return old_handle(runtime,text)

core.BuddyRuntime.handle=handle

if __name__=='__main__':
    MODEL=v6.base.vision.get_model()
    v6.MODEL=MODEL
    v6.base.MODEL=MODEL
    v6.base.base.net=MODEL
    sys.argv=[arg for arg in sys.argv if arg!='--supervised-search']
    print('[BUDDY] Explore-and-find-bottle ready; supervised=',RUN_ENABLED,flush=True)
    v6.base.base.previous.base.buddy.ultra.main()
