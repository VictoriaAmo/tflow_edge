from ldtool.msg import Eog
import rospy
from utils import reref_channels
from twisted.internet import reactor, defer, task
from Traumschreiber import *
import time
import numpy as np
import logging
loglevel = logging.INFO
logging.basicConfig(level=loglevel)
# ROS tools
#import sys
#sys.path.insert(0, "/home/felix/catkin_ws/src")

SHOWPLOT = False

########################################
# ID of the traumschreiber you are using
ID = 1
########################################
GAIN = 4
TRAUMSCHREIBER_ADDR = "74:72:61:75:6D:{:02x}".format(ID)
# reference channel
REF_CHANNEL = 4
duration = 25000
data = np.zeros((duration, 9), dtype='<i2')
# Publishers
rospy.init_node("traumschreiber_data", anonymous=False)
EOG_pub = rospy.Publisher("/EOG_data", Eog, queue_size=0)


def data_callback(data_in):
    global data
    print(data.shape)
    data = np.roll(data, -1, axis=0)
    #data[-1, :] = np.hstack(([[0]], data_in))
    data[-1, :] = reref_channels(data_in, REF_CHANNEL)
    #new_row = [time.time(),data[-1,:][0],data[-1,:][1],data[-1,:][2]]
    msg = Eog()
    msg.timestamp = time.time()
    msg.ch0 = data[-1, :][0]
    msg.ch1 = data[-1, :][1]
    msg.ch2 = data[-1, :][2]
    print(msg)
    EOG_pub.publish(msg)


if SHOWPLOT:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib import pyplot as pp

    def plot():
        try:
            for i, line in enumerate(lines):
                fig.canvas.restore_region(background[i])
                line.set_data(tt, data[:, i])
                ax[i].draw_artist(line)
                #fig.canvas.set_window_title("Data (received {} packages/second)".format(pkgs_per_second))
                fig.canvas.blit(ax[i].bbox)
        except Exception as e:
            print("Encountered exception in plot callback: {}".format(e))


async def run():
    async with Traumschreiber(addr=TRAUMSCHREIBER_ADDR) as t:
        await t.start_listening(data_callback)
        # await async_sleep(1)
        await t.set(gain=GAIN)
        # await t.set(a_on=1,b_on=1,color=(255,0,0), gain=GAIN)
        # await async_sleep(1)
        # await t.set(a_on=0,color=(0,255,0))
        # await async_sleep(1)
        # await t.set(a_on=1,b_on=0,color=(0,255,0))
        # await async_sleep(1)
        # await t.set(color=(255,255,0))
        # await async_sleep(1)
        # await t.set(b_on=1,color=(255,255,0))
        # await async_sleep(1)
        # await t.set(a_on=1,color=(125,125,0))
        # await async_sleep(1)
        # await t.set(a_on=0,b_on=0,color=(0,0,0))
        await async_sleep(2*3600)
        if SHOWPLOT:
            plot()


def main(reactor):
    d = defer.ensureDeferred(run())
    return d


if SHOWPLOT:
    # Plot lines
    fig, ax = pp.subplots(nrows=9, ncols=1, figsize=(
        15, 10), sharex=True, sharey=True)
    fig.show()
    fig.canvas.draw()

    tt = np.arange(duration)
    lines = [ax[i].plot(tt, data[:, i])[0] for i in range(9)]
    hlines = [(ax[i].axhline(y=2**11, c="black"),
               ax[i].axhline(y=-2**11, c="black")) for i in range(9)]
    ax[0].set_ylim([-2**12, 2**12])
    background = [fig.canvas.copy_from_bbox(ax[i].bbox) for i in range(9)]
    task.LoopingCall(plot).start(0.5)

task.react(main)
