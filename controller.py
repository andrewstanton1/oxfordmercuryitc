import sys
import time
import threading 
import mercuryITC as itc
import serial.tools.list_ports
import pyvisa as visa
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import QObject, QTimer, QThread, pyqtSignal, pyqtSlot, Qt, QEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, \
							QGridLayout, QLabel, QLineEdit, QComboBox, QStatusBar, \
							QPushButton, QProgressBar, QAction, QMenu, QCheckBox, \
							QVBoxLayout, QHBoxLayout

import devices

class MainWindow(QMainWindow):
	def __init__(self, parent=None):
		super(MainWindow, self).__init__(parent=parent)
		
		self.central_widget = QStackedWidget()
		self.setCentralWidget(self.central_widget)
		self.central_widget.setStyleSheet("background-color: black; margin:0px; \
										   border:0px solid rgb(128, 128, 128); ")
		
		#temperature controller
		self.tc = None

		# devices
		self.devices = devices.devices
		self.sensor_name = devices.sensor_name
		self.commands = devices.commands

		self.valid_connection = False

		self.sensor_display = sensorUIWindow(self)
		self.control_display = controlUIWindow(self)
		self.heater_display	 = heaterUIWindow(self)
		self.sweep_display = sweepTableUIWindow(self)

		self.central_widget.addWidget(self.sensor_display)
		self.central_widget.addWidget(self.control_display)
		self.central_widget.addWidget(self.heater_display)
		self.central_widget.addWidget(self.sweep_display)
		self.central_widget.setCurrentWidget(self.sensor_display)

		self.sensor_display.control_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.control_display))
		self.sensor_display.heater_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.heater_display))

		self.control_display.home_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.sensor_display))
		self.control_display.sweeptable_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.sweep_display))

		self.heater_display.home_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.sensor_display))
		self.heater_display.control_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.control_display))

		self.sweep_display.control_clicked.connect(lambda: self.central_widget.setCurrentWidget(self.control_display))
	
		self.createWriterThread()
		self.selectUSB()


	def selectUSB(self):
		self.menu_bar = self.menuBar()
		self.menu_bar.setStyleSheet("background-color: gray")
		self.port_selection = self.menu_bar.addMenu("PORTS")
		self.com_port = None

		self.valid_connection = False
		self.statusBar().showMessage("Select PORT")

		self.rm = visa.ResourceManager()

		self.serial_ports = sorted(self.rm.list_resources())

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
			self.valid_connection = True
			self.createWriterThread()
			self.central_widget.currentWidget().startThread()
			self.statusBar().showMessage("Connected to PORT " + self.com_port)
		except:
			self.statusBar().showMessage("ITC not connected to PORT " + self.com_port)
			self.valid_connection = False
			self.sensor_display.panel.connected(self.valid_connection)


	def createWriterThread(self):
		self.write = writerThread(self)
		self.writer_thread = QThread(self)
		self.assignWriterThread()
		self.connectWriterThread()

	def assignWriterThread(self):
		self.write.itc(self.tc)
		self.write.connected(self.valid_connection)

	def connectWriterThread(self):
		self.write.moveToThread(self.writer_thread)
		# self.writer_thread.started.connect(self.write.getMaxVoltage)
		self.writer_thread.started.connect(self.write.tryWrite)
		self.write.write.connect(self.displayWriteReadMessage)
		self.writer_thread.start()

	@pyqtSlot(str)
	def displayWriteReadMessage(self, message):
		self.statusBar().showMessage(message, 2000)

