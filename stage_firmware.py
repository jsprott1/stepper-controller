# import PyTrinamic
from pytrinamic.connections.connection_manager import ConnectionManager 
from pytrinamic.modules import TMCM6110
import time
import numpy as np


class Stage:
    microStepDict = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7, 256: 8}
    
    def __init__(self, config):
        self.config = config
        self.axes = self.config["axes"]
        self.motors = self.config["motors"]
        self.axis_bounds = self.config["limits"]
        self.microsteps = self.config["microsteps"]
        self.stepsPerMm = self.config["steps_per_mm"] * self.microsteps
        self.initialize_interface()
        self.initialize_motors()
        
        
    def initialize_interface(self):
        connectionManager = ConnectionManager()
        self.myInterface = connectionManager.connect()
        self.module = TMCM6110(self.myInterface)
        
    def initialize_motors(self):
        self.module.set_global_parameter(self.module.GP0.reverseShaftDirection, 0, 3) # Reverses direction of all motors
        # Preparing parameters
        for motor_i in self.motors.values():
            motor = self.module.motors[motor_i]
            motor.drive_settings.run_current = 152
            motor.drive_settings.max_current = 175
            motor.drive_settings.standby_current = 0
            motor.drive_settings.microstep_resolution = self.microStepDict[self.microsteps]
            motor.drive_settings.freewheeling_delay = 1
            motor.max_acceleration = min(5 * self.microsteps, 500)
            motor.max_velocity = min(self.config["max_velocity"] * self.microsteps, 1000)
            motor.linear_ramp.max_acceleration = int(motor.max_acceleration) 
            motor.linear_ramp.max_velocity = int(motor.max_velocity)
            
    def home(self,axis):
        axis_i = self.axes.index(axis)
        motor = self.motors[axis_i]
        home_pos = self.config["home"][axis_i]
        home_dir = self.config["home_direction"][axis_i]
        self.close()
        self.initialize_interface()
        for vidx, velocity in enumerate([500,100]):
            initial_pos = self.module.get_axis_parameter(self.module.motors[motor].AP.ActualPosition, motor)
            self.module.rotate(motor, velocity*home_dir)
            while not self.module.get_axis_parameter(self.module.motors[motor].AP.LeftEndstop,motor):
                pass
            self.module.rotate(motor, 0)
            final_pos = self.module.get_axis_parameter(self.module.motors[motor].AP.ActualPosition, motor)
            if vidx == 1 and final_pos == initial_pos :
                print("WARNING: Limit switch may be disconnected")
            self.module.motors[motor].actual_position = home_pos * self.stepsPerMm[axis_i] 
            self.initialize_motors()
            if vidx == 0:
                self.module.move_to(motor,round((home_pos - 1 * home_dir) * self.stepsPerMm[axis_i]))
                while not self.module.get_axis_parameter(self.module.motors[motor].AP.PositionReachedFlag,motor):
                    pass
            time.sleep(0.3)
        self.moveTo_mm(axis,home_pos)
        print("stage homed!")
        
    
    def move_to(self,axis, position, velocity=None):
        self.module.move_to(self.motors[self.axes.index(axis)],position,velocity)
        
    def move_to_mm(self,axis, position_mm, velocity=None, blocking=True):
        if position_mm < self.axis_bounds[axis][0] or position_mm > self.axis_bounds[axis][1]:
            raise Exception(f"Axis bounds error. position {position_mm}mm is out of the allowed range for axis {axis}.")
        axis_i = self.axes.index(axis)
        self.move_to(axis,round(position_mm * self.stepsPerMm[axis_i]),velocity)
        if blocking:
            while not self.module.get_axis_parameter(self.module.motors[self.motors[axis_i]].AP.PositionReachedFlag,self.motors[axis_i]):
                pass

    def moveTo_mm_vec(self, pos_mm_vec, velocity=None, blocking=True):
        self.move_to_mm(self.axes[0], pos_mm_vec[0], velocity, False)
        self.move_to_mm(self.axes[1], pos_mm_vec[1], velocity, False)
        if blocking:
            while not self.positionReachedFlag():
                pass
    
    def positionReachedFlag(self):
        flags = []
        for motor in self.motors.values():
            flags.append(self.module.get_axis_parameter(self.module.motors[motor].AP.PositionReachedFlag,motor))
        if sum(flags) == len(flags):
            return True
        return False
        
    def close(self):
        self.myInterface.close()
        


if __name__ == '__main__':
    
#     #%% test Stage class
      stage = Stage()
      stage.home("y")
      stage.home("x")
      stage.moveTo_mm("x",24,120)
#      stage.moveTo_mm_vec([10,12])
    
