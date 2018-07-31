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
filename = '03_BTC_LTC_TIME_DELAY.txt'
full_filename = os.path.join(data_folder, filename)
bins = 10

with open(full_filename, 'r') as infile:
    lines = infile.readlines()[2:]

def parse_delay(line):
    if 'second' in line:
        number = line.split('+')[0].split(' ')[0]
        count = line.split(': ')[1]
        return {int(number):int(count)}

def get_delays_hist(delays):
    hist = []
    edges = []
    for i in range(61):
        edges.append(i)
        hist.append(delays.get(i, 0))
    edges.append(61)
    return np.array(hist), np.array(edges)

delays = {}
for line in lines:
    delays.update(parse_delay(line))

hist, edges = get_delays_hist(delays)

#hist, edges = np.histogram(gap_sizes, bins=bins)


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
            width=1000,
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
p1.xaxis.axis_label = 'Delay time'
p1.yaxis.axis_label = 'Count'
p1.add_tools(HoverTool(tooltips=[#('Value', '$x{1.1111}'),
                                 ('Range', '@left{1.1}-@right{1.1}'),
                                 ('Count', '@count'),
                                 ]))

output_file('delay_test.html')

show(p1)
