
#FIRMWARE VERSION 1.2 11-8-2017
#THOMPSON
import time
import socket
import threading
from threading import Thread, current_thread
import subprocess				#accessing shutdown
import LIS3DH
from zeroconf import ServiceBrowser, Zeroconf	#for service discovery nds
from neopixel import *                          #modules for ws2812b LED strip
import uuid

server_address = ""
server_port  = 0
UUID =  str(hex(uuid.getnode()))

class Client(object):
	def __init__(self, server, port, connection_lost):
		self.server = server
		self.port = port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.settimeout(100)
		self.connection_lost = connection_lost
		try:
			self.sock.connect((self.server, self.port))
			listen = threading.Thread(target = self.acceptCommand)
			listen.start()
			print "connection established"
		except:
			print "Could not connect to server at address: ", self.server, "port: ", self.port
			connection_lost.set()

	def acceptCommand(self):
		#uncomment for debug
		print "acceptCommand thread started"
		buffer = 100
		cl = CommandList()
		while True:
			try:
				command = self.sock.recv(buffer)
				if command:
					#uncomment for debug
					#print "Received:", command
					#response = "got it: " + command
					#self.sock.send(response)
					if buffer == "-1" : #-1 is for app checking open socket
						pass
					else :
						execute  = threading.Thread(target = cl.call, args = (command, self.sock, self.connection_lost, ))
						execute.start()
						print "started command execution"
						print(command)
				else:
					print "disconnected from server"
					self.sock.close()
					self.connection_lost.set()
					break
			except:
				print "read error"
				#self.connection_lost.set()
				#break

	def sendCommand(self, info):
		try:
			self.sock.send(info)
		except:
			print "server unreachable"

class LEDS(object):
	LED_FREQ_HZ	= 800000  # LED signal frequency in hertz (usually 800khz)
        LED_DMA		= 5       # DMA channel to use for generating signal (try 5)
        LED_BRIGHTNESS	= 200     # Set to 0 for darkest and 255 for brightest
        LED_INVERT	= False   # True to invert the signal (when using NPN transistor level shift)
        LED_CHANNEL	= 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
        LED_STRIP	= ws.WS2811_STRIP_GRB   # Strip type and colour ordering
	COLUMN_LENGTH	= 5
	ROW_LENGTH	= 41
	LED_PIN		= 18

	lights_off	= threading.Event()

	def __init__(self):
		self.LED_COUNT = self.COLUMN_LENGTH * self.ROW_LENGTH
		self.strip = Adafruit_NeoPixel(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL, self.LED_STRIP)
		self.strip.begin()
		self.TARGET_COLOR = 0x00ffff
		self.MISTAKE_COLOR = 0xff0000
		self.POINT_COLOR = 0x00ff00

	def clear_all(self):
		#print "clearing all"
		for i in range(0, self.strip.numPixels()):
			self.strip.setPixelColor(i, 0)
		self.strip.show()

	def flash_rows(self, color, delay):
		print "flashing rows"
		for i in range(0, self.COLUMN_LENGTH):
			for j in range(i*self.ROW_LENGTH, i*self.ROW_LENGTH + self.ROW_LENGTH):
				self.strip.setPixelColor(j, color)
			self.strip.show()
			time.sleep(delay)
			self.clear_all()

	def flash_columns(self, color, delay):
		print "flashing columns"
		for i in range(0, self.ROW_LENGTH):
			j = i
			self.strip.setPixelColor(j, color)
			j = (self.ROW_LENGTH*2 -1) - i
			self.strip.setPixelColor(j, color)
			j = self.ROW_LENGTH*2 + i
			self.strip.setPixelColor(j,color)
			j = (self.ROW_LENGTH*4 - 1) - i
			self.strip.setPixelColor(j, color)
			j = self.ROW_LENGTH*4 + i
			self.strip.setPixelColor(j, color)

			self.strip.show()
			time.sleep(delay)
			self.clear_all()
	def linear(self, gap, color, delay):
		print "linear"
		i = 0
		while i < self.strip.numPixels():
			self.strip.setPixelColor(i, color)
			self.strip.show()
			i = i + 1 + gap
			time.sleep(delay)
	def flash_all(self, color, gap, times, delay):
		print "flash all"
		for i in range(0, times):
			j = 0
			while j < self.strip.numPixels():
				self.strip.setPixelColor(j, color)
				j = j + 1 + gap
			self.strip.show()
			time.sleep(delay)
			self.clear_all()

	#def impact_flash(self, color):
	#	i = 0
	#	while i < self.LED_COUNT :
	#		self.strip.setPixelColor(i, color)
	#		i = i + 2
	#	self.strip.show()
	#	time.sleep(.5)
	#	self.clear_all()

	def all_on(self, color, gap):
		print "all on"
		i = 0
		while i < self.strip.numPixels():
			self.strip.setPixelColor(i, color)
			i = i + 1 + gap
		self.strip.show()

