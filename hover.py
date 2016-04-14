from threading import Thread
import time
import cflib
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
import json
import matplotlib.pyplot as plt

import pid

import logging

logging.basicConfig(level=logging.ERROR)

class Hover:
    
    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """

        self._cf = Crazyflie()

        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        self._lg_stab = LogConfig(name="Logger", period_in_ms=10)
        self._lg_stab.add_variable('acc.x', "float")
        self._lg_stab.add_variable('acc.y', "float")
        self._lg_stab.add_variable('acc.zw', "float")
        
        #self._lg_stab.add_variable('stabilizer.roll', "float")
        #self._lg_stab.add_variable('stabilizer.pitch', 'float')
        
        #PID for Z velocity??
        #self._lg_stab.add_variable('acc.z', "float")
        #self._lg_stab.add_variable("", "float")
        
        self._cf.open_link(link_uri)

        print("Connecting to %s" % link_uri)
        
        self._acc_x = 0.0
        self._acc_y = 0.0
        self._acc_zw = 0.0
        
        #self._actual_roll = 0.0
        #self._actual_pitch = 0.0
        #self._acc_z = 0.0
        #self._vel_z = 0.0
        
        #ROLL/PITCH
        maxangle = 5
        
        kpangle = 3.5        
        kiangle = 0.002
        kdangle = 1
        
        self._acc_pid_x = pid.PID(0, 0, kpangle, kiangle, kdangle, -maxangle, maxangle)
        self._acc_pid_y = pid.PID(0, 0, kpangle, kiangle, kdangle, -maxangle, maxangle)
        self._acc_pid_z = pid.PID(0, 0, 2, 0.018, 2, 1/6, 2)
        
        #self._pitch_pid = pid.PID(0, 0, kpangle, kiangle, kdangle, -maxangle, maxangle)
        #self._roll_pid = pid.PID(0, 0, kpangle, kiangle, kdangle, -maxangle, maxangle)
        
        
        self._is_connected = True
        #self._acc_log = []
        self.exit = False


    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        
        try:
            self._cf.log.add_config(self._lg_stab)
            # This callback will receive the data
            self._lg_stab.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_stab.start()
        except KeyError as e:
            print("Could not start log configuration,"
                  "{} not found in TOC".format(str(e)))
        except AttributeError:
            print("Could not add Stabilizer log config, bad configuration.")
        
        Thread(target=self._hover).start()
        Thread(target=self._log_task).start()
        Thread(target=self._exit_task).start()

    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        print("Error when logging %s: %s" % (logconf.name, msg))

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback froma the log API when data arrives"""
        self._acc_x = float(data['acc.x'])
        self._acc_y = float(data['acc.y'])
        self._acc_zw = float(data['acc.zw'])
        self._acc_z = float(data['acc.z'])
        #self._actual_roll = float(data['stabilizer.roll'])
        #self._actual_pitch = float(data['stabilizer.pitch'])
        #self._vel_z = float(data["acc.x"])
        
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
        self._is_connected = False
    
    def _exit_task(self):
        while not self.exit:
            inp = int(input('Want to exit? [NO:0/YES:1]\n'))
            if inp != 0:
                self.exit = True
    
    def _log_task(self):
        
        time.sleep(3)
        print("Done log sleep!")
        
        x = [0]
        it = 0
        data = {'acc.x':[0],'acc.y':[0],'acc.zw':[0],'out_pitch':[0],'out_roll':[0],'out_thrust':[0],
            'stabilizer.pitch':[0], 'stabilizer.roll':[0]}
        
        plt.ion()
        fig = plt.figure()
        
        ax1 = fig.add_subplot(411)
        line1, = ax1.plot(x, data['acc.x'], 'b-')
        line2, = ax1.plot(x, data['out_pitch'], 'r-')
        
        ax2 = fig.add_subplot(412)
        line3, = ax2.plot(x,data['acc.y'],'b-')
        line4, = ax2.plot(x,data['out_roll'], 'r-')
        
        ax3 = fig.add_subplot(413)
        line5, = ax3.plot(data['acc.zw'], 'b-')
        line6, = ax3.plot(data['out_thrust'], 'r-')
        
        #ax4 = fig.add_subplot(414)
        #line7, = ax4.plot(data['stabilizer.roll'],'b-')
        #line8, = ax4.plot(data['stabilizer.pitch'],'b-')
        
        fig.canvas.draw()
        plt.show(block=False)
        
        while not self.exit:
            it += 1
            x.append(it)
            
            data['acc.x'].append(self._acc_x)
            data['acc.y'].append(self._acc_y)
            data['acc.zw'].append(self._acc_zw)
            data['out_pitch'].append(self._output_pitch_raw)
            data['out_roll'].append(self._output_roll_raw)
            data['out_thrust'].append(self._output_thrust_raw)
            #data['stabilizer.roll'].append(self._actual_roll)
            #data['stabilizer.pitch'].append(self._actual_pitch)
            
            print(int(60000*(self._output_thrust_raw)/2))
            
            line1.set_ydata(data['acc.x'])
            line1.set_xdata(x)
            line2.set_ydata(data['out_pitch'])
            line2.set_xdata(x)
            line3.set_ydata(data['acc.y'])
            line3.set_xdata(x)
            line4.set_ydata(data['out_roll'])
            line4.set_xdata(x)
            line5.set_ydata(data['acc.zw'])
            line5.set_xdata(x)
            line6.set_ydata(data['out_thrust'])
            line6.set_xdata(x)
            #line7.set_ydata(data['stabilizer.roll'])
            #line7.set_xdata(x)
            #line8.set_ydata(data['stabilizer.pitch'])
            #line8.set_xdata(x)
            
            ax1.relim()
            ax1.autoscale_view(True,True,True)
            ax2.relim()
            ax2.autoscale_view(True,True,True)
            ax3.relim()
            ax3.autoscale_view(True,True,True)
            #ax4.relim()
            #ax4.autoscale_view(True,True,True)
            
            fig.canvas.draw()
            
            #time.sleep(0.5)
            plt.pause(0.05)

        filename = str(input('Log Image Name: '))
        if filename != '0':
            fig.savefig(filename)
        
        self._cf.close_link()
        print("Closing Log task")


    def _hover(self):
        print("Starting Hover")
        self._cf.commander.send_setpoint(0,0,0,0)
        
        self._output_pitch_raw = None
        self._output_roll_raw = None
        self._output_thrust_raw = None
        
        while not self.exit:
            self._output_pitch_raw = self._acc_pid_x.compute(self._acc_x)[0]
            self._output_roll_raw = self._acc_pid_y.compute(self._acc_y)[0]
            self._output_thrust_raw = self._acc_pid_z.compute(self._acc_zw)[0]
            
            self._output_pitch = -(self._output_pitch_raw)*5
            self._output_roll = self._output_roll_raw*5
            self._output_thrust = int(60000*(self._output_thrust_raw)/2)
            
            #self._cf.commander.send_setpoint(0,0,0,0)
            self._cf.commander.send_setpoint(self._output_pitch, self._output_roll, 0, self._output_thrust)
            time.sleep(0.02)

        self._cf.commander.send_setpoint(0, 0, 0, 0)
        time.sleep(0.1)
        #self._cf.close_link()

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
        le = Hover(available[index][0])
        while le._is_connected:
            time.sleep(1)
    else:
        print("No Crazyflies found, cannot run example")
