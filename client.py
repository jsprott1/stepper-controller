import requests

# server_ip = "192.168.178.38"
spectro_ip = "132.187.38.38"
clara_ip = "132.187.38.163"
# server_ip = "10.10.0.1" 

#%% stage

stage_url = 'http://' + spectro_ip + ':5000/stage'

def move_to_mm(pos_mm):
    response = requests.post(stage_url, json={"pos_mm": pos_mm})
    print(response.text)

#%% actual stages

def move_to_mm_k_space(pos_mm):
    response = requests.post('http://' + spectro_ip + ':5000/stage', json={"pos_mm": pos_mm})
    print(response.text)

def move_to_mm_r_space(pos_mm):
    response = requests.post('http://' + spectro_ip + ':5006/stage', json={"pos_mm": pos_mm})
    print(response.text)

def move_to_degree_quarter_lambda(pos_degree):
    response = requests.post('http://' + spectro_ip + ':5003/stage', json={"pos_degree": pos_degree})
    print(response.text)

def move_to_degree_half_lambda(pos_degree):
    response = requests.post('http://' + spectro_ip + ':5004/stage', json={"pos_degree": pos_degree})
    print(response.text)

def move_to_degree_quarter_lambda_exc(pos_degree):
    response = requests.post('http://' + spectro_ip + ':5010/stage', json={"pos_degree": pos_degree})
    print(response.text)

def move_to_degree_half_lambda_exc(pos_degree):
    response = requests.post('http://' + spectro_ip + ':5011/stage', json={"pos_degree": pos_degree})
    print(response.text)

def move_to_mm_michelson(pos_mm):
    response = requests.post('http://' + spectro_ip + ':5030/michelson_stage', json={"pos_mm": pos_mm})
    print(response.text)

#%% PBS

pbs_url = 'http://' + clara_ip + ':5001/pbs'

def set_pbs_voltage(u):
    response = requests.post(pbs_url, json={"target_voltage": u})
    # print(response.text)
change_pbs_voltage = set_pbs_voltage

# import numpy as np
# from time import time
# u0 = 0
# u1 = 2
# f = 0.1

# voltages = []
# times = []

# t0 = time()
# while True:
#     t = time() - t0
#     u = u0 + (u1 - u0) * (0.5 + np.sin(2 * np.pi * f * t) / 2)
#     print(u)
#     voltages.append(u)
#     times.append(t)
#     change_pbs_voltage(u)

#%% power meter change params 


pm_settings_url = 'http://' + spectro_ip + ':5002/power_meter_settings'

def change_pm_wavelength(lambda_nm):
    response = requests.post(pm_settings_url, json={"wavelength": lambda_nm})
    print(response.text)

# def get_power():
#     response = requests.get(pm_url, json={"wavelength": lambda_nm})

#%% power meter get power

pm_value_url = 'http://' + spectro_ip + ':5002/get_power'

def get_pm_value():
    response = requests.get(pm_value_url)
    data = response.json()  # Parse the JSON response
    value = data.get("value")
    # print(value)
    return value

def get_pm_value_live():
    response = requests.get(pm_value_url + "_live")
    data = response.json()  # Parse the JSON response
    value = data.get("value")
    # print(value)
    return value

#%% elliptec bus

elliptec_url = 'http://' + spectro_ip + ':5005/elliptec_bus'

def change_filter(position, device):
    print("moving. filter:", position, "stage:",device)
    response = requests.post(elliptec_url, json={device: position})

def set_detection_od(od):
    # determine filter indices
    coarse_dict = {6.0:0, 4.0:1, 2.0:2, 0.0:3}
    fine_dict = {1.5:0, 1.0:1, 0.5:2, 0.0:3}
    od_rounded = round(2 * od) / 2
    if od_rounded != od:
        raise Exception(f"Invalid OD filter for detection: {od}. Use floats from 0.0 to 7.5 in 0.5 steps.")
    od = round(od, 10)
    fine_filter = od % 2
    coarse_filter = od - fine_filter
    # print(coarse_filter, fine_filter)
    # print(coarse_dict[coarse_filter], fine_dict[fine_filter])
    
    # change filters
    change_filter(coarse_dict[coarse_filter], 2)
    change_filter(fine_dict[fine_filter], 1)


