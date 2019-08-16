""" M CLOCK 2.0.

by Guido van Rossum

after a design by Rob Juda

adapted too much with added buglets by Johnny Gill.

"""
import sys

from datetime import timedelta, datetime

import random
import math
import time
import curio

from matplotlib import pyplot as plt

from .magic import Ball, fig2data



MINUTES_TO_MIDNIGHT = -5.0

class GuidoClock(Ball):

    def __init__(self):

        super().__init__()

        self.width = 480
        self.height = 640
        segments=9
        
        self.segments = segments

        #self.tkcanvas.bind("<ButtonPress-1>", self.on_press)
        #self.tkcanvas.bind("<B1-Motion>", self.on_motion)
        #self.tkcanvas.bind("<ButtonRelease-1>", self.on_release)

        self.timewarp = None
        self.event_map.update(M=self.midnight,
                              R=self.random_hour)

    credits = ("M Clock 2.0\n"
               "by Guido van Rossum\n"
               "after a design by Rob Juda")

    creditxy = None
    showtext = False

    def on_press(self, event):
        self.creditxy = event.x, event.y
        
        self.showtext = not self.showtext

    def on_motion(self, event):
        
        if self.creditxy:
            self.creditxy = event.x, event.y

    def on_release(self, event):
        self.creditxy = None

    def on_zoom(self, event):
        if self.root.wm_overrideredirect():
            self.root.wm_overrideredirect(False)
            self.root.wm_state("normal")
            self.root.wm_geometry("400x400")
        else:
            self.root.wm_overrideredirect(True)
            self.root.wm_state("zoomed")

    def set_radius(self):

        radius = min(self.width, self.height) // 2
        self.radius = radius
        self.bigsize = radius * .975
        self.litsize = radius * .67


    def demo(self, speed=1, colors=(0, 1, 2), segments=None):
        if segments is not None:
            self.segments = segments
        if self.creditid:
            text = "N=%s\nv=%s\n%s" % (self.segments, speed, list(colors))
            self.canvas.itemconfigure(self.creditid, text=text)
        hh, mm, ss = time.localtime()[3:6]
        self.showtext = False
        while not self.showtext:
            try:
                self.draw(hh, mm, ss, colors)
            except Tkinter.TclError:
                break
            self.root.update()
            ss += speed
            mm, ss = divmod(mm*60 + ss, 60)
            hh, mm = divmod(hh*60 + mm, 60)
            hh %= 24

    async def midnight(self, mtm=MINUTES_TO_MIDNIGHT):
        """ Bulletin of Atomic Scientists """
        if self.timewarp:
            self.timewarp = None
            return

        deltam = timedelta(seconds=int(mtm * 60))

        to_midnight = self.to_hour(hour=0)
       
        warp_to = to_midnight + deltam
        
        self.timewarp =  warp_to.seconds - 3600

    def to_hour(self, now=None, hour=0):

        now = now or datetime.now()

        to_midnight = timedelta(
            hours = 24 - now.hour,
            minutes = 60 - now.minute)

        return to_midnight + timedelta(hours=hour)

    async def random_hour(self, mtm=MINUTES_TO_MIDNIGHT):
        """ Warp to just before a random hour """
        
        deltam = timedelta(seconds=int(mtm * 60))

        hour = self.to_hour(hour=random.randint(0, 23))

        warp_to = hour + deltam

        self.timewarp = warp_to.seconds - 3600

    async def run(self):

        print('GUIDOCLOCK run')
        self.redraw()

        # blit the image to the canvas
        await self.outgoing.put(fig2data(plt))

        return True
        await curio.sleep(1)

            
    def redraw(self):
        t = time.time()
        if self.timewarp:
            t += self.timewarp
            
        hh, mm, ss = time.localtime(t)[3:6]
        self.draw(hh, mm, ss)


    def draw(self, hh, mm, ss, colors=(0, 1, 2)):

        plt.cla()
        self.set_radius()
        radius = self.radius
        bigsize = self.bigsize / 100
        litsize = self.litsize / 100
        #bigsize = 1.1
        #litsize = 1.1
        

        xx = int(self.width / 2)
        yy = int(self.height / 2)

        # Set bigd, litd to angles in degrees for big, little hands
        # 12 => 90, 3 => 0, etc.
        bigd = (90 - (mm*60 + ss) / 10) % 360
        litd = (90 - (hh*3600 + mm*60 + ss) / 120) % 360
        # Set bigr, litr to the same values in radians
        bigr = math.radians(bigd)
        litr = math.radians(litd)
        # Draw the background colored arcs
        self.drawbg(bigd, litd, colors)
        print('bigd/litd', bigd, litd, bigsize, litsize)
        # Draw the hands
        #plt.plot(range(3))
        xx = yy = 0.0
        b = plt.plot(
            [xx, xx + int(bigsize*math.cos(bigr))],
            [yy, yy - int(bigsize*math.sin(bigr))],
            linewidth=int(radius/50), color='yellow')
        
        l = plt.plot(
            [xx, xx + int(litsize*math.cos(litr))],
            [yy, yy - int(litsize*math.sin(litr))],
            linewidth=int(radius/33), color='green')
        
        # Draw the text
        if self.showtext:
            t = self.text(
                (xx - bigsize, yy + bigsize),
                text="%02d:%02d:%02d" % (hh, mm, ss),
                fill="white")

                # FIXME: PIL fonts, font="helvetica 16 bold")
            
        if self.creditxy:
            self.text(self.creditxy, self.credits)


    def drawbg(self, bigd, litd, colors=(0, 1, 2)):
        # This is tricky.  We have to simulate a white background with
        # three transparent discs in front of it; one disc is
        # stationary and the other two are attached to the big and
        # little hands, respectively.  Each disc has 9 pie segments in
        # sucessive shades of pigment applied to it, ranging from
        # fully transparent to only allowing one of the three colors
        # Cyan, Magenta, Yellow through.
        N = self.segments
        table = []
        for angle, colorindex in [(bigd - 180/N, 0),
                                  (litd - 180/N, 1),
                                  (  90 - 180/N, 2)]:
            angle %= 360
            for i in range(N):
                color = 255
                if colorindex in colors:
                    color = (N-1-i)*color//(N-1)
                table.append((angle, color, colorindex))
                angle += 360/N
                if angle >= 360:
                    angle -= 360
                    table.append((0, color, colorindex))
        table.sort()
        table.append((360, None))
        radius = self.radius
        xx = int(self.width / 2)
        yy = int(self.height / 2)
        
        fill = [0, 0, 0]

        colors = []
        wedges = []
        for i, (angle, color, colorindex) in enumerate(table[:-1]):
            fill[colorindex] = color
            if table[i+1][0] > angle:
                extent = table[i+1][0] - angle
                if extent < 1.:
                    # XXX Work around a bug in Tk for very small angles
                    extent = 1.

                colors.append("#%02x%02x%02x" % tuple(fill))
                wedges.append(extent)
                #patches.Wedge((xx, yy), radius, angle, extent + angle,
                #              facecolor="#%02x%02x%02x" % tuple(fill))
        plt.pie(wedges, colors=colors, radius=1.5)