class ImpactSensor(object):

        sensor_on = threading.Event()
        impact_detected = threading.Event()


	def __init__ (self):
		self.accel = LIS3DH.Accelerometer('spi', i2cAddress = 0x0, spiPort = 0, spiCS = 0)  # spi connection alternative
		self.accel.set_ODR(odr=50, powerMode='normal')
		self.accel.axis_enable(x='on',y='on',z='on')
		self.accel.interrupt_high_low('high')
		self.accel.latch_interrupt('on')
		self.accel.set_BDU('on')
		self.accel.set_scale()


	def setup_interrupt(self, threshold, timelimit, latency, axis):
		self.accel.set_int1_pin(click=1,aoi1=0, aoi2=0, drdy1=0, drdy2=0, wtm=0, overrun=0) # turn on CLICK interrupt
		self.interrupt = "ON"
		self.interrupt_axis = axis
		if axis == 'x':
			self.accel.set_click_config(zd=0, zs=0, yd=0, ys=0, xd=0, xs=1) # enable X single click on CLICK_CFG
		elif axis == 'y':
			self.accel.set_click_config(zd=0, zs=0, yd=0, ys=1, xd=0, xs=0) # enable Y single click on CLICK_CFG
		elif axis == 'z':
			self.accel.set_click_config(zd=0, zs=1, yd=0, ys=0, xd=0, xs=0) # enable Z single click on CLICK_CFG
													#standards VVV
		self.accel.set_click_threshold(threshold)       # set CLICK_THS to 1088 mg
		self.accel.set_click_timelimit(timelimit)        # set TIME_LIMIT to 120ms
		self.accel.set_click_timelatency(latency)      # set TIME_LATENCY to 320ms


        def waitForImpact(self):
            print "Beginning 'Detect Impact' loop"
            self.setup_interrupt(800, 120, 320, 'z')
            while self.sensor_on.isSet():
                time.sleep(.05)
                if(self.interrupt_axis == 'x'):
                    axis_reading = self.accel.x_axis_reading()
                elif(self.interrupt_axis == 'y'):
                    axis_reading = self.accel.y_axis_reading()
                elif(self.interrupt_axis == 'z'):
                    axis_reading  =self.accel.z_axis_reading()

                interrupt1 = self.accel.get_clickInt_status()
                #print (self.interrupt_axis + ': '+str(axis_reading)+ ' Click Interrupt Status  '+str(interrupt1))
                if interrupt1 > 0 and not self.impact_detected.isSet():
                    print str(axis_reading) + " : int-" + str(interrupt1) + " :Sensor - Impact detected " + current_thread().name
                    self.impact_detected.set()

            self.accel.set_int1_pin(click=0,aoi1=0, aoi2=0, drdy1=0, drdy2=0, wtm=0, overrun=0) # turn off CLICK interrupt
            self.accel.set_click_config(zd=0, zs=0, yd=0, ys=0, xd=0, xs=0) # disable Z single click on CLICK_CFG
            print "Sensor Off"


