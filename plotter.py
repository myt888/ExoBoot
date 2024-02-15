import csv
import os
import scipy.io
import pandas as pd
import processor as proc
import numpy as np
import matplotlib.pyplot as plt

def load_csv(file_path, adjust = False):
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

            return adjusted_time[:end_index], adjusted_angles[:end_index]
        else:
            return time, ankle_angle


def load_mat(file_path, calibration_path=None, adjust=False, lpf=False, cutoff=5, fs=100, order=5):
    mat_data = scipy.io.loadmat(file_path)
    JIM_time = mat_data['output'][:,0]
    JIM_angle = np.degrees(mat_data['output'][:,1])
    JIM_torque = mat_data['output'][:,2]

    if calibration_path:
        calibration_data = scipy.io.loadmat(calibration_path)
        calibration_torque = calibration_data['output'][:,2]
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
    all_angle, all_torque = [], []

    for i in range(1, 6):
        file_index = f"{i:03d}"

        file_path_JIM_cal = f"ExoBoot\\cam_torque_angle\\CAL_long_slowsinewithpad{file_index}.mat"
        file_path_JIM = f"ExoBoot\\cam_torque_angle\\EXO_long_slowsinewithpad{file_index}.mat"

        JIM_time, JIM_angle, JIM_torque = load_mat(file_path_JIM, file_path_JIM_cal, False, True)

        # plt.scatter(JIM_angle, JIM_torque, label=f'Torque_cam_{i}', s=1)
        all_angle.extend(JIM_angle)
        all_torque.extend(JIM_torque)

    all_angle = np.array(all_angle)
    all_torque = np.array(all_torque)

    file_path_csv = "ExoBoot\\cam_torque_angle\\cam_torque_data.csv"
    if not os.path.exists(file_path_csv):
        os.makedirs(os.path.dirname(file_path_csv), exist_ok=True)
        data = pd.DataFrame({'Angle': all_angle, 'Torque': all_torque})
        data.to_csv(file_path_csv, index=False)
    else:
        print(f"The file {file_path_csv} already exists.")


def plot_angle_data(encoder_time, encoder_angle, JIM_time = None, JIM_angle = None):
    plt.figure(figsize=(8, 6))
    plt.scatter(encoder_time, encoder_angle, label='Encoder Angle', color='blue', s=3)

    if JIM_time is not None and JIM_angle is not None:
        plt.scatter(JIM_time, JIM_angle, label='JIM Angle', color='red', s=3)

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

encoder_file = "I:\\My Drive\\Neurobionics\\ExoBoot\\data\\encoder_check_test_5.csv"
encoder_time, encoder_angle = load_csv(encoder_file, False)
if __name__ == '__main__':
    plot_angle_data(encoder_time, encoder_angle)

