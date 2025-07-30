import time
# import numpy as np
import json
from flask import Flask, request
from stage_firmware import Stage

class CryoStepperMicroservice:
    def __init__(self):
        self.conf_fname = "./config.json"
        self.init_config()
        #shared data updated by the api
        self.flask_app = Flask(__name__)
        self.filter_ip = bool(int(self.config["stepper_controller_api"]["restrict_network_partner"]))
        self.is_busy = False
        self.stepper_controller = Stage(self.config["stepper_controller"])
        for axis in self.config["stepper_controller"]["axes"]:
            self.stepper_controller.home(axis)
        
        @self.flask_app.route(self.config["route"], methods=['POST'])
        def flask_receive_data(self):
            new_data = request.get_json()
            addr = request.remote_addr
            if self.filter_ip and addr != self.config["allowed_network_partner"]:
                abort(403)
            elif self.is_busy:
                abort(409, description="device busy")
            
            # device specific stuff
            if "absolute_position" in new_data:
                self.is_busy = True
                self.stepper_controller.moveTo_mm_vec(new_data["absolute_position"], velocity=new_data["velocity"])
                self.is_busy = False
                return "moved to " + stepper_controller.get_position()
            elif "relative_position" in new_data:
                self.is_busy = True
                self.stepper_controller.moveTo_mm_vec(new_data["relative_position"]+self.stepper_controller.get_position(), velocity=new_data["velocity"])
                self.is_busy = False
                return "moved to " + stepper_controller.get_position()
            elif "home" in new_data and new_data["home"]:
                self.is_busy = True
                self.stepper_controller.home(new_data["axis"])
                self.is_busy = False
                return "homed " + new_data["axis"] + " axis"
            else:
                abort(400)
                
        @self.flask_app.route(self.config["route"], methods=['GET'])
        def flask_request_data(self):
            return {"position": stepper_controller.get_position(), "busy": self.is_busy}
        
    def run(self):
        self.flask_app.run()
        
    def init_config(self):
        with open(self.conf_fname, 'r') as file:
            self.config = json.load(file)
            
    def close(self):
        self.stepper_controller.close()
            
if __name__ == '__main__':
    cryo_microservice = CryoStepperMicroservice()
