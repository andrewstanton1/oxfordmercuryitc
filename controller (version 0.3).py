import sys
import time
import threading 
import mercuryITC as itc
import serial.tools.list_ports
import pyvisa as visa
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QGridLayout, QLabel, QComboBox, QStatusBar, QPushButton, QProgressBar, QAction, QMenu, QCheckBox, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QObject, QTimer, QThread, pyqtSignal, pyqtSlot, Qt

from collections import defaultdict

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent=parent)
		
		self.central_widget = QStackedWidget()
		self.setCentralWidget(self.central_widget)
		self.central_widget.setStyleSheet("background-color: black; margin:0px; border:0px solid rgb(128, 128, 128); ")
		
		self.sensor_display = sensorUIWindow(self)
		self.options_display = optionsUIWindow(self)

		self.central_widget.addWidget(self.sensor_display)
		self.central_widget.addWidget(self.options_display)
		self.central_widget.setCurrentWidget(self.sensor_display)

		self.sensor_display.options_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.options_display))
		self.options_display.home_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.sensor_display))
		
		#temperature controller
		self.tc = None
		
		self.selectUSB()

	def selectUSB(self):
		self.menu_bar = self.menuBar()
		self.menu_bar.setStyleSheet("background-color: gray")
		self.port_selection = self.menu_bar.addMenu("PORTS")
		self.com_port = None

		self.valid_connection = False
		# self.status_bar = QStatusBar()
		self.statusBar().showMessage("Select PORT")

		self.rm = visa.ResourceManager()

		self.serial_ports = sorted(self.rm.list_resources())#sorted([comport.device for comport in serial.tools.list_ports.comports()])

		if not self.serial_ports:
			self.statusBar().showMessage("No available ports")

		for ports in self.serial_ports:
			com = QAction(ports, self)
			self.port_selection.addAction(com)
			self.port_selection.triggered[QAction].connect(self.portClicked)


	def portClicked(self, port):
		
		self.com_port = port.text()

		try:
			self.serial_ports = sorted(self.rm.list_resources())
			self.tc = itc.temperatureController(self.com_port)
			self.statusBar().showMessage("Connected to PORT " + self.com_port)
			self.valid_connection = True
			self.sensor_display.createThreading()

		except:
			self.statusBar().showMessage("ITC not connected to PORT " + self.com_port)
			self.valid_connection = False

