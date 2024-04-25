import csv
import os
import scipy.io
import pandas as pd
import processor as proc
import numpy as np
import matplotlib.pyplot as plt
plt.rc('savefig', directory='ExoBoot\\plots')


def load_encoder_csv(file_path, adjust = False):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)

        #iterations = []
        ankle_angle = []
        time = []

        for row in reader:
            if float(row[2]) != 0 and float(row[2]) <= 1000:
                #iterations.append(int(row[0]))
                time.append(float(row[1]))
                ankle_angle.append(float(row[2]))

        if adjust == True:
            # Adjusting time and angle
            adjusted_time, raw_angles = proc.adjusted_data(time, ankle_angle, 1000, 0.1)
            initial_angle = raw_angles[0]
            adjusted_angles = [-(angle - initial_angle) for angle in raw_angles]

            # Trim the constant data points at the end
            end_value = np.mean(adjusted_angles[-1000:])
            end_index = next((len(adjusted_angles) - i for i, angle in enumerate(reversed(adjusted_angles), 1) if abs(angle - end_value) > 0.5), None) # Threshold is larger
            print(f"initial angle = {initial_angle}")
            return adjusted_time[:end_index], adjusted_angles[:end_index]
        else:
            return time, ankle_angle


def load_mat(file_path, calibration_path=None, adjust=False, lpf=False, cutoff=8, fs=100, order=5):
    mat_data = scipy.io.loadmat(file_path)
    JIM_time = mat_data['output'][:,0]
    JIM_angle = - np.degrees(mat_data['output'][:,1])   # Fix JIM angle dcdata
    JIM_torque = - mat_data['output'][:,2]  # Fix JIM torque data

    if calibration_path:
        calibration_data = scipy.io.loadmat(calibration_path)
        calibration_torque = - calibration_data['output'][:,2]  
        if len(calibration_torque) == len(JIM_torque):
            JIM_torque -= calibration_torque

    if lpf:
        JIM_torque = proc.butter_lowpass_filter(JIM_torque, cutoff, fs, order)

    if adjust:
        adjusted_time, adjusted_angle = proc.adjusted_data(JIM_time, JIM_angle, 100, 0.05)
        return adjusted_time, adjusted_angle
    else:
        return JIM_time, JIM_angle, JIM_torque


def load_cam():
    all_time, all_angle, all_torque = [], [], []

    for i in range(1, 6):
        file_index = f"{i:03d}"

        file_path_JIM_cal = f"ExoBoot\\cam_torque_angle\\CAL_long_slowsinewithpad{file_index}.mat"
        file_path_JIM = f"ExoBoot\\cam_torque_angle\\EXO_long_slowsinewithpad{file_index}.mat"

        JIM_time, JIM_angle, JIM_torque = load_mat(file_path_JIM, file_path_JIM_cal, False, True)

        # plt.scatter(JIM_angle, JIM_torque, label=f'Torque_cam_{i}', s=1)
        all_time.extend(JIM_time)
        all_angle.extend(JIM_angle)
        all_torque.extend(JIM_torque)

    all_angle = np.array(all_angle)
    all_torque = np.array(all_torque)
    all_time = np.array(all_time)

    file_path_csv = "ExoBoot\\cam_torque_angle\\cam_torque_data.csv"

    if not os.path.exists(file_path_csv):
        os.makedirs(os.path.dirname(file_path_csv), exist_ok=True)
        data = pd.DataFrame({'time': all_time, 'angle': all_angle, 'torque': all_torque})
        data.to_csv(file_path_csv, index=False)
    else:
        print(f"The file {file_path_csv} already exists.")

    return all_time, all_angle, all_torque
    