class sensorUIWindow(QWidget):

	control_clicked = pyqtSignal()
	heater_clicked = pyqtSignal()

	def __init__(self, parent=None):
		super(sensorUIWindow, self).__init__(parent=parent)
		self.parent = parent

		# layouts
		self.initUI()


	def initUI(self):

		# window layout
		self.setWindowTitle("Mercury ITC controller")

		# front panel layout
		self.background_layout = QVBoxLayout()
		self.mainDisplay = QGridLayout()
		self.setStyleSheet("background-color: black; margin:0px; border:0px solid rgb(128, 128, 128); ")
		self.setLayout(self.background_layout)
		self.background_layout.addLayout(self.mainDisplay)

		# devices
		self.devices = self.parent.devices
		self.sensor_name = self.parent.sensor_name
		self.commands = self.parent.commands

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


	def deviceWidget(self):

		self.panel_widgets = {}

		for device, name in self.sensor_name.items():
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
		self.createThreading()

		options_panel = [ 	hoverPushButton("Plot"), 
							hoverPushButton("Control"), 
							hoverPushButton("Settings"),
							hoverPushButton("Heater") ]

		for option in options_panel:
			self.lower_display.addWidget(option.getHoverButton())
			option.getHoverButton().clicked.connect(self.pauseThread)

		options_panel[1].getHoverButton().clicked.connect(self.resumeControlDisplay)
		options_panel[1].getHoverButton().clicked.connect(self.control_clicked.emit)

		options_panel[3].getHoverButton().clicked.connect(self.resumeHeaterDisplay)
		options_panel[3].getHoverButton().clicked.connect(self.heater_clicked.emit)


	def resumeHeaterDisplay(self):
		self.parent.heater_display.startThread()

	def resumeControlDisplay(self):
		self.parent.control_display.startThread()

	def createThreading(self):
		self.panel = panelThread(self)
		self.thread = QThread(self)
		self.connectThreading()

	def connectThreading(self):
		self.panel.itc(self.parent.tc)
		self.panel.selectDevice(self.sensor_name, self.commands)
		self.panel.connected(self.parent.valid_connection)
		self.panel.moveToThread(self.thread)
		self.thread.started.connect(self.panel.monitorValues)
		self.panel.signal.connect(self.monitorValues)
		self.panel.ended.connect(self.thread.quit)

	def startThread(self):
		self.panel.selectDevice(self.sensor_name, self.commands)
		self.panel.connected(self.parent.valid_connection)
		self.panel.itc(self.parent.tc)
		self.panel.resume()
		self.thread.start()

	def pauseThread(self):
		self.panel.pause()

	@pyqtSlot(list)
	def monitorValues(self, reading):
		if reading[1] != "INVALID":
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
		# self.device_title.setFont(QFont("Ariel", 10))
		self.device_title.setStyleSheet("background-color: black; font: 25px; color: white; border: 0px; ")
	
	def setReading(self, reading):	
		self.device_reading = QLabel(reading)
		self.device_reading.setAlignment(Qt.AlignCenter)
		# self.device_reading.setFont(QFont("Ariel", 16))
		self.device_reading.setStyleSheet("background-color: black; font: 30px; color: gold; border: 0px")

	def createMeterBar(self, meter_device=None):
		if meter_device:
			self.meter_bar = QProgressBar(self)
			self.meter_bar.setFixedSize(200, 25)
			if self.meter_reading:
				CSS = "QProgressBar::chunk {color: white; font: bold; \
					   background-color: #05B8CC; width: 10px; margin: \
					   1.2px; text-align: center;}"
			else:
				CSS = "QProgressBar::chunk {color: white; font: bold; \
					   background-color: #CD96CD; width: 10px; margin: \
					   1.2px; text-align: center;}"
			self.meter_bar.setStyleSheet(CSS)
			self.meter_bar.setValue(0.0)
	
			self.meter_reading[meter_device] = self.meter_bar


	def updateReading(self, reading):
		self.device_reading.setText(reading)

	def updateMeterBar(self, meter_device, value):
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
		self.device_box.setStyleSheet("color: white; font: bold; background-color: black; \
									   margin:1px; border:2px solid rgb(0, 122, 122);     \
									   border-radius: 5px; text-align: center")
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

class hoverPushButton(QObject):
	def __init__(self, name, parent=None):
		super(hoverPushButton, self).__init__(parent=parent)
		self.name = name
		self.CSS_pressed = "QPushButton::hover {background-color : green}"

		self.CSS = "QPushButton \
							{color: white; background-color: black; \
							font: 10pt; font: bold; margin:1px; 	\
							border:2px solid rgb(0, 122, 122); 		\
							border-radius: 5px; border-style: outset }" 

		self.CSS_settings = "QPushButton \
							{color: red; background-color: black;	\
							font: 10pt; font: bold; margin:1px;		\
							border:2px solid rgb(0, 122, 122); 		\
							border-radius: 5px; border-style: outset; }" 

		self.CSS_disabled = "QPushButton \
							{color: #F5F5F5; background-color: grey; \
							font: 10pt; font: bold; margin:1px; 	\
							border:2px solid rgb(0, 122, 122); 		\
							border-radius: 5px; border-style: outset }"

		self.createHoverButton()

	def createHoverButton(self):
		if self.name == "Settings":
			self._CSS = self.CSS_pressed + self.CSS_settings
		else:
			self._CSS = self.CSS_pressed + self.CSS

		self.hover_button = QPushButton(self.name)
		self.hover_button.setStyleSheet(self._CSS)
		self.hover_button.setFixedSize(220, 75)

	def getHoverButton(self):
		return self.hover_button

	def disabled(self):
		self.hover_button.setEnabled(False)
		self.hover_button.setStyleSheet(self.CSS_disabled)


	def enabled(self):
		self.hover_button.setEnabled(True)
		self.hover_button.setStyleSheet(self._CSS)



class focusLineEdit(QLineEdit):
	def __init__(self, name=None, parent=None):
		super(focusLineEdit, self).__init__(parent=parent)
		self.name = name

		self.CSS_focus = "QLineEdit::focus {border: 3px solid green}"
		self.CSS = self.CSS_focus + 'QLineEdit {color: gold; background-color: black; \
									 font: 16pt; margin 1px; border: 2px solid rgb(0, 122, 122); \
									 border-radius: 5px; }'
		self.CSS_disabled = "QLineEdit {color: 	#F8DE7E; background-color: grey; \
									 font: 16pt; margin 1px; border: 2px solid rgb(0, 122, 122); \
									 border-radius: 5px; }"


	
	def createFocusLineEdit(self):
		self.textbox = QLineEdit()
		self.textbox.setStyleSheet(self.CSS)
		self.textbox.setFixedSize(250, 75)
		self.textbox.setValidator((QDoubleValidator()))
		if self.name ==  "Set Point":
			self.textbox.installEventFilter(self)


	def eventFilter(self, watched, event):
		if watched == self.textbox:
			if event.type()==QEvent.MouseButtonPress:
				if len(self.textbox.text())>1 and self.textbox.text()[-1] == "K":
					self.textbox.setText(self.textbox.text()[:-1])
			elif event.type()==QEvent.FocusOut:
				if len(self.textbox.text())>1 and self.textbox.text()[-1] != "K":
					self.textbox.setText(self.textbox.text()+"K")

		return QWidget.eventFilter(self, watched, event)

	def createSmallFocusLineEdit(self):
		self.textbox = QLineEdit()
		self.textbox.setStyleSheet(self.CSS)
		self.textbox.setFixedSize(100, 75)
		self.textbox.setValidator((QDoubleValidator()))

	def getFocusLineEdit(self):
		return self.textbox

	def getSmallFocusLineEdit(self):
		return self.textbox

	def disabled(self):
		self.textbox.setEnabled(False)
		self.textbox.setStyleSheet(self.CSS_disabled)	

	def enabled(self):
		self.textbox.setEnabled(True)
		self.textbox.setStyleSheet(self.CSS)


