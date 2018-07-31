import numpy as np
import pandas as pd
import os
import sys

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file, save
from bokeh.models import HoverTool, ColumnDataSource, WheelZoomTool
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

trade_ids = []
indicators = []
missing = set(num for gap in gaps for num in range(gap[0], gap[1]+1))
for i in range(min_trade, max_trade+1):
    trade_ids.append(i)
    indicators.append(i not in missing)

quads = []
cur_indicator = indicators[0]
quad_left = trade_ids[0]
quad_indicators = []
i = 0
while i < len(trade_ids):
    if indicators[i] == cur_indicator:
        quad_right = trade_ids[i]
    if indicators[i] != cur_indicator or i==len(trade_ids)-1:
        quad_indicators.append(cur_indicator)
        quads.append((quad_left, quad_right))
        quad_left = trade_ids[i]
        quad_right = trade_ids[i]
        cur_indicator = indicators[i]
    i += 1
TOOLS = 'save,pan,box_zoom,xwheel_zoom,reset'

left = min_trade-100
right = max_trade+100
top = 1.2
bottom = -.2
x_range = Range1d(start=left, end=right, bounds=(left,right))
y_range = Range1d(start=bottom, end=top, bounds=(bottom,top))

p = figure(title=filename, tools=TOOLS,
            plot_width=1000,
            plot_height=300,
            x_range=x_range,
           # y_range=y_range,
            active_scroll='xwheel_zoom',
            toolbar_location='above',
            background_fill_color='#E8DDCB')
#p.add_tools(WheelZoomTool(dimensions='width'))

source = ColumnDataSource(data={
            'quad_left': [quad[0] for quad in quads],
            'quad_right': [quad[1]+1 for quad in quads],
            'top': [1 for x in quads],
            'bottom': [0 for x in quads],
            'range': quads,
            'fill': ['blue' if x else 'red' for x in quad_indicators],
            'indicator': quad_indicators
            })

p.quad(top='top', bottom='bottom', left='quad_left', right='quad_right',
       fill_color='fill',source=source)

p.legend.location='center_right'
p.legend.background_fill_color = 'darkgrey'
p.xaxis.axis_label = 'trade_id'
#p.yaxis.axis_label = 'Count'
p.yaxis.visible = False
p.add_tools(HoverTool(tooltips=[('trade_ids', '@range'),
                                #('missing', '@indicator'),
                                ]))

output_file('gap_bar_test.html')

show(p)

