import sys
import datetime
import mercuryITC as itc
import serial.tools.list_ports
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QComboBox, QPushButton, QAction, QMenu, QCheckBox, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt

from collections import defaultdict

class MainWindow(QMainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		
		#temperature controller
		self.tc = None

		# layouts
		self.initUI()

		# update
		self.timer = QTimer(self)

		self.createThreading()

		self.timer.start(2000)

		for device in self.devices:
			self.panel[device].start()

	def initUI(self):

		# window layout
		self.setWindowTitle("Mercury ITC controller")
		self.vbox1 = QVBoxLayout()
		self.hbox1 = QHBoxLayout()
		self.layout = QHBoxLayout()
		self.layout.addLayout(self.hbox1)
		self.hbox1.addLayout(self.vbox1)

		# devices
		self.devices = {"MB1" : "DEV:MB1.T1:TEMP", "MB0" : "DEV:MB0.H1:HTR", "DB4" : "DEV:DB4.G1:AUX", "DB6" : "DEV:DB6.T1:TEMP", "DB1" : "DEV:DB1.H1:HTR"}   # secondary
		self.commands = {"MB1": "TEMP", "MB0": "VOLT", "DB4": "PERC", "DB6": "TEMP", "DB1": "VOLT"}

		self.deviceSelection()
		self.vbox1.addStretch(10)

		# ports
		self.selectUSB()

		# front panel readings
		self.hbox2 = QHBoxLayout()
		self.layout.addLayout(self.hbox2)
		self.vbox2 = QVBoxLayout()
		self.vbox3 = QVBoxLayout()
		self.hbox1.addLayout(self.vbox2)
		self.hbox1.addLayout(self.vbox3)

		self.hbox1.addStretch(2)
		self.vbox2.addStretch(5)
		self.vbox3.addStretch(3)
		self.frontPanel()
		self.vbox2.addStretch(5)
		self.vbox3.addStretch(5)
		# self.hbox2.addStretch(1)

		widget = QWidget()
		widget.setLayout(self.layout)
		# widget.setLayout(self.hbox2)
		self.setCentralWidget(widget)

	def deviceSelection(self):
		device_label = QLabel("Devices")
		device_label.setFont(QFont("Ariel", 11))
		self.vbox1.addWidget(device_label)

		self.dev_select = {}

		for device, name in self.devices.items():
			if device ==  'MB1' or device == 'MB0' or device == 'DB4':
				primary_devices = True 
			else:
				primary_devices = False

			self.dev_select[name] = QCheckBox(device, self)
			self.vbox1.addWidget(self.dev_select[name])
			self.dev_select[name].setChecked(primary_devices)
			self.dev_select[name].stateChanged.connect(self.deviceManager)


	def deviceManager(self, device_state):
		if device_state == Qt.Checked:
			if self.sender() == self.dev_select[self.devices['MB1']]:
				self.dev_select[self.devices['DB6']].setChecked(False)
			elif self.sender() == self.dev_select[self.devices['DB6']]:
				self.dev_select[self.devices['MB1']].setChecked(False)

			if self.sender() == self.dev_select[self.devices['MB0']]:
				self.dev_select[self.devices['DB1']].setChecked(False)
			elif self.sender() == self.dev_select[self.devices['DB1']]:
				self.dev_select[self.devices['MB0']].setChecked(False)


	def selectUSB(self):
		menu_bar = self.menuBar()
		port_selection = menu_bar.addMenu("PORTS")
		self.com_port = None

		self.valid_connection = False
		self.statusBar().showMessage("Select PORT")

		self.serial_ports = sorted([comport.device for comport in serial.tools.list_ports.comports()])

		if not self.serial_ports:
			self.statusBar().showMessage("No available ports")

		for ports in self.serial_ports:
			com = QAction(ports, self)
			port_selection.addAction(com)
			port_selection.triggered[QAction].connect(self.portClicked)

	
	def portClicked(self, port):
		
		self.com_port = port.text()

		try:
			self.tc = itc.temperatureController(self.com_port)
			self.statusBar().showMessage("Connected to PORT " + self.com_port)
			self.valid_connection = True
			for device in devices:
				self.connectThreading(device)
		except:
			self.statusBar().showMessage("ITC not connected to PORT " + self.com_port)
			self.valid_connection = False
	

	def frontPanel(self):

		self.device_reading = {}
		self.displayTemp()
		self.displayHeater()
		self.displayGas()


	def displayTemp(self):
		temp_dev1 = QLabel("MB1.T1:TEMP")
		self.device_reading['MB1'] = QLabel("N/A")
		self.formatPanel(temp_dev1, self.device_reading['MB1'])

		temp_dev2 = QLabel("DB6.T1:TEMP")
		self.device_reading['DB6'] = QLabel("N/A")
		self.formatPanel(temp_dev2, self.device_reading['DB6'])


		self.vbox2.addWidget(temp_dev1)
		self.vbox2.addWidget(self.device_reading['MB1'])
		self.vbox3.addWidget(temp_dev2)
		self.vbox3.addWidget(self.device_reading['DB6'])


	def displayHeater(self):
		htr_dev1 = QLabel("MB0.H1:HTR")
		self.device_reading['MB0'] = QLabel("N/A")
		self.formatPanel(htr_dev1, self.device_reading['MB0'])

		htr_dev2 = QLabel("DB1.H1:HTR")
		self.device_reading['DB1'] = QLabel("N/A")
		self.formatPanel(htr_dev2, self.device_reading['DB1'])

		self.vbox2.addWidget(htr_dev1)
		self.vbox2.addWidget(self.device_reading['MB0'])
		self.vbox3.addWidget(htr_dev2)
		self.vbox3.addWidget(self.device_reading['DB1'])


	def displayGas(self):
		gas_dev = QLabel("GAS")
		self.device_reading['DB4'] = QLabel("N/A")
		self.formatPanel(gas_dev, self.device_reading['DB4'])

		self.vbox2.addWidget(gas_dev)
		self.vbox2.addWidget(self.device_reading['DB4'])


	def formatPanel(self, label, reading):
		label.setFont(QFont("Ariel", 10))
		reading.setFont(QFont("Ariel", 10))
		reading.setStyleSheet("background-color: white; border: 1px solid grey; max-width: 150px")

	def createThreading(self):
		self.panel = {}
		for device in self.devices:
			self.panel[device] = panelThread(self)
			self.connectThreading(device)

	def connectThreading(self, device):
			self.panel[device].itc(self.tc)
			self.panel[device].selectDevice(device, self.commands[device])
			self.panel[device].connected(self.valid_connection)
			if self.valid_connection:
				self.panel[device].connect(self.updatePanel)


	def updatePanel(self, value):
		# self.current_time = str(datetime.datetime.now().time())

		if self.valid_connection:
			self.device_reading[value[0]].setText(value[1])
		else:
			for device in devices:
				self.device_reading[device].setText("N/A")
	


# Thread
class panelThread(QThread):
	signal = pyqtSignal(list)

	def __init__(self, parent=None):
		super(panelThread, self).__init__(parent=parent)
		self.connected()


	def connected(self, connect = False):
		self.connect = connect

	def itc(self, tc = None):
		self.tc = tc

	def selectDevice(self, device, measure):
		self.device = device
		self.measure = measure

	def run(self):
		if self.connect:
			while True:
				self.signal.emit(self.tc.getSignal(self.device, self.measure))
		else:
			self.signal.emit(["N/A"])


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(800, 500)
    window.show()

    sys.exit(app.exec_())