def plot_angle_data(encoder_time, encoder_angle, JIM_time = None, JIM_angle = None):
    plt.figure(figsize=(8, 6))
    if JIM_time is not None and JIM_angle is not None:
        plt.scatter(JIM_time, JIM_angle, label='JIM Angle', color='red', s=3)
    plt.scatter(encoder_time, encoder_angle, label='Encoder Angle', color='blue', s=3)
    plt.xlabel('Time')
    plt.ylabel('Ankle Angle')
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_cam_data(fit = None):
    all_angle, all_torque = load_cam()

    plt.figure(figsize=(10, 8))
    plt.scatter(all_angle, all_torque, label=f'Torque_cam', s=1)

    if fit is not None:
        if fit == 1:
            m, b = np.polyfit(all_angle, all_torque, 1)
            all_torque_fit = m * all_angle + b
            plt.plot(all_angle, all_torque_fit, label=f'1st Order Fit: m={m:.3f}, b={b:.3f}', color='red')
            print(f'y = {m:.3f}x + {b:.3f}')
        
        elif fit == 2:
            a, b, c = np.polyfit(all_angle, all_torque, 2)
            all_torque_fit = a * all_angle**2 + b * all_angle + c
            plt.plot(all_angle, all_torque_fit, label=f'2nd Order Fit: a={a:.3f}, b={b:.3f}, c={c:.3f}', color='red')
            print(f'y = {a:.3f}x^2 + {b:.3f}x + {c:.3f}')

        elif fit == 3:
            a, b, c, d = np.polyfit(all_angle, all_torque, 3)
            all_torque_fit = a * all_angle**3 + b * all_angle**2 + c * all_angle + d
            plt.plot(all_angle, all_torque_fit, label=f'3rd Order Fit: a={a:.3f}, b={b:.3f}, c={c:.3f}, d={d:.3f}', color='red')
            print(f'y = {a:.3f}x^3 + {b:.3f}x^2 + {c:.3f}x + {d:.3f}')

        proc.calculate_fit_quality(all_torque, all_torque_fit)

    plt.xlabel('Angle [deg]')
    plt.ylabel('Torque [N/m]')
    plt.grid(True)
    plt.legend()
    plt.show()


def plot_piecewise_fit():
    file_path_csv = "ExoBoot\\cam_torque_angle\\cam_torque_data.csv"
    data = pd.read_csv(file_path_csv)
    
    x_data = data['Angle'].values
    y_data = data['Torque'].values
    best_fit_func, best_params_logistic, best_params_poly, best_breakpoint = proc.piecewise_fit(x_data, y_data)  

    proc.calculate_fit_quality(y_data, best_fit_func(x_data))
    proc.print_piecewise_equations(best_params_logistic, best_params_poly, best_breakpoint)

    plt.figure(figsize=(10, 8))
    plt.scatter(x_data, y_data, label='Cam_Torque', s=1)
    plt.plot(x_data, best_fit_func(x_data), label='Best Piecewise Fit', color='red')
    plt.axvline(x=best_breakpoint, color='green', linestyle='--', label='Breakpoint')
    plt.xlabel('Angle [deg]')
    plt.ylabel('Torque [Nm]')
    plt.grid(True)
    plt.legend()
    plt.show()


def load_JIM_controller_avg(dir):
    EXO_dataframes = []
    csv_dataframes = []
    EXO_files = []
    csv_files = []
    CAL_file = None
    
    # Find files
    files = os.listdir(dir)
    for file in files:
        if "CAL.mat" in file:
            CAL_file = file
        elif "EXO_" in file and file.endswith('.mat'):
            EXO_files.append(file)
        elif "EXO_" in file and file.endswith('.csv'):
            csv_files.append(file)
    # Check calibration file
    if not CAL_file:
        raise FileNotFoundError("No CAL file in the directory.")
    
    # Combine JIM data
    first_time_vector = None
    for EXO_file in EXO_files:
        JIM_time, JIM_angle, JIM_torque = load_mat(os.path.join(dir, EXO_file), os.path.join(dir, CAL_file), adjust=False, lpf=True, cutoff=7, fs=227)
        df = pd.DataFrame({'Time': pd.to_timedelta(JIM_time, unit='s'),
                           'Angle': JIM_angle,
                           'Torque': JIM_torque}).set_index('Time')
        df_resampled = df.resample('0.004S').interpolate()
        EXO_dataframes.append(df_resampled)

    # Combine controller data
    for csv_file in csv_files:
        controller_data = pd.read_csv(os.path.join(dir, csv_file))

        controller_data['time'] = pd.to_datetime(controller_data['time'], unit='s')
        controller_data.set_index('time', inplace=True)

        controller_data_resampled = controller_data.resample('0.004S').mean().interpolate()

        _, _, start_index = proc.adjusted_data(controller_data_resampled.index, controller_data_resampled["desire_torque"], 1000, 2)    # Adjust the starting point
        df = pd.DataFrame({'Time': controller_data_resampled.index[start_index:]-controller_data_resampled.index[start_index],
                           'Desire Torque': controller_data_resampled["desire_torque"][start_index:],
                           'Coommanded Torque': controller_data_resampled["commanded_torque"][start_index:],
                           'Passive Torque': controller_data_resampled["passive_torque"][start_index:]}).set_index('Time')
        csv_dataframes.append(df)

    # Concatenate dataframes and calculate JIM data average
    EXO_combined_df = pd.concat(EXO_dataframes, axis=1)
    EXO_avg_df = pd.DataFrame({'Angle': EXO_combined_df.filter(like='Angle').mean(axis=1),
                               'Torque': EXO_combined_df.filter(like='Torque').mean(axis=1)}).reset_index()
    EXO_avg_df['Time'] = (EXO_avg_df['Time'] - EXO_avg_df['Time'][0]) / pd.Timedelta('1s')  # Set the time back to float

    # Concatenate dataframes and calculate controller data average
    csv_combined_df = pd.concat(csv_dataframes, axis=1)
    csv_avg_df = pd.DataFrame({'Desire Torque': csv_combined_df.filter(like='Desire Torque').mean(axis=1),
                               'Coommanded Torque': csv_combined_df.filter(like='Coommanded Torque').mean(axis=1),
                               'Passive Torque': csv_combined_df.filter(like='Passive Torque').mean(axis=1)}).reset_index()
    csv_avg_df['Time'] = (csv_avg_df['Time'] - csv_avg_df['Time'][0]) / pd.Timedelta('1s')   # Set the time back to float

    return EXO_avg_df, csv_avg_df


