import sys
import time
import pandas as pd
import processor as proc
import trigger as trigger
sys.path.append(r"I:\My Drive\Locomotor\NeuroLocoMiddleware")
from SoftRealtimeLoop import SoftRealtimeLoop

dt = 1/250
i = 0
line = 0
t0 = time.time()

traj_data = pd.read_csv(f'I:\\My Drive\\Locomotor\\ExoBoot\\JIM_setup\\traj_data_Katharine.csv')

trigger.wait_for_manual_trigger()  # Waiting for trigger

loop = SoftRealtimeLoop(dt = dt, report=True, fade=0.01)
time.sleep(0.5)
        
for t in loop: 
    t_curr = time.time() - t0 
            
    i += 1

    passive_torque = 0

    des_torque = traj_data['commanded_torque'][line]

    encoder_angle = -traj_data['ankle_angle'][line] # Encoder: Plantar -
    current_angle = encoder_angle - 90  # Initial angle set at 90

    if -18 <= current_angle <= 25:
        passive_torque = proc.get_passive_torque(current_angle)
    elif current_angle < -18:
        passive_torque = proc.get_passive_torque(-18)
    elif current_angle > 25:
        passive_torque = proc.get_passive_torque(25)

    command_torque = des_torque - passive_torque
            
    if i >= 50:
        i = 0
        print("des torque = ", des_torque, ", passive_torque = ", passive_torque, ", ankle angle = ", current_angle)
                
    line += 1
print("Controller closed")