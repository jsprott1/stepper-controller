import time
import numpy as np
import json
from flask import Flask, request, abort
from stage_firmware import Stage
from autofocus import focus

class CryoStepperMicroservice:
    def __init__(self):
        self.conf_fname = "./config.json"
        self.init_config()
        #shared data updated by the api
        self.flask_app = Flask(__name__)
        self.filter_ip = bool(int(self.config["stepper_controller_api"]["restrict_network_partner"]))
        self.init_controller()
        
        @self.flask_app.route(self.config["stepper_controller_api"]["route"] + "/post", methods=['POST'])
        def flask_receive_data():
            new_data = request.get_json()
            addr = request.remote_addr
            if self.filter_ip and addr != self.config["stepper_controller_api"]["allowed_network_partner"]:
                abort(403)
            elif "reset" in new_data and new_data["reset"]:
                self.close()
                self.init_config()
                self.init_controller(home=False)
                return "reset stepper motors"
            elif "config" in new_data:
                self.update_config(new_data["config"], new_data["config_data"], new_data["by_factor"])
            elif "focus" in new_data:
                return f"best focus value {focus(camera, self.stepper_controller, 100, 1/2, 3, (1000, 1000))}"
            elif self.is_busy:
                abort(409, description="device busy")
            
            # device specific stuff
            if "home" in new_data and new_data["home"]:
                self.is_busy = True
                self.stepper_controller.home(new_data["axis"])
                self.is_busy = False
                return "homed " + new_data["axis"] + " axis"
            elif "absolute_position" in new_data:
                self.is_busy = True
                target_position = np.array(new_data["absolute_position"])
                delta = target_position - self.stepper_controller.get_position()
            elif "relative_position" in new_data:
                self.is_busy = True
                delta = np.array(new_data["relative_position"])
                target_position = delta + self.stepper_controller.get_position()
            elif "calibrate_backlash" in new_data:
                return self.stepper_controller.calibrate_backlash(new_data["calibrate_backlash"][0], new_data["calibrate_backlash"][1], new_data["velocity"])
            else:
                abort(400)
                
            if "backlash_correction" in new_data and new_data["backlash_correction"]:
                b_inds = np.full_like(delta, 0)
                for i, d in enumerate(delta):
                    if d > 0:
                        b_inds[i] = 1
                self.stepper_controller.move_to_mm_vec(target_position + 0.1*delta*b_inds, velocity=new_data["velocity"])
            self.stepper_controller.move_to_mm_vec(target_position, velocity=new_data["velocity"])
            self.is_busy = False
            return "moved to " + str(self.stepper_controller.get_position())
                
            
                
        @self.flask_app.route(self.config["stepper_controller_api"]["route"] + "/get", methods=['GET'])
        def flask_request_data():
            return {"position": self.stepper_controller.get_position().tolist(), "busy": self.is_busy}
        
    def run(self):
        self.flask_app.run(host=self.config["stepper_controller_api"]["flask_listen_ip"], port=self.config["stepper_controller_api"]["server_port"])
        
    def init_config(self):
        with open(self.conf_fname, 'r') as file:
            self.config = json.load(file)
            
    def update_config(self, path, value, by_factor):
        element = self.config
        for ind in path[:-1]:
            element = element[ind]
        if by_factor:
            element[path[-1]] *= value
        else:
            element[path[-1]] = value
        with open(self.conf_fname, 'w', encoding='utf-8') as file:
            json.dump(self.config, file, ensure_ascii=False, indent=4)
        
            
    def init_controller(self, home=True):
        self.is_busy = False
        self.stepper_controller = Stage(self.config["stepper_controller"])
        if home:
            for axis in self.config["stepper_controller"]["axes"]:
                self.stepper_controller.home(axis)
            
    def close(self):
        self.stepper_controller.close()
            

