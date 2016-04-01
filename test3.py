import pid
import matplotlib.pyplot as plt
import json

test_pid_x = pid.PID(0, 0, 10, 0.05, 0.1, -3.0, 3.0)
test_pid_y = pid.PID(0, 0, 10, 0.05, 0.1, -3.0, 3.0)
test_pid_zw = pid.PID(0, 0, 100, 0.0005, 0.1, 0, 2)

data = []
with open('pid.txt') as file:
    data = json.load(file)

x = []
y = []
zw = []
out_x = []
out_y = []
out_z = []
length = range(0, 100)

ex_dict = {"X": {}, "Y": {}, "Z": {}}
ex_dict['X']['minInp'] = data[0]["IN_X"]
ex_dict['X']['maxInp'] = data[0]["IN_X"]
ex_dict['Y']['minInp'] = data[0]["IN_Y"]
ex_dict['Y']['maxInp'] = data[0]["IN_Y"]
ex_dict['Z']['minInp'] = data[0]["IN_Z"]
ex_dict['Z']['maxInp'] = data[0]["IN_Z"]


for i in length:
    x.append(data[i]["IN_X"])
    out_x.append(data[i]["OUT_X"])

    if abs(data[i]["IN_X"]) < ex_dict['X']['minInp']:
        ex_dict['X']['minOut'] = data[i]["OUT_X"]
        ex_dict['X']['minInp'] = data[i]["IN_X"]
    elif abs(data[i]["IN_X"]) >= ex_dict['X']['maxInp']:
        ex_dict['X']['maxOut'] = data[i]["OUT_X"]
        ex_dict['X']['maxInp'] = data[i]["IN_X"]

    y.append(data[i]["IN_Y"])
    out_y.append(data[i]["OUT_Y"])

    if abs(data[i]["IN_Y"]) < ex_dict['Y']['minInp']:
        ex_dict['Y']['minOut'] = data[i]["OUT_Y"]
        ex_dict['Y']['minInp'] = data[i]["IN_Y"]
    elif abs(data[i]["IN_Y"]) >= ex_dict['Y']['maxInp']:
        ex_dict['Y']['maxOut'] = data[i]["OUT_Y"]
        ex_dict['Y']['maxInp'] = data[i]["IN_Y"]

    zw.append(data[i]["IN_Z"])
    out = test_pid_zw.compute(data[i]["IN_Z"])[0]
    out_z.append(out)

    if data[i]["IN_Z"] < ex_dict['Z']['minInp']:
        ex_dict['Z']['minOut'] = out
        ex_dict['Z']['minInp'] = data[i]["IN_Z"]
    elif data[i]["IN_Z"] >= ex_dict['Z']['maxInp']:
        ex_dict['Z']['maxOut'] = out
        ex_dict['Z']['maxInp'] = data[i]["IN_Z"]

print(json.dumps(ex_dict, indent=4, sort_keys=True))

plt.subplot(311)
plt.plot(length, x, 'b-',
         length, out_x, 'r-')
plt.subplot(312)
plt.plot(length, y, 'b-',
         length, out_y, 'r-')
plt.subplot(313)
plt.plot(length, zw, 'b-',
         length, out_z, 'r-')
plt.show()
