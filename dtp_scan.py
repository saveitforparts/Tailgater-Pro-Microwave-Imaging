#Python program to scan with Dish Tailgater Pro (Hyland version) and output signal strength bitmap
#Version 1.0
#Gabe Emerson / Saveitforparts 2026, Email: gabe@saveitforparts.com

#This should work with any orange board Tailgater with the Hyland firmware
#Green boards with the Lutsen firmware need a different unlock code and different az/el commands

import serial
import time
from PIL import Image
import regex as re
import numpy as np
import subprocess

#generate timestamp
timestr = time.strftime("%Y%m%d-%H%M%S")

#define "dish" as the serial port device to interface with
dish = serial.Serial(
	port='/dev/ttyACM0', #sometimes this is ACM0, ACM1 or USB0
	baudrate = 115200,
	parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	timeout=1)

print ('Serial port connected')
print ('')

print ('Unlocking antenna firmware...')
dish.write(b'help Hyland\r') #the unlock code for SW23193 and similar firmware
reply = dish.read(207).decode().strip()      #read dish response
#print (reply) #optional / debug
if "rewind" in reply:
	print ('Unlock success!')
else:
	print ('Unlock failed! Is this a Tailgater Pro / Hyland model?')
	print ('Antenna response was: '+reply)
	dish.close()
	exit()

#Prompt for scan parameters, with default values and valid range checks
az_start = int(input('Starting Azimuth in degrees (0-360, default 120): ') or 120)

if az_start < 0:
	print('Azimuth out of range, setting to 0')
	az_start=0
if az_start > 360:
	print('Azimuth out of range, setting to 360')
	az_start=360

az_end = int(input('Ending Azimuth in degrees (default 240): ') or 240)
if az_end < 0:
	print('Azimuth out of range, setting to 0')
	az_end=0
if az_end > 360:
	print('Azimuth out of range, setting to 360')
	az_end=360

el_start = int(input('Starting Elevation in degrees (15-65, default 15): ') or 15)
if el_start < 15:
	print('Elevation out of range, setting to 15')
	el_start=15
if el_start > 65:
	print('Elevation out of range, setting to 65')
	el_start=65

el_end = int(input('Ending Elevation in degrees (default 55): ') or 55)
if el_end < 15:
	print('Elevation out of range, setting to 15')
	el_end=15
if el_end > 65:
	print('Elevation out of range, setting to 65')
	el_end=65


#Choose between between azangle/elangle for low res and aznudge/elnudge for high res
resolution = int(input('Resolution (1=low, 2=high, default 1): ') or 1)
if not resolution in (1,2):
	print('Unknown selection, setting to 1 (low)')
	resolution=1 

#Do we want to run a live preview?
preview_mode = int(input('Preview results? (1=on, 0=off, default 1): ') or 1)

np.savetxt("scan-settings-" + timestr +".txt", (az_start,az_end,el_start,el_end,resolution))	

