import numpy as np
import pandas as pd
import os
import sys

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file, save
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.embed import components
from bokeh.models import Range1d

data_folder = '../data/Output_Example/'
filename = '08_BTC_BCH_1_FINAL.csv'
full_filename = os.path.join(data_folder, filename)
df = pd.read_csv(full_filename)

filename = '02_BTC_BCH_TRADE_ID_GAPS.txt'
full_filename = os.path.join(data_folder, filename)
with open(full_filename, 'r') as infile:
    lines = infile.readlines()[2:]

def parse_gap(line):
    if 'to' in line:
        split = line.split(' to ')
        return int(split[0]), int(split[1])
    else:
        return int(line), int(line)

def get_gap_sizes(gaps):
    return [gap[1]-gap[0]+1 for gap in gaps]

gaps = []
for line in lines:
    gaps.append(parse_gap(line))

min_trade = min(df[df['Start_trade_id']>0]['Start_trade_id'].min(), min(gap[0] for gap in gaps))
max_trade = max(df['End_trade_id'].max(), max(gap[1] for gap in gaps))

bars = []
indicator = []
missing = set(num for gap in gaps for num in range(gap[0], gap[1]+1))
for i in range(min_trade, max_trade+1):
    continue


gap_sizes = get_gap_sizes(gaps)


sys.exit()


centers = (edges[:-1]+edges[1:])/2
width = abs(centers[0]-centers[1])

TOOLS = 'save,pan,box_zoom,wheel_zoom,reset'

left = min(centers)*.75
right = max(centers)*1.2
top = max(hist)*1.2
bottom = 0
x_range = Range1d(start=left, end=right, bounds=(left,right))
y_range = Range1d(start=bottom, end=top, bounds=(bottom,top))

p1 = figure(title=filename, tools=TOOLS,
            x_range=x_range,
            y_range=y_range,
            active_scroll='wheel_zoom', background_fill_color='#E8DDCB')

source = ColumnDataSource(data={
            'count': hist,
            'center': centers,
            'left': edges[:-1],
            'right': edges[1:]})

p1.vbar(x='center', top='count', width=width, source=source,
       line_color='white', fill_color='black', hover_line_color='grey')
p1.legend.location='center_right'
p1.legend.background_fill_color = 'darkgrey'
p1.xaxis.axis_label = 'Gap size'
p1.yaxis.axis_label = 'Count'
p1.add_tools(HoverTool(tooltips=[#('Value', '$x{1.1111}'),
                                 ('Range', '@left{1.1}-@right{1.1}'),
                                 ('Count', '@count'),
                                 ]))

output_file('gap_test1.html')

show(p1)
