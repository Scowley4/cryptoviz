import numpy as np
import pandas as pd
import os
import sys

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool, ColumnDataSource



df = pd.read_csv('./08_BTC_BCH_1_FINAL.csv')

BINS=50


hist, edges = np.histogram(df['Open'], bins=BINS)


#mu, sigma = 0, .5
#samples = np.random.normal(mu, sigma, 1000)
#hist, edges = np.histogram(samples, density=False, bins=50)




TOOLS = 'save,pan,box_zoom,wheel_zoom'
p1 = figure(title='Normal Dist', tools=TOOLS, active_scroll='wheel_zoom',background_fill_color='#E8DDCB')

centers = (edges[:-1]+edges[1:])/2
width = abs(centers[0]-centers[1])

#p1.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
#        fill_color='#036564', line_color='#033649')
source = ColumnDataSource(data={'count':hist, 'centers':centers})
p1.vbar(x='centers', top='count', width=width, source=source,
       line_color='white', fill_color='black', hover_line_color='grey')
p1.legend.location='center_right'
p1.legend.background_fill_color = 'darkgrey'
p1.xaxis.axis_label = 'x'
p1.yaxis.axis_label = 'P(x)'
p1.add_tools(HoverTool(tooltips=[('Value', '$x{1.1111}'), ('Count', '@count')]))

#p1.toolbar.active_scroll='wheel_zoom'

output_file('single_histogram.html', title='histogram example')
show(p1)
