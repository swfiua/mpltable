"""
**A new paradigm for the universe.**

https://msp.warwick.ac.uk/~cpr/paradigm

ISBN: 9781973129868

I keep dipping into this book.

Each time with new understanding.  Each time with a new perspective.

It is a wonderful work, with compelling arguments.

Chapter 2, Sciama's principle finishes with:

   Sciama's initiative, to base a dynamical theory on Mach's principle as
   formulated i Sciama's principle, has never been followed up and this
   approach to dynamics remains dormant.  One of the aims of this book is to
   reawaken this approach.

One of the aims of `blume` is to help understanding of such theories.

In particular, help my own understanding with computer simulations.

This module will explore some of the mathematics of the book.

It will require `astropy`.  

Solar system, galactic and local galaxy visualsation and simulation.

Simulation of gravitational waves generated by black hole mergers using the
physics of *the book*.

Simulations of gravitational wave from a new galactic arrival.
"""

import argparse

import random

import math

import curio

import astropy.units as u
import astropy.coordinates as coord

from . import magic
from . import farm as fm
from . import taybell

from matplotlib import pyplot as plt
from matplotlib import colors

import numpy as np

from scipy import integrate

async def run(**args):

    farm = fm.Farm()

    if args['galaxy']:
        gals = list(near_galaxies(open(args['galaxy'])))

        skymap = SkyMap(gals)
        farm.add(skymap)
    
    spiral = Spiral()
    farm.add(spiral)

    await farm.start()
    print('about to run farm')
    await farm.run()


def main(args=None):

    parser = argparse.ArgumentParser()
    parser.add_argument('--galaxy', help="file of local galaxy data")

    args = parser.parse_args(args)

    curio.run(run(**args.__dict__), with_monitor=True)

class SkyMap(magic.Ball):

    def __init__(self, gals):

        super().__init__()

        print('clean galaxy data')
        print(gals[0])

        self.balls = gals
        self.sleep=1.0

        

    def decra2rad(self, dec, ra):

        ra = (ra - 12) * math.pi / 12.

        while ra > math.pi:
            ra -= 2 * math.pi
        
        return dec * math.pi / 180., ra
        

    def spinra(self, ra):

        ra += self.offset
        while ra > math.pi:
            ra -= 2 * math.pi

        while ra < math.pi * -1:
            ra += 2 * math.pi

        return ra
        
    async def run(self):

        fig = plt.figure()

        fig.clear()
                
        #ax = fig.add_axes((0,0,1,1), projection='mollweide')
        ax = fig.add_subplot(1, 1, 1,
                             projection='mollweide')

        locs = [self.decra2rad(ball['dec'], ball['ra'])
                    for ball in self.balls]
            
        self.offset = 0
            

        ball_colours = [x['distance'] for x in self.balls]
        
        ax.scatter([self.spinra(xx[1]) for xx in locs],
                   [xx[0] for xx in locs],
                   c=ball_colours,
                   s=[x['major_axis'] or 1 for x in self.balls])

        norm = colors.Normalize(min(ball_colours), max(ball_colours))
        cm = plt.get_cmap()
        for ball, loc, colour in zip(self.balls, locs, ball_colours):
            ma = ball['major_axis'] or 1
            ngn = ball.get('neighbor_galaxy_name', '')
            constellation = ''
            #if (ma or 1) > 20:
            if 'ilky' in ngn or 'ilky' in constellation:
            #if 'ilky' in ball.name:

                print()
                print(constellation)
                print(ball)
                
                ax.text(
                    self.spinra(loc[1]), loc[0],
                    '\n'.join((ball.get('name'), constellation)),
                    color='red',
                    #color=cm(1.0-norm(colour)),
                    fontsize=15 * math.log(max(ma, 10)) / 10)
                                   
        ax.axis('off')

        await self.put(magic.fig2data(plt))


        fig.clear()

        ax = fig.add_subplot(111)
        rv = [xx.get('radial_velocity', 0.0) or 0. for xx in self.balls]
        distance = [xx.get('distance', 0.0) or 0. for xx in self.balls]

        rrv = []
        dd = []
        for vel, dist in zip(rv, distance):
            if dist > 11:
                continue
            
            if vel == 0.0:
                # use Hubble relationship
                vel = dist * 70.
            rrv.append(vel)
            dd.append(dist)

        ax.scatter(dd, rrv)

        #await curio.sleep(self.sleep)
        #await self.outgoing.put(magic.fig2data(fig))
        #await curio.sleep(self.sleep)

        #await self.outgoing.put(magic.fig2data(fig))
        fig.clear()
        ax = fig.add_subplot(111)
        ax.plot(distance)
        #await self.outgoing.put(magic.fig2data(fig))

        fig.clear()
        ax = fig.add_subplot(111)
        ax.plot([xx[1] for xx in locs])
        #await self.outgoing.put(magic.fig2data(fig))


