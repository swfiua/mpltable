"""
Handle with care.

Runs any python code it finds in examples folders.

Hopes it is producing matplotlib plots.

If so displays them.

Press h for help.
"""


from blume.magic import Farm, Carpet, Ball, Hat, fig2data
from .mclock2 import GuidoClock

import curio

import random

from matplotlib import pyplot as plt
from pathlib import Path
import argparse
import traceback

class Examples(Ball):

    def __init__(self, args):

        super().__init__()
        
        self.path = Path(args.path)

    async def start(self):

        if self.path.is_file():
            self.paths = [self.path]
        else:
        
            self.paths = list(
                Path(self.path).glob('**/*.py'))

        print('PATHS', len(self.paths))
        self.bans = ['embedding', '_runner', 'tick_labels']

        # not sure this works -- stop others stealing the show
        plt.show = show
        self.bads = set()

    async def run(self):

        idx = 0
        if len(self.paths) > 1:
            idx = random.randint(0, len(self.paths)-1)

        path = self.paths[idx]
        
        if str(path) in self.bads:
            return

        for ban in self.bans:
            if ban in str(path):
                self.bads.add(str(path))
                    
        if str(path) in self.bads:
            return

        print(path)
        try:
            exec(path.open().read(), globals())
        except:
            print('BAD ONE', path)
            traceback.print_exc(limit=20)
            self.bads.add(str(path))
            return

        print('publishing', path)
        await self.outgoing.put(fig2data(plt))

        plt.close()

        return True


def show():
    print('NO SHOW TODAY')


async def run(args):
    """ Don't do things this way until things settle down ..."""

    farm = Farm()

    clock = GuidoClock()

    carpet = Carpet()
    
    farm.event_map.update(clock.event_map)
    farm.event_map.update(carpet.event_map)

    examples = Examples(args)

    hat = Hat()
    farm.add_node(hat, background=True, hat=True)
    farm.add_node(carpet, background=True)
    farm.add_node(examples)
    farm.add_node(clock)

    farm.add_edge(carpet, hat)
    farm.add_edge(examples, carpet)
    farm.add_edge(clock, carpet)


    farm.setup()
    starter = await curio.spawn(farm.start())

    print('farm runnnnnnnnnning')
    runner = await farm.run()
    
        
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('path', default='.')

    args = parser.parse_args()
    curio.run(run(args))
