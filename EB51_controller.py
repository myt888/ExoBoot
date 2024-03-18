
from SoftRealtimeLoop import SoftRealtimeLoop   # Exit upon cntl+C (runs as infinite loop otherwise)
import numpy as np   # Numerical python
import math
import pickle  # Document read/save (record foot sensor file)
import os  # For document read/save (combined with pickle)
import gc   # Memory leak clearance
import time
import sys
import csv

from EB51Man import EB51Man    # Dephy Exoboot Manager
from ActPackMan import _ActPackManStates 
from ActPackMan import NM_PER_AMP
from ActiSenseMan_threadrobust import ActiSenseMan  # Read foot sensor
from AhrsManager import AhrsManager     # IMU manager
from IIR2Filter import IIR2Filter
from MTOES_C import MTOES
from State_ZMQ import ZmqVICONpi

sys.path.append(r"/home/pi/MBLUE/ThermalCharacterization/logic_board_temp_cal/")
from thermal_model import ThermalMotorModel

MAX_TORQUE = 30
ANKLE_LOG_VARS = ["Time", "State", "Global Foot Angle", "Global Shank Angle", "Phi Angle", "Phi Angle Velocity", "Ankle Angle", "Ankle Velocity", "Belt Slack", "GRF", "Controller Torque", "Commanded Torque", "Output Torque", "Motor Current", "Motor Angle", "Position Control Flag", "Vicon Sync Flag", "Current Output Angle", "Desired Output Angle"]
GRF_THRESHOLD = 0.15
TOE_OFF_GRF_THRESHOLD = 0.2
MAX_GRF = 1.5
SLACK_THRESHOLD = -0.8
DEFAULT_SLACK = 0.1

        
class Controller():
    def __init__(self, dev, imuShank, imuFoot, dt):
        self.dt = dt
        self.dev = dev
        self.imuShank = imuShank
        self.imuFoot = imuFoot
        self.fsr = fsr
        self.state = None   # 1=stance, 2=swing, 3=pos control during stance
        self.vicon_synch = ZmqVICONpi(connectport="tcp://192.168.1.140:5555")

        # CSV Writer
        self.cf_name = 'PEA_test_R_{0}.csv'.format(time.strftime("%Y%m%d-%H%M%S"))
        self.cf_path = os.path.join('/home/pi/ExoBoot/data_controller', self.cf_name)
        self.cf = open(self.cf_path, 'w', encoding='UTF8', newline='')
        self.writer = csv.writer(self.cf)

    def __enter__(self):
        self.imuShank.update()
        self.imuFoot.update()
        self.dev.update()

        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.cf.close()
        self.vicon_synch.stop()

        imuFoot.node.setToIdle()
        imuShank.node.setToIdle()
        fsr.stop() 
        
        print("exiting")

    def initialize_fsr(self):
    # Initialize FSR storage file
        fsr_calibration_file='fsr_calibration_file'
        if os.stat(fsr_calibration_file).st_size==0:
            pickle.dump([0.0,0.0,0.0],open(fsr_calibration_file,'wb'))  # Open and save foot sensor calibration file

        #Initialize foot sensor
        print("Foot sensor initialized")

        answer = input("Do you want to recalibrate FSRs, y ? ")
        if answer == 'y': 
            GRF_buffer_size = int(3/self.dt)
            GRF_50_buffer = np.zeros(GRF_buffer_size)
            GRF_0_buffer = np.zeros(GRF_buffer_size)
            GRF_100_buffer = np.zeros(GRF_buffer_size)

            input('50 Stance record ')  # Code continues after "enter"
            count = 0
            for t in SoftRealtimeLoop(dt=self.dt):
                if count >= GRF_buffer_size:
                    break
                else:
                    fsrvalues = self.fsr.read()
                    GRF_50 = (fsrvalues['Hallux'] + fsrvalues['Toes'] + fsrvalues['Met1'] + fsrvalues['Met3'] + fsrvalues['Met5'] + fsrvalues['Arch'] + fsrvalues['HeelMedial'] + fsrvalues['HeelLateral'])
                    GRF_50_buffer[count] = GRF_50
                    count = count + 1
            GRF_50 = sum(GRF_50_buffer)/GRF_buffer_size
            gc.collect()
            print(f"GRF_50 = {GRF_50}")

            input('Swing record')
            count = 0
            for t in SoftRealtimeLoop(dt=self.dt):
                if count >= GRF_buffer_size:
                    break
                else:
                    fsrvalues = self.fsr.read()
                    GRF_0 = (fsrvalues['Hallux'] + fsrvalues['Toes'] + fsrvalues['Met1'] + fsrvalues['Met3'] + fsrvalues['Met5'] + fsrvalues['Arch'] + fsrvalues['HeelMedial'] + fsrvalues['HeelLateral'])
                    GRF_0_buffer[count] = GRF_0
                    count = count + 1
            GRF_0 = max(GRF_0_buffer) 
            gc.collect()
            print(f"GRF_0 = {GRF_0}")

            input('100 Stance record')
            count = 0
            for t in SoftRealtimeLoop(dt=self.dt):
                if count >= GRF_buffer_size:
                    break
                else:
                    fsrvalues = self.fsr.read()
                    GRF_100 = (fsrvalues['Hallux'] + fsrvalues['Toes'] + fsrvalues['Met1'] + fsrvalues['Met3'] + fsrvalues['Met5'] + fsrvalues['Arch'] + fsrvalues['HeelMedial'] + fsrvalues['HeelLateral'])
                    GRF_100_buffer[count] = GRF_100
                    count = count + 1
            GRF_100 = sum(GRF_100_buffer)/GRF_buffer_size
            gc.collect()
            print(f"GRF_100 = {GRF_100}")
            pickle.dump([GRF_0, GRF_50, GRF_100],open(fsr_calibration_file,'wb'))  # Save into calibration file
        else:
            GRF_buffer = pickle.load(open(fsr_calibration_file,'rb'))
            GRF_0, GRF_50, GRF_100 = GRF_buffer[0], GRF_buffer[1], GRF_buffer[2] # Directly use?

        return GRF_0, GRF_50, GRF_100

    def float_input(self, input_phrase):
        response = input(input_phrase)
        try:
            float(response)
            return float(response)
        except ValueError:
            print("Please input a floating point number")
            return self.float_input(input_phrase)

    def get_angle0(self, imu):
        msData = imu.readIMUnode()
        for rotation in msData:
            if 'roll' in rotation: angle0 = rotation['roll']
        try: 
            if angle0 != 0:
                return angle0
        except:
            return self.get_angle0(imu)


    def energy_shaping(self):
        # Thermal model initialization
        thermal_model = ThermalMotorModel(temp_limit_windings=80, soft_border_C_windings=10, temp_limit_case=70, soft_border_C_case=10)
        thermal_model.T_w = self.dev.act_pack.temperature

        # Filter initialization
        FilterTemp = IIR2Filter(3,[2],'lowpass',fs=1.0/self.dt) 
        FilterTorq = IIR2Filter(2,[2],'lowpass',fs=1.0/self.dt) 
        FilterGRF = IIR2Filter(2, [6],'lowpass',fs=1.0/self.dt)
        FilterVel = IIR2Filter(2, [15],'lowpass',fs=1.0/self.dt)
        FilterIMUVel = IIR2Filter(2, [15],'lowpass',fs=1.0/self.dt)
        FilterIMUVel2 = IIR2Filter(2,[6],'lowpass',fs=1.0/self.dt) 
        
        # Write log header
        self.writer.writerow(ANKLE_LOG_VARS)

        # Controller initialization
        controller = MTOES(8)

        hip_a_l = 0.0
        knee_a_l = 0.0
        ankle_a_l = 0.0
        hip_v_l = 0.0
        knee_v_l = 0.0
        ankle_v_l = 0.0
        IMU_l = 0.0
        GRF_l = 0.0

        knee_a_r = 0.0
        knee_v_r = 0.0
        knee_v_r = 0.0
        hip_a_r = 0.0
        hip_v_r = 0.0

        # Sensor initialization
        [GRF_0, GRF_50, GRF_100] = self.initialize_fsr()

        # Control inputs
        subject_mass = self.float_input('Weight: ')
        assist_fraction = self.float_input('Assistance Fraction: ')

        input('Realign Calibration, stand up straight')

        self.dev.realign_calibration()

        imuS0 = self.get_angle0(imuShank)
        imuF0 = self.get_angle0(imuFoot)
        ankle_a_r0 = imuF0 - imuS0 - np.pi

        input('Start Controller')

        self.dev.set_position_gains()
        self.state = 2

        i = 0
        t0 = time.time()
        ankle_a_r_prev = 0.0
        IMU_r_prev = 0.0
        pos_cntl_engaged = 0
        t_since_stance = int(0)
        controller_prev = 0
        loop = SoftRealtimeLoop(dt = self.dt, report=True, fade=0.01)
        time.sleep(0.5)
        for t in loop: 
            i = i + 1
            
            # Update
            self.dev.update()

            msShank = self.imuShank.readIMUnode()
            for rotation in msShank:
                if 'roll' in rotation: global_shank_angle = rotation['roll']
            msFoot = self.imuFoot.readIMUnode()
            for rotation in msFoot:
                if 'roll' in rotation: global_phi_angle = rotation['roll']

            fsrvalues = self.fsr.read()
            GRF_raw = fsrvalues['Hallux'] + fsrvalues['Toes'] + fsrvalues['Met1'] + fsrvalues['Met3'] + fsrvalues['Met5'] + fsrvalues['Arch'] + fsrvalues['HeelMedial'] + fsrvalues['HeelLateral']
            if GRF_raw < GRF_0: GRF_raw = GRF_0
            if GRF_raw <= GRF_50:
                GRF_raw = 0.5/(GRF_50 - GRF_0)*(GRF_raw - GRF_0)
            else:
                GRF_raw = 0.5/(GRF_100 - GRF_50)*(GRF_raw - GRF_50)+0.5
            if GRF_raw < 0.0: GRF_raw = 0.0
            GRF_r = FilterGRF.filter(GRF_raw)

            if GRF_r < 0.0: GRF_r = 0.0
            if GRF_r > MAX_GRF: GRF_r = MAX_GRF

            thermal_model.T_c = FilterTemp.filter(self.dev.act_pack.temperature)

            # Determine stance or swing

            if GRF_r >= GRF_THRESHOLD:
                if (t_since_stance < 20) and (GRF_r < 0.3): 
                    pass
                elif self.state == 2:
                    self.state = 3 # Stance
            elif GRF_r < GRF_THRESHOLD:
                if self.state != 2:
                    self.dev.set_slack(DEFAULT_SLACK)
                    if self.state != 3:
                        self.dev.set_output_torque_newton_meters(0)  
                        self.dev.set_position_gains()
                    self.state = 2 # Swing 

            # Calculate ankle angle 
            ankle_a_r = global_phi_angle - global_shank_angle - np.pi - ankle_a_r0
            ankle_v_r = 1.0/self.dt*(ankle_a_r - ankle_a_r_prev)
            ankle_v_r = FilterVel.filter(ankle_v_r)
            ankle_a_r_prev = ankle_a_r

            IMU_r = imuF0 - global_phi_angle
            IMU_v_r = 1.0/self.dt*(IMU_r - IMU_r_prev)
            IMU_v_r = FilterIMUVel.filter(IMU_v_r) 
            IMU_v_r = FilterIMUVel2.filter(IMU_v_r)
            IMU_r_prev = IMU_r 

            # Get sync status
            sync_flag = self.vicon_synch.update()
            
            if i >= 50:
                # print("GRF_r ", GRF_r, " ankle_a_r ", ankle_a_r, " ankle_v_r ", ankle_v_r, " IMU_r ", IMU_r)
                # print(self.dev.get_slack())
                pass

            belt_slack = self.dev.get_actual_slack() 
            curr_output_angle = self.dev.get_output_angle_radians()
            des_output_angle = self.dev.get_desired_motor_angle_radians(curr_output_angle) 

            if self.state == 1 or self.state == 3:   # Stance
                knee_a_r = global_shank_angle
                ankle_v_r = IMU_v_r 
                state = np.array([ankle_a_r, knee_a_r, hip_a_r, hip_a_l, knee_a_l, ankle_a_l, ankle_v_r, knee_v_r, hip_v_r, hip_v_l, knee_v_l, ankle_v_l, IMU_r, IMU_l])
                controller.update(state, GRF_r, GRF_l)
                controller_torque = controller.generate_torque() 

                # controller_torque = FilterTorq.filter(controller_torque) 

                if controller_torque >= 0:
                    if controller_torque < controller_prev:
                        if controller_torque < 0.25:
                            self.dev.set_slack(0.02)
                        
                    if self.state != 3: 
                        self.dev.set_slack(DEFAULT_SLACK)
                        self.state = 3
                        self.dev.set_output_torque_newton_meters(0)
                        self.dev.set_position_gains()

                    if belt_slack < SLACK_THRESHOLD or pos_cntl_engaged == 1:
                        if pos_cntl_engaged == 0: pos_cntl_engaged = 1
                        curr_output_angle = self.dev.get_output_angle_radians()
                        self.dev.set_output_angle_radians(curr_output_angle, slacked = True)

                elif controller_torque < 0:
                    if self.state == 3:
                        self.dev.set_slack(DEFAULT_SLACK)
                        self.state = 1
                        self.dev.set_current_gains() 
                        pos_cntl_engaged = 0

                    torque = assist_fraction * subject_mass * controller_torque 

                    # Torque tapering
                    torque = torque * 1.0/(1+np.exp(-30*(GRF_r-TOE_OFF_GRF_THRESHOLD)))

                    if abs(torque) > MAX_TORQUE: 
                        sign = np.sign(torque)
                        torque = sign * MAX_TORQUE

                    scale = thermal_model.update_and_get_scale(self.dt, torque/NM_PER_AMP/self.dev.gear_ratio, FOS=1.0)
                    commanded_torque = scale * torque 

                    self.dev.set_output_torque_newton_meters(commanded_torque)  
                
                controller_prev = controller_torque

                if i >= 50:
                    # print("Stance mode")
                    # print("Stance mode", " commanded torque ", commanded_torque)
                    pass

            elif self.state == 2:   # Swing
                # controller_torque = FilterTorq.filter(0)
                controller_torque = 0
                commanded_torque = 0

                if belt_slack < SLACK_THRESHOLD or pos_cntl_engaged == 1:
                    if pos_cntl_engaged == 0: pos_cntl_engaged = 1 
                    curr_output_angle = self.dev.get_output_angle_radians()
                    self.dev.set_output_angle_radians(curr_output_angle, slacked = True) 

                if i >= 50:
                    # print("Swing mode")
                    # print("ankle angle ", ankle_a_r, " global phi angle ", global_phi_angle)
                    pass

            if i >= 50:
                i = 0
                print("state", self.state, " GRF ", GRF_r, " controller torque ", controller_torque, " commanded torque ", commanded_torque, "ankle angle ", ankle_a_r, " position cntrl flag ", pos_cntl_engaged)
                # print("ankle angle ", self.dev.get_output_angle_radians(), " position control flag ", pos_cntl_engaged)
                # print("ankle angle", ankle_a_r, " model motor angle ", self.dev.get_desired_motor_angle_radians(self.dev.get_output_angle_radians()), " actual motor angle ", self.dev.get_motor_angle_radians())
                # print("ankle angle ", ankle_a_r, " phi angle ", IMU_r)


            t_curr = time.time() - t0 
            self.writer.writerow([t_curr, self.state, global_phi_angle, global_shank_angle, IMU_r, IMU_v_r, ankle_a_r, ankle_v_r, belt_slack, GRF_r, controller_torque, commanded_torque, self.dev.get_output_torque_newton_meters(), self.dev.get_current_qaxis_amps(), self.dev.get_motor_angle_radians(), pos_cntl_engaged, sync_flag, curr_output_angle, des_output_angle])

        print("Controller closed")  

if __name__ == '__main__':
    dt = 0.004
    with EB51Man(devttyACMport = '/dev/ttyActPackA', whichAnkle = 'right', updateFreq=1000, csv_file_name = "ankle_log.csv", dt = dt, slack = DEFAULT_SLACK) as dev:
        with AhrsManager(port="/dev/ttyAhrsA", baud = 115200) as imuShank:
            with AhrsManager(port = "/dev/ttyAhrsB", baud = 115200) as imuFoot:
                fsr = ActiSenseMan(fsr_port = "/dev/ttyFSR")
                fsr.start()
                with Controller(dev, imuShank, imuFoot, dt = dt) as controller:
                    controller.energy_shaping()