import datetime as dt #16384/rotation
import sys
import csv
import os, math, sched
from time import sleep, time, strftime, perf_counter
import numpy as np

thisdir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(thisdir)

import traceback
from flexsea import flexsea as flex
from flexsea import fxUtils as fxu
from flexsea import fxEnums as fxe


def main(writer_Loop_l):

	port_cfg_path = '/home/pi/ExoBoot/ports.yaml'
	ports, baud_rate = fxu.load_ports_from_file(port_cfg_path)

	port_right = ports[0]
	print("port_right:{}".format(port_right))

	try:
		run_time_total = 30 # s

		inProcedure = True # Run Time Control
		input('Do you want to start streaming the exos?')
		
		streamFreq = 1000 # Hz
		data_log = False  # False means no logs will be saved
		debug_logging_level = 6  # 6 is least verbose, 0 is most verbose

		fxs = flex.FlexSEA()
		dev_id_right = fxs.open(port_right, baud_rate, debug_logging_level)
		fxs.start_streaming(dev_id_right, freq=streamFreq, log_en=data_log)
		
		i = 0
		globalStart = time()
		degToCount = 45.5111
		countToDeg = 1/degToCount
		SCALE_FACTOR = 360/16384

		fxs.set_gains(dev_id_right, 40, 400, 0, 0, 0, 128)

		while inProcedure:
			i += 1

			currentTime = time()
			run_time = currentTime - globalStart
			
			actPackStateR = fxs.read_device(dev_id_right)
			sideMultiplierR = 1
	
			act_mot_angleR = sideMultiplierR * -((actPackStateR.mot_ang * countToDeg)) # deg
			act_ank_angleR = sideMultiplierR * (SCALE_FACTOR * actPackStateR.ank_ang) # deg
			
			data_frame_vec = [i, round(run_time,6), act_ank_angleR, act_mot_angleR]

			writer_Loop_l.writerow(data_frame_vec)
			sleep(0.001)

		
	
	except:
		print('EXCEPTION: Stopped')
		print("broke: ")
		print(traceback.format_exc())

	finally:
		fxs.send_motor_command(dev_id_right, fxe.FX_NONE, 0)
		# sleep(0.5)

		fxs.close(dev_id_right)

		print("Average execution frequency: {}".format(float(i)/(currentTime - globalStart))  )
		print("END SCRIPT")


if __name__ == '__main__':
	data_filename = '{0}_encoder_data_R.csv'.format(strftime("%Y%m%d-%H%M%S"))
	file_path = '/home/pi/ExoBoot/data_encoder'
	data_path = os.path.join(file_path, data_filename)

	with open(data_path, "w", newline="\n") as fd_Loop_l:
		writer_Loop_l = csv.writer(fd_Loop_l)
		main(writer_Loop_l)