class sensorUIWindow(QWidget):

	options_clicked = pyqtSignal()

	def __init__(self, parent=None):
		super(sensorUIWindow, self).__init__(parent=parent)
		self.parent = parent


		# layouts
		self.initUI()

		# ports
		# self.selectUSB()



	def initUI(self):

		# window layout
		self.setWindowTitle("Mercury ITC controller")

		# front panel layout
		# self.central_widget = QWidget(self)
		self.background_layout = QVBoxLayout()
		# self.setCentralWidget(self.central_widget)
		self.mainDisplay = QGridLayout()
		self.setStyleSheet("background-color: black; margin:0px; border:0px solid rgb(128, 128, 128); ")
		self.setLayout(self.background_layout)
		self.background_layout.addLayout(self.mainDisplay)

		# devices
		self.devices = {
			"MB1" : "DEV:MB1.T1:TEMP", 
			"DB6" : "DEV:DB6.T1:TEMP", 
			"DB4" : "DEV:DB4.G1:AUX", 
			"MB0" : "DEV:MB0.H1:HTR", 
			"DB1" : "DEV:DB1.H1:HTR" }

		self.sensorName = defaultdict(list)
		self.sensorName["MB1"] = ["VTI_Hx_MB1.T", "primary"]
		self.sensorName["DB6"] = ["VTI_SR_DB6.T", "secondary"]
		self.sensorName["DB4"] = ["DB4.G1.%", "primary"]
		self.sensorName["MB0"] = ["Hx_htr_MB0.V", "secondary"]
		self.sensorName["DB1"] = ["SR_htr_DB1.V", "primary"]
		

		self.commands = {
			"MB1": "TEMP", 
			"MB0": "VOLT", 
			"DB4": "PERC", 
			"DB6": "TEMP", 
			"DB1": "VOLT" }

		# self.deviceSelection()

		# front panel readings
		self.deviceWidget()

		# lower panel layout
		self.lower_widget = QWidget(self)
		self.lower_display = QHBoxLayout()
		self.lower_widget.setStyleSheet("background-color: black; margin:0px; border:0px; ")
		self.background_layout.addWidget(self.lower_widget)
		self.lower_widget.setLayout(self.lower_display)

		# lower panel buttons
		self.panelOptions()


	# def deviceSelection(self):
	# 	device_label = QLabel("Devices")
	# 	self.panel_widget.createTitle("Devices")
	# 	device_label.setFont(QFont("Ariel", 11))
	# 	self.vbox1.addWidget(device_label)

	# 	self.dev_select = {}

	# 	for device, name in self.devices.items():
	# 		if device ==  'MB1' or device == 'MB0' or device == 'DB4':
	# 			primary_devices = True 
	# 		else:
	# 			primary_devices = False

	# 		self.dev_select[name] = QCheckBox(device, self)
	# 		self.vbox1.addWidget(self.dev_select[name])
	# 		self.dev_select[name].setChecked(primary_devices)
	# 		self.dev_select[name].stateChanged.connect(self.deviceManager)


	# def deviceManager(self, device_state):
	# 	if device_state == Qt.Checked:
	# 		if self.sender() == self.dev_select[self.devices['MB1']]:
	# 			self.dev_select[self.devices['DB6']].setChecked(False)
	# 		elif self.sender() == self.dev_select[self.devices['DB6']]:
	# 			self.dev_select[self.devices['MB1']].setChecked(False)

	# 		if self.sender() == self.dev_select[self.devices['MB0']]:
	# 			self.dev_select[self.devices['DB1']].setChecked(False)
	# 		elif self.sender() == self.dev_select[self.devices['DB1']]:
	# 			self.dev_select[self.devices['MB0']].setChecked(False)




	def deviceWidget(self):

		self.panel_widgets = {}

		for device, name in self.sensorName.items():
			self.panel_widgets[device] = createDisplayObject()
			self.panel_widgets[device].setTitle(name[0])
			self.panel_widgets[device].setReading("N/A")

			if 'T' in name[0].split('.'):
				if name[0] == 'VTI_Hx_MB1.T':
					self.panel_widgets[device].createMeterBar(self.devices['MB0'])
					self.panel_widgets[device].createMeterBar(self.devices['DB4'])
				else:
					self.panel_widgets[device].createMeterBar(self.devices['DB1'])

			self.panel_widgets[device].createDeviceContainer()

		self.frontPanel()

	def frontPanel(self):

		row = 0
		col = 0

		for display in self.panel_widgets:
			if col == 3:
				col = 0
				row = 1
			self.mainDisplay.addWidget(self.panel_widgets[display].getDeviceContainer(), row, col)
			col += 1


	def panelOptions(self):

		self.options_panel = {'plot_option' : QPushButton("Plot"), 'control_option' : QPushButton("Control"), 'setting_option' : QPushButton("Settings"),
								'heater_option' : QPushButton("Heater")}

		CSS = "color: white; background-color: black; font: 10pt; font: bold; margin:1px; border:2px solid rgb(0, 122, 122); border-radius: 5px; " 
		CSS_settings = "color: red; background-color: black; font: 10pt; font: bold; margin:1px; border:2px solid rgb(0, 122, 122); border-radius: 5px; " 

		for option in self.options_panel:
			self.options_panel[option].setFixedSize(220, 65)
			if option is 'setting_option':
				self.options_panel[option].setStyleSheet(CSS_settings)
			else:
				self.options_panel[option].setStyleSheet(CSS)
			self.lower_display.addWidget(self.options_panel[option])


		self.options_panel['control_option'].clicked.connect(self.options_clicked.emit)


	# def startOptionWindow(self):
	# 	self.parent.central_widget.setCurrentWidget(self.parent.options_display)

	def createThreading(self):
		# self.panel = {}
		# self.threads = {}
		# self.k = 0
		self.panel = panelThread(self)
		self.thread = QThread(self)
		self.connectThreading()
		# for device in self.devices:
		# 	self.k += 1
		# 	if self.k <= 1:
		# 		self.panel[device] = panelThread(self)
		# 		self.threads[device] = QThread(self)
		# 		self.connectThreading(device)


	def connectThreading(self):
		self.panel.itc(self.parent.tc)
		self.panel.selectDevice(self.sensorName, self.commands)
		self.panel.connected(self.parent.valid_connection)
		self.panel.moveToThread(self.thread)
		self.thread.started.connect(self.panel.monitorValues)
		self.panel.signal.connect(self.monitorValues)
		self.thread.start()
	# def connectThreading(self, device):
	# 		self.panel[device].itc(self.tc)
	# 		self.panel[device].selectDevice(device, self.commands[device])
	# 		if self.valid_connection:
	# 			self.panel[device].connected(self.valid_connection)
	# 			self.panel[device].moveToThread(self.threads[device])
	# 			self.threads[device].started.connect(self.panel[device].monitor_values)
	# 			self.panel[device].signal.connect(self.monitorValues)
	# 			self.threads[device].start()

	@pyqtSlot(list)
	def monitorValues(self, reading):

		if isinstance(reading[1], str):
			if reading[0] == "DB4":
				self.panel_widgets[reading[0]].updateReading(reading[1])
				try:
					self.panel_widgets["MB1"].updateMeterBar(self.devices[reading[0]], float(reading[1][:-1]))
				except:
					self.panel_widgets["MB1"].updateMeterBar(self.devices[reading[0]], 0.0)
			else:
				self.panel_widgets[reading[0]].updateReading(reading[1])
		else:
			if reading[0] == "MB0":
				self.panel_widgets["MB1"].updateMeterBar(self.devices[reading[0]], reading[1])
			elif reading[0] == "DB1":
				self.panel_widgets["DB6"].updateMeterBar(self.devices[reading[0]], reading[1])
			

