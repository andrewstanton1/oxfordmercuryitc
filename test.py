import mercuryITC as itc 
import pyvisa as visa
import constants

rm = visa.ResourceManager()

tc = itc.TemperatureController('ASRLCOM3::INSTR')

print(tc.set_sweep_table("new", "DEV:MB1.T1:TEMP"))
