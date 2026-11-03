"""Prepare the explicitly requested, electrically unqualified direct trial.
No board access. Preserve the level-adapter design and all production files.
"""
import json
import shutil
from pathlib import Path

project = Path(__file__).resolve().parent
source = project / 'camera_capture_20261103'
target = project / 'camera_direct_trial_20261103'
for directory in ('rtl', 'sim', 'host', 'hardware'):
    (target / directory).mkdir(parents=True, exist_ok=True)
for name in ('rtl/dvp_frame.v', 'rtl/camera_axi.v', 'rtl/camera_io.v',
             'sim/tb_camera.sv', 'sim/tb_full_frame.sv',
             'host/camera_driver.py', 'host/test_driver.py', 'host/ov5640_qvga_candidate.json',
             'hardware/camera_pins.xdc', 'build.tcl', 'run_tools.ps1'):
    shutil.copyfile(source / name, target / name)

def edit(name, old, new):
    path = target / name
    text = path.read_text(encoding='utf-8')
    assert old in text, (name, old)
    path.write_text(text.replace(old, new), encoding='utf-8')

edit('rtl/camera_axi.v', "32'h43414d01", "32'h43414d02")
edit('sim/tb_camera.sv', "32'h43414d01", "32'h43414d02")
edit('host/camera_driver.py', '0x43414d01', '0x43414d02')
edit('host/test_driver.py', '0x43414d01', '0x43414d02')
edit('hardware/camera_pins.xdc', '# PYNQ-Z2 physical header allocation; requires the reviewed voltage adapter.',
     '# Electrically unqualified direct trial only. No level-adapter compatibility claim.')
edit('hardware/camera_pins.xdc', 'PACKAGE_PIN W18 [get_ports cam_scl]', 'PACKAGE_PIN F19 [get_ports cam_scl]')
edit('hardware/camera_pins.xdc', 'PACKAGE_PIN W19 [get_ports cam_sda]', 'PACKAGE_PIN F20 [get_ports cam_sda]')
edit('hardware/camera_pins.xdc', 'PACKAGE_PIN Y16 [get_ports cam_pwdn]', 'PACKAGE_PIN Y18 [get_ports cam_pwdn]')
edit('run_tools.ps1', 'camera_capture_20261103', 'camera_direct_trial_20261103')

edit('build.tcl', 'create_bd_cell -type module -reference camera_io io_0',
     'create_bd_cell -type module -reference camera_io io_0\ncreate_bd_cell -type module -reference camera_control_io control_0')
edit('build.tcl', '''foreach signal {cam_reset_n cam_pwdn bridge_enable} {
    create_bd_port -dir O $signal
    connect_bd_net [get_bd_ports $signal] [get_bd_pins camera_0/$signal]
}''', '''connect_bd_net [get_bd_pins camera_0/cam_reset_n] [get_bd_pins control_0/reset_value]
connect_bd_net [get_bd_pins camera_0/cam_pwdn] [get_bd_pins control_0/pwdn_release]
connect_bd_net [get_bd_pins camera_0/bridge_enable] [get_bd_pins control_0/trial_enable]
create_bd_port -dir O cam_reset_n
connect_bd_net [get_bd_ports cam_reset_n] [get_bd_pins control_0/cam_reset_n]
create_bd_port -dir IO cam_pwdn
connect_bd_net [get_bd_ports cam_pwdn] [get_bd_pins control_0/cam_pwdn]
create_bd_port -dir O bridge_enable
connect_bd_net [get_bd_ports bridge_enable] [get_bd_pins camera_0/bridge_enable]''')

driver = target / 'host/camera_driver.py'
text = driver.read_text(encoding='utf-8')
start = text.index('REQUIRED_REVIEW = (')
end = text.index('\ndef board_temperature():', start)
text = text[:start] + '''REQUIRED_REVIEW = (
    'direct_trial_explicitly_requested', 'power_and_common_ground_checked',
    'wiring_matches_direct_trial_table', 'maintenance_mode_display_stopped',
    'diagnostic_bitstream_hash_checked',
)


def validate_review(review):
    missing = [key for key in REQUIRED_REVIEW if review.get(key) is not True]
    if review.get('electrical_qualification') != 'not_performed_direct_trial':
        missing.append('electrical_qualification must remain explicitly not performed')
    if missing:
        raise RuntimeError('Direct-trial preparation incomplete: ' + ', '.join(missing))

''' + text[end:]
text = text.replace('Camera did not acknowledge SCCB byte', 'Camera did not acknowledge SCCB byte; stop this trial')
text = text.replace('SCCB SDA held low; check adapter and pull-ups', 'SCCB SDA held low; stop and check direct-trial wiring')
text = text.replace('enable adapter, RESETB low, PWDN high', 'enable trial controls, RESETB low, PWDN released to camera pull-up')
text = text.replace('Bounded diagnostic capture library', 'Explicitly requested, electrically unqualified direct-trial capture library')
driver.write_text(text, encoding='utf-8')
edit('host/test_driver.py', "return dict({key: True for key in REQUIRED_REVIEW}, measured_camera_io_volts=2.8)",
     "return dict({key: True for key in REQUIRED_REVIEW}, electrical_qualification='not_performed_direct_trial')")
edit('build.tcl', 'OFFLINE_DIAGNOSTIC_BUILD_PASSED_NOT_DEPLOYED', 'OFFLINE_DIRECT_TRIAL_BUILD_PASSED_NOT_DEPLOYED')
policy = {
    'profile': 'direct_trial_20261103', 'electrical_qualification': 'not_performed_direct_trial',
    'authorization': 'User explicitly requested a direct connection and a single image test, accepting abandonment if unsuccessful',
    'not_a_guaranteed_compatible_connection': True,
    'risk_disclosed': 'Unqualified direct wiring can damage the camera; a failed image is not the only possible outcome',
    'meter_step_skipped_at_user_request': True,
    'board_accessed': False, 'board_programmed': False, 'camera_id_read': False,
    'capture_attempts_limit': 1, 'sensor_probe_attempts_limit': 1,
    'geometry': [320, 240], 'temperature_start_below_c': 50,
    'temperature_abort_c': 52, 'capture_timeout_s': 3,
    'screen_during_diagnostic': 'HDMI temporarily stops because this is a camera-only overlay',
    'restore_production_overlay_after_trial': True,
    'wiring': {'5V':2,'GND':6,'D0':8,'D1':15,'D2':16,'D3':19,'D4':21,'D5':23,'D6':33,'D7':35,
               'PCLK':11,'HS':37,'VS':40,'SCL':24,'SDA':22,'RST':29,'PDN':7},
    'leave_disconnected': ['XCLK','NC1','NC2','physical pin 26 bridge_enable'],
    'state': 'PREPARING_OFFLINE_DO_NOT_POWER_YET',
}
(target / 'trial_policy.json').write_text(json.dumps(policy, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
print('Prepared isolated direct-trial sources. No adapter checks were falsely marked as measured or passed.')
