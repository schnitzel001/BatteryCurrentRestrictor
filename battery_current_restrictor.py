#!/usr/bin/env python3
import logging
from logging.handlers import RotatingFileHandler
import time
import json
import dbus
from dbus.mainloop.glib import DBusGMainLoop

CONFIG_FILE = "/data/battery-current-restrictor/config.json"

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create rotating file handler (2MB max, keep 3 backups)
handler = RotatingFileHandler(
    "/data/battery-current-restrictor/app.log",
    maxBytes=2048,  # 2 MB
    backupCount=3
)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


class BatteryCurrentRestrictor:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.config = load_config()
        self.calculated_sp = 0

    def get_value(self, service, path):
        try:
            obj = self.bus.get_object(service, path)
            return obj.GetValue()
        except Exception as e:
            logger.error("Read error:", e)
            return None

    def set_value(self, service, path, value):
        try:
            obj = self.bus.get_object(service, path)
            obj.SetValue(dbus.Int32(value))
        except Exception as e:
            logger.error("Write error:", e)

    def calculate(self, grid_power, battery_power, max_charge_power):
        # calculate difference and use it as new set point
        delta = battery_power - max_charge_power
        target = grid_power - delta
        # restrict to absolute limits
        target = max(target, self.config["min_setpoint"])
        target = min(target, self.config["max_setpoint"]) # max should be 0!
        return int(target)

    def run(self):
        logger.info("Battery current restrictor started")

        #store default set point
        default_sp = 0
        limitation_active = False

        while True:
            soc = int(self.get_value("com.victronenergy.battery.socketcan_can1","/Soc"))
            battery_power = int(self.get_value("com.victronenergy.system", "/Dc/Battery/Power"))

            max_charge_current = self.get_value("com.victronenergy.battery.socketcan_can1",
                                                "/Info/MaxChargeCurrent")
            dc_voltage = self.get_value("com.victronenergy.battery.socketcan_can1",
                                        "/Dc/0/Voltage")
            max_charge_power = int(max_charge_current * dc_voltage)

            L1_grid_power = self.get_value("com.victronenergy.system", "/Ac/Grid/L1/Power")
            L2_grid_power = self.get_value("com.victronenergy.system", "/Ac/Grid/L2/Power")
            L3_grid_power = self.get_value("com.victronenergy.system", "/Ac/Grid/L3/Power")
            grid_power = int(L1_grid_power + L2_grid_power + L3_grid_power)

            # only perform restriction when SOC<100%
            if soc < 100:
                # check if already in limiting mode
                if limitation_active:
                    # calculate new set point and set this value
                    self.calculated_sp = self.calculate(grid_power, battery_power, max_charge_power)
                    self.set_value("com.victronenergy.settings",
                                   "/Settings/CGwacs/AcPowerSetPoint",
                                   self.calculated_sp
                                   )
                    logger.info(f"Grid={grid_power}W, Battery={battery_power}W, Limit={max_charge_power}W → SP={self.calculated_sp}W")

                    # if new set point matches default, limitation can be deactivated
                    if self.calculated_sp == default_sp:
                        limitation_active = False
                        logger.info("Limitation got deactivated")

                # check if limitation needs to be activated
                elif battery_power > max_charge_power:
                    limitation_active = True
                    logger.info("Limitation got activated")

            #otherwise restore default grid set point and deactivate limitation if still active
            elif limitation_active:
                self.set_value("com.victronenergy.settings",
                               "/Settings/CGwacs/AcPowerSetPoint",
                               default_sp
                               )
                limitation_active = False
                logger.info("Limitation got deactivated")

            time.sleep(self.config["interval"])


if __name__ == "__main__":
    BatteryCurrentRestrictor().run()
