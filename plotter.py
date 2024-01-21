import csv
import scipy.io
import numpy as np
import matplotlib.pyplot as plt


def load_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)

        iterations = []
        ankle_angle = []
        time = []

        for row in reader:
            if float(row[2]) != 0:
                iterations.append(int(row[0]))
                time.append(float(row[1]))
                ankle_angle.append(float(row[2]))
        
        initial_average_range = 1000
        initial_value = np.mean(ankle_angle[:initial_average_range])
        threshold = 0.08

        for index, value in enumerate(ankle_angle):
            if abs(value - initial_value) > threshold:
                start_index = index
                break

        return iterations[start_index:], time[start_index:], ankle_angle[start_index:]
    
def load_mat(file_path): 
    mat_data = scipy.io.loadmat(file_path)

    JIM_time = mat_data['output'][:,0]
    JIM_angle = np.degrees(mat_data['output'][:,1])
    # torque = mat_data['output'][:,2]

    return JIM_time, JIM_angle

#Load Files
file_path_encoder = r"I:\My Drive\Neurobionics\ExoBoot\Data\20240118-171052_encoder_test_data_R.csv"
file_path_JIM = r"I:\My Drive\Neurobionics\ExoBoot\Data\JIM\encoderchecktest2.mat"

encoder_i, encoder_time, encoder_angle = load_csv(file_path_encoder)
JIM_time, JIM_angle = load_mat(file_path_JIM)

print("Encoder Starting Time:{:.2f} s".format(encoder_time[0]))
print("First Ankle Angle:{:.2f} deg".format(encoder_angle[0]))

#Plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

# First subplot
ax1.scatter(encoder_time, encoder_angle, label='Encoder Angle', color='blue', s=5)
ax1.set_xlabel('Time')
ax1.set_ylabel('Ankle Angle')
ax1.grid(True)
ax1.legend()
# Second subplot
ax2.scatter(JIM_time, JIM_angle, label='JIM Angle', color='red',s=5)
ax2.set_xlabel('Time')
ax2.set_ylabel('JIM Angle')
ax2.grid(True)
ax2.legend()

plt.show()