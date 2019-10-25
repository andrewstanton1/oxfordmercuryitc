# from PyQt5.QtWidgets import *
# from PyQt5.QtCore import *
# from PyQt5.QtGui import *

# # Only needed for access to command line arguments
# import sys


# # Subclass QMainWindow to customise your application's main window
# class MainWindow(QMainWindow):

#     def __init__(self, *args, **kwargs):
#         super(MainWindow, self).__init__(*args, **kwargs)
        
#         self.setWindowTitle("My Awesome App")
        

#         layout = QVBoxLayout()
#         widgets = [QCheckBox,
#             QComboBox,
#             QDateEdit,
#             QDateTimeEdit,
#             QDial,
#             QDoubleSpinBox,
#             QFontComboBox,
#             QLCDNumber,
#             QLabel,
#             QLineEdit,
#             QProgressBar,
#             QPushButton,
#             QRadioButton,
#             QSlider,
#             QSpinBox,
#             QTimeEdit]
        
#         for w in widgets:
#             layout.addWidget(w())
            
        
#         widget = QWidget()
#         widget.setLayout(layout)
        
#         # Set the central widget of the Window. Widget will expand
#         # to take up all the space in the window by default.
#         self.setCentralWidget(widget)


# # You need one (and only one) QApplication instance per application.
# # Pass in sys.argv to allow command line arguments for your app.
# # If you know you won't use command line arguments QApplication([]) works too.
# app = QApplication(sys.argv)

# window = MainWindow()
# window.show() # IMPORTANT!!!!! Windows are hidden by default.

# # Start the event loop.
# app.exec_()


# # Your application won't reach here until you exit and the event 
# # loop has stopped.

from PyQt5 import QtWidgets, QtGui, QtCore
import pyowm


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("Tom")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(800, 600)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.Date = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.Date.setFont(font)
        self.Date.setAlignment(QtCore.Qt.AlignCenter)
        self.Date.setObjectName("Date")
        self.verticalLayout.addWidget(self.Date)
        self.Time = QtWidgets.QLabel(self.centralwidget)

        self.verticalLayout.addWidget(self.Time)
        self.Weather = QtWidgets.QLabel(self.centralwidget)
        self.Weather.setAlignment(QtCore.Qt.AlignCenter)
        self.Weather.setWordWrap(False)
        self.Weather.setObjectName("Weather")
        self.verticalLayout.addWidget(self.Weather)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem2)
        spacerItem3 = QtWidgets.QSpacerItem(771, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem3)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem4)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem5)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("Tom", "Tom"))
        self.Date.setText(_translate("Tom", "Today is "))
        self.Time.setText(_translate("Tom", "It is currently "))
        self.Weather.setText(_translate("Tom", "New York City" ))


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)
        self.setupUi(self)
        timerTime = QtCore.QTimer(self)
        timerTime.timeout.connect(self.updateDate)
        timerTime.start(1000)
        self.pyowm = PyownThread(self)
        self.pyowm.tempSignal.connect(self.updateTemp)
        self.pyowm.start()

    def updateDate(self):
        date = QtCore.QDateTime.currentDateTime()
        self.Date.setText("Today is " + date.toString("ddd MMMM d yyyy"))
        self.Time.setText("It is currently " + date.toString("hh:mm:ss ap"))

    def updateTemp(self, temp):
        self.Weather.setText("New York City temperature:" + str(temp['temp']) + " \u00B0C")


class PyownThread(QtCore.QThread):
    tempSignal = QtCore.pyqtSignal(dict)
    def __init__(self, parent=None):
        super(PyownThread, self).__init__(parent=parent)
        self.owm = pyowm.OWM('1589dbcc0e9608e5b70f0ede23e757c8') 

    def run(self):
        while True:
            observation = self.owm.weather_at_place('New York,us')
            w = observation.get_weather()
            ctemp = w.get_temperature('celsius')
            self.tempSignal.emit(ctemp)
            QtCore.QThread.sleep(5*60)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())