class Spiral(magic.Ball):
    """  Model a spiral galaxy

    Or any rotating mass?
    """

    def __init__(self):

        super().__init__()

        # A = K * \omega_0.  K = M for Sciama principle
        self.A = 0.0005

        # Apparent rate of precession of the roots of the spiral.
        self.B = 0.00000015

        self.Mcent = 0.03
        self.Mball = 0.
        self.Mdisc = 0.

        self.K = self.Mcent
        self.omega0 = self.A / self.K   # angular velocity in radians per year

        # magic constant determined by overall energy in the orbit
        self.EE = -0.00000345

        # constant, can be read from tangential velocity for small r
        self.CC = -10

        # range of radius r to consider, in light years
        self.rmin = 5000
        self.rmax = 50000

        # key bindings
        self.add_filter('a', self.alower)
        self.add_filter('A', self.araise)
        self.add_filter('b', self.blower)
        self.add_filter('B', self.braise)
        self.add_filter('m', self.mlower)
        self.add_filter('M', self.mraise)

    def rmin_check(self):
        """ The length of the roots of the spirals 

        This can be used to set the B value.

        Assume that the spiral roots end at radius r0

        And assume the roots are moving with the inertial frame at that
        radius.

        The rate of precession will match that of the inertial frame at
        that radius.

        """
        return self.A / self.B

    async def araise(self):
        """ Raise the value of A """
        self.A *= 10

    async def alower(self):
        """ Lower the value of A """
        self.A /= 10

    async def braise(self):
        """ Raise the value of B """
        self.B *= 10

    async def blower(self):
        """ Lower the value of B """
        self.B /= 10

    async def mraise(self):
        """ Raise the value of M """
        self.M *= 10

    async def mlower(self):
        """ Lower the value of A """
        self.M /= 10

    def v(self, r):
        """ Velocity at radius r 

        A = 0.0005
        K = Mcent
        CC = -10

        ??
        """
        A = self.A
        K = self.K
        CC = self.CC

        return (2 * A) - (2 * K * A * math.log(1 + K) / r) + CC / r


    def vinert(self, r, v):
        """ Inertial part of the velocity

        Part of velocity relative to inertial frame.

        Notes
        -----

        K is central mass.   A = 0.0005
        """
        return v - (self.A * r) / (self.K + r)

    def rdoubledot(self, r, vinert):

        rdd = ((vinert ** 2) / r) - (self.Mcent/(r**2))

        # if we have Mdisc of Mball, adjust as appropriate?
        rdd -= self.Mdisc/(self.rmax ** 2)
        rdd -= self.Mball * r /(self.rmax ** 3)

        return rdd

    def energy(self, r):

        CC = self.CC
        Mcent = self.Mcent
        Mdisc = self.Mdisc
        Mball = self.Mball
        rmax = self.rmax
        EE = self.EE
        K = self.K
        A = self.A
        Log = math.log

        # ok this deserves an explanation!
        energy = (-CC**2/(2*r**2) + (Mcent - 2*A*CC)/r -
                    Mdisc*r/rmax**2 +
                    Mball*r**2/(2*rmax**3) +
                    A**2*K/(K + r) +
                    A**2*Log(K + r) +
                    2 * A*K * (CC + 2*A*r) * Log(1 + r/K)/(r**2)
                    - (2 * A*K*Log(1 + r/K)/r)**2 + EE);
        
        return energy

    async def run(self):

        #xrdot, xvinert, xv, xtheta = cpr()
        #await self.put(magic.fig2data(plt))

        # close previous plot if there is one
        plt.close()
        ax = plt.subplot(121)

        rr = np.arange(self.rmin, self.rmax, 10)
        #vv = [self.v(r) for r in rr]
        vv = self.v(rr)
        ii = self.vinert(rr, vv)
        rdd = self.rdoubledot(rr, ii)
        energy = np.array([self.energy(r) for r in rr])
        #ii = [self.vinert(r, v) for (r, v) in zip(rr, vv)]
        #rdd = [self.rdoubledot(r, v) for (r, v) in zip(rr, ii)]
        ax.plot(rr, vv, label='velocity')
        ax.plot(rr, ii, label='vinert')
        ax.plot(rr, rdd, label='rdoubledot')
        #ax.plot(rr, energy, label='energy')
        
        plt.xlabel('r', color='r')
        plt.ylabel('velocity', color='y')
        
        rdot = np.sqrt(2 * energy)
        #print('spiral', len(rr), len(rdot))
        ax.plot(rr, rdot, label='rdot')
        ax.legend(loc=0)
          

        thetadot = vv/rr;

        dthetabydr = thetadot/rdot 
        dtbydr = 1/rdot

        NIntegrate = integrate.cumtrapz

        thetaValues = NIntegrate(dthetabydr, rr, initial=0.)
        tvalues = NIntegrate(dtbydr, rr, initial=0.)

        B = self.B
        ax = plt.subplot(122, projection='polar')
        ax.plot(thetaValues - (B * tvalues), rr)
        ax.plot(thetaValues - (B * tvalues) + math.pi, rr)

        await self.put(magic.fig2data(plt))
        plt.close()


