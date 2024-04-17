import json
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import butter, filtfilt
from scipy.optimize import curve_fit, minimize
from sklearn.metrics import r2_score, mean_squared_error


def adjusted_data(x, y, initial_average_range, threshold):
    initial_value = np.mean(y[:initial_average_range])
    start_index = next((i for i, j in enumerate(y) if abs(j - initial_value) > threshold), None)

    adjusted_time = [t - x[start_index] for t in x[start_index:]]
    adjusted_angle = y[start_index:]
    return adjusted_time, adjusted_angle, start_index


def fft(time, data):
    fs = 1 / np.mean(np.diff(time))

    n = len(data)
    data_fft = np.fft.fft(data)
    freqs = np.fft.fftfreq(n, 1/fs)

    return data_fft, freqs
    # plt.figure()
    # plt.plot(freqs[:n // 2], np.abs(data_fft)[:n // 2] * 1 / n)
    # plt.title('FFT')
    # plt.xlabel('Frequency [Hz]')
    # plt.ylabel('Amplitude')
    # plt.show()


def butter_lowpass_filter(data, cutoff, fs, order):
    nyq = 0.5 * fs  # Nyquist Frequency
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y


def logistic_function(x, L, k, x0):
    z = -k * (x - x0)
    z = np.clip(z, -100, 100)
    return L / (1 + np.exp(z))
def polynomial_function(x, a, b, c):
    return a * x**2 + b * x + c
def piecewise_function(x, logistic_params, poly_params, breakpoint):
    return np.piecewise(x, [x > breakpoint], 
                        [lambda x: logistic_function(x, *logistic_params),
                         lambda x: polynomial_function(x, *poly_params)])


def calculate_fit_quality(y, y_fit):
    r2 = r2_score(y, y_fit)
    rmse = np.sqrt(mean_squared_error(y, y_fit))

    print(f"Fit Quality: R² = {r2:.3f}, RMSE = {rmse:.3f}")


def piecewise_fit(x_data, y_data):
    def objective(params):
        L, k, x0, a, b, c, breakpoint = params
        
        mask = x_data < breakpoint
        x_data_1, y_data_1 = x_data[mask], y_data[mask]
        x_data_2, y_data_2 = x_data[~mask], y_data[~mask]
        
        residuals_1 = logistic_function(x_data_1, L, k, x0) - y_data_1
        residuals_2 = polynomial_function(x_data_2, a, b, c) - y_data_2
        
        ssr = np.sum(residuals_1**2) + np.sum(residuals_2**2)
        continuity_penalty = (logistic_function(breakpoint, L, k, x0) - polynomial_function(breakpoint, a, b, c))**2
        return ssr + 1000 * continuity_penalty

    initial_params = [1, 1, np.median(x_data), 1, 1, 1, np.median(x_data)]  # L, k, x0, a, b, c, breakpoint
    bounds = [(-np.inf, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), 
              (-np.inf, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), 
              (min(x_data), max(x_data))]
    result = minimize(objective, initial_params, method='L-BFGS-B', bounds=bounds)

    if result.success:
        fit_logistic_params = result.x[:3]
        fit_poly_params = result.x[3:6]
        fit_breakpoint = result.x[6]
        fit_function = (lambda x: piecewise_function(x, fit_logistic_params, fit_poly_params, fit_breakpoint))
        return fit_function, fit_logistic_params, fit_poly_params, fit_breakpoint
    else:
        print("Optimization failed:", result.message)
        return None


def print_piecewise_equations(logistic_params, poly_params, breakpoint):
    L, k, x0 = logistic_params
    a, b, c = poly_params

    logistic_eq = f"Logistic Equation: y = {L:.3f} / (1 + exp(-{k:.3f} * (x - {x0:.3f})))"
    polynomial_eq = f"Polynomial Equation: y = {a:.3f}x^2 + {b:.3f}x + {c:.3f}"

    print(logistic_eq)
    print(polynomial_eq)
    print(f"Breakpoint: x = {breakpoint:.3f}")  


def get_passive_torque(angle, angular_speed, speed_threshold):
    angle = np.asarray(angle, dtype=float)

    filename = f'/home/pi/ExoBoot/cam_torque_angle/piecewise_fit_params.json'
    # filename = f'I:\My Drive\Locomotor\ExoBoot\cam_torque_angle\piecewise_fit_params.json'
    with open(filename, 'r') as file:
        fit_results = json.load(file)

    logistic_params = (fit_results['L'], fit_results['k'], fit_results['x0'])
    poly_params = (fit_results['a'], fit_results['b'], fit_results['c'])
    breakpoint = fit_results['breakpoint']

    fit_function = (lambda x: piecewise_function(x, logistic_params, poly_params, breakpoint))

    angle = float(max(min(angle, 25), -18))
    passive_torque = fit_function(angle)

    if abs(angular_speed) > speed_threshold:
        if angular_speed > 0:
            passive_torque += -0.5  # Increase passive torque by 0.5 for plantar
        elif angular_speed < 0:
            passive_torque += 0.5  # Decrease passive torque by 0.5 for dorsi

    return passive_torque


def read_traj_data(file_path, num_rows, freq):
    data = pd.read_csv(file_path)
    start_time = time.time()
    period = 1 / freq

    if num_rows is None:
        num_rows = len(data)
        
    for i in range(num_rows):
        ankle_angle = data['Ankle Angle'][i]
        controller_torque = data['Controller Torque'][i]
        yield ankle_angle, controller_torque
            
        elapsed_time = time.time() - start_time
        sleep_time = period - elapsed_time % period
        if sleep_time > 0:
            time.sleep(sleep_time)

    total_time = time.time() - start_time
    print(f"Total time to read all data: {total_time:.3f} seconds")
    print(f"Actual frequency: {num_rows/total_time:.3f} Hz")