class CommandList:
	#Commands to send to App
	CONNECTED = "1\n"
	DISCONNECTED = "2\n"
	IMPACT_DETECTED = "3\n"

	leds = LEDS()							#creates dedicated LED object
	sensor = ImpactSensor()						#creates dedicated senor object


	target_on = threading.Event()
	#accept_target_color = threading.Event()

	def call(self,NUM, socket, connection_lost):
		#print "call function reached"
		if(NUM == "0"):
			print "Received 0 - Connection Terminated"
			socket.close()

		elif(NUM == "1"):
			print "Received 1 - Connection Established"
			socket.send(self.CONNECTED)
			socket.send(UUID+"\n")

			self.leds.flash_rows(Color(255,255,255), 1)		#0x000080 = NAVY BLUE

		elif(NUM == "2"):
			print "Received 2 - Sensor On, Detecting Impacts"
			self.sensor.sensor_on.set()
			sensor = threading.Thread(target = self.sensor.waitForImpact)
			sensor.start()
			self.sensor.impact_detected.clear()

			while self.sensor.sensor_on.isSet():
				if connection_lost.isSet():
					self.sensor.sensor_on.clear()
					self.sensor.impact_detected.clear()
					break
				while not self.sensor.impact_detected.isSet() and self.sensor.sensor_on.isSet():
					if connection_lost.isSet():
						self.sensor.sensor_on.clear()
						self.sensor.impact_detected.clear()
						print "*******"
						break
					time.sleep(.2)
				if self.sensor.impact_detected.isSet():
					try :

						print "CL- Impact Detected " + current_thread().name
						if self.target_on.isSet():
							socket.send(self.IMPACT_DETECTED)
							#self.leds.flash_all(self.leds.POINT_COLOR, 1, 1, .1)
							self.target_on.clear()
						#else:
						#	self.leds.flash_all(self.leds.MISTAKE_COLOR, 1, 1, .1)
						time.sleep(.5)
						self.sensor.impact_detected.clear()
					except:
						print "bad socket connection"
						self.sensor.sensor_on.clear()
						self.target_on.clear()
						break
			self.leds.clear_all()
			self.sensor.impact_detected.clear()
			self.target_on.clear()
			print "sensor turned off, closing thread"

		elif(NUM == "3"):
			print "Received 3 - Target On"
			while self.target_on.isSet() and self.sensor.impact_detected.isSet():
				pass

			self.target_on.set()
			self.leds.all_on(self.leds.TARGET_COLOR, 1)

		elif(NUM == "4"):
			print "Received " + NUM + "Turning off sensor"
			self.sensor.sensor_on.clear()
			self.leds.clear_all()


		#elif(NUM == "5"):
		#	print "waiting for target color assignment"
		#	self.accept_target_color.set()
		#	print self.leds.TARGET_COLOR

		elif(NUM == "6"):
			print "6"

		elif(NUM == "99"):
			print NUM
			u = Utilities()
			u.shutdown()
		elif self.accept_target_color.isSet():
			print hex(NUM)
			self.leds.TARGET_COLOR = hex(NUM)
			self.accept_target_color.clear()
		else:
			print "not recognized", NUM
			#return "unkown"
		print current_thread().name + " closing"


#app service discovery
#thank you https://pypi.python.org/pypi/zeroconf
class MyListener(object):

        def remove_service(self, zeroconf, type, name):
                print("Service %s removed" % (name,))

        def add_service(self, zeroconf, type, name):
                global server_address, server_port
                info = zeroconf.get_service_info(type, name)
                print("Service %s added, service info: %s" % (name, info))
                if info.name.find('skillcourtapp')  >= 0:         #if skillcourtapp is in name, save info to glob vars
                        server_address = socket.inet_ntoa(info.address)
                        server_port = info.port
                        print "ServerAddress and Port Found: ",server_address, server_port

class  Utilities(object):

	def findAppConnection(self, event_handler):
		print "looking for server address and port of Skill Court App"
		thread = threading.Thread(target = self.appBrowse, args = (event_handler,))
		thread.start()
		print "App browsing thread started"

	def appBrowse(self, event_handler):
                zeroconf = Zeroconf()
                listener = MyListener()
                browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
                while server_port == 0:
                        pass
		event_handler.set()
                zeroconf.close()
                print "closed zeroconf"
		return True
	def shutdown(self):
                print "Shutting Down"
                command = "/usr/bin/sudo /sbin/shutdown now"
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                output = process.communicate()[0]

	def reboot(self):
                print "Rebooting"
                command = "/usr/bin/sudo /sbin/shutdown -r now"
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
                output = process.communicate()[0]

if __name__ == "__main__":
	server_found = threading.Event()
	connection_lost = threading.Event()
	strip = LEDS()
	while 1:
		Utilities().findAppConnection(server_found)
		#server_found.wait()
		print "waiting for discovery"
		while not server_found.isSet() :
			strip.flash_columns(Color(255,0,0), .01)
			time.sleep(1)
		connection = Client(server_address, server_port, connection_lost)
		connection_lost.wait()
		connection_lost.clear()
		server_found.clear()
		server_address = ""
		server_port = 0
