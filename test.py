import pandas as pd

traj_data = pd.read_csv(f'I:\\My Drive\\Locomotor\\ExoBoot\\JIM_setup\\traj_data_Katharine.csv')
des_torque = traj_data['commanded_torque'][4799]
print(des_torque)

print(len(traj_data))