# Thread
class panelThread(QObject):

	signal = pyqtSignal(list)
	ended = pyqtSignal()

	def __init__(self, parent=None):
		QObject.__init__(self)
		self.run = False
		self.connected()

	def connected(self, connect = False):
		self.connect = connect

	def itc(self, tc):
		self.tc = tc

	def selectDevice(self, devices, measure):
		self.devices = devices
		self.measure = measure

	def pause(self):
		self.run = False

	def resume(self):
		self.run = True

	@pyqtSlot()
	def monitorValues(self):
		time.sleep(1)
		secondary_refresh = 0
		meter_refresh = 0
		gas_set = 0
		while self.run:
			if self.connect:
				for device in self.devices:
					if self.devices[device][1] == 'primary':
						self.signal.emit(self.tc.getSignal(device, self.measure[device]))
						self.tc.close()
						self.tc.open()
						if meter_refresh == 1 and self.devices[device][0].split('.')[1] == 'V':
							self.signal.emit(self.tc.getHeaterPowerRatio(device))
							self.tc.close()
							self.tc.open()
					else:
						if secondary_refresh == 0:
							self.signal.emit(self.tc.getSignal(device, self.measure[device]))
							self.tc.close()
							self.tc.open()
						elif meter_refresh == 1 and self.devices[device][0].split('.')[1] == 'V':
							self.signal.emit(self.tc.getHeaterPowerRatio(device))
							self.tc.close()
							self.tc.open()
			else:
				for device in self.devices:
					self.signal.emit([device, "N/A"])
					self.signal.emit([device, 0.0])
				break
			if self.devices["DB4"][1] == "primary":
				gas_set +=1 
				if gas_set == 10:
					self.devices["DB4"][1] = "secondary"
					gas_set = 0

			secondary_refresh += 1
			meter_refresh += 1

			if secondary_refresh > 3:
				secondary_refresh = 0
			if meter_refresh > 3:
				meter_refresh = 0

			time.sleep(1)
		self.ended.emit()

class heaterThread(QObject):
	signal = pyqtSignal(list)
	volt_value = pyqtSignal(list)
	res_value = pyqtSignal(list)
	ended = pyqtSignal()

	def __init__(self, parent=None):
		QObject.__init__(self)
		self.run = False
		self.connected()

	def connected(self, connect = False):
		self.connect = connect

	def itc(self, tc):
		self.tc = tc

	def selectDevice(self, devices):
		self.devices = devices

	def pause(self):
		self.run = False

	def resume(self):
		self.run = True

	@pyqtSlot()
	def monitorValues(self):
		if self.connect and self.devices:
			for device in self.devices:
				self.volt_value.emit(self.tc.getMaxVoltage(device))
				self.openAndclose()
				self.res_value.emit(self.tc.getResistance(device))
				self.openAndclose()


		while self.run:
			if self.connect:
				for device in self.devices:
					self.signal.emit(self.tc.getHeaterPowerRatio(device))
					self.tc.close()
					time.sleep(1)
					self.tc.open()
			else:
				for device in self.devices:
					self.signal.emit([device, 0.0])
				break
			time.sleep(3)
		self.ended.emit()

	def openAndclose(self):
		if self.connect:
			self.tc.close()
			self.tc.open()

class controlThread(QObject):
	value = pyqtSignal(list)
	ended = pyqtSignal()

	def __init__(self, parent=None):
		QObject.__init__(self)
		self.run = False
		self.connected()

	def connected(self, connect = False):
		self.connect = connect

	def itc(self, tc=None):
		self.tc = tc

	def selectDevice(self, device):
		self.device = device

	def pause(self):
		self.run = False

	def resume(self):
		self.run = True

	def getSetPointUpdate(self, target):
		while True:
			self.current_set_point = self.tc.getSetPoint(self.device)
			if self.current_set_point == target:
				break
			time.sleep(1)

	@pyqtSlot()
	def getValues(self):
		if self.connect and self.run:
			self.askValues(self.tc.getHeater)
			self.askValues(self.tc.getFlow)
			self.askValues(self.tc.getSetPoint)
			self.askValues(self.tc.getP)
			self.askValues(self.tc.getI)
			self.askValues(self.tc.getD)

		self.pause()
		self.ended.emit()

	@pyqtSlot()
	def askValues(self, getMethod=None):
		if self.connect:
			for i in range(5):
				try:
					self.temp = getMethod(self.device)
					# if self.temp[0] == "Set Point":
					# 	float(self.temp[1][:-1])
					# else:
					# 	float(self.temp[1])
					self.value.emit(self.temp)
					break
				except:
					self.openAndclose()
			self.openAndclose()

	def openAndclose(self):
		if self.connect:
			self.tc.close()
			self.tc.open()


