import csv
import scipy.io
from scipy.signal import butter, filtfilt
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error


def adjusted_data(time, angle, initial_average_range, threshold):
    initial_value = np.mean(angle[:initial_average_range])
    start_index = next((i for i, angle in enumerate(angle) if abs(angle - initial_value) > threshold), None)

    adjusted_time = [t - time[start_index] for t in time[start_index:]]
    adjusted_angle = angle[start_index:]
    return adjusted_time, adjusted_angle


def fft(time, torque):
    JIM_time = np.array(time)
    JIM_torque = np.array(torque)

    fs = 1 / np.mean(np.diff(JIM_time))

    n = len(JIM_torque)
    torque_fft = np.fft.fft(JIM_torque)
    freqs = np.fft.fftfreq(n, 1/fs)

    plt.figure()
    plt.plot(freqs[:n // 2], np.abs(torque_fft)[:n // 2] * 1 / n)  # 1/n is normalization factor
    plt.title('Magnitude Spectrum')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude')
    plt.show()


def butter_lowpass_filter(data, cutoff, fs, order):
    nyq = 0.5 * fs  # Nyquist Frequency
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y


def calculate_fit_quality(y, y_fit):
    r2 = r2_score(y, y_fit)
    rmse = np.sqrt(mean_squared_error(y, y_fit))

    print(f"Fit Quality: R² = {r2:.3f}, RMSE = {rmse:.3f}")


def load_csv(file_path, adjust = False):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)

        #iterations = []
        ankle_angle = []
        time = []

        for row in reader:
            if float(row[2]) != 0:
                #iterations.append(int(row[0]))
                time.append(float(row[1]))
                ankle_angle.append(float(row[2]))

        if adjust == True:
            # Adjusting time and angle
            adjusted_time, raw_angles = adjusted_data(time, ankle_angle, 1000, 0.1)
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
        calibration_time = calibration_data['output'][:,0]
        calibration_angle = np.degrees(calibration_data['output'][:,1])
        calibration_torque = calibration_data['output'][:,2]
        if len(calibration_torque) == len(JIM_torque):
            JIM_torque -= calibration_torque

    if lpf:
        JIM_torque = butter_lowpass_filter(JIM_torque, cutoff, fs, order)

    if adjust:
        adjusted_time, adjusted_angle = adjusted_data(JIM_time, JIM_angle, 100, 0.05)
        return adjusted_time, adjusted_angle, JIM_torque
    else:
        return JIM_time, JIM_angle, JIM_torque


def load_cam():
    for i in range(1, 6):
        all_angle, all_torque = [], []
        file_index = f"{i:03d}"  # Formats the index as 3 digits with leading zeros

        file_path_JIM_cal = f"I:\\My Drive\\Neurobionics\\ExoBoot\\cam_torque_angle\\CAL_long_slowsinewithpad{file_index}.mat"
        file_path_JIM = f"I:\\My Drive\\Neurobionics\\ExoBoot\\cam_torque_angle\\EXO_long_slowsinewithpad{file_index}.mat"

        JIM_time, JIM_angle, JIM_torque = load_mat(file_path_JIM, file_path_JIM_cal, False, True)

        # plt.scatter(JIM_angle, JIM_torque, label=f'Torque_cam_{i}', s=1)

        all_angle.extend(JIM_angle)
        all_torque.extend(JIM_torque)

    all_angle = np.array(all_angle)
    return all_angle, all_torque

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

def plot_torque_data(angle_1, torque_1, angle_2 = None, torque_2 = None):
    plt.figure(figsize=(8, 6))
    plt.scatter(angle_1, torque_1, label='Torque_cam', color='Black', s=1)
    if angle_2 is not None and torque_2 is not None:
        plt.scatter(angle_2, torque_2, label='Torque_cam_filtered', color='Red', s=1)
    plt.xlabel('Angle')
    plt.ylabel('Torque')
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

        calculate_fit_quality(all_torque, all_torque_fit)

    plt.xlabel('Angle [deg]')
    plt.ylabel('Torque [N/m]')
    plt.grid(True)
    plt.legend()
    plt.show()




#Load Files
file_path_encoder = r"I:\My Drive\Neurobionics\ExoBoot\data\encoder_check_test_1.csv"
file_path_JIM_cal = r"I:\My Drive\Neurobionics\ExoBoot\cam_torque_angle\CAL_long_slowsinewithpad001.mat"
file_path_JIM = r"I:\My Drive\Neurobionics\ExoBoot\cam_torque_angle\EXO_long_slowsinewithpad001.mat"

JIM_time, JIM_angle, JIM_torque = load_mat(file_path_JIM, file_path_JIM_cal, False, False)
JIM_time_lpf, JIM_angle_lpf, JIM_torque_lpf = load_mat(file_path_JIM, file_path_JIM_cal, False, True)

# plot_torque_data(JIM_angle, JIM_torque, JIM_angle_lpf, JIM_torque_lpf)
plot_cam_data(1)