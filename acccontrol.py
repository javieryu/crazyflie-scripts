from threading import Thread
import time
import cflib
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
import json

import pid

import logging

logging.basicConfig(level=logging.ERROR)


class UpDown:

    """docstring for UpDown"""

    def __init__(self, link_uri):

        self._cf = Crazyflie()

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        self._logger = LogConfig(name='Logger', period_in_ms=10)
        self._logger.add_variable('acc.x', 'float')
        self._logger.add_variable('acc.y', 'float')
        self._logger.add_variable('acc.z', 'float')
        self._logger.add_variable('acc.zw', 'float')

        self._acc_x = 0
        self._acc_y = 0
        self._acc_z = 0
        self._acc_zw = 0
        self._vel_x = 0
        self._vel_y = 0
        self._vel_z = 0

        self.acc_pid_x = None
        self.acc_pid_y = None
        self.acc_pid_z = None

        self.vel_pid_x = None
        self.vel_pid_y = None
        self.vel_pid_z = None

        print("Connecting to %s" % link_uri)
        self._cf.open_link(link_uri)
        self.is_connected = True
        self.exit = False
        self.init = False

        Thread(target=self._exit_task).start()
        Thread(target=self._run_task).start()

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        self.initTime = time.clock()
        self.log_file = open('log.txt', 'w')
        self.pid_log = open('pid.txt', 'w')
        self.log_file.write('[\n')
        self.pid_log.write('[\n')
        try:
            self._cf.log.add_config(self._logger)
            # This callback will receive the data
            self._logger.data_received_cb.add_callback(self._acc_log_data)
            # This callback will be called on errors
            self._logger.error_cb.add_callback(self._acc_log_error)
            # Start the logging
            self._logger.start()
        except KeyError as e:
            print('Could not start log configuration,'
                  '{} not found in TOC'.format(str(e)))
        except AttributeError:
            print('Could not add Logger log config, bad configuration.')

    def _acc_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print('Error when logging %s: %s' % (logconf.name, msg))

    def _acc_log_data(self, timestamp, data, logconf):
        """Callback from the log API when data arrives"""
        self._acc_x = float(data['acc.x'])
        self._acc_y = float(data['acc.y'])
        self._acc_z = float(data['acc.z'])
        self._acc_zw = data['acc.zw']

        self.log_file.write(json.dumps(data, sort_keys=True) + ",\n")

        self.init = True

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the specified address)"""
        print('Connection to %s failed: %s' % (link_uri, msg))
        self.is_connected = False
        self.log_file.write(']')
        self.pid_log.write(']')
        self.log_file.close()
        self.pid_log.close()

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print('Connection to %s lost: %s' % (link_uri, msg))
        self.log_file.write(']')
        self.pid_log.write(']')
        self.log_file.close()
        self.pid_log.close()

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print('Disconnected from %s' % link_uri)
        self.is_connected = False

    def _exit_task(self):
        while not self.exit:
            inp = int(input('Want to exit? [NO:0/YES:1]\n'))
            if inp == 1:
                self.exit = 1

    def _run_task(self):
        print("Running thread")
        self._cf.commander.send_setpoint(0, 0, 0, 0)

        while not self.exit:

            if not self.init:

                self.acc_pid_x = pid.PID(0, 0, 4.4, 0.05, 0.1, -1.5, 1.5)
                self.acc_pid_y = pid.PID(0, 0, 4.4, 0.05, 0.1, -1.5, 1.5)
                self.acc_pid_z = pid.PID(0, 0, 100, 0.0005, 0.1, 0, 2)
                continue

            inp_acc_x = self._acc_x
            out_acc_x, err_acc_x = self.acc_pid_x.compute(inp_acc_x)
            setPitch = -out_acc_x*10

            inp_acc_y = self._acc_y
            out_acc_y, err_acc_y = self.acc_pid_y.compute(inp_acc_y)
            setRoll = out_acc_y*10

            inp_acc_z = self._acc_zw
            out_acc_z, err_acc_z = self.acc_pid_z.compute(inp_acc_z)
            setThrust = int(60000*out_acc_z/2)
            self._thrust = setThrust

            data = {"IN_X": inp_acc_x, "OUT_X": out_acc_x,
                    "IN_Y": inp_acc_y, "OUT_Y": out_acc_y,
                    "IN_Z": inp_acc_z, "OUT_Z": out_acc_z,
                    "OUT_Roll": setRoll, "OUT_Pitch": setPitch,
                    "OUT_Thrust": setThrust}

            self.pid_log.write(json.dumps(data, sort_keys=True) + ",\n")

            self._cf.commander.send_setpoint(
                setRoll, setPitch, 0, self._thrust)
            time.sleep(0.01)

        self.log_file.write(']')
        self.pid_log.write(']')
        self.log_file.close()
        self.pid_log.close()

        self._cf.commander.send_setpoint(0, 0, 0, 0)
        time.sleep(1)
        self._cf.close_link()

if __name__ == '__main__':
    cflib.crtp.init_drivers(enable_debug_driver=False)
    print("Scanning interfaces for Crazyflies...")
    available = cflib.crtp.scan_interfaces()
    print("Crazyflies found:")
    index = 0
    for i in available:
        print("[%d] %s" % (index, i[0]))
        index += 1

    if len(available) > 0:
        index = int(input('Radio? '))
        le = UpDown(available[index][0])
        while le.is_connected:
            time.sleep(1)
    else:
        print("No Crazyflies found, cannot run example")