class writerThread(QObject):
	write = pyqtSignal(str)

	def __init__(self, parent=None):
		QObject.__init__(self)
		self.run = False
		self.connected()

	def connected(self, connect = False):
		self.connect = connect

	def itc(self, tc):
		self.tc = tc

	def setHeater(self, value, device=None):
		if value < 0.0 or value > 100.0:
			self.write.emit("heater percentage must be 0-100")
		else:
			if self.connect and device:
				self.tryWrite(self.tc.setHeater, device, "heater %", value)
			else:
				self.write.emit("ITC not connected")

	def setFlow(self, value, device=None):
		if value < 0.0 or value > 100.0:
			self.write.emit("flow percentage must be 0-100")
		else:
			if self.connect and device:
				self.tryWrite(self.tc.setFlow, device, "flow %", value)
			else:
				self.write.emit("ITC not connected")

	def setSetPoint(self, value, device=None):
		if value < 0.0 or value > 2000.0:
			self.write.emit("set point must be 0-2000")
		else:
			if self.connect and device:
				self.tryWrite(self.tc.setSetPoint, device, "set point", value)
			else:
				self.write.emit("ITC not connected")

	def setP(self, value, device=None):
		if self.connect and device:
			self.tryWrite(self.tc.setP, device, "P value", value)
		else:
			self.write.emit("ITC not connected")

	def setI(self, value, device=None):
		if self.connect and device:
			self.tryWrite(self.tc.setI, device, "I value", value)
		else:
			self.write.emit("ITC not connected")

	def setD(self, value, device=None):
		if self.connect and device:
			self.tryWrite(self.tc.setD, device, "D value", value)
		else:
			self.write.emit("ITC not connected")

	def setHeaterSetting(self, device=None):
		if self.connect and device:
			pass
		else:
			self.write.emit("ITC not connected")

	def setFlowSetting(self, setting, device=None):
		if self.connect and device:
			if setting == "OFF":
				text = "flow control disabled"
			else:
				text = "flow control enabled"
			self.tryWrite(self.tc.setFlowSetting, device, text, setting)
		else:
			self.write.emit("ITC not connected")

	def setSetPointSetting(self, setting, device=None):
		if self.connect and device:
			if setting == "OFF":
				text = "set point control disabled"
			else:
				text = "set point control enabled"
			self.tryWrite(self.tc.setSetPointSetting, device, text, setting)
		else:
			self.write.emit("ITC not connected")

	def setPIDSetting(self, setting, device=None):
		if self.connect and device:
			if setting == "OFF":
				text = "PID control disabled"
			else:
				text = "PID control enabled"
			self.tryWrite(self.tc.setPIDSetting, device, text, setting)
		else:
			self.write.emit("ITC not connected")

	def setMaxVoltage(self, value, device=None):
		if self.connect and device:
			self.tryWrite(self.tc.setMaxVoltage, device, "max voltage", value)
		else:
			self.write.emit("ITC not connected")

	def setResistance(self, value, device=None):
		if self.connect and device:
			self.tryWrite(self.tc.setResistance, device, "resistance", value)
		else:
			self.write.emit("ITC not connected")

	@pyqtSlot()
	def tryWrite(self, setDevice=None, device=None, text=None, value=None):
		if self.connect and device:
			for i in range(5):
				try:
					if setDevice(value, device) == "VALID":
						self.write.emit(text + " write succeeded")
						break
					else:
						raise ValueError
				except:
					self.write.emit(text + " write failed")
				self.openAndclose()
		else:
			if not self.connect:
				self.write.emit("ITC not connected")


	def openAndclose(self):
		if self.connect:
			self.tc.close()
			# time.sleep(2)  	
			self.tc.open()