def set_excitation_od(od):
    od_dict = {3.0:0, 2.0:1, 1.0:2, 0.0:3}
    if od not in [0.0, 1.0, 2.0, 3.0]:
        raise Exception(f"Invalid OD filter for excitation: {od}. Use float from 0.0 to 3.0 in 1.0 steps.")
    change_filter(od_dict[od], 0)

sdo = set_detection_od
seo = set_excitation_od

#%% beam blocker
blocker_url = 'http://' + spectro_ip + ':6135/blocker'
def set_all_beam_blocks(path_1, path_2, path_3, path_4):
    response = requests.post(blocker_url, json={"0": path_1, "1": path_2, "2": path_3, "3": path_4})
    print(response.text)


def set_michelson_beam_block(path_1, path_2):
    response = requests.post(blocker_url, json={"0": path_1, "1": path_2, "2": 1, "3": 1})
    print(response.text)

def set_mach_zehnder_beam_block(path_1, path_2):
    response = requests.post(blocker_url, json={"0": 1, "1": 1, "2": path_1, "3": path_2})
    print(response.text)
    
#%% temperature controller

ls331_url = 'http://' + clara_ip + ':5033/'

def get_tempeature():
    response = requests.get(ls331_url + "get_temperature")
    data = response.json()  # Parse the JSON response
    value = data.get("value")
    # print(value)
    return value

def get_setpoint():
    response = requests.get(ls331_url + "get_setpoint")
    data = response.json()  # Parse the JSON response
    value = data.get("value")
    # print(value)
    return value

def get_heaterrange():
    response = requests.get(ls331_url + "get_heaterrange")
    data = response.json()  # Parse the JSON response
    value = data.get("value")
    # print(value)
    return value

def change_heaterrange(heatrange):
    allowed = ["off", "Low", "Medium", "High"]
    if heatrange not in allowed:
        raise Exception(f"Wrong value for the range - Values {allowed} are expected.")
    response = requests.post(ls331_url, json={"heaterrange": heatrange})
    print(response.text)
    
def change_setpoint(temp):
    if temp > 300 and temp < 0:
        raise Exception("Temperature out of range (0...300K)")
    response = requests.post(ls331_url, json={"setpoint": temp})
    print(response.text)
    
    
#%% cryostat stepper controller

c_step_url = 'http://' + spectro_ip + ':5001/stepper'
c_post_url = c_step_url + "/post"
c_get_url = c_step_url + "/get"

def get_position():
    response = requests.get(c_get_url)
    data = response.json()
    value = data["position"]
    return value

def get_is_busy():
    response = requests.get(c_get_url)
    data = response.json()
    value = data["busy"]
    return value    

def cryo_move_to_mm_abs(x,y,velocity=None, bc=False):
    response = requests.post(c_post_url, json={"absolute_position":[x,y],"velocity":velocity, "backlash_correction":bc})
    print(response.text)
    
def cryo_move_to_mm_rel(x,y,velocity=None, bc=False):
    response = requests.post(c_post_url, json={"relative_position":[x,y],"velocity":velocity, "backlash_correction":bc})
    print(response.text)
    
def cryo_move_to_um_abs(x,y,velocity=None, bc=False):
    response = requests.post(c_post_url, json={"absolute_position":[x/1000,y/1000],"velocity":velocity, "backlash_correction":bc})
    print(response.text)
    
def cryo_move_to_um_rel(x,y,velocity=None, bc=False):
    response = requests.post(c_post_url, json={"relative_position":[x/1000,y/1000],"velocity":velocity, "backlash_correction":bc})
    print(response.text)
    
def cryo_home(axis):
    response = requests.post(c_post_url, json={"home":True,"axis":axis})
    print(response.text)
    
def cryo_reset():
    response = requests.post(c_post_url, json={"reset":True})
    print(response.text)
    
def calibrate_move(axis, distance, velocity=None):
    response = requests.post(c_post_url, json={"calibrate_backlash":[axis, distance], "velocity":velocity})
    return response.text
    
def update_config(path, value, by_factor = False):
    response = requests.post(c_post_url, json={"config":path, "config_data": value, "by_factor":by_factor})