"""Auditable, manually curated summaries of official manufacturer sections.

This is not a live mirror: each record links to the official document it summarizes.
Run `python -m roboguide.ingest --online` in a networked environment to acquire
fresh original HTML and build an independently evaluated larger corpus.
"""
import json
from pathlib import Path

FAQ='https://docs.sunfounder.com/projects/pidog/en/latest/faq.html'
DOC='https://docs.sunfounder.com/projects/pidog/en/latest/'
HAT='https://docs.sunfounder.com/projects/robot-hat/en/latest/'
PRE='https://docs.sunfounder.com/projects/pidog/en/latest/python/py_b6_preset_action.html'
CAL='https://docs.sunfounder.com/projects/pidog/en/latest/python/py_0_calibrate.html'
API='https://docs.sunfounder.com/projects/pidog/en/latest/python/play_with_python.html'
GIT='https://github.com/sunfounder/pidog'
# Each entry: id, title, subsystem, hardware, URL, evidence-based paraphrase / short supported command.
data=[
('versions','Hardware compatibility: Standard vs V2','hardware','shared',DOC,'PiDog Standard/V1 supports Raspberry Pi 3B+, Raspberry Pi 4B and Zero 2W; it does not support Raspberry Pi 5. PiDog V2 has updated Robot HAT and servo circuitry and supports Raspberry Pi 3/4/5 and Zero 2W. Confirm your PiDog hardware version before following platform-specific guidance.'),
('zero_v1','V1 or Standard servo zeroing','calibration','standard',FAQ,'For Standard/V1 PiDog, use the manufacturer-provided zeroing script before assembly: cd ~/pidog/examples ; sudo python3 servo_zeroing.py. Return the servos to zero before reassembling legs. This procedure differs from V2 zero button.'),
('zero_v2','V2 servo zero button','calibration','v2',FAQ,'PiDog V2 with Robot HAT V5 has an onboard zeroing button that sets servos to zero without a script. Power the robot and press the zeroing button before reassembling misaligned legs following the official assembly instructions. This button is not present on Standard/V1.'),
('calibration','Step-by-step calibration with ruler','calibration','shared',CAL,'Place PiDog on a flat platform. Go to ~/pidog/examples and run sudo python3 0_calibration.py. In the interactive menu select ruler type 1 for 90 degrees or 2 for 60 degrees. Align each servo using the instructions and the w/s keys; repeat for leg servos and recheck smooth walking. If there is large misalignment, return to servo zeroing rather than forcing a mechanism.'),
('unstable','Walking instability and wobbling','motion','shared',FAQ,'If PiDog walks or stands unstably: verify all servos were installed at zero, check alignment with the 60/90 degree calibration ruler, ensure the battery is charged, and check servo screws. Follow official calibration before attempting higher-speed movement.'),
('gpio_hat','V2 zero button works but control script fails','hardware','v2',FAQ,'If V2 Robot HAT zero button moves servos but Python calibration cannot, the Raspberry Pi to Robot HAT GPIO header connection may be faulty. SunFounder notes soldering issues in the Pi 40-pin header and Robot HAT socket; take clear pictures of both for manufacturer support. Do not improvise electrical repairs.'),
('actions','do_action signatures and permitted actions','motion','shared',PRE,'Pidog.do_action(action_name, step_count=1, speed=50) executes supported preset actions; documented names include sit, stand, forward, backward, turn_left, turn_right, trot, stretch, push_up, shake_head and wag_tail. step_count sets repetition count, speed controls rate.'),
('action_sequence','Wait for actions and cleanup','software','shared',PRE,'The official multi-action example performs a half_sit and push_up sequence then calls my_dog.wait_all_done() before following actions. It also calls wait_head_done() after head movement, stop_and_lie() for safe termination, and my_dog.close() in finally. Use supported PiDog API calls, not invented queue-clearing functions.'),
('install','Official PiDog Python module install dependencies','installation','shared',GIT,'SunFounder’s repository installation guide installs dependencies including robot-hat and vilib before pidog. It provides cloned repository installation instructions and points users to the current official Python setup guide. Review current official instructions for the appropriate OS and version.'),
('install_error','Piper TTS unavailable on 32-bit Raspberry Pi OS','installation','shared',FAQ,'If installation reports No matching distribution found for piper-tts==1.3.0, the SunFounder FAQ associates the issue with running a 32-bit Raspberry Pi OS instead of 64-bit. Its guidance is to use a supported 64-bit Raspberry Pi OS configuration.'),
('demo','Official first wake-up demonstration','software','shared',FAQ,'To run the official first demonstration, navigate to ~/pidog/examples and run sudo python3 1_wake_up.py. The wake-up demo sits and wags its tail. Follow setup and calibration before moving the robot.'),
('sensors','PiDog sensor families and applications','sensors','shared',API,'PiDog lessons cover ultrasonic distance, dual touch detection, IMU readings, sound-direction sensing and RGB light control. The ultrasonic sensor supports obstacle avoidance; touch sensors support contact interactions; sound-direction sensor responds to direction of sound.'),
('ultrasonic','Ultrasonic sensor returns -1','ultrasonic','shared',FAQ,'For no ultrasonic reading or -1, SunFounder recommends cd ~/pidog/test && sudo python3 ultrasonic_test.py. Check that the white wire goes to GPIO17 and yellow wire to GPIO4; if -1 persists after verified wiring, contact support.'),
('touch','Touch sensor LOW signal and troubleshooting','touch','shared',FAQ,'A LOW touch-sensor signal indicates touch. When the touch module does not respond, check cables, orientation and the relevant GPIO readout using a documented test. Do not assume HIGH means touched.'),
('sound','Sound direction module failure','sound','shared',FAQ,'Sound-direction sensor issues: verify its SPI interface and cable orientation, check supply stability and obstructions, reboot and rerun the appropriate manufacturer example. A microphone is a separate audio-input issue.'),
('mic','Microphone detection and input test','audio','shared',FAQ,'Check microphone detection with arecord -l; test audio recording using arecord -D plughw:1,0 -f cd test.wav, selecting the actual input device if different. Adjust input volume using system settings or alsamixer and rule out another process occupying the audio device.'),
('speaker','Robot HAT speaker and I2S setup','audio','shared',FAQ,'For speaker silence, ensure it is enabled with robot_hat enable_speaker (per boot); a PiDog initialization also enables it. Check volume and I2S driver. The FAQ suggests cd ~/robot-hat ; sudo bash i2samp.sh, followed by Raspberry Pi restart when appropriate.'),
('hat','Robot HAT speaker and interfaces','hardware','shared',HAT,'Robot HAT provides an I2S speaker output, MCU PWM/ADC features, GPIO connectors and power interfaces. The board includes a mono speaker and supports I2C, SPI and GPIO modules. Hardware-specific wiring is described in the official Robot HAT documentation.'),
('camera','Camera CSI cable diagnostic','camera','shared',FAQ,'If the PiDog camera fails, first power off the Raspberry Pi before connecting or disconnecting the camera. Confirm the CSI ribbon cable is seated and its locking tab secured. The SunFounder FAQ suggests an OS-appropriate camera test such as libcamera-hello or raspistill.'),
('led','RGB LED board not detected','rgb','shared',FAQ,'For LED board failure, check 3.3V power and I2C wiring, verify that I2C is enabled, then run i2cdetect -y 1. If the device is not detected, verify wiring and restart the Raspberry Pi.'),
('imu','IMU and RGB shared I2C failure','imu','shared',FAQ,'If both IMU and RGB board fail, inspect the shared I2C path. The FAQ lists bus address 0x36 for IMU and 0x74 for RGB. Try sudo i2cdetect -y 1 and official imu_test.py/rgb_strip_test.py scripts, checking the pass-through port using the official connection instructions.'),
('power','Power supply and battery symptoms','power','shared',FAQ,'SunFounder FAQ says PiDog charges via a 5V 3A Type-C supply; the charging indicator is red during charging and turns off when full. If there is no charge indicator, review power and charging before motion tests. Do not attempt battery disassembly.'),
('voice','AI speech options and offline speech recognition','audio','shared',FAQ,'The PiDog documentation describes text-to-speech with Espeak, Pico2Wave, Piper and OpenAI; speech-to-text with offline Vosk; and local LLMs using Ollama. Speech recognition and sound-direction sensing are separate components.'),
('safety','Scope and mechanical/electrical safety','safety','shared',CAL,'Mechanical misalignment can damage servos. If the alignment deviation is large, return to official servo-zeroing and reassembly instructions. Power off the Raspberry Pi before touching camera wiring. RoboGuide does not remotely execute commands or diagnose internal hardware faults.'),
]
rows=[]
for i,title,sub,ver,url,body in data:
 rows.append({'id':i,'title':title,'subsystem':sub,'version':ver,'source_url':url,'source_type':'official_curated_summary','content':body,'authority':1.0,'retrieved_on':'2026-11-10','review_status':'human_review_required','attribution':'Summary of SunFounder docs; verify latest original before operating physical hardware'})
if __name__=='__main__':
 p=Path(__file__).with_name('curated_official_summaries.json')
 p.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(len(rows),p)
