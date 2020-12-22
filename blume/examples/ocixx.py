"""Ottawa c19

Data thanks to open ottawa

https://open.ottawa.ca/datasets/covid-19-source-of-infection/geoservice

This short little example, originally written to explore Ottawa
datasets relating to covid 19.

There are a number of interesting datasets.

The actual data itself is hosted by arcgis.  

The endpoints all include random hexadecimal ids.

So far I have not been able to find stable endpoints for these
datasets and they have had a half-life of about one month.

A script will stop working as a dataset no longer seems to exist.

This is not all bad news, the breakages usually also mean some more
data is available.  There are now 9 covid related datasets.

The primary dataset now has more fields and the date field is now called Date.

Data for the last 14 days in these datasets is typically incomplete,
so it is useful to keep a few days of data so get a better idea of the
evolving picture.

I've started saving data each time the code is run.

Aim to add checksums and scrolling through data sets to see how the
plots change in time.

Seems this little problem has all the key ingredients of the costs of
keeping a data pipeline going.

29th September 2020 update
==========================

Things are moving along.  An initial stab at downloading csv files and
checking differences into git is up and running.

Also starting to develop a class to help guessing what sort of values are in each column.

For now, I am just looking for int's, float's and dates.

As things are going it might work for a lot of the Ottawa datasets.

3rd October 2020
================

I've been using the automatic check for new data and check into git if
it changes for a few days now.

It is a bit clunky, but at least I now have history with the data.
There's a hard named filename, imaginitively called data.csv.

The Ottawa data changes every day, and often the changes go back quite
a way in time.

This is useful, as well as interesting for this data, as cases evolve.

I am having trouble with some of the columns, where the early rows
(where I try to guess what type of column it is), have no data, and
the latter are a mixture of integers and floats, since they are the
seven day average of the daily case numbers.  There is other
wierdness, related to the results of my attempts to guess column types
breaks in different ways for different commits.

I think the fix here is to get the magic spell working!

Update: bug in my code, wrote key where it should have been value.

Still need to get the magic spell working.

Back to the git tracking of data
================================

There are all sorts of reasons for updates, such as guidelines on how
to classify cases changing, or being clarified.  

As I write, there are emerging details of a spreadsheet fail in the
UK, where the sheet recently, and presumably, silently, ran out of
columns and so recent reports have been out of line (on the good
side).

I am assuming that this is really just the result of choosing excel as
the data exchange medium.
 
And having one column per case, which worked really well if there were
15 cases and very soon there would be none.

The spreadsheets perhaps generated by software, unaware of the column
limit, pulling data from some central database.

** UPDATE ** 

Turns out to be a data format problem.  *xls* rather than *xlsx*.  The
former limits to the pre-Excel 2007 limit of 65,536.

Still not clear if this is the ultimate database or just a file
created by a data pull. 

Using spreadsheets can, in theory, remove the "guess the type" issues
that I am dealing with here, but introduce a whole host of
complications, it would appear.

Exchanging data as `csv` files, stored in a git repository offers a
lot more flexibility.

Others are also using git for covid data:

https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_daily_reports

Now about that magic spell...

"""

from matplotlib import pyplot as plt

import sys
import requests
import json
import datetime
import csv
from pprint import pprint

from pathlib import Path
from collections import deque, Counter

import numpy as np

import traceback
import hashlib

from blume import magic
from blume import farm as fm

import git


class River(magic.Ball):
    """ Like a river that """

    def __init__(self):

        super().__init__()
        p = Path('.')
        self.format = '.csv'
        
        data = p.glob(f'*{self.format}')
        
        self.files = deque(sorted(data))
        

    async def xstart(self):
        pass


    def save(self, data, filename='data.csv'):

        #path = Path(str(datetime.datetime.now()) + self.format)
        path = Path(filename)
        path.write_text(data)
        self.files.append(path)
        

BASE_URL = 'https://www.arcgis.com/sharing/rest/content/items/'
ITEM_IDS = [
    '6bfe7832017546e5b30c5cc6a201091b',
    '26c902bf1da44d3d90b099392b544b81',
    '7cf545f26fb14b3f972116241e073ada',
    '5b24f70482fe4cf1824331d89483d3d3',
    'd010a848b6e54f4990d60a202f2f2f99',
    'ae347819064d45489ed732306f959a7e',
]

def get_response(url):
    
    return requests.get(url)


def data_to_rows(data):
    
    # figure out what we have
    for row in csv.reader(data):
        keys = [x.strip() for x in row]
        break

    for row in csv.DictReader(data[1:], keys):
        yield row
    

                      


