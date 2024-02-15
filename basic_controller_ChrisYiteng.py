from SoftRealtimeLoop import SoftRealtimeLoop   # Exit upon cntl+C (runs as infinite loop otherwise)
import numpy as np   # Numerical python
import json
import math
import pickle  # Document read/save (record foot sensor file)
import os  # For document read/save (combined with pickle)
import gc   # Memory leak clearance
import processor as proc
import sys
import csv
from time import sleep, time, strftime, perf_counter
sys.path.append(r"/home/pi/MBLUE/ThermalCharacterization/logic_board_temp_cal/")
from EB51Man import EB51Man  # Dephy Exoboot Manager
from ActPackMan import _ActPackManStates 
from StatProfiler import SSProfile
from thermal_model import ThermalMotorModel


MAX_TORQUE = 30
NM_PER_AMP = 0.146

ANKLE_LOG_VARS = ['time', 'commanded_torque', 'passive_torque', 'ankle_angle', 'device_current']


def get_passive_torque(angle):
    filename = f'ExoBoot\cam_torque_angle\piecewise_fit_params.json'
    with open(filename, 'r') as file:
        fit_results = json.load(file)

    logistic_params = (fit_results['L'], fit_results['k'], fit_results['x0'])
    poly_params = (fit_results['a'], fit_results['b'], fit_results['c'])
    breakpoint = fit_results['breakpoint']

    passive_torque = - proc.piecewise_function(angle, logistic_params, poly_params, breakpoint) # Negative for dorsiflexion
    return passive_torque


class Controller():
    def __init__(self, dev, dt):
        self.dt = dt
        self.dev = dev

        self.cf_name = '{0}_PEA_test_R.csv'.format(strftime("%Y%m%d-%H%M%S"))
        self.cf_path = os.path.join('/home/pi/ExoBoot/Data', self.cf_name)
        self.cf = open(self.cf_path, 'w', encoding='UTF8', newline='')
        self.writer = csv.writer(self.cf)

    def __enter__(self):
        self.dev.update()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.cf.close()
        print("exiting")

    def control(self):
        # Write log header
        self.writer.writerow(ANKLE_LOG_VARS)

        self.dev.realign_calibration()
        self.dev.set_current_gains() 

        i = 0
        t0 = time.time()
        
        loop = SoftRealtimeLoop(dt = self.dt, report=True, fade=0.01)
        time.sleep(0.5)
        
        for t in loop: 
            i = i + 1
            self.dev.update() # Update

            des_torque = -5
            # JIM: Plantar +
            # Encoder: Dorsi + (Convention)
            current_angle = 92.5 - self.dev.get_output_angle_degrees # Initial angle set at 92.5
            if -25 <= -current_angle <= 18:
                passive_torque = get_passive_torque(-current_angle)
                des_torque =- passive_torque
            elif -current_angle > 18:
                passive_torque = get_passive_torque(18)
                des_torque =- passive_torque
                
            self.dev.set_output_torque_newton_meters(des_torque)

            qaxis_curr = self.dev.get_current_qaxis_amps()
            
            if i >= 50:
                i = 0
                print("des torque = ", des_torque, ", qaxis current = ", qaxis_curr)

            t_curr = time.time() - t0 
            self.writer.writerow([t_curr, des_torque, passive_torque, current_angle, qaxis_curr])    

        print("Controller closed")  

if __name__ == '__main__':
    dt = 1/200
    with EB51Man(devttyACMport = '/dev/ttyACM0', whichAnkle = 'right', updateFreq=1000, csv_file_name = "ankle_log.csv", dt = dt) as dev:
        with Controller(dev, dt = dt) as controller:
            controller.control()