class controlUIWindow(QWidget):

	home_clicked = pyqtSignal()
	sweeptable_clicked = pyqtSignal()

	def __init__(self, parent=None):
		super(controlUIWindow, self).__init__(parent=parent)
		self.parent = parent
		self.temp_heater_pair = devices.temp_heater_pair
		self.controls = devices.controls

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
		self.main_title.setStyleSheet('color: white ; font: 10pt ; \
									   text-decoration: underline; border: 1px ;')

		self.control_labels = {'sensor' : QLabel('Sensor'), 'heat' : QLabel('Heat(%)'), \
							   'flow' : QLabel('Flow(%)'), 'set point' : QLabel('Set Point') }

		for labels in self.control_labels:
			self.control_labels[labels].setStyleSheet('color: white; font: 24px; text-align: center; border: 0px')
			self.control_labels[labels].setFixedWidth(130)
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

		self.sensor_setting = {}
		self.sensor_labels = {}
		self.sensor_textbox = {}

		self.sensorConfig()
		self.pidConfig()
		self.heatConfig()
		self.flowConfig()
		self.optionButtons()
		self.setpointConfig()
		self.createThreading()

	def sensorConfig(self):
		self.device_selection = QComboBox(self)
		for device, name, in self.parent.sensor_name.items():
			if self.parent.sensor_name[device][0].split(".")[1] == "T":
				self.device_selection.addItem(self.parent.sensor_name[device][0])
				if name[1] == "primary":
					self.primary_device = self.parent.devices[device]
		self.device_selection.setStyleSheet('color: white; background-color : black; \
											 border-radius : 5px; font: 24px; \
											 border:2px solid rgb(0, 122, 122)')
		self.device_selection.setFixedWidth(460)
		self.device_selection.setFixedHeight(75)
		self.device_selection.view().setFixedWidth(460)
		self.device_selection.activated[str].connect(self.primaryTempSensor)

		self.sensor_row.addWidget(self.device_selection)
		self.sensor_row.addSpacing(50)


	def primaryTempSensor(self, sensor):
		self.primary_device = self.temp_heater_pair[sensor][1]
		for device, name in self.parent.sensor_name.items():
			if device in self.primary_device:
				self.parent.sensor_name[device][1] = "primary"
				self.parent.sensor_name[self.temp_heater_pair[sensor][0]][1] = 'primary'
			elif name[0].split(".")[1] == "T":
				self.parent.sensor_name[device][1] = "secondary"
				self.parent.sensor_name[self.temp_heater_pair[sensor][0]][1] = 'secondary'
		self.startThread()


	def heatConfig(self):
		self.createPushButton("Heat")
		self.heat_row.addWidget(self.sensor_setting["Heat"])
		self.createInputBox("Heat")
		self.heat_row.addWidget(self.sensor_textbox["Heat"].getFocusLineEdit())
		self.heat_row.addWidget(self.sensor_labels["P"])
		self.createInputBox("P")
		self.heat_row.addWidget(self.sensor_textbox["P"].getFocusLineEdit())
		self.sensor_textbox["Heat"].getFocusLineEdit().returnPressed.connect(lambda: self.setHeater(self.primary_device, self.sensor_textbox["Heat"].getFocusLineEdit().text()))
		self.sensor_setting["Heat"].clicked.connect(lambda: self.setHeaterSetting(self.primary_device, self.sensor_setting["Heat"].text(), "Heat"))
		self.sensor_textbox["P"].getFocusLineEdit().returnPressed.connect(lambda: self.setP(self.primary_device, self.sensor_textbox["P"].getFocusLineEdit().text()))


	def flowConfig(self):
		self.createPushButton("Flow")
		self.flow_row.addWidget(self.sensor_setting["Flow"])
		self.createInputBox("Flow")
		self.flow_row.addWidget(self.sensor_textbox["Flow"].getFocusLineEdit())
		self.flow_row.addWidget(self.sensor_labels["I"])
		self.createInputBox("I")
		self.flow_row.addWidget(self.sensor_textbox["I"].getFocusLineEdit())
		self.sensor_textbox["Flow"].getFocusLineEdit().returnPressed.connect(lambda: self.setFlow(self.primary_device, self.sensor_textbox["Flow"].getFocusLineEdit().text()))
		self.sensor_setting["Flow"].clicked.connect(lambda: self.setFlowSetting(self.primary_device, self.sensor_setting["Flow"].text(), "Flow"))
		self.sensor_textbox["I"].getFocusLineEdit().returnPressed.connect(lambda: self.setI(self.primary_device, self.sensor_textbox["I"].getFocusLineEdit().text()))


	def setpointConfig(self):
		self.createPushButton("Set Point")
		self.setpoint_row.addWidget(self.sensor_setting["Set Point"])
		self.createInputBox("Set Point")
		self.setpoint_row.addWidget(self.sensor_textbox["Set Point"].getFocusLineEdit())
		self.setpoint_row.addWidget(self.sensor_labels["D"])
		self.createInputBox("D")
		self.setpoint_row.addWidget(self.sensor_textbox["D"].getFocusLineEdit())
		self.sensor_textbox["Set Point"].getFocusLineEdit().returnPressed.connect(lambda: self.setSetPoint(self.primary_device, self.sensor_textbox["Set Point"].getFocusLineEdit().text()))
		self.sensor_textbox["Set Point"].getFocusLineEdit().mousePressEvent = lambda _ : self.sensor_textbox["Set Point"].getFocusLineEdit().selectAll()

		self.sensor_setting["Set Point"].clicked.connect(lambda: self.setSetPointSetting(self.primary_device, self.sensor_setting["Set Point"].text(), "Set Point"))
		self.sensor_textbox["D"].getFocusLineEdit().returnPressed.connect(lambda: self.setD(self.primary_device, self.sensor_textbox["D"].getFocusLineEdit().text()))


	def pidConfig(self):
		self.createPIDLabels('PID (H)')
		self.sensor_row.addWidget(self.sensor_labels['PID (H)'])
		self.createPushButton('PID')
		self.sensor_row.addWidget(self.sensor_setting['PID'])
		self.sensor_setting["PID"].clicked.connect(lambda: self.setPIDSetting(self.primary_device, self.sensor_setting["PID"].text(), "PID"))
		self.createPIDLabels('P')
		self.createPIDLabels('I')
		self.createPIDLabels('D')

	def setHeater(self, device, text):
		self.parent.write.setHeater(float(text), device)

	def setFlow(self, device, text):
		self.parent.write.setFlow(float(text), device)
		self.parent.sensor_name["DB4"][1] = "primary"

	def setSetPoint(self, device, text):
		self.parent.write.setSetPoint(float(text), device)
		# self.sensor_textbox["Set Point"].getFocusLineEdit().setText(self.sensor_textbox["Set Point"].getFocusLineEdit().text())

	def setP(self, device, value):
		self.parent.write.setP(value, device)

	def setI(self, device, value):
		self.parent.write.setI(value, device)

	def setD(self, device, value):
		self.parent.write.setD(value, device)

	def setHeaterSetting(self, device, setting, name):
		if setting == "Manual":
			self.sensor_textbox[name].enabled()
			self.sensor_setting["Set Point"].setDisabled(True)
			self.sensor_setting["Set Point"].setText("Fixed")
			self.sensor_setting["Set Point"].setStyleSheet('color: #F5F5F5; background-color: grey; font: 14pt; \
															margin 1px; border: 2px solid rgb(0, 122, 122); \
														 	border-radius: 5px; ')
			self.sensor_textbox["Set Point"].enabled()
			self.parent.write.setSetPointSetting("OFF", device)
		else:
			self.sensor_textbox[name].disabled()
			self.sensor_setting["Set Point"].setDisabled(False)
			self.sensor_setting["Set Point"].setStyleSheet('color: white; background-color: blue; font: 14pt; \
															margin 1px; border: 2px solid rgb(0, 122, 122); \
														 	border-radius: 5px; ')

	def setFlowSetting(self, device, setting, name):
		if setting == "Manual":
			self.sensor_textbox[name].enabled()
			self.parent.write.setFlowSetting("OFF", device)
		else:
			self.sensor_textbox[name].disabled()
			self.parent.write.setFlowSetting("ON", device)

	def setSetPointSetting(self, device, setting, name):
		if setting == "Fixed":
			self.sensor_textbox[name].enabled()
			self.parent.write.setSetPointSetting("OFF", device)
		else:
			self.sensor_textbox[name].disabled()
			self.parent.write.setSetPointSetting("ON", device)
			self.startThread()


	def setPIDSetting(self, device, setting, name):
		if setting == "Manual":
			self.sensor_textbox["P"].enabled()
			self.sensor_textbox["I"].enabled()
			self.sensor_textbox["D"].enabled()
			self.options_buttons["PID table"].enabled()
			self.parent.write.setPIDSetting("OFF", device)
		else:
			self.sensor_textbox["P"].disabled()
			self.sensor_textbox["I"].disabled()
			self.sensor_textbox["D"].disabled()
			self.options_buttons["PID table"].disabled()			
			self.parent.write.setPIDSetting("ON", device)

	def createPIDLabels(self, text):
		self.sensor_labels[text] = QLabel(text)
		self.sensor_labels[text].setStyleSheet('color: white; border: 0px; font: 24px; text-align: right')
		self.sensor_labels[text].setFixedWidth(80)
		self.sensor_labels[text].setFixedHeight(75)
		self.sensor_labels[text].setAlignment(Qt.AlignVCenter | Qt.AlignRight)


	def createPushButton(self, text):
		if text == 'Set Point':
			self.sensor_setting[text] = QPushButton('Fixed')
			self.sensor_setting["Set Point"].setStyleSheet('color: #F5F5F5; background-color: grey; font: 14pt; \
															margin 1px; border: 2px solid rgb(0, 122, 122); \
														 	border-radius: 5px; ')
			self.sensor_setting["Set Point"].setDisabled(True)
		else:
			self.sensor_setting[text] = QPushButton('Manual')
			self.sensor_setting[text].setStyleSheet('color: white; background-color: blue; font: 14pt; \
												 margin 1px; border: 2px solid rgb(0, 122, 122);   \
												 border-radius: 5px; ')
		self.sensor_setting[text].setFixedSize(200, 75)
		self.sensor_setting[text].clicked.connect(lambda: self.updatePushButton(text))

	def updatePushButton(self, text):
		if text == 'Set Point':
			if self.sensor_setting[text].text() == "Fixed":
				self.sensor_setting[text].setText("Auto")
				self.sensor_setting[text].setStyleSheet('color: white; background-color: orange; \
														 font: 14pt; margin 1px; border: 2px solid rgb(0, 122, 122); \
														 border-radius: 5px; ')
			else:
				self.sensor_setting[text].setText("Fixed")
				self.sensor_setting[text].setStyleSheet('color: white; background-color: blue; \
														 font: 14pt; margin 1px; border: 2px solid rgb(0, 122, 122); \
														 border-radius: 5px; ')
		else:
			if self.sensor_setting[text].text() == "Manual":
				self.sensor_setting[text].setText("Auto")
				self.sensor_setting[text].setStyleSheet('color: white; background-color: orange; \
														 font: 14pt; margin 1px; border: 2px solid rgb(0, 122, 122); \
														 border-radius: 5px; ')

			else:
				self.sensor_setting[text].setText('Manual')
				self.sensor_setting[text].setStyleSheet('color: white; background-color: blue; \
														 font: 14pt; margin 1px; border: 2px solid rgb(0, 122, 122); \
														 border-radius: 5px; ')


	def createInputBox(self, device):
		self.sensor_textbox[device] = focusLineEdit(device)
		self.sensor_textbox[device].createFocusLineEdit()

	@pyqtSlot(list)
	def getValues(self, value):
		self.sensor_textbox[value[0]].getFocusLineEdit().setText(value[1])


	def optionButtons(self):
		self.options_buttons = { "Home" : hoverPushButton("Home"), 
								 "Sweep table" : hoverPushButton("Sweep table"), 
								 "Gas Cfg" : hoverPushButton("Gas Cfg"), 
								 "PID table" : hoverPushButton("PID table") }

		for option in self.options_buttons:
			self.options_row.addWidget(self.options_buttons[option].getHoverButton())
			self.options_buttons[option].getHoverButton().clicked.connect(self.pauseThread)

		self.options_buttons["Home"].getHoverButton().clicked.connect(self.home_clicked.emit)
		self.options_buttons["Home"].getHoverButton().clicked.connect(self.resumeHomeDisplay)
		self.options_buttons["Sweep table"].getHoverButton().clicked.connect(self.sweeptable_clicked.emit)

	def resumeHomeDisplay(self):
		self.parent.sensor_display.startThread()

	def pauseThread(self):
		self.text.pause()

	def startThread(self):
		self.text.connected(self.parent.valid_connection)
		self.text.itc(self.parent.tc)
		self.text.selectDevice(self.primary_device)
		self.text.resume()
		self.thread.start()

	def createThreading(self):
		self.text = controlThread(self)
		self.thread = QThread(self)
		self.connectThreading()

	def connectThreading(self):
		self.text.itc(self.parent.tc)
		self.text.selectDevice(self.primary_device)
		self.text.connected(self.parent.valid_connection)
		self.text.moveToThread(self.thread)
		self.thread.started.connect(self.text.getValues)
		self.thread.started.connect(self.text.askValues)
		self.text.value.connect(self.getValues)
		self.text.ended.connect(self.thread.quit)

