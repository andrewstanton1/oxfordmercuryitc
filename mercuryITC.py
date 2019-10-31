# -*- coding: utf-8 -*-
"""
"""


from constants import DEVICES
import pyvisa as visa
import serial
import time


class TemperatureController:
    """
    A simple module for one-to-one remote operation from device to computer over USB.
    All commands written with SCPI command set. Please refer to device manual for list 
    of implemented SCPI commands.

    Attributes:
        instrument: Oxford MecuryiTC 
    """

    TERMINATION = "\n\r"

    _version = ("*IDN?", "")
    _devices = ("SYS:CAT",)
    _signal = "%s:SIG:%s"
    _voltage = "%s:VLIM"
    _resistance = "%s:RES"
    _p = "%s:LOOP:P"
    _i = "%s:LOOP:I"
    _d = "%s:LOOP:D"
    _heater = "%s:LOOP:HSET"
    _flow = "%s:LOOP:FSET"
    _setpoint = "%s:LOOP:TSET"
    _flow_setting = "%s:LOOP:FAUT"
    _setpoint_setting = "%s:LOOP:SWMD"
    _pid_setting = "%s:LOOP:ENAB"
    _sweep = "%s:LOOP:SWFL"

    def __init__(self, resource):
        try:
            self.instrument = visa.ResourceManager().open_resource(resource)
            # sleep to confirm connection to port 
            time.sleep(1)
            self.ratio = 0.0
        except visa.errors.VisaIOError:
            pass

    def __enter__(self):
        self.resource = self.instrument.open()
        return self.resource

    def __exit__(self, *exc):
        if self.resource:
            self.instrument.close()

    @property
    def devices(self) -> str:
        """
        iTC is multi-channel which may have several sensor devices. They are the 
        devices listed on the front panel of the iTC 

        Returns:
            A list of existing hardware devices
        """
        return self.read(*self._devices)

    @property
    def version(self) -> str:
        """
        Get the name of connected device      

        Returns:
            iTC version information
        """
        return self.read(*self._version)

    def write(self, value: str) -> None:
        """
        write a string operation to device followed by values

        Args:
            value: read or set value to device
        """
        try:
            self.instrument.write("%s%s" % (value, self.TERMINATION))
        except TypeError:
            pass
        # self.instrument.flush()


    def read(self, value: str, prefix: str = "READ:") -> str:
        """
        Reads data from device or interface synchronously

        Args:
            value: device ID, device command, and option (DEV:UID:command:option)
            prefix: read command prefix
        Returns:
            data read, return value of the libary call
        """
        # write a read command to device
        self.write("%s%s" % (prefix, value))
        # read_raw - read the unmodified string sent from the instrument to the computer
        # truncate read_raw to remove write termination characters \r\n
        try:
            self.raw_data = str(self.instrument.read_raw()).split(":")[-1][:-3]
        except TypeError:
            return self.raw_data


    def set(self, value: str) -> str:
        """
        Query the device to set values

        Args:
            value: device ID, device command, and option (DEV:UID:command:option)
            prefix: read command prefix
        Returns:
            data read, return value of the libary call
        """        
        return self.read(value, "SET:")

    def open(self) -> None:
        """
        Opens a session to the specified resource   

        """
        try:
            self.instrument.open()
        except serial.serialutil.SerialException:
            pass

    def close(self) -> None:
        """
        Closes the VISA session and marks the handle as invalid

        """
        try:
            self.instrument.close()
        except serial.serialutil.SerialException:
            pass

