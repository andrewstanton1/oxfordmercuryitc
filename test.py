import mercuryITC as itc 
import pyvisa as visa
import devices

rm = visa.ResourceManager()
# print(rm.list_resources())

tc = itc.TemperatureController('ASRLCOM3::INSTR')
# print(tc.setP(10, "DEV:MB1.T1:TEMP"))
# tc.close()
# tc.open()
# # print(tc.getHeaterPowerRatio('DB1'))
# temp = devices.sensor_name
# temp['DB4'][1] = 'hey'
# print(temp['DB4'])
print(tc.get_max_voltage('DB1'))
# import sys

# from PyQt5.QtGui import *
# from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QGridLayout, QLabel, QLineEdit, QComboBox, QStatusBar, QPushButton, QProgressBar, QAction, QMenu, QCheckBox, QVBoxLayout, QHBoxLayout
# from PyQt5.QtCore import QObject, QTimer, QThread, pyqtSignal, pyqtSlot, Qt

# class App(QMainWindow):

# 	def __init__(self):
# 	    super().__init__()
# 	    self.initUI()


# 	def initUI(self):

# 	    label = QLabel('Python', self)
# 	    label.move(50,50)
# 	    self.show()

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     ex = App()
#     sys.exit(app.exec_())

# from collections import defaultdict

# sensor_name = defaultdict(list)
# sensor_name["MB1"] = ["VTI_Hx_MB1.T", "primary"]
# sensor_name["DB6"] = ["VTI_SR_DB6.T", "secondary"]
# sensor_name["DB4"] = ["DB4.G1.%", "primary"]
# sensor_name["MB0"] = ["Hx_htr_MB0.V", "secondary"]
# sensor_name["DB1"] = ["SR_htr_DB1.V", "primary"]


# if "MB1" in sensor_name["DB6"][0]:
# 	print("Yes")