if resolution==1: #standard scan using angles
	az_range = az_end - az_start
	el_range = el_end - el_start

	#Provide runtime estimate (I'm making a rough guess based on prior runs on two different computers)
	time_est = az_range * el_range
	time_output = (time_est+(time_est/6))/60
	time_output = round(time_output, 2)
	if time_output > 60:
		print ('Estimated scan time with your parameters is ', time_output/60, ' hours.')
	else:
		print ('Estimated scan time with your parameters is ', time_output, ' minutes.')
	print ('')
	user_confirm = input('Proceed with scan? (y/n):')
	if user_confirm.lower().startswith("y"):
		print ('Scan in progress...')
	else:
		print ('exiting.')
		exit()

	#create bitmap to preview signal strengths
	sky_image = Image.new('RGB', [az_range+1,el_range+1], 255) 
	data = sky_image.load()

	#create 2D array for raw signal strengths
	sky_data = np.zeros((el_range+1,az_range+1))
	start_time = time.time() #record start time of scan

	print ('Moving dish to starting position...')
	#initialize starting dish position
	#Tailgater pro doesn't need single bytes
	dish.write(b'azangle ')
	angle=str(az_start)
	if (len(angle)==3):
		dish.write(angle[0].encode())
		dish.write(angle[1].encode())
		dish.write(angle[2].encode())
	elif len(angle)==2:
		dish.write(angle[0].encode())
		dish.write(angle[1].encode())
	else: 
	        #single-digit number
	        dish.write(angle.encode())
	dish.write(b'\r')

	time.sleep(10)   #Give motors time to drive dish to scan origin
	dish.flush()
	dish.reset_output_buffer()

	dish.write(b'elangle ')
	angle=str(el_start)
	if (len(angle)==3):
		dish.write(angle[0].encode())
		dish.write(angle[1].encode())
		dish.write(angle[2].encode())
	elif len(angle)==2:
	        dish.write(angle[0].encode())
	        dish.write(angle[1].encode())
	else: 
	        #single-digit number
	        dish.write(angle.encode())
	dish.write(b'\r')
	dish.flush()
	dish.reset_output_buffer()
	dish.reset_input_buffer()
	time.sleep(10)


	if preview_mode == 1:
		np.savetxt(f"raw-data-" + timestr +".txt", sky_data)
		subprocess.Popen(['python3', 'dtp_preview.py', 'raw-data-' + timestr +'.txt']) #call preview script with current data file

		
	direction=0		
	#aiming loop
	#valid elangle range is 15-65 degrees. 
	for elevation in range (el_start,el_end):
		direction=direction+1
		#valid azangle 0-360. Remember dish increments ccw. 
		for azimuth in range (az_start,az_end):
	
			print("Azimuth: ", azimuth, ", Elevation: ", elevation)  #display current position

			#command dish to next azimuth	
			dish.write(b'azangle ')
			#we have to break up 3 and 2 digit numbers into single characters
			angle=str(azimuth)
			if (len(angle)==3):
			        dish.write(angle[0].encode())
			        dish.write(angle[1].encode())
			        dish.write(angle[2].encode())
			elif len(angle)==2:
			        dish.write(angle[0].encode())
			        dish.write(angle[1].encode())
			else: #shouldn't need this for typical range, but might want it later
			        #single-digit number
			        dish.write(angle.encode())
			dish.write(b'\r')
			
			#this seems necessary to avoid SerialException issue? (probably also kludgy)
			while True:
				try:
					dish.reset_input_buffer() #avoid overflow 
				
					#request signal strength
					print('Reading signal strength...') 
					dish.write(b'rfwatch 1\r')
					dish.flush()
					dish.reset_output_buffer()
	                		                					                    
					reply = dish.read(207).decode().strip()      #read dish response
					header, *readings = reply.split('[5D')       #Split into list of signal strengths
					output = readings[0]			     #grab first list element
					output = re.sub(r'\p{C}', '', output)        #remove any control chars
					output = re.sub('[^\d]', '', output).strip() #clean up partial garbage
	
					signal_strength = int(output)                #convert to integer
					time.sleep(0.1)
				except serial.SerialException as e:
					#dish hasn't replied yet
					time.sleep(0.2)
					continue
				else:
					print('')
				break
	
			print('Signal: ', signal_strength)    #display signal strength
	
			#record raw data to array
			sky_data[abs(elevation-el_end),abs(azimuth-az_end)]=signal_strength
			#write to text file
			np.savetxt(f"raw-data-" + timestr +".txt", sky_data)
			
			#create preview bitmap	
			image_x = abs(azimuth-az_end)    #write bitmap the same way the dish is scanning
			image_y = abs(elevation-el_end)   #write bitmap the same way the dish is scanning
			data[image_x,image_y] = (signal_strength % 255,	0, 0)
			#write bitmap to time stamped image file
			sky_image.save('result-' + timestr +'.png')	
		
		
		#Return to starting azimuth for each elevation position
		dish.write(b'azangle ')
		angle=str(az_start)
		if (len(angle)==3):
			dish.write(angle[0].encode())
			dish.write(angle[1].encode())
			dish.write(angle[2].encode())
		elif len(angle)==2:
			dish.write(angle[0].encode())
			dish.write(angle[1].encode())
		else: 
		        #single-digit number
		        dish.write(angle.encode())
		dish.write(b'\r')		
		
		#delay to allow dish to return to starting azimuth, dynamic based on az_range
		wait_time = int((az_range)*0.1)+1 #Dish takes ~0.1sec to rotate 1 degree, plus 1 sec buffer
		time.sleep(wait_time)
		
		#command dish to next elevation
		dish.write(b'elangle ')
		#We have to break up 2 digit numbers into single characters
		angle=str(elevation)
		if len(angle)==2: #will only ever have 1 and 2-digit elevations
		        dish.write(angle[0].encode())
		        dish.write(angle[1].encode())
		else: 
		        #single-digit number
		        dish.write(angle.encode())
		dish.write(b'\r')


