# -*- coding: utf-8 -*-
"""
"""


DEVICES = {
    "MB1": "DEV:MB1.T1:TEMP",
    "DB6": "DEV:DB6.T1:TEMP",
    "DB4": "DEV:DB4.G1:AUX",
    "MB0": "DEV:MB0.H1:HTR",
    "DB1": "DEV:DB1.H1:HTR",
}

SENSORS = {}
SENSORS["MB1"] = ["VTI_Hx_MB1.T", "primary"]
SENSORS["DB6"] = ["VTI_SR_DB6.T", "secondary"]
SENSORS["DB4"] = ["DB4.G1.%", "primary"]
SENSORS["MB0"] = ["Hx_htr_MB0.V", "primary"]
SENSORS["DB1"] = ["SR_htr_DB1.V", "secondary"]

TEMP_HEATERS = {}
TEMP_HEATERS["VTI_Hx_MB1.T"] = ["MB0", "DEV:MB1.T1:TEMP"]
TEMP_HEATERS["VTI_SR_DB6.T"] = ["DB1", "DEV:DB6.T1:TEMP"]

COMMANDS = {"MB1": "TEMP", "MB0": "VOLT", "DB4": "PERC", "DB6": "TEMP", "DB1": "VOLT"}

CONTROLS = {
    "Heat": {"VTI_Hx_MB1.T": "DEV:MB1.T1:TEMP", "DEV:DB6.T1:TEMP": "DEV:DB6.T1:TEMP"},
    "Flow": "DEV:DB4.G1:AUX",
    "Set Point": {
        "VTI_Hx_MB1.T": "DEV:MB1.T1:TEMP",
        "DEV:DB6.T1:TEMP": "DEV:DB6.T1:TEMP",
    },
    "PID": {"Hx_htr_MB0.V": "DEV:MB0.H1:HTR", "SR_htr_DB1.V": "DEV:DB1.H1:HTR"},
}
