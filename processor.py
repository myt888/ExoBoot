import numpy as np
from scipy.signal import butter, filtfilt
from scipy.optimize import curve_fit, minimize
from sklearn.metrics import r2_score, mean_squared_error


def adjusted_data(x, y, initial_average_range, threshold):
    initial_value = np.mean(y[:initial_average_range])
    start_index = next((i for i, j in enumerate(y) if abs(j - initial_value) > threshold), None)

    adjusted_time = [t - x[start_index] for t in x[start_index:]]
    adjusted_angle = y[start_index:]
    return adjusted_time, adjusted_angle


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


def calculate_fit_quality(y, y_fit):
    r2 = r2_score(y, y_fit)
    rmse = np.sqrt(mean_squared_error(y, y_fit))

    print(f"Fit Quality: R² = {r2:.3f}, RMSE = {rmse:.3f}")


# def try_piecewise_fit(x_data, y_data, breakpoint):
#     mask = x_data < breakpoint
    
#     x_data_logistic = x_data[mask]
#     y_data_logistic = y_data[mask]

#     x_data_poly = x_data[~mask]
#     y_data_poly = y_data[~mask]

#     popt_logistic, _ = curve_fit(logistic_function, x_data_logistic, y_data_logistic)
#     popt_poly, _ = curve_fit(polynomial_function, x_data_poly, y_data_poly)

#     def piecewise_fit(x):
#         return np.piecewise(x, [x < breakpoint], 
#                             [lambda x: logistic_function(x, *popt_logistic), 
#                              lambda x: polynomial_function(x, *popt_poly)])
    
#     return piecewise_fit, popt_logistic, popt_poly
    
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

    initial_params = [1, 1, np.median(x_data), 1, 1, 1, np.median(x_data)] 
    bounds = [(-np.inf, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), 
              (-np.inf, np.inf), (-np.inf, np.inf), (-np.inf, np.inf), 
              (min(x_data), max(x_data))]
    result = minimize(objective, initial_params, method='L-BFGS-B', bounds=bounds)

    if result.success:
        fit_logistic_params = result.x[:3]  # L, k, x0
        fit_poly_params = result.x[3:6] # a, b, c
        fit_breakpoint = result.x[6]

        def piecewise_function(x):
            return np.piecewise(x, [x < fit_breakpoint], 
                                [lambda x: logistic_function(x, *fit_logistic_params),  # Logistic part
                                 lambda x: polynomial_function(x, *fit_poly_params)])
        
        return piecewise_function, fit_logistic_params, fit_poly_params, fit_breakpoint
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