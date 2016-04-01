import pid
import matplotlib.pyplot as plt
import json

test_pid_x = pid.PID(0, 0, 4.4, 0.05, 0.1, -1, 1)
test_pid_y = pid.PID(0, 0, 4.4, 0.05, 0.1, -1, 1)
test_pid_zw = pid.PID(0, 0, 100, 0.0005, 0.1, 0.4, 2)

data = []
with open('log.txt') as file:
    data = json.load(file)

x = []
y = []
zw = []
out_x = []
out_y = []
out_z = []
err_x = []
err_y = []
err_z = []

print ("Data size = %d" % len(data))
low_range = input("Range start = ")
hi_range = input("Range end = ")

length = range(low_range, hi_range)

ex_dict = {"X": {}, "Y": {}, "Z": {}}
ex_dict['X']['minInp'] = data[0]["acc.x"]
ex_dict['X']['maxInp'] = data[0]["acc.x"]
ex_dict['Y']['minInp'] = data[0]["acc.y"]
ex_dict['Y']['maxInp'] = data[0]["acc.y"]
ex_dict['Z']['minInp'] = data[0]["acc.zw"]
ex_dict['Z']['maxInp'] = data[0]["acc.zw"]

for i in length:
    x.append(data[i]["acc.x"])
    out, err = test_pid_x.compute(data[i]["acc.x"])
    out_x.append(out)
    err_x.append(err)

    if abs(data[i]["acc.x"]) < ex_dict['X']['minInp']:
        ex_dict['X']['minOut'] = out
        ex_dict['X']['minErr'] = err
        ex_dict['X']['minInp'] = data[i]["acc.x"]
    elif abs(data[i]["acc.x"]) >= ex_dict['X']['maxInp']:
        ex_dict['X']['maxOut'] = out
        ex_dict['X']['maxErr'] = err
        ex_dict['X']['maxInp'] = data[i]["acc.x"]

    y.append(data[i]["acc.y"])
    out, err = test_pid_y.compute(data[i]["acc.y"])
    out_y.append(out)
    err_y.append(err)

    if abs(data[i]["acc.y"]) < ex_dict['Y']['minInp']:
        ex_dict['Y']['minOut'] = out
        ex_dict['Y']['minErr'] = err
        ex_dict['Y']['minInp'] = data[i]["acc.y"]
    elif abs(data[i]["acc.y"]) >= ex_dict['Y']['maxInp']:
        ex_dict['Y']['maxOut'] = out
        ex_dict['Y']['maxErr'] = err
        ex_dict['Y']['maxInp'] = data[i]["acc.y"]

    zw.append(data[i]["acc.zw"])
    out, err = test_pid_zw.compute(-data[i]["acc.zw"])
    out_z.append(out)
    err_z.append(err)

    if data[i]["acc.zw"] < ex_dict['Z']['minInp']:
        ex_dict['Z']['minOut'] = out
        ex_dict['Z']['minErr'] = err
        ex_dict['Z']['minInp'] = data[i]["acc.zw"]
    elif data[i]["acc.zw"] >= ex_dict['Z']['maxInp']:
        ex_dict['Z']['maxOut'] = out
        ex_dict['Z']['maxErr'] = err
        ex_dict['Z']['maxInp'] = data[i]["acc.zw"]


# print("X:\tMax Output: %.5f | Max Input: %.5f | Max Err: %.5f\n" %
#       (max(out_x), max(x), max(err_x)))
# print("Y:\tMax Output: %.5f | Max Input: %.5f | Max Err: %.5f\n" %
#       (max(out_y), max(y), max(err_y)))
# print("Z:\tMax Output: %.5f | Max Input: %.5f | Max Err: %.5f\n" %
#       (max(out_z), max(zw), max(err_z)))

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
