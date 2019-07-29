# encoding: utf-8
"""
Implementation of the "low-level" functionality used by the common
implementation of the API, for the Brian2 simulator.

Classes and attributes usable by the common implementation:

Classes:
    ID
    Connection

Attributes:
    state -- an instance of the _State class.

All other functions and classes are private, and should not be used by other
modules.

:copyright: Copyright 2006-2016 by the PyNN team, see AUTHORS.
:license: CeCILL, see LICENSE for details.

"""

import logging
import brian2
import numpy
from pyNN import common
import pdb

name = "Brian2"
logger = logging.getLogger("PyNN")

ms = brian2.ms


class ID(int, common.IDMixin):

    def __init__(self, n):
        """Create an ID object with numerical value `n`."""
        int.__init__(n)
        common.IDMixin.__init__(self)


class State(common.control.BaseState):

    def __init__(self):
        common.control.BaseState.__init__(self)
        self.mpi_rank = 0
        self.num_processes = 1
        self._min_delay = 'auto'
        self.current_sources = []
        self.network = brian2.Network()
        self.network.clock = brian2.Clock(0.1 * ms)
        self.clear()

    def run(self, simtime):
        #pdb.set_trace()
        self.running = True
        self.network.run(simtime * ms) # previously simtime * ms

    def run_until(self, tstop):
        self.run(tstop - self.t)

    def clear(self):
        self.recorders = set([])
        self.id_counter = 0
        self.current_sources = []
        self.segment_counter = -1
        if self.network:
            for item in self.network.objects:
                del item
        self.reset()

    def reset(self):
        """Reset the state of the current network to time t = 0."""
        # self.network.reinit() # Not required by Brian2
        self.running = False
        self.t_start = 0
        self.segment_counter += 1
        for obj in self.network.objects:  # Brian2 `objects` instead of `groups`
            if hasattr(obj, "initialize"):
                logger.debug("Re-initalizing %s" % obj)
                obj.initialize()

    def _get_dt(self):
        if self.network.clock is None:
            raise Exception("Simulation timestep not yet set. Need to call setup()")
        return float(self.network.clock.dt / ms)

    def _set_dt(self, timestep):
        logger.debug("Setting timestep to %s", timestep)
        #if self.network.clock is None or timestep != self._get_dt():
        #    self.network.clock = brian2.Clock(dt=timestep*ms)
        self.network.clock.dt = timestep * ms
    dt = property(fget=_get_dt, fset=_set_dt)

    @property
    def t(self):
        return float(self.network.clock.t / ms)

    def _get_min_delay(self):
        if self._min_delay == 'auto':
            min_delay = numpy.inf
            for item in self.network.groups:
                if isinstance(item, brian2.Synapses):
                    min_delay = min(min_delay, item.delay.to_matrix().min())
            if numpy.isinf(min_delay):
                self._min_delay = self.dt
            else:
                self._min_delay = min_delay * self.dt  # Synapses.delay is an integer, the number of time steps
        return self._min_delay

    def _set_min_delay(self, delay):
        self._min_delay = delay
    min_delay = property(fget=_get_min_delay, fset=_set_min_delay)

state = State()