class heaterUIWindow(QWidget):

	home_clicked = pyqtSignal()
	control_clicked = pyqtSignal()

	def __init__(self, parent=None):
		super(heaterUIWindow, self).__init__(parent=parent)
		self.parent = parent
		self.devices = devices.devices
		self.sensor_name = devices.sensor_name
		# layouts
		self.heaterOptionUI()


	def heaterOptionUI(self):

		self.background_layout = QVBoxLayout()
		self.input_layout = QHBoxLayout()
		self.options_layout = QHBoxLayout()

		self.background_layout.addLayout(self.input_layout)
		self.background_layout.addLayout(self.options_layout)

		self.heater_col = QVBoxLayout()
		self.name_col = QVBoxLayout()
		self.volt_col = QVBoxLayout()
		self.res_col = QVBoxLayout()
		self.power_col = QVBoxLayout()

		self.input_layout.addLayout(self.heater_col)
		self.input_layout.addLayout(self.name_col)
		self.input_layout.addLayout(self.volt_col)
		self.input_layout.addLayout(self.res_col)
		self.input_layout.addLayout(self.power_col)
		
		self.setLayout(self.background_layout)

		self.createHeaterTitles()
		self.optionButtons()

		self.heater_col.addStretch(2)
		self.name_col.addStretch(2)
		self.volt_col.addStretch(2)
		self.res_col.addStretch(2)
		self.power_col.addStretch(2)


	def createHeaterTitles(self):
		self.heater_titles = {
							'heater' : QLabel('Heater #'),
							'name' : QLabel('Name'),
							'voltlim' : QLabel('Lim(V)'), 
							'res' : QLabel('Res(\u03A9)'),
							'power' : QLabel('P(W)') }

		for title in self.heater_titles:
			self.heater_titles[title].setStyleSheet('color: white ; font: 12pt; text-decoration: underline; border: 0px ;')
			if title == 'heater':
				self.heater_titles[title].setAlignment(Qt.AlignCenter)

		self.heater_col.addWidget(self.heater_titles['heater'])
		self.name_col.addWidget(self.heater_titles['name'])
		self.volt_col.addWidget(self.heater_titles['voltlim'])
		self.res_col.addWidget(self.heater_titles['res'])
		self.power_col.addWidget(self.heater_titles['power'])

		self.createHeaterLabels()
		self.createDeviceInputs()
		self.createMaxVoltInputs()
		self.createResInputs()
		self.createMeterBar()
		self.createThreading()


	def createHeaterLabels(self):
		self.heater_names = {"DB1" : QLabel("DB1.H1"), "MB0" : QLabel('MB0.H1')}

		for name in self.heater_names:
			self.heater_names[name].setStyleSheet('color: white; border: 0px; font: 24px')
			self.heater_names[name].setFixedWidth(130)
			self.heater_names[name].setFixedHeight(75)
			self.heater_names[name].setAlignment(Qt.AlignCenter)
			self.heater_col.addWidget(self.heater_names[name])

	def createDeviceInputs(self):
		self.device_inputs = {}
		for device, names in devices.sensor_name.items():
			if names[0].split('.')[1] == 'V':
				self.device_input = focusLineEdit(self.devices[device])
				self.device_input.createFocusLineEdit()
				self.device_inputs[self.devices[device]] = self.device_input.getFocusLineEdit()
				self.device_inputs[self.devices[device]].setText(self.sensor_name[device][0].split(".")[0])
				self.name_col.addWidget(self.device_inputs[self.devices[device]])

	def createMaxVoltInputs(self):
		self.voltlim_inputs = {}
		for device in self.device_inputs:
				self.voltlim_input = focusLineEdit(device)
				self.voltlim_input.createSmallFocusLineEdit()
				self.voltlim_inputs[device] = self.voltlim_input.getSmallFocusLineEdit()
				self.voltlim_inputs[device].returnPressed.connect(lambda: self.updateMaxVoltage(device, self.voltlim_inputs[device].text()))
				self.volt_col.addWidget(self.voltlim_inputs[device])

	def createResInputs(self):
		self.res_inputs = {}
		for device in self.device_inputs:
				self.res_input = focusLineEdit(device)
				self.res_input.createSmallFocusLineEdit()
				self.res_inputs[device] = self.res_input.getSmallFocusLineEdit()
				self.res_inputs[device].returnPressed.connect(lambda: self.updateResistance(device, self.voltlim_inputs[device].text()))
				self.res_col.addWidget(self.res_inputs[device])


	def updateMaxVoltage(self, device, value):
		self.parent.write.setMaxVoltage(value, device)

	def updateResistance(self, device, value):
		self.parent.write.setResistance(value, device)

	def createMeterBar(self):
		self.meter_reading = {}
		CSS_1 = "QProgressBar {color : white; font : bold; text-align : center; border-radius : 5px; \
							   border: 2px solid rgb(0, 122, 122); }"
		for device, names in devices.sensor_name.items():
			if names[0].split('.')[1] == 'V':
				self.meter_reading[device] = QProgressBar(self)
				self.meter_reading[device].setFixedSize(200, 25)
				if device == 'DB1':
					CSS_2 = "QProgressBar::chunk {background-color: #05B8CC; width: 10px; margin: 1.2px; }"
				else:
					CSS_2 = "QProgressBar::chunk {background-color: #CD96CD; width: 10px; margin: 1.2px; }"
				
				self.meter_reading[device].setStyleSheet(CSS_1+CSS_2)
				self.meter_reading[device].setValue(0.0)

				self.power_col.addWidget(self.meter_reading[device])


	@pyqtSlot(list)
	def updateMeterbar(self, reading):
		self.meter_reading[reading[0]].setValue(reading[1])

	@pyqtSlot(list)
	def updateVoltReading(self, reading):
		self.voltlim_inputs[reading[0]].setText(reading[1])

	@pyqtSlot(list)
	def updateResReading(self, reading):
		self.res_inputs[reading[0]].setText(reading[1])

	def optionButtons(self):
		self.createThreading()

		self.options_buttons = [ hoverPushButton("Home"), 
								 hoverPushButton("Control"), 
								 hoverPushButton("Calibrate") ]

		for option in self.options_buttons:
			if option == 'Calibrate':
				self.options_layout.addStretch(1)
			self.options_layout.addWidget(option.getHoverButton())
			option.getHoverButton().clicked.connect(self.pauseThread)

		self.options_buttons[0].getHoverButton().clicked.connect(self.home_clicked.emit)
		self.options_buttons[0].getHoverButton().clicked.connect(self.resumeHomeDisplay)

		self.options_buttons[1].getHoverButton().clicked.connect(self.control_clicked.emit)
		self.options_buttons[1].getHoverButton().clicked.connect(self.resumeControlDisplay)

	def pauseThread(self):
		self.meter.pause()

	def startThread(self):
		self.meter.connected(self.parent.valid_connection)
		self.meter.itc(self.parent.tc)
		self.meter.resume()
		self.thread.start()

	def resumeHomeDisplay(self):
		self.parent.sensor_display.startThread()

	def resumeControlDisplay(self):
		self.parent.control_display.startThread()

	def createThreading(self):
		self.meter = heaterThread(self)
		self.thread = QThread(self)
		self.connectThreading()

	def connectThreading(self):
		self.meter.itc(self.parent.tc)
		self.meter.selectDevice(list(self.heater_names.keys()))
		self.meter.connected(self.parent.valid_connection)
		self.meter.moveToThread(self.thread)
		self.thread.started.connect(self.meter.monitorValues)
		self.meter.signal.connect(self.updateMeterbar)
		self.meter.volt_value.connect(self.updateVoltReading)
		self.meter.res_value.connect(self.updateResReading)
		self.meter.ended.connect(self.thread.quit)


