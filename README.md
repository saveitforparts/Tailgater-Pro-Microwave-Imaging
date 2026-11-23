#Microwave imaging using Tailgater Pro satellite antenna. 

Gabe Emerson / Saveitforparts 2026. Email: gabe@saveitforparts.com

Video demo: 

**Introduction:**

This code controls a Tailgater Pro (or similar) satellite antenna over USB using 
serial commands. The dtp_scan.py program aims the dish to a selected portion of 
the sky and records the RF signal strength. The dish_image.py program reads the 
resulting data and creates	a heatmap of the scanned area. Frequencies using stock
Tailgater antenna hardware will be in the Ku band (~12ghz)

Please note that the author is not an expert in Python, Linux, satellites, or 
radio theory! This code is very experimental, amateur, and not optimized. 
There are probably better, faster, and more efficient ways	to do some of the 
functions and calculations in the code. Please feel free to fix, improve, or add 
to anything (If you do, I'd love to hear what you did and how it worked!)


**Applications:**

- Imaging geostationary TV satellites
- Surveying an environment or room for microwave radiation
- Imaging an environment using ambient or reflected microwaves from Ku band source
- Imaging other wavelengths with a different feedhorn or LNB 
- Integration with an SDR and other antenna elements 


**Hardware Requirements:**

This code has been developed and tested with a Tailgater Pro (Model DP4900) portable
satellite antenna, made by King Controls (King went out of business in 2026).
These have a USB "A" connector on the mainboard (located inside the enclosure, behind 
the dish reflector). There are several variations, models, and versions of this 
antenna, including Tailgater 4, King One, VQ4500, etc. For older models in the 
classic octagonal case, see my original Tailgater code on Github.

My test unit uses firmware version SW23193 or "Hyland" from 2018. The same code appears
to work on SW23480 from 2019. Other versions sometimes have different firmware and 
console commands available. For example, the 2020 "Lutsen" firmware does not seem to 
include "azangle" and needs raw azim values mapped to degrees. 

This code has been tested mainly on Linux Mint. 


**Notes on power supply:**

The USB connection only provides data to/from the dish. Power for the board, LNB, and 
motors comes from the coax "F" connector. This requires 12V DC, center pin positive.
I used a coax power injector or simply a barrel jack soldered to an F male plug. I 
generally use at least a 1000mA power supply. 


**Package Requirements:**

See requirements.txt.
They can be installed individually or by running "pip install -r requirements.txt"


**Setting up / testing Tailgater console:**

To connect to a Tailgater antenna with USB A port, you will need an A-to-A cable
(available online). 

You can check for proper connection by running "lsusb" on Linux. The dish should show
up as "Microchip Technology, Inc. CDC RS-232 Emulation Demo".

Run "dmesg | grep tty" to see which port the dish is using. This is usually something
like /dev/ttyACM0, although I have seen it jump to ttyACM1 or USB1 if the power or USB
connection are interrupted. If your Tailgater is NOT on /dev/ttyACM0 you will need to 
edit line 15 of dish_scan.py to reflect the correct port. 
	
To connect to the serial console on the dish, run "screen /dev/ttyACM0" (or appropriate
port) on Linux, or use a Windows serial terminal to connect to the usb device (typically
com3 or similar). You will initially get a blank screen. Typing "help" should return a
limited menu of available commands and a "GO>" prompt. You will need to unlock the 
firmware by typing "help Hyland". The dish should reply with "Be kind, rewind", and then 
typing "help" again will give you the full menu. This needs to be done on each power cycle.
(Lutsen models with a green motherboard can be unlocked with "help Lutsen").
	
Note that the console does not accept backspace, so if you make a mistake while typing,
just hit enter to clear the console. If necessary, close the console or unplug the 
dish to avoid a motor overrun. 


**Positioning the dish:**

The Tailgater dish uses a 360-degree counter-clockwise coordinate system, with the handle
as "North" / 0 degrees. The dish considers an azimuth of 90 to be 90 degrees
counterclockwise from the carry handle (looking down at the dish from above). Azimuth 180
is directly opposite the handle and azimuth 270 is 90 degrees clockwise from the handle.
This is technically "backwards" from a standard compass heading. The code is written to
take this into account, but please note that image and array outputs will show azimuth in
the dish's reference plane, opposite of standard compass or orbital azimuth. 
		
Generally I place the dish with the handle facing due North (for scans of the Southern sky),
but you can place it in any orientation you want. The dish scans left to right, incrementing
up from the starting elevation. Remember the coordinate system is "backwards" compared to 
standard compass headings.


**Running a scan:**

Once the dish is connected, powered, and ready on a USB port, run:
"python3 dish_scan.py"
The menu will be automatically unlocked (assuming you have a compatible model).
You will be prompted for the starting and ending azimuth and elevation of your scan. 
You will also be prompted for the resolution (low or high). 
Valid azimuth range is 0-360, and valid elevations are 15-65 degrees. (the dish can go 
slightly farther but enounters physical stops at ~10 and 77 degrees elevation) If you enter
a value outside the valid range, the program will use the minimum or maximum asappropriate.
The default values are from azimuth 120 to 240, and from elevation 15 to 55 degrees. This 
covers most of the Southern sky (if the dish is placed with coax jack aiming due North). 
A low-resolution scan with default values takes approximately 1.5 hours due to the minimum 
rfwatch runtime of 1 second. A high-resolution scan with default values could take several
days and is not recommended!

Scans of smaller azimuth/elevation ranges should take less time. Estimated scan time for
your parameters will be shown once the scan starts, and you will be asked to confirm
or cancel the scan. 
	
During the scan, the current azimuth, elevation, and signal strength will be displayed for
each dish position. A small preview image, "result-<timestamp>.png" will be created and will 
update live during the scan. On Gnome Image Viewer, this file should automatically refresh as
it updates. It will be very small (x pixels equal to your scan's azimuth range, and y pixels
equal to your scan's elevation range). However, it should be enough to get an idea if the
scan is working. 

You can also enable a live preview of the data, processed and normalized as it is stored. 
This has some issues on my machine and sometimes crashes (work in progress). 

	
**Generating an image from a scan:**
	
Once a scan has completed, you will have three output files with the same timestamp:

- "result-<timestamp>.png"         The low-resolution preview image.
	
- "raw-data-<timestamp>.txt"       The raw scan values in a numpy array.
	
- "scan-settings-<timestamp>.txt"  The scan parameters (start and end azimuth / elevation)
	
dish_image.py will use the two text files to create a heatmap of your scan. Run the code 
along with the name of the raw-data scan you want to process. For example:
"python3 dish_image.py raw-data-20230322-153935.txt"
	
The code will load the corresponding scan-settings file automatically, and opens a
heatmap of the scan in a new window. You can save this heatmap for later use. 


**Example Images:**
I have included several example images to show what a scan looks like:
	 
- "dish_image example.png"  The result of running a default scan with dish_scan.py and 
processing with dish_image.py. Shows geostationary TV satellites.
				  
- "house.png"		  A structure scan comparing KU band (with "hsv" colormap), visible
light, and 50% overlay of each. 
				  
- "tailgater_pro.png"		  Example of the antenna unit used for this project.
		

**Example Files**

I have included some example data files output by dish_scan.py, for processing with dish_image.py

- "raw-data-XXXXXXXXXXXXXXXX.txt":   numpy matrix of signal strength at each azimuth and elevation pair

- "scan-settings-XXXXXXXXXXXXXXX.txt":    scan parameters for dish_image to use when processing

- "result-XXXXXXXXXXXXXXX.png":     Preview image created by dish_scan (not used by dish_image)


**Additional notes:**
	
The dish_scan.py code contains code for two resolution settings. Low resolution (default) uses
azangle and elangle commands on the Tailgater console, so each scan position is one degree. The
high-resolution version uses the "nudge" commands available in the Tailgater console. 
These "nudges" are not always consistent, so you may see banding or other image artifacts when
using it. High-res scans of smaller areas seem to have fewer errors. Scans of very large spatial
areas using the high-res scan may cause undue wear to your dish motors, as well as taking
a very long time to complete. 

The heatmap generated by dish_image.py uses CMRmap. If you wish to use another colormap, you can
change line 67 of dish_image.py. I also like "seismic" and "gnuplot2", but I feel that they lose
some definition on the background landscape. "hsv" may also be useful for noisy scans. 

