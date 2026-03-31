#!/usr/bin/env python3
import time
import json
import dbus
from dbus.mainloop.glib import DBusGMainLoop

CONFIG_FILE = "/data/battery-current-restrictor/config.json"


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


class BatteryCurrentRestrictor:
    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        #self.config = load_config()

    def get_value(self, service, path):
        try:
            obj = self.bus.get_object(service, path)
            return obj.GetValue()
        except Exception as e:
            print("Read error:", e)
            return None

    def set_value(self, service, path, value):
        try:
            obj = self.bus.get_object(service, path)
            obj.SetValue(dbus.Int32(value))
        except Exception as e:
            print("Write error:", e)

    def calculate(self, grid_power, battery_power, max_charge_power):
        target = 0
        # if battery_power exceeds allowed max_charge_power calculate difference and use it as new set point
        if battery_power > max_charge_power:
            delta = battery_power - max_charge_power
            target = grid_power - 1.1 * delta
        # restrict to absolute limits
        target = max(target, self.config["min_setpoint"])
        target = min(target, self.config["max_setpoint"])
        return int(target)

    def run(self):
        print("Battery current restritor started")

        #store default set point
        default_sp = self.get_value("com.victronenergy.settings",
                                    "/Settings/CGwacs/AcPowerSetPoint")

        while True:
            soc = self.get_value("com.victronenergy.battery.socketcan_can1",
                                 "/Soc")
            battery_charging = self.get_value("com.victronenergy.battery.socketcan_can1","/Dc/0/Power") > 0
            # only perform restriction when SOC<100% and battery is currently charging
            if soc < 100 and battery_charging:
                L1_grid_power = self.get_value("com.victronenergy.system","/Ac/Grid/L1/Power")
                L2_grid_power = self.get_value("com.victronenergy.system","/Ac/Grid/L2/Power")
                L3_grid_power = self.get_value("com.victronenergy.system","/Ac/Grid/L3/Power")
                grid_power = L1_grid_power + L2_grid_power + L3_grid_power
                battery_power = self.get_value("com.victronenergy.system","/Dc/Battery/Power")
                max_charge_current = self.get_value("com.victronenergy.battery.socketcan_can1",
                                                    "/Info/MaxChargeCurrent")
                dc_voltage = self.get_value("com.victronenergy.battery.socketcan_can1",
                                                    "/Dc/0/Voltage")
                max_charge_power =  max_charge_current * dc_voltage
                if None in (grid_power, battery_power, max_charge_power):
                    print("Error on reading values:")
                    print(f"Grid={grid_power}W, Battery={battery_power}W, Limit={max_charge_power}W")
                    time.sleep(self.config["interval"])
                    continue
                new_sp = self.calculate(grid_power, battery_power, max_charge_power)
                self.set_value("com.victronenergy.settings",
                               "/Settings/CGwacs/AcPowerSetPoint",
                                new_sp
                )
                print(f"Grid={grid_power}W, Battery={battery_power}W, Limit={max_charge_power}W → SP={new_sp}W")

            #otherwise restore default grid set point
            else:
                self.set_value("com.victronenergy.settings",
                               "/Settings/CGwacs/AcPowerSetPoint",
                               default_sp
                               )


            time.sleep(self.config["interval"])


if __name__ == "__main__":
    BatteryCurrentRestrictor().run()
