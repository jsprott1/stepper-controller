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
        self.steps_per_mm = self.config["steps_per_mm"]# In format of {axis:[-,+]}
        self.steps_per_mm.update((x, np.array(y)*self.microsteps) for x, y in self.steps_per_mm.items())
        self.max_velocity = min(self.config["max_velocity"] * self.microsteps, 1000)
        self.max_current = self.config["max_current"]
        self.current_position = np.zeroes(self.axes)
        self.initialize_interface()
        self.initialize_motors()

        
        
    def initialize_interface(self):
        connectionManager = ConnectionManager()
        self.myInterface = connectionManager.connect()
        self.module = TMCM6110(self.myInterface)
        
    def initialize_motors(self):
        self.module.set_global_parameter(self.module.GP0.reverseShaftDirection, 0, 3) # Reverses direction of all motors
        # Preparing parameters
        for i, motor_i in enumerate(self.motors):
            motor = self.module.motors[motor_i]
            motor.drive_settings.run_current = min(self.max_current[i], 152)
            motor.drive_settings.max_current = motor.drive_settings.run_current
            motor.drive_settings.standby_current = 0
            motor.drive_settings.microstep_resolution = self.microStepDict[self.microsteps]
            motor.drive_settings.freewheeling_delay = 1
            motor.max_acceleration = min(5 * self.microsteps, 500)
            motor.max_velocity = self.max_velocity
            motor.linear_ramp.max_acceleration = int(motor.max_acceleration) 
            motor.linear_ramp.max_velocity = int(motor.max_velocity)
            
            motor.min_velocity = self.config["min_velocity"]
            
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
            self.module.motors[motor].actual_position = round(home_pos * self.steps_per_mm[axis][0]) 
            self.current_position[axis_i] = home_pos
            self.initialize_motors()
            if vidx == 0:
                self.move_to_mm(axis,home_pos - 1 * home_dir)
                while not self.module.get_axis_parameter(self.module.motors[motor].AP.PositionReachedFlag,motor):
                    pass
            time.sleep(0.3)
        self.move_to_mm(axis,home_pos)
        print("stage homed!")
        
    
    def move_to(self,axis, position, velocity=None):
        motor = self.motors[self.axes.index(axis)]
        if velocity == None:
            velocity = self.module.motors[motor].max_velocity
        if velocity > self.max_velocity:
            velocity = self.max_velocity
        self.module.move_to(motor,position,velocity)
        
    def move_to_mm(self,axis, position_mm, velocity=None, blocking=True):
        if position_mm < self.axis_bounds[axis][0] or position_mm > self.axis_bounds[axis][1]:
            raise Exception(f"Axis bounds error. position {position_mm}mm is out of the allowed range for axis {axis}.")
        axis_i = self.axes.index(axis)
        delta = position_mm - self.current_position[axis_i]
        delta_steps = round(delta * self.steps_per_mm[axis][delta > 0])
        self.move_to(axis,delta_steps + self.get_motor_position(axis),velocity)
        if blocking:
            while not self.module.get_axis_parameter(self.module.motors[self.motors[axis_i]].AP.PositionReachedFlag,self.motors[axis_i]):
                pass
        self.current_position[axis_i] += delta_steps/self.steps_per_mm[axis][delta > 0]

    def move_to_mm_vec(self, pos_mm_vec, velocity=None, blocking=True):
        self.move_to_mm(self.axes[0], pos_mm_vec[0], velocity, False)
        self.move_to_mm(self.axes[1], pos_mm_vec[1], velocity, False)
        if blocking:
            while not self.positionReachedFlag():
                pass
    
    def positionReachedFlag(self):
        flags = []
        for motor in self.motors:
            flags.append(self.module.get_axis_parameter(self.module.motors[motor].AP.PositionReachedFlag,motor))
        if sum(flags) == len(flags):
            return True
        return False
    
    def get_position(self):
        return np.array(self.current_position)
        
    def get_motor_position(self, axis):
        return self.module.motors[self.motors[self.axes.index(axis)]].actual_position
        
    def close(self):
        self.myInterface.close()
        
    # Returns distance recorded returning to limit after moving $distance away
    def calibrate_backlash(self, axis, distance, velocity=None):
        if velocity == None:
            velocity = 200
        axis_i = self.axes.index(axis)
        motor = self.motors[axis_i]
        home_pos = self.config["home"][axis_i]
        home_dir = self.config["home_direction"][axis_i]
        
        self.home(axis)
        self.move_to_mm(axis, home_pos - distance*home_dir, velocity)
        initial_pos = self.get_position()[axis_i]
        self.module.rotate(motor, velocity*home_dir)
        while not self.module.get_axis_parameter(self.module.motors[motor].AP.LeftEndstop,motor):
            pass
        self.module.rotate(motor, 0)
        final_pos = self.get_position()[axis_i]
        return str(abs(final_pos - initial_pos))
        
        


if __name__ == '__main__':
    
#     #%% test Stage class
      stage = Stage()
      stage.home("y")
      stage.home("x")
      stage.moveTo_mm("x",24,120)
#      stage.moveTo_mm_vec([10,12])
    