class createDisplayObject(QMainWindow):
	def __init__(self, parent=None):
		super(createDisplayObject, self).__init__(parent=parent)
		self.meter_reading = {}

	def setTitle(self, title):
		self.device_title = QLabel(title)
		self.device_title.setAlignment(Qt.AlignCenter)
		self.device_title.setFont(QFont("Ariel", 10))
		self.device_title.setStyleSheet("background-color: black; color: white; border: 0px; ")
	
	def setReading(self, reading):	
		self.device_reading = QLabel(reading)
		self.device_reading.setAlignment(Qt.AlignCenter)
		self.device_reading.setFont(QFont("Ariel", 16))
		self.device_reading.setStyleSheet("background-color: black; color: gold; border: 0px")

	def createMeterBar(self, meter_device=None):
		if meter_device:
			self.meter_bar = QProgressBar(self)
			self.meter_bar.setFixedSize(200, 25)
			if self.meter_reading:
				CSS = "QProgressBar::chunk {color: white; font: bold; background-color: #05B8CC; width: 10px; margin: 1.2px; text-align: center}"
			else:
				CSS = "QProgressBar::chunk {color: white; font: bold; background-color: #CD96CD; width: 10px; margin: 1.2px; text-align: center}"
			self.meter_bar.setStyleSheet(CSS)
			self.meter_bar.setValue(0.0)
	
			self.meter_reading[meter_device] = self.meter_bar


	def updateReading(self, reading):
		self.device_reading.setText(reading)

	def updateMeterBar(self, meter_device, value):
		self.meter_bar.setValue(value)
		self.meter_reading[meter_device].setValue(value)

	def getTitle(self):
		return self.device_title

	def getReading(self):
		return self.device_reading

	def createDeviceContainer(self):
		self.device_box = QWidget(self)
		self.device_box.setFixedSize(300, 200)

		self.setCentralWidget(self.device_box)
		self.device_layout = QVBoxLayout()
		self.device_box.setStyleSheet("color: white; font: bold; background-color: black; margin:1px; border:2px solid rgb(0, 122, 122); border-radius: 5px; text-align: center")
		self.device_box.setLayout(self.device_layout)

		self.device_layout.addWidget(self.device_title)
		self.device_layout.addWidget(self.device_reading)
		self.device_layout.addStretch(2)


		for device, device_meter in self.meter_reading.items():
			self.meter_layout = QHBoxLayout()
			device_name = device.split(':')[1]
			meter_device = QLabel(device_name)
			meter_device.setFixedSize(70, 25)
			meter_device.setStyleSheet("color: white; text-align: center; border: 0px")
			self.meter_layout.addWidget(meter_device)
			self.meter_layout.addWidget(device_meter)
			self.device_layout.addLayout(self.meter_layout)

	def getDeviceContainer(self):
		return self.device_box


