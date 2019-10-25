import pyvisa as visa
import time
import sys
import serial


class temperatureController:
    def __init__(self, port, baudrate=115200):
        try:
            rm = visa.ResourceManager()
            self.ser = rm.open_resource(port)
            time.sleep(1)
            self.defineDevices()
            self.ratio = 0.0
        except: errors.VisaIOError

    def defineDevices(self):
        # store the device addresses in a dictionary
        self.devices = {
            "MB1": "DEV:MB1.T1:TEMP",
            "MB0": "DEV:MB0.H1:HTR",
            "DB4": "DEV:DB4.G1:AUX",  # main
            "DB6": "DEV:DB6.T1:TEMP",
            "DB1": "DEV:DB1.H1:HTR",
        }  # secondary

    def getVersion(self):
        string = self.readValue("*IDN?", readPrefix="")
        return string

    def getDevices(self):
        devices = self.readValue("SYS:CAT")

    def writeValue(self, value):
        self.ser.write((value + "\n\r"))

    def readValue(self, value, readPrefix="READ:"):
        self.writeValue(readPrefix + value)
        string = str(self.ser.read_raw()).split(":")[-1][:-3]
        return string

    def setValue(self, value):
        self.writeValue("SET:" + value)
        string = str(self.ser.read_raw()).split(":")[-1][:-3]
        return string

    def open(self):
        try:
            self.ser.open()
        except: serial.serialutil.SerialException

    def close(self):
        try:
            self.ser.close()
        except: SerialException

    def getSignal(self, device, signal):
        ans = self.readValue(self.devices[device] + ":SIG:" + signal)  # .decode().split(":")[-1]
        return [device, ans]

    def getMaxVoltage(self, device):
        try:
            self.max_voltage = float(self.readValue(self.devices[device] + ":VLIM"))
        except:
            return [self.devices[device], "0.0"]

        return [self.devices[device], str(self.max_voltage)]

    def getResistance(self, device):
        try:
            self.resistance = float(self.readValue(self.devices[device] + ":RES"))
        except:
            return [self.devices[device], "0.0"]

        return [self.devices[device], str(self.resistance)]

    def getHeaterPowerRatio(self, device):
        try:
            voltage = float(self.getSignal(device, "VOLT")[1][:-1])
            self.close()
            self.open()
            max_voltage = float(self.getMaxVoltage(device)[1])
            self.ratio = 100.0 * (voltage / max_voltage) ** 2
        except:
            self.ratio = self.ratio

        return [device, self.ratio]

    def getHeater(self, device):
        return ["Heat", self.readValue(device + ":LOOP:HSET")]

    def getFlow(self, device):
        return ["Flow", self.readValue(device + ":LOOP:FSET")]

    def getSetPoint(self, device):
        return ["Set Point", self.readValue(device + ":LOOP:TSET")]

    def getP(self, device):
        return ["P", self.readValue(device + ":LOOP:P")]

    def getI(self, device):
        return ["I", self.readValue(device + ":LOOP:I")]

    def getD(self, device):
        return ["D", self.readValue(device + ":LOOP:D")]
    

    ### setters ####

    def setMaxVoltage(self, value, device):
        return self.setValue(self.devices[device] + ":VLIM:" + str(value))

    def setResistance(self, value, device):
        return self.setValue(self.devices[device] + ":RES:" + str(value))

    def setHeater(self, value, device):
        return self.setValue(device + ":LOOP:HSET:" + str(value))

    def setFlow(self, value, device):
        return self.setValue(device + ":LOOP:FSET:" + str(value))

    def setSetPoint(self, value, device):    
        return self.setValue(device + ":LOOP:TSET:" + str(value))
 
    def setP(self, value, device):
        return self.setValue(device + ":LOOP:P:" + str(value))

    def setI(self, value, device):
        return self.setValue(device + ":LOOP:I:" + str(value))

    def setD(self, value, device):
        return self.setValue(device + ":LOOP:D:" + str(value))

    def setFlowSetting(self, value, device):
        return self.setValue(device + ":LOOP:FAUT:" + str(value))

    def setPIDSetting(self, value, device):
        return self.setValue(device + ":LOOP:ENAB:" + str(value))