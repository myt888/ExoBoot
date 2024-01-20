import csv
import scipy.io
import numpy as np
import matplotlib.pyplot as plt

def load_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)

        iterations = []
        ankle_angle = []

        for row in reader:

            iterations.append(int(row[0]))
            ankle_angle.append(float(row[2]))

        return iterations, ankle_angle
    
def load_mat(file_path):
    mat_data = scipy.io.loadmat(file_path)

    JIM_time = mat_data['output'][:,0]
    JIM_angle = np.degrees(mat_data['output'][:,1])
    # torque = mat_data['output'][:,2]

    return JIM_time, JIM_angle

file_path_encoder = r'I:\My Drive\Neurobionics\ExoBoot\Data\20240118-171052_encoder_test_data_R.csv'
encoder_i, encoder_angle = load_csv(file_path_encoder)

file_path_JIM = r"I:\My Drive\Neurobionics\ExoBoot\Data\JIM\encoderchecktest2.mat"
JIM_time, JIM_angle = load_mat(file_path_JIM)

#Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

# First subplot
ax1.scatter(encoder_i, encoder_angle, label='Encoder Angle', color='blue')
ax1.set_xlabel('Iteration')
ax1.set_ylabel('Ankle Angle')
ax1.grid(True)
ax1.legend()

# Second subplot
ax2.scatter(JIM_time, JIM_angle, label='JIM Angle', color='red')
ax2.set_xlabel('Time')
ax2.set_ylabel('JIM Angle')
ax2.grid(True)
ax2.legend()

plt.show()