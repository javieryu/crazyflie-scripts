import time
import logging


class PID:

    def __init__(self, pid_input, setpoint, kp, ki, kd, outMin, outMax):

        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s-> %(message)s')

        self.setpoint = setpoint
        self.lastInput = pid_input

        self.dt = 10.0  # ms

        self.kp = 0
        self.ki = 0
        self.kd = 0
        self.set_tunings(kp, ki, kd)

        self.outMax = 0
        self.outMin = 0
        self.setOutputLimits(outMin, outMax)

        self.integ = 0

        self.lastTime = float(time.clock() * 1000)
        self.init = True

    def set_tunings(self, kp, ki, kd):
        sampleTime_sec = self.dt / 1000.0
        self.ki = ki * sampleTime_sec
        self.kd = kd / sampleTime_sec
        self.kp = kp

    def set_sampleTime(self, new_sampleTime):
        if new_sampleTime > 0:
            ratio = new_sampleTime/self.dt
            self.ki *= ratio
            self.kd /= ratio
            self.dt = new_sampleTime

    def setOutputLimits(self, outMin, outMax):
        if outMin > outMax:
            raise ValueError('min greater than max: %f > %f'
                             % (outMin, outMax))
        self.outMin = outMin
        self.outMax = outMax

    def constrainTerm(self, term):
        if term > self.outMax:
            return self.outMax
        elif term < self.outMin:
            return self.outMin
        else:
            return term

    def compute(self, inp):

        now = time.clock() * 1000
        timeChange = (now - self.lastTime)
        while True:
            if timeChange >= self.dt:
                err = self.setpoint - inp

                self.integ += (self.ki * err)
                self.integ = self.constrainTerm(self.integ)

                dInput = (inp - self.lastInput)

                output = self.kp * err + self.integ - self.kd * dInput
                output = self.constrainTerm(output)

                self.lastInput = inp
                self.lastTime = now
                # computed = False
                return output, err
            now = time.clock() * 1000
            timeChange = (now - self.lastTime)

    def isInit(self):
        return self.init

    def getPID(self):
        return (self.kp, self.ki, self.kd)

    def getTerms(self):
        return (self.integ, self.lastInput, self.setpoint)

    def getErr(self, inp):
        return inp - self.lastInput

    def getSetpoint(self):
        return self.setpoint


if __name__ == '__main__':
    test_pid = PID(0, 10, 2.0, 0.05, 0.0, 0, 33.3)
    # now = time.clock() * 1000
    # print("%f" % now)
    inp = [x for x in range(0, 20)]
    # out = [test_pid.compute(x) for x in inp]
    out = []
    for x in range(0, len(inp)):
        # time.sleep(0.)
        out.append(test_pid.compute(inp[x]))

    logging.debug('INPUT: %s \nOUTPUT: %s' % (str(inp), str(out)))

    # print("END: %f" % (time.clock()*1000 - now))