class Ocixx(magic.Ball):


    def __init__(self):

        super().__init__()
        self.spell = None
        self.fields = None

    def get_data(self, commit):

        repo.git.checkout(commit)

        path = Path(self.filename)

        if not path.exists():
            return

        data = list(data_to_rows(path.open().read().split('\n')))
        if not data:
            return

        if self.spell is None:
            self.spell = magic.Spell()
            self.spell.find_casts(data, self.sniff)
        else:
            self.spell.check_casts(data, self.sniff)
            
        results = list(self.spell.spell(data))
        
        return results

    async def start(self):

        self.repo = git.Repo(search_parent_directories=True)
        self.repo.git.checkout('master')

        self.commits = deque(self.repo.iter_commits(paths=self.filename))
        while len(self.commits) > self.history:
            self.commits.pop()

        self.master = self.commits[0]
        
    async def run(self):

        from matplotlib import dates as mdates

        # Make dates on X-axis pretty
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax = plt.gca()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        
        while True:

            commit = self.commits[0]
            print(commit)
            results = self.get_data(commit)

            if self.fields is None:
                self.fields = deque(self.spell.fields())
                
            key = self.fields[0]
            print(key)
            if results:
                # fixme: give spell an index
                spell = self.spell
                index = [x[spell.datekey] for x in results]

                for ii in index:
                    # fixme 2: let's use matplotlib's mdates.
                    if type(index) == mdates.datetime:
                        print('date oops')

                start, end = drange(index)
                if start.year == 20:
                    print('20 20 wtf!')
                print()

                #print('field,commit', key, self.commits[0])

                #print(stats(data))

                #print(Counter(type(x) for x in data), key)
                #print(data[-10:])

                try:
                    data = [x[key] for x in results]

                    plt.plot(index, data, label=key)
                except:
                    print(f'oopsie plotting {key}') 

                #plt.legend(loc=0)
                plt.title(self.fields[0])
                plt.grid(True)

            self.commits.rotate()
            if self.rotate and self.commits[0] is self.master:

                keytype = str
                while keytype not in (float, int):

                    self.fields.rotate()
                    key = self.fields[0]
                    keytype = self.spell.casts[key]
                break
            
        
        await self.put()

def drange(data):

    return min(data), max(data)
        
def stats(data):

    data = np.array(data)
    results = {}
    results['count'] = len(data)
    results['mean'] = data.mean()
    results['std'] = data.std()
    for percentile in [50, 75, 90, 95]:
        results[percentile] = np.percentile(data, percentile)

    return results

async def run(args):
    
    ocixx = Ocixx()
    ocixx.update(args)
    
    farm = fm.Farm()
    
    farm.add(ocixx)
    farm.shep.path.append(ocixx)

    await farm.start()
    await farm.run()


def hexarg(value):

    hexx = set('abcdef0123456789')
    for char in str(value):
        if char.lower() not in hexx:
            return False
            
    return True

if __name__ == '__main__':

    from pprint import pprint
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*', default='.')
    parser.add_argument('-cumulative', action='store_true')
    parser.add_argument('-update', action='store_true')
    parser.add_argument('-itemid', default=None)
    parser.add_argument('-filename', default='data.csv')
    parser.add_argument('-rotate', action='store_true')
    parser.add_argument('-hint', action='store_true')
    parser.add_argument('-sniff', type=int, default=10)
    parser.add_argument('-history', type=int, default=14)

    args = parser.parse_args()

    if args.hint:
        print('Try these with --itemid:')
        for x in ITEM_IDS:
            print(x)
        import sys
        sys.exit(0)

    """ # FIXME: create an object that digests the inputs and gives filename and itemid

    aiming to support a range of possibilities

    a better approach would just be to look and see what is there and figure out what is what.

    imagine a folder:

          foo/data.csv
              26c902bf1da44d3d90b099392b544b81/data.csv

    problem: want to check out different git commits, so need to re-scan for each commit

    so this code needs putting in a function somewhere
    """
    itemid = ITEM_IDS[0]
    for path in args.paths:
        path = Path(path)

        # if it is a folder, assume target is data.csv
        if path.is_dir():
            path = path / 'data.csv'

        if path.name == 'data.csv':
            tag = path.parent
            if len(str(tag)) == 32 and hexarg(tag):
                itemid = str(tag)
                args.filename = path
                break

    url = BASE_URL + itemid + '/data' 

    resp = get_response(url)

    repo = git.Repo(search_parent_directories=True)

    if list(repo.iter_commits('--all')):
        repo.git.checkout('master')

    print(args.filename)
    print(itemid)
    River().save(resp.text, args.filename)
    
    if args.filename in repo.untracked_files:
        print(f"Add {args.filename} to git repo to track")
        sys.exit(0)
        
    if diff:=repo.index.diff(None):
        print('New data, updating git repo')
        repo.index.add(diff[0].a_path)
        repo.index.commit('latest data')
        
    import curio
    curio.run(run(args))
    
            

    
