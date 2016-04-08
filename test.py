from pid import PID
import matplotlib.pyplot as plt
import math

test_pid = PID(0, 0, 100, 0.05, 0.8, 0, 10)

inp = [math.sin(math.radians(x)) for x in range(0, 359)]
out = [test_pid.compute(x)[0] for x in inp]
err = [test_pid.compute(x)[1] for x in inp]

print("Max Output: %.5f | Max Err: %.5f\n" % (max(out), max(err)))
plt.ion()
fig = plt.figure()
plt.plot(range(0, 359), inp, 'b-',
         range(0, 359), out, 'r-',
         range(0, 359), [0 for x in range(0, 359)], 'k--',
         range(0, 359), err, 'm--')
fig.canvas.draw()
plt.show(block=False)

while True:
    
    fig.canvas.draw()
    plt.pause(0.05)
