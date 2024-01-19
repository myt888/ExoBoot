import csv
import matplotlib.pyplot as plt

def load_csv(file_path):
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)

        iterations = []
        ankle_angles = []

        for row in reader:
            iterations.append(int(row[0]))
            ankle_angles.append(float(row[2]))

        return iterations, ankle_angles

file_path = r'I:\My Drive\Neurobionics\ExoBoot\Data\20240118-171052_encoder_test_data_R.csv'
iterations, ankle_angles = load_csv(file_path)

plt.figure(figsize=(10, 6))
plt.scatter(iterations, ankle_angles, label='Ankle Angle', color='blue')
plt.title('Ankle Angle vs Iteration Number (Scatter Plot)')
plt.xlabel('Iteration Number')
plt.ylabel('Ankle Angle')
plt.grid(True)
plt.legend()
plt.show()