elif resolution==2: #high res scan using nudge instead of angle

	#"nudge" is "about 0.2 degrees" azimuth and about 0.33 degrees elevation
	#So for each degree in Az range we have 5 dish positions, and for each degree in El we have 3 positions. 
	az_range = (az_end - az_start)*5
	el_range = (el_end - el_start)*3

	#Provide runtime estimate (I'm making a rough guess based on prior runs on two different computers)
	time_est = az_range * el_range
	time_output = ((time_est+(time_est/6))/60)+((el_range*10)/60) #High-res takes longer, returns to az_start on each elevation
	time_output = round(time_output, 2)
	if time_output > 60:
		print ('Estimated scan time with your parameters is ', time_output/60, ' hours.')
	else:
		print ('Estimated scan time with your parameters is ', time_output, ' minutes.')
	print ('')
	user_confirm = input('Proceed with scan? (y/n):')
	if user_confirm.lower().startswith("y"):
		print ('Scan in progress...')
	else:
		print ('exiting.')
		exit()
		

	#create bitmap to preview signal strengths
	sky_image = Image.new('RGB', [az_range+1,el_range+1], 255) 
	data = sky_image.load()

	#create 2D array for raw signal strengths
	sky_data = np.zeros((el_range+1,az_range+1))

	print ('Moving dish to starting position...')
	#initialize starting dish position
	#for some reason, the dish only receives single char from each write(), so send one at a time
	#(wow much kludge, such ugly)
	dish.write(b'azangle ')
	angle=str(az_start)
	if (len(angle)==3):
		dish.write(angle[0].encode())
		dish.write(angle[1].encode())
		dish.write(angle[2].encode())
	elif len(angle)==2:
		dish.write(angle[0].encode())
		dish.write(angle[1].encode())
	else: 
	        #single-digit number
	        dish.write(angle.encode())
	dish.write(b'\r')

	time.sleep(10)   #Give motors time to drive dish to scan origin
	dish.flush()
	dish.reset_output_buffer()

	dish.write(b'elangle ')
	angle=str(el_start)
	if (len(angle)==3):
		dish.write(angle[0].encode())
		dish.write(angle[1].encode())
		dish.write(angle[2].encode())
	elif len(angle)==2:
	        dish.write(angle[0].encode())
	        dish.write(angle[1].encode())
	else: 
	        #single-digit number
	        dish.write(angle.encode())
	dish.write(b'\r')
	dish.flush()
	dish.reset_output_buffer()
	dish.reset_input_buffer()
	time.sleep(10)
					
	#aiming loop
	#valid elangle range is 15-65 degrees 
	for elevation in range (0,el_range):
		#valid azangle 0-360. Remember dish increments ccw. 
				
		for azimuth in range (0,az_range):
	
			print("X: ", azimuth, ", Y: ", elevation)  #display current position

			#command dish to next azimuth	
			dish.write(b'aznudge ccw\r')
			
			#this seems necessary to avoid SerialException issue? (probably also kludgy)
			while True:
				try:
					dish.reset_input_buffer() #avoid overflow 
				
					#request signal strength 
					dish.write(b'rfwatch 1\r')
	
					dish.flush()
					dish.reset_output_buffer()
	                		                					                    
					reply = dish.read(207).decode().strip()      #read dish response
					header, *readings = reply.split('[5D')       #Split into list of signal strengths
					output = readings[0]			     #grab first list element
					output = re.sub(r'\p{C}', '', output)        #remove any control chars
					output = re.sub('[^\d]', '', output).strip() #clean up partial garbage
	
					signal_strength = int(output)                #convert to integer
	
				except serial.SerialException as e:
					#dish hasn't replied yet
					time.sleep(0.1)
					continue
				else:
					print('')
				break
	
			print('Signal: ', signal_strength)    #display signal strength
	
			#record raw data to array
			sky_data[abs(elevation-el_range),abs(azimuth-az_range)]=signal_strength
			#write to text file
			np.savetxt(f"raw-data-" + timestr +".txt", sky_data)
			
			#create preview bitmap	
			image_x = abs(azimuth-az_range)    #write bitmap the same way the dish is scanning
			image_y = abs(elevation-el_range)   #write bitmap the same way the dish is scanning
			data[image_x,image_y] = (signal_strength % 255,	0, 0)
			#write bitmap to time stamped image file
			sky_image.save('result-' + timestr +'.png')
			
		#Return to starting azimuth for each elevation position
		dish.write(b'azangle ')
		angle=str(az_start)
		if (len(angle)==3):
			dish.write(angle[0].encode())
			dish.write(angle[1].encode())
			dish.write(angle[2].encode())
		elif len(angle)==2:
			dish.write(angle[0].encode())
			dish.write(angle[1].encode())
		else: 
		        #single-digit number
		        dish.write(angle.encode())
		dish.write(b'\r')		
		
		#delay to allow dish to return to starting azimuth, dynamic based on az_range
		wait_time = int((az_range/5)*0.05)+1 #Dish takes ~0.05sec to rotate 1 degree, plus 1 sec buffer
		time.sleep(wait_time)
		
		#command dish to next elevation
		dish.write(b'elnudge up\r')
		


else: #possibly implement medium resolution in the future?
	print ('Invalid resolution')


#Wrap things up, give some statistics on the runtime. 
print ('Scan complete!')
end_time = time.time() #record end time of scan
run_time = round(end_time - start_time)
elapsed_time = round(run_time/60, 2)
if elapsed_time > 60:
	print('Elapsed time: ', elapsed_time/60, ' hours.')
else:
	print('Elapsed time: ', elapsed_time, ' minutes.')
if time_output > 60:
	print ('(Estimated runtime was ', time_output/60, ' hours.)')
else:
	print ('(Estimated runtime was ', time_output, ' minutes.)') 


#close serial connection
dish.close()
exit()

