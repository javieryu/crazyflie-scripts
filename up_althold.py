import time
import sys
from threading import Thread
import logging

sys.path.append("../src/cflib")
import cflib  # noqa
from cflib.crazyflie import Crazyflie  # noqa
from cflib.crazyflie.log import LogConfig

logging.basicConfig(level=logging.ERROR)


class UpAlthold:
    """Example that connects to a Crazyflie and ramps the motors up/down and
    the disconnects"""

    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """

        self._cf = Crazyflie()

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        self._asl = 0
        self._thrust = 0
        self.exit = False
        
        self._logger = LogConfig(name='Logger', period_in_ms=10)
        self._logger.add_variable("baro.asl", "float")
        self._logger.add_variable("stabilizer.thrust", "float")
         
        self._cf.open_link(link_uri)

        print("Connecting to %s" % link_uri)

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        try:
            self._cf.log.add_config(self._logger)
            # This callback will receive the data
            self._logger.data_received_cb.add_callback(self._log_data)
            # This callback will be called on errors
            self._logger.error_cb.add_callback(self._log_error)
            # Start the logging
            self._logger.start()
        except KeyError as e:
            print("Could not start log configuration,"
                  "{} not found in TOC".format(str(e)))
        except AttributeError:
            print("Could not add Stabilizer log config, bad configuration.")
        
        # Start a separate thread to do the motor test.
        # Do not hijack the calling thread!
        Thread(target=self._up_althold).start()
        Thread(target=self._run).start()

    def _log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print("Error when logging %s: %s" % (logconf.name, msg))

    def _log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        #print("[%d][%s]: %s" % (timestamp, logconf.name, data))
        self._asl = data['baro.asl']
        self._thrust = data['stabilizer.thrust']
    
    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the specified address)"""
        print("Connection to %s failed: %s" % (link_uri, msg))

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print("Connection to %s lost: %s" % (link_uri, msg))

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print("Disconnected from %s" % link_uri)

    def _run (self):
        inp = 0
        while not self.exit:
            inp = int(input())
            if inp != 0:
                self.exit = True
    
    def _up_althold(self):
        thrust_mult = 1
        thrust_step = 0
        thrust = 0
        maxthrust = 45000
        pitch = 0
        roll = 0    
        yawrate = 0
        state = 1
        t = 0
        
        # Unlock startup thrust protection
        self._cf.commander.send_setpoint(0, 0, 0, 0)
        
        print('Waiting for ASL data')
        time.sleep(5)
        print('Done waiting, starting rise')

        initasl = self._asl
        targetasl = initasl + 2
        
        #self._cf.param.set_value('altHold.kd', '0.13')
        
        #Rises off of the ground
        while not self.exit:
            if state == 0:
                self._cf.commander.send_setpoint(roll, pitch, yawrate, thrust)
                thrust += thrust_step*thrust_mult
                print("targetasl: %s" % targetasl)
                print("currentasl: %s" % self._asl)
                time.sleep(0.1)
                #print("Thrust: %s" % thrust)
                if self._asl >= targetasl:
                    print("target asl reached")
                    state=1
                if thrust >= maxthrust:
                    print("max thrust reached")
                    state = 1
            elif state==1:
                self._cf.commander.send_setpoint(0,0,0,32767)
                self._cf.param.set_value('flightmode.althold', "True")
                time.sleep(0.01)
                t += 1
                if t==300:
                    print('Hovered for 10s')
                    state = 2
            elif state==2:
                break
            print('State: %s' % state)
            print('Thrust: %s' % self._thrust)
        
        print('reached close link sequence')
        self._cf.commander.send_setpoint(0, 0, 0, 0)
        # Make sure that the last packet leaves before the link is closed
        # since the message queue is not flushed before closing
        time.sleep(0.1)
        self._cf.close_link()


if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    # Scan for Crazyflies and use the first one found
    print("Scanning interfaces for Crazyflies...")
    available = cflib.crtp.scan_interfaces()
    print("Crazyflies found:")
    for i in available:
        print(i[0])

    if len(available) > 0:
        le = UpAlthold(available[0][0])
    else:
        print("No Crazyflies found, cannot run example")
