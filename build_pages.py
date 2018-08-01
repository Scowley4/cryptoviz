import numpy as np
import pandas as pd
import os
import sys
import contextlib
from bs4 import BeautifulSoup

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file, save
from bokeh.models import HoverTool, ColumnDataSource, WheelZoomTool
from bokeh.embed import components
from bokeh.models import Range1d

C_TITLE = '#4FB3B7'
C_TEXT = '#4FB3B7'
C_AXES = '#519397'
C_CHART_BG = '#111818'
C_LEGEND_BG = 'red'
C_BAR = '#355AA6'
C_BUY = '#117E1A'
C_SELL = '#7B1111'

DATA_FOLDER = './data/'
OUTPUTDATA_FOLDER = './data/Output_Example'

PAGES = './pages'

os.makedirs(PAGES, exist_ok=True)

def delay_histogram(filename):
    full_filename = os.path.join(DATA_FOLDER, filename)
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

    p = figure(title=filename, tools=TOOLS,
                width=1000,
                x_range=x_range,
                y_range=y_range,
                active_scroll='wheel_zoom', background_fill_color=C_CHART_BG)

    source = ColumnDataSource(data={
                'count': hist,
                'center': centers,
                'left': edges[:-1],
                'right': edges[1:]})

    p.vbar(x='center', top='count', width=width, source=source,
           line_color='white', fill_color='black', hover_line_color='grey')
    p.legend.location='center_right'
    p.legend.background_fill_color = 'darkgrey'
    p.xaxis.axis_label = 'Delay time'
    p.yaxis.axis_label = 'Count'
    p.add_tools(HoverTool(tooltips=[#('Value', '$x{1.1111}'),
                                     ('Range', '@left{1.1}-@right{1.1}'),
                                     ('Count', '@count'),
                                     ]))

    output_file('delay_test.html')

    show(p)

def bundle_files(soup, css_files, js_files, write=False):
    """Bundle all files into one"""
    for filename in css_files:
        tag = soup.new_tag('style')
        with open(filename, 'r') as infile:
            tag.append(infile.read())
        soup.head.append(tag)

    for filename in js_files:
        tag = soup.new_tag('script')
        with open(filename, 'r') as infile:
            tag.append(infile.read())
        soup.body.insert_after(tag)

    if write:
        with open('outfile.html', 'w') as outfile:
            outfile.write(soup.prettify())



filename = './practice/sub_tab_test/test_plots.html'
with open(filename) as infile:
    html = infile.read()

soup = BeautifulSoup(html, 'html.parser')

css_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.css',
'./practice/sub_tab_test/styles.css']
js_files = ['./practice/sub_tab_test/bokehjs/bokeh-0.13.0.min.js']
bundle_files(soup, css_files, js_files, write=True)






def main():
    pass
    # Build visualizations and plug into files

    # Gaps

    # Distributions

    # Delays

    # Time Series

if __name__ == '__main__':
    main()

