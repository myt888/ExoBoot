from SoftRealtimeLoop import SoftRealtimeLoop   # Exit upon cntl+C (runs as infinite loop otherwise)
import numpy as np   # Numerical pythonimport math
import pickle  # Document read/save (record foot sensor file)
import os  # For document read/save (combined with pickle)
import gc   # Memory leak clearance
import processor as proc
import pandas as pd
import TCP_trigger as trigger
import sys
import csv
import time
sys.path.append(r"/home/pi/MBLUE/ThermalCharacterization/logic_board_temp_cal/")
from EB51Man import EB51Man  # Dephy Exoboot Manager
from ActPackMan import _ActPackManStates 
from StatProfiler import SSProfile
from thermal_model import ThermalMotorModel


MAX_TORQUE = 30
NM_PER_AMP = 0.146

ANKLE_LOG_VARS = ['time', 'desire_torque', 'commanded_torque', 'passive_torque', 'ankle_angle', 'device_current']
traj_data = pd.read_csv(f'/home/pi/ExoBoot/JIM_setup/ankle_test_right_swing_112run1.csv')

class Controller():
    def __init__(self, dev, dt):
        self.dt = dt
        self.dev = dev

        self.cf_name = 'PEA_test_R_{0}.csv'.format(time.strftime("%Y%m%d-%H%M%S"))
        self.cf_path = os.path.join('/home/pi/ExoBoot/data_basic_controller', self.cf_name)
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
        line = 0
        t0 = time.time()
        
        loop = SoftRealtimeLoop(dt = self.dt, report=True, fade=0.01)
        time.sleep(0.5)
        
        for t in loop: 
            t_curr = time.time() - t0 
            
            i += 1
            self.dev.update()   # Update

            passive_torque = 0

            des_torque = traj_data['Commanded Torque'][line]

            # Encoder: Plantar -
            encoder_angle = self.dev.get_output_angle_degrees()
            current_angle = encoder_angle - 90  # Initial angle set at 90

            if -18 <= current_angle <= 25:
                passive_torque = proc.get_passive_torque(current_angle)
            elif current_angle < -18:
                passive_torque = proc.get_passive_torque(-18)

            command_torque = des_torque - passive_torque
            self.dev.set_output_torque_newton_meters(command_torque)

            qaxis_curr = self.dev.get_current_qaxis_amps()
            
            if i >= 50:
                i = 0
                print("des torque = ", des_torque, ", passive_torque = ", passive_torque, ", ankle angle = ", current_angle)

            self.writer.writerow([t_curr, des_torque, command_torque, passive_torque, current_angle, qaxis_curr])
                
            line += 1
        print("Controller closed")


if __name__ == '__main__':
    dt = 1/250
    ip = ''
    port = 12345
    data_path = 'I:\\My Drive\\Locomotor\\ExoBoot\\JIM_setup\\ankle_test_right_swing_112run1.csv'

    with EB51Man(devttyACMport = '/dev/ttyACM0', whichAnkle = 'right', updateFreq=1000, csv_file_name = "ankle_log.csv", dt = dt) as dev:
        with Controller(dev, dt = dt) as controller:
            controller.control()