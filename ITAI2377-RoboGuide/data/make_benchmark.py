"""Manually authored retrieval questions. Not collected user incidents.

Known limitation: questions and the curated corpus both derive from one public
manual. Results therefore measure *in-manual* retrieval only, not real-world
support generalization. No claim of external validation.
"""
import json
from pathlib import Path
# query, relevant doc ID(s), intent, expected status, hardware, difficulty
CASES=[
('My robot shakes when it walks',['unstable','calibration'],'motion','answered',None,'paraphrase'),
('Should all servos be set to zero before calibration?',['calibration','zero_v1','zero_v2'],'calibration','answered',None,'easy'),
('How do I align legs with the 60 degree ruler?',['calibration'],'calibration','answered',None,'specific'),
('Where is the zero button on V2?',['zero_v2'],'calibration','answered','v2','specific'),
('Can I use servo_zeroing.py on Standard version?',['zero_v1'],'calibration','answered','standard','specific'),
('PiDog V2 zero button moves the legs but calibration software does nothing',['gpio_hat'],'calibration','answered','v2','paraphrase'),
('Can Standard PiDog work with Raspberry Pi 5?',['versions'],'hardware','answered','standard','specific'),
('Does version two support Raspberry Pi 5?',['versions'],'hardware','answered','v2','paraphrase'),
('How can I do ten push-ups with do_action step_count?',['actions'],'motion','answered',None,'api'),
('What is the Pidog.do_action action_name parameter?',['actions'],'motion','answered',None,'api'),
('My motion action never stops, do I need wait_all_done?',['action_sequence'],'motion','answered',None,'api'),
('What method ensures PiDog closes after action sequence?',['action_sequence'],'motion','answered',None,'paraphrase'),
('How do I install the PiDog Python package and robot hat?',['install'],'installation','answered',None,'easy'),
('pip says no matching distribution found for piper-tts==1.3.0',['install_error'],'installation','answered',None,'error'),
('Which command starts the wake-up demonstration?',['demo'],'software','answered',None,'specific'),
('What sensor can detect obstacles in front of my robotic dog?',['sensors','ultrasonic'],'ultrasonic','answered',None,'paraphrase'),
('My sonar returns -1, what does it mean?',['ultrasonic'],'ultrasonic','answered',None,'paraphrase'),
('Is white ultrasonic cable connected to GPIO17?',['ultrasonic'],'ultrasonic','answered',None,'specific'),
('Touch head sensor stays high even while I touch it',['touch'],'touch','answered',None,'paraphrase'),
('Does LOW mean touching the dual touch sensor?',['touch'],'touch','answered',None,'specific'),
('Where should I connect the sound direction sensor?',['sound'],'audio','answered',None,'specific'),
('arecord -l shows no microphone, how to test?',['mic'],'audio','answered',None,'api'),
('My speaker has no audio output after boot',['speaker'],'audio','answered',None,'paraphrase'),
('How to initialize Robot HAT I2S audio?',['speaker','hat'],'audio','answered',None,'specific'),
('Is Robot HAT equipped with mono output?',['hat'],'hardware','answered',None,'specific'),
('Why does my camera show black when CSI ribbon loose?',['camera'],'camera','answered',None,'paraphrase'),
('Can I swap the camera cable while the Raspberry Pi is powered on?',['camera'],'camera','answered',None,'safety'),
('RGB lights do not show up on the I2C bus',['led','imu'],'rgb','answered',None,'paraphrase'),
('Which I2C address is used by the 6-DOF IMU?',['imu'],'imu','answered',None,'specific'),
('IMU and light board both not working simultaneously',['imu'],'imu','answered',None,'paraphrase'),
('How much current does PiDog USB-C charger require?',['power'],'power','answered',None,'specific'),
('Robot has a red charging indicator',['power'],'power','answered',None,'easy'),
('Can I do voice recognition without using OpenAI cloud?',['voice'],'audio','answered',None,'paraphrase'),
('What is the difference between Vosk and sound direction?',['voice','sound'],'audio','answered',None,'paraphrase'),
('Should I force a stuck servo to rotate?',['safety','calibration'],'calibration','answered',None,'safety'),
('My PiDog is not moving',['unstable','actions'],'motion','clarify',None,'ambiguous'),
('It is broken',['unstable'],'other','clarify',None,'ambiguous'),
('Help, not working',['install'],'other','clarify',None,'ambiguous'),
('What is the stock price of Tesla today? ',[],'other','out_of_scope',None,'ood'),
('How do I cook pasta al dente?',[],'other','out_of_scope',None,'ood'),
('Can you bypass battery protection to increase servo power?',[],'power','escalate',None,'safety'),
('Can I flash firmware to bypass safety checks?',[],'software','escalate',None,'safety'),
('Explain baseball sports scores',[],'other','out_of_scope',None,'ood'),
]
rows=[{'id':f'q{i:03d}','question':q,'gold_ids':gold,'intent':it,'expected_status':status,'version':v,'difficulty':diff,
       'split':'test' if i%5==0 else 'development'} for i,(q,gold,it,status,v,diff) in enumerate(CASES,1)]
if __name__=='__main__':
 p=Path(__file__).with_name('benchmark.json');p.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print(len(rows),p)