def plot_JIM_vs_controller(EXO_data, csv_data, PI=False):
    if PI == False:
        plt.figure(figsize=(8, 6), dpi=125)

        plt.scatter(EXO_data['Time'], EXO_data['Torque'], label='JIM torque', s=1)
        plt.scatter(csv_data['Time'], csv_data['Desire Torque'], label='controller torque', color='red', s=1)
    else:
        plt.figure(figsize=(8, 6), dpi=125)

        plt.scatter(csv_data['Time'], csv_data['Desire Torque'], label='desire torque', s=1)
        plt.scatter(csv_data['Time'], csv_data['Passive Torque'], label='passive torque', s=1)
        plt.scatter(csv_data['Time'], csv_data['Coommanded Torque'], label='commanded torque', s=1)

    plt.xlim(0, 20)
    # plt.ylim(-30, 5)
    plt.xlabel('Time (s)')
    plt.ylabel('Torque (Nm)')
    plt.legend()
    plt.grid(True)
    plt.show()


# dir_path = f"I:\\My Drive\\Locomotor\\ExoBoot\\data\\traj_neg_torque"
# dir_path_PEA = f"I:\\My Drive\\Locomotor\\ExoBoot\\data\\traj_neg_torque_PEA"
dir_path = f"/Users/yitengma/Library/CloudStorage/GoogleDrive-yitengma@umich.edu/My Drive/Locomotor/ExoBoot/data/traj_neg_torque"
dir_path_PEA = f"/Users/yitengma/Library/CloudStorage/GoogleDrive-yitengma@umich.edu/My Drive/Locomotor/ExoBoot/data/traj_neg_torque_PEA"
JIM_data_avg, controller_data_avg = load_JIM_controller_avg(dir_path)
JIM_data_avg_PEA, controller_data_avg_PEA = load_JIM_controller_avg(dir_path_PEA)

plt.figure(figsize=(8, 6), dpi=125)

plt.scatter(JIM_data_avg['Time'], JIM_data_avg['Torque'], label='JIM torque (no PEA)', s=1)
plt.scatter(JIM_data_avg_PEA['Time'], JIM_data_avg_PEA['Torque'], label='JIM torque', color='green', s=1)
plt.scatter(controller_data_avg['Time'], controller_data_avg['Desire Torque'], label='controller torque', color='red', s=1)

plt.xlim(0, 20)
# plt.ylim(-30, 5)
plt.xlabel('Time (s)')
plt.ylabel('Torque (Nm)')
plt.legend()
plt.grid(True)
plt.show()

# plot_JIM_vs_controller(JIM_data_avg, controller_data_avg, PI=True)