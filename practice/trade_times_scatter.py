import numpy as np
import pandas as pd
import os
import sys

from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.sampledata.commits import data
from bokeh.transform import jitter
from bokeh.palettes import Category20

csv_path = '../data/example.csv'

df = pd.read_csv(csv_path,
                 index_col=None,
                 parse_dates=['server_datetime',
                              'exchange_datetime'])

product_ids = set(df['product_id'])

product_df = df[df['product_id']=='BTC_BCH'].copy()

product_df['weekday_name'] = product_df['exchange_datetime'].dt.weekday_name
product_df['time'] = product_df['exchange_datetime'].dt.time

# Setting color based on product_id
#color_map = {product_id: Category20[len(product_ids)][i] for i, product_id in enumerate(product_ids)}
#color_map = {product_id: 'red' for product_id in product_ids}
#product_df['color'] = [color_map[product_id] for product_id in product_df['product_id']]

# Setting color based on buy/sell
color_map = {'sell': 'red', 'buy': 'blue'}
product_df['color'] = [color_map[side] for side in product_df['side']]


DAYS = ['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tueday',
'Monday']

source = ColumnDataSource(product_df)

TOOLS = 'save,pan,box_zoom,xwheel_zoom,reset'
p = figure(plot_width=800, plot_height=300, y_range=DAYS,
           tools=TOOLS,
           active_scroll='xwheel_zoom',
           x_axis_type='datetime',
           title='title')

p.circle(x='time', y=jitter('weekday_name', width=0.6, range=p.y_range),
         source=source, alpha=0.3, fill_color='color')

p.xaxis[0].formatter.days = ['%Hh']

p.x_range.range_padding = 0

p.ygrid.grid_line_color = None

output_file('scatter_test.html')
show(p)
