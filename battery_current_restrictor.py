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
    maxBytes=2048,
    backupCount=3
)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
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

    def get_charge_limit(self, soc):
        list_of_limits =[]
        # from BMS
        if self.config.get("bms_limit_activated"):
            bms_limit = self.get_value(self.config.get("bms_limit_dbus_service"),
                                       self.config.get("bms_limit_value_path"))
            list_of_limits.append(bms_limit)

        # from configured charge curve
        if self.config.get("charge_curve_limit_activated"):
            curve = self.config.get("individual_charge_curve", [])
            charge_curve_limit = self.get_allowed_current_from_curve(soc, curve)
            list_of_limits.append(charge_curve_limit)

        # based on forecast
        #ToDo: implementation missing

        if list_of_limits:
            return min(list_of_limits)
        else:
            return -1


    def get_allowed_current_from_curve(self, soc, curve):
        # sort values
        curve = sorted(curve, key=lambda x: x["soc"])

        # edge-cases
        if soc <= curve[0]["soc"]:
            return curve[0]["current"]
        if soc >= curve[-1]["soc"]:
            return curve[-1]["current"]

        # interpolate
        for i in range(len(curve) - 1):
            p1 = curve[i]
            p2 = curve[i + 1]

            if p1["soc"] <= soc <= p2["soc"]:
                soc_range = p2["soc"] - p1["soc"]
                current_range = p2["current"] - p1["current"]
                factor = (soc - p1["soc"]) / soc_range

                return p1["current"] + factor * current_range

    def run(self):
        logger.info("Battery current restrictor started")

        #store default set point
        default_sp = 0
        limitation_active = False

        while True:
            soc = int(self.get_value("com.victronenergy.battery.socketcan_can1","/Soc"))
            battery_power = int(self.get_value("com.victronenergy.system", "/Dc/Battery/Power"))

            max_charge_current = self.get_charge_limit(soc)
            if max_charge_current == -1:
                # no limit activated - skip all
                continue

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
                        continue

                # check if limitation needs to be activated
                elif battery_power > max_charge_power:
                    limitation_active = True
                    logger.info("Limitation got activated")
                    continue

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