# Thread
class panelThread(QObject):

	signal = pyqtSignal(list)

	def __init__(self, parent=None):
		QObject.__init__(self)
		self.connected()

	def connected(self, connect = False):
		self.connect = connect

	def itc(self, tc):
		self.tc = tc

	def selectDevice(self, devices, measure):
		self.devices = devices
		self.measure = measure	

	@pyqtSlot()
	def monitorValues(self):
		### TODO ####
		### implement primary and second device setting from heater window ####
		# self.main_sensors = {}
		# k = 0
		# for device in self.devices:
		# 	if k < 2 or k > 3:
		# 		self.main_sensors[device] = 'primary'
		# 	else:
		# 		self.main_sensors[device] = 'secondary'

		secondary_refresh = 0
		while True:
			if self.connect:
				for device in self.devices:
					if self.devices[device][1] == 'primary':
						self.signal.emit(self.tc.getSignal(device, self.measure[device]))
						self.tc.ser.close()
						self.tc.ser.open()
						if secondary_refresh == 1 and self.devices[device][0].split('.')[1] == 'V':
							self.signal.emit(self.tc.getHeaterPowerRatio(device))
							self.tc.ser.close()
							self.tc.ser.open()
					else:
						if secondary_refresh == 0:
							self.signal.emit(self.tc.getSignal(device, self.measure[device]))
							self.tc.ser.close()
							self.tc.ser.open()
						elif secondary_refresh == 1 and self.devices[device][0].split('.')[1] == 'V':
							self.signal.emit(self.tc.getHeaterPowerRatio(device))
							self.tc.ser.close()
							self.tc.ser.open()
			else:
				self.signal.emit("N/A")

			secondary_refresh += 1

			if secondary_refresh > 2:
				secondary_refresh = 0

			time.sleep(1)

class optionsUIWindow(QWidget):

	home_clicked = pyqtSignal()

	def __init__(self, parent=None):
		super(optionsUIWindow, self).__init__(parent=parent)
		self.parent = parent

		# layouts
		self.controlLoopUI()


	def controlLoopUI(self):

		self.layout = QVBoxLayout()
		self.setLayout(self.layout)

		self.sensor_row = QHBoxLayout()
		self.heat_row = QHBoxLayout()
		self.flow_row = QHBoxLayout()
		self.setpoint_row = QHBoxLayout()
		self.options_row = QHBoxLayout()

		self.main_title = QLabel('Control Loop Configuration')
		self.main_title.setStyleSheet('color: white ; font: 10pt ; text-decoration: underline; border: 1px ;')


		self.control_labels = {'sensor' : QLabel('Sensor'), 'heat' : QLabel('Heat(%)'), 'flow' : QLabel('Flow(%)'), 'set point' : QLabel('Set Point') }

		for labels in self.control_labels:
			self.control_labels[labels].setStyleSheet('color: white ; font: 10pt ; border: 0px')

		self.layout.addWidget(self.main_title)
		self.main_title.setFixedHeight(20)

		self.sensor_row.addWidget(self.control_labels['sensor'])
		self.heat_row.addWidget(self.control_labels['heat'])
		self.flow_row.addWidget(self.control_labels['flow'])
		self.setpoint_row.addWidget(self.control_labels['set point'])

		self.layout.addLayout(self.sensor_row)
		self.layout.addLayout(self.heat_row)
		self.layout.addLayout(self.flow_row)
		self.layout.addLayout(self.setpoint_row)
		self.layout.addLayout(self.options_row)
		
		self.setLayout(self.layout)

		self.optionButtons()

	def sensorConfig(self):
		self.device_selection = QComboBox()
		

	def heatConfig(self):
		pass

	def flowConfig(self):
		pass

	def setpointConfig(self):
		pass

	def pidConfig(self):
		pass


	def createPushButton(self):
		pass

	def createInputBox(self):
		pass



	def optionButtons(self):
		self.options_buttons = {}
		self.createOptionButtons(self.options_buttons, 'Home')
		self.createOptionButtons(self.options_buttons, 'Sweep table')
		self.createOptionButtons(self.options_buttons, 'Gas Cfg')
		self.createOptionButtons(self.options_buttons, 'PID table')

		self.options_buttons['Home'].clicked.connect(self.home_clicked.emit)

	def createOptionButtons(self, button, name):
		button[name] = QPushButton(name, self)
		self.options_row.addWidget(button[name])
		button[name].setStyleSheet("color: white; background-color: black; font: 10pt; font: bold; margin:1px; border:2px solid rgb(0, 122, 122); border-radius: 5px; ")
		button[name].setFixedSize(220, 65)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    window.resize(900, 500)
    window.show()

    sys.exit(app.exec_())

