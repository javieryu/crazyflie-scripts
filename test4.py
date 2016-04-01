import pid
import matplotlib.pyplot as plt
import json

test_pid_x = pid.PID(0, 0, 10, 0.05, 0.1, -3.0, 3.0)
test_pid_y = pid.PID(0, 0, 10, 0.05, 0.1, -3.0, 3.0)
test_pid_zw = pid.PID(0, 0, 100, 0.0005, 0.1, 0, 2)

data = []
with open('pid.txt') as file:
    data = json.load(file)

zw = []
thrust = []
length = range(0, 100)

for d in data:
    zw.append(d['IN_Z'])
    thrust.append(d['OUT_Thrust'])


plt.plot(zw, 'b-',
         thrust, 'r-')
plt.show()