class sweepTableUIWindow(QWidget):

	control_clicked = pyqtSignal()

	def __init__(self, parent=None):
		super(sweepTableUIWindow, self).__init__(parent=parent)
		self.parent = parent
		# self.devices = devices.devices
		# self.sensor_name = devices.sensor_name
		# layouts
		self.sweepTableUI()


	def sweepTableUI(self):

		self.background_layout = QVBoxLayout()
		self.title_layout = QHBoxLayout()
		self.input_layout = QHBoxLayout()
		self.options_layout = QHBoxLayout()

		self.background_layout.addLayout(self.title_layout)
		self.background_layout.addLayout(self.input_layout)
		self.background_layout.addLayout(self.options_layout)
		
		self.setLayout(self.background_layout)

		self.createSweepTitles()
		self.createInputs()
		self.optionButtons()


	def createSweepTitles(self):
		self.sweep_titles = {
							'Sweep Table' : QLabel('Sweep Table'),
							'VTI' : QLabel('VTI') }

		for title in self.sweep_titles:
			self.sweep_titles[title].setStyleSheet('color: white ; font: 12pt; \
													text-decoration: underline; \
													border: 0px ;')
			self.title_layout.addWidget(self.sweep_titles[title])
			self.title_layout.addStretch(1)

	def createInputs(self):
		temp_layout = [QVBoxLayout(), QVBoxLayout(), QVBoxLayout()] 

		for layout in temp_layout:
			self.input_layout.addLayout(layout)
		temp_layout[0].addWidget(self.sweepLabels("FinalT (K)"))
		temp_layout[1].addWidget(self.sweepLabels("Time to final T (mins)"))
		temp_layout[2].addWidget(self.sweepLabels("Hold at final T (mins)"))

		self.tempT = focusLineEdit()
		self.tempT.createFocusLineEdit()
		self.timeT = focusLineEdit()
		self.timeT.createFocusLineEdit()
		self.finalT = focusLineEdit()
		self.finalT.createFocusLineEdit()


		temp_layout[0].addWidget(self.tempT.getFocusLineEdit())
		temp_layout[1].addWidget(self.timeT.getFocusLineEdit())
		temp_layout[2].addWidget(self.finalT.getFocusLineEdit())

	def sweepLabels(self, label):
		self.label = QLabel(label)
		self.label.setStyleSheet('color: white; background-color: blue; font: 14pt; \
								  margin 1px; border: 2px solid rgb(0, 122, 122); \
								  border-radius: 5px; ')
		return self.label

	def optionButtons(self):
		# self.createThreading()

		self.option_button = hoverPushButton("Back")
		self.options_layout.addWidget(self.option_button.getHoverButton())
		# self.option_button.getHoverButton().clicked.connect(self.pauseThread)

		self.option_button.getHoverButton().clicked.connect(self.control_clicked.emit)
		self.option_button.getHoverButton().clicked.connect(self.resumeControlDisplay)

	def resumeControlDisplay(self):
		self.parent.control_display.startThread()


	#	TODO matt is cool 
	'''
	implement PID table and sweep table
	update control textboxes when new value is entered
	update setpoint when auto is enabled until value is reached
	set up power value in watts on heater page
	handle DB4 update to primary
	'''

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()

    window.resize(900, 500)
    window.show()

    sys.exit(app.exec_())