def pick(x, v, vmin, vmax):

    n = len(v)
    loc = n * (x - vmin) / vmax

    return v[loc]


def cpr():
    """  Started as Mathematica code from the new paradigm.
    
    adapted to python over time.

    See spiral class for more information over time.
    """

    Plot = plt.plot
    Log = np.log
    Sqrt = np.sqrt
    NIntegrate = integrate.cumtrapz
    
    A = 0.0005; Mcent = .03; EE = -.00000345; CC = -10;
    B = .00000015; Mball = 0; Mdisc = 0; K = Mcent;
    rmin = 5000; rmax = 50000; iterate = 1000;
    
    step = (rmax - rmin)/(iterate - 1)

    r = np.arange(rmin, rmax)

    ax = plt.subplot(121)

    v = 2*A - 2*K*A*Log(1 + r/K)/r + CC/r
    inert = v - A*r/(K + r);
    ax.plot(r, v, label='velocity')
    ax.plot(r, inert, label='vinert')
    
    rdoubledot = inert**2/r - Mcent/r**2 - Mdisc/rmax**2 - Mball*r/rmax**3
    ax.plot(r, rdoubledot, label='rdoubledot')

    energy = (-CC**2/(2*r**2) + (Mcent - 2*A*CC)/r -
                  Mdisc*r/rmax**2 +
                  Mball*r**2/(2*rmax**3) +
                  A**2*K/(K + r) +
                  A**2*Log(K + r) +
                  2 * A*K * (CC + 2*A*r) * Log(1 + r/K)/(r**2)
                  - (2 * A*K*Log(1 + r/K)/r)**2 + EE);
    #Plot(energy, r, label='energy')
    rdot = Sqrt(2*energy)

    ax.plot(r, rdot, label='rdot')

    ax.legend(loc=0)
    
    thetadot = v/r;
    dthetabydr = thetadot/rdot 
    dtbydr = 1/rdot

    
    thetaValues = NIntegrate(dthetabydr, r, initial=0.)
    print(thetaValues)
    print(len(thetaValues))

    tvalues = NIntegrate(dtbydr, r, initial=0.)

    #thetavalues = Table(
    #    NIntegrate(dthetabydr, rmin, rmax), ivalue, i, iterate))
    #tvalues = Table(
    #    NIntegrate(dtbydr, r, ivalue, i, iterate))
    
    #ListPolarPlot[{ Table[{thetavalues[[i]] - B*tvalues[[i]], ivalue},
    #{i, iterate}] ,
    #Table[{thetavalues[[i]] - B*tvalues[[i]] + Pi, ivalue},
    #{i, iterate}] }]

    print('theta', thetaValues[:5])
    ax = plt.subplot(122, projection='polar')
    ax.plot(thetaValues - (B * tvalues), r)
    ax.plot(thetaValues - (B * tvalues) + math.pi, r)

    values = (thetaValues - (B * tvalues))
    print(min(values), max(values))
    return rdot, inert, v, values


def near_galaxies(infile):
    """ parse galaxy.txt from 

    https://heasarc.gsfc.nasa.gov/w3browse/all/neargalcat.html

    """
    for item in taybell.read(infile):
        yield cleanse(item)

def parse_radec(value):

    d, m, s = [float(s) for s in value.split()]

    scale = 1
    if d < 0:
        d *= -1
        scale = -1

    d += m / 60.
    d += s / 3600.

    return d * scale
    
def cleanse(data):

    clean = {}

    for key, value in data.items():

        try:
            value = float(value)
        except:
            pass

        if key in ('ra', 'dec'):
            value = parse_radec(value)
            
        clean[key] = value

    return clean




if __name__ == '__main__':

    
 
    #cpr()
    #plt.show()
    main()