# getters
    def get_signal(self, device: str, signal: str) -> list:
        """
        Get front panel data for each device: temperature, voltage, gas flow 

        Args:
            device: device ID
            signal: read command 
        Returns:
            device and data read 
        """
        try:
            self.open()
        except:
            pass
        value = self.read(self._signal % (DEVICES[device], signal))
        return [device, value]


    def get_max_voltage(self, device: str) -> list:
        """
        Reads the max voltage data from device 

        Args:
            device: device ID
        Returns:
            device and max voltage data read 
        """
        try:
            self.max_voltage = self.read(self._voltage % (DEVICES[device],))
        except:
            pass
        return [device, self.max_voltage]
    
    def get_resistance(self, device: str) -> list:
        """
        Reads the resistance data from device 

        Args:
            device: device ID
        Returns:
            device and resistance data read 
        """      
        self.resistance = self.read(self._resistance % (DEVICES[device],))
        return [device, self.resistance]
    
    def get_heat_power_ratio(self, device: str) -> float:
        """
        Reads the current voltage and max voltage data from device to calcuate power ratio

        Args:
            device: device ID
        Returns:
            device and calculated power ratio 
        """

        # TODO: is the exception a ZeroDivisionError?
        # truncated voltage value to remove volt unit "V"
        try:
            voltage = float(self.get_signal(device, "VOLT")[1][:-1])
            self.close()
            self.open()
            max_voltage = self.get_max_voltage(device)[1]
            self.ratio = 100.0 * (voltage / float(self.get_max_voltage(device)[1]) ** 2)
        except:
            self.ratio = self.ratio
        # Resource is closed then opened since there is a delay to query/write consecutive values

        return [device, self.ratio]

    def get_heater(self, device: str) -> list:
        """
        Reads the heater percentage data from device

        Args:
            device: device ID
        Returns:
            device and heater percentage read 
        """
        return ["Heat", self.read(self._heater % (device,))]
    
    def get_flow(self, device: str) -> list:
        """
        Reads the flow percentage data from device

        Args:
            device: device ID
        Returns:
            device and flow percentage read 
        """
        return ["Flow", self.read(self._flow % (device,))]

    def get_setpoint(self, device: str) -> list:
        """
        Reads the set point data from device

        Args:
            device: device ID
        Returns:
            device and set point read 
        """
        return ["Set Point", self.read(self._setpoint % (device,))]

    def get_p(self, device: str) -> list:
        """
        Reads the P data from device

        Args:
            device: device ID
        Returns:
            device and P read 
        """
        p = self.read(self._p % (device,))
        return ["P", p]

    def get_i(self, device: str) -> list:
        """
        Reads the I data from device

        Args:
            device: device ID
        Returns:
            device and I read 
        """
        i = self.read(self._i % (device,))
        return ["I", i]

    def get_d(self, device: str) -> list:
        """
        Reads the D data from device

        Args:
            device: device ID
        Returns:
            device and D read 
        """
        d = self.read(self._d % (device,))
        return ["D", d]

    def get_sweep_table(self, device: str) -> list:
        """
        Reads the sweep table data from device

        Args:
            device: device ID
        Returns:
            device and sweep table read 
        """
        sweep_file = self.read(self._sweep % (device, ))
        return sweep_file

# setters
    def set_max_voltage(self, value: str, device: str) -> str:
        """
        Set the maximum voltage limit for the heater

        Args:
            value: max voltage value (0-40)
            device: device ID
        Returns:
            device and valid or invalid write 
        """  
        return self.set(self._voltage % (device, value))

    def set_resistance(self, value: str, device: str) -> str:
        """
        Set the heater resistance 

        Args:
            value: resistance value (10-2000)
            device: device ID
        Returns:
            device and valid or invalid write 
        """          
        return self.set(self._resistance % (device, value))

    def set_heater(self, setting: str, device: str) -> str:
        """
        Set the heater percentage (in manual)

        Args:
            value: heater percentage (0-100)
            device: device ID
        Returns:
            device and valid or invalid write 
        """  
        return self.set((self._heater + ":%s") % (device, str(setting)))
        # return self.heater_percent
 
    def set_flow(self, value: str, device: str) -> str:
        """
        Set the flow percentage (manual flow)

        Args:
            value: flow value between (0-100)
            device: device ID
        Returns:
            device and valid or invalid write 
        """  
        return self.set(self._flow + ":" % (device, value))

    def set_setpoint(self, value: str, device: str) -> str:
        """
        Set the temperature set point

        Args:
            value: set point value (0-2000)
            device: device ID
        Returns:
            device and valid or invalid write 
        """  
        return self.set(self._setpoint + ":" % (device, value))

    # TODO: why do these all set TEMP????
    def set_p(self, device: str, value: str) -> str:
        """
        Set the P value

        Args:
            value: P value
            device: device ID
        Returns:
            device and valid or invalid write 
        """  
        return self.set(self._p % (device, value))

    def set_i(self, device: str, value: str) -> str:
        """
        Set the I value

        Args:
            value: I value
            device: device ID
        Returns:
            device and valid or invalid write 
        """  
        return self.set("%s%s" % (self._i % device, value))

    def set_d(self, device: str, value: str) -> str:
        """
        Set the D value

        Args:
            value: D value
            device: device ID
        Returns:
            device and valid or invalid write 
        """   
        return self.set("%s%s" % (self._d % device, value))

    def set_flow_setting(self, value: str, device: str) -> str:
        """
        Enables/disabeles flow control

        Args:
            value: enable ON or OFF 
            device: device ID
        Returns:
            device and valid or invalid write 
        """   
        return self.set(self._flow_setting % (device, value))

    def set_setpoint_setting(self, value: str, device: str) -> str:
        """
        Sets the sweep mode

        Args:
            value: enable ON or OFF 
            device: device ID
        Returns:
            device and valid or invalid write 
        """        
        return self.set(self._setpoint_setting % (device, value))

    def set_pid_setting(self, value: str, device: str) -> str:
        """
        Enables/disables the PID (proportional-integral-derivative) control

        Args:
            value: enable ON or OFF 
            device: device ID
        Returns:
            device and valid or invalid write 
        """
        return self.set(self._pid_setting % (device, value))

    def set_sweep_table(self, table: list, device: str) -> str:
        """
        Sets file to read from the sweep table

        Args:
            value: sweep table list 
            device: device ID
        Returns:
            device and valid or invalid write 
        """   
        return self.set(self._sweep % (device, table))
