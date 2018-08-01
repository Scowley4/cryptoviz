import numpy as np
import pandas as pd
import os
import sys
import contextlib

from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file, save
from bokeh.models import HoverTool, ColumnDataSource, WheelZoomTool
from bokeh.embed import components
from bokeh.models import Range1d

C_TITLE = '#4FB3B7'
C_AXES = '#519397'
C_BG = '#111818'
C_BAR = '#355AA6'
C_BUY = '#117E1A'
C_SELL = '#7B1111'

DATA_FOLDER = './data/'
OUTPUTDATA_FOLDER = './data/Output_Example'

PAGES = './pages'

os.makedirs(PAGES, exist_ok=True)

def replace_nav(html, product_ids, active):
    pass


def replace_subnav(html, thiswer):
    pass




def main():
    pass
    # Build the nav bars and pages from templates

    # Build visualizations and plug into files

    # Gaps

    # Distributions

    # Delays

    # Time Series

if __name__ == '__main__':
    main()

