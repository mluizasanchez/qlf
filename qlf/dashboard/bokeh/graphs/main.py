from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Slider, CheckboxGroup, RadioButtonGroup, Div, LabelSet,\
    OpenURL, TapTool, HoverTool, Button

from bokeh.plotting import curdoc, figure
from bokeh.charts.utils import df_from_json
from bokeh.charts import Donut
import datetime
import time

from dashboard.bokeh.helper import get_exposures, get_cameras
import pandas as pd
import logging

from dashboard.bokeh.utils.monitor_helper import MonitorHelper
from dashboard.bokeh.utils.graphs_helper import GraphsHelper

logger = logging.getLogger(__name__)

# Metrics Box
metrics_box = Div(text="<p class=\"metrix_box\">Metrics</p>")

# Header Variables
time_widget = Div(text="")
date_widget = Div(text="")
exposure = Div(text="")

date_widget.text = "<p class=\"date_label\">" + datetime.datetime.now().strftime("%Y-%m-%d") + "</p>"
time_widget.text = "<p class=\"time_label\">" + datetime.datetime.now().strftime("%H:%M:%S") + "</p>"

header_row = row(GraphsHelper.create_header(time_widget, date_widget, exposure))

stage_title = Div(text="<p class=\"box_label\">Stage</p>")

stage_label = Div(text="")

stage_names = ["Pre Processing", "Spectral Extraction", "Fiber Flattening", "Sky Subtraction"]
stage_label.text = stage_names[0]
selected_stage = dict()
selected_stage['id'] = 0

select_stage = row(GraphsHelper.create_previous_button(stage_label, stage_names, selected_stage), stage_label, GraphsHelper.create_next_button(stage_label, stage_names, selected_stage))

spectrograph_title = Div(text="<p class=\"box_label\">Spectrograph</p>")

spectrograph_label = Div(text="")

spectrograph_names = [str(i) for i in range(10)]
spectrograph_label.text = spectrograph_names[0]
selected_spectrograph = dict()
selected_spectrograph['id'] = 0

select_spectrograph = row(GraphsHelper.create_previous_button(spectrograph_label, spectrograph_names, selected_spectrograph), spectrograph_label, GraphsHelper.create_next_button(spectrograph_label, spectrograph_names, selected_spectrograph))

camera_title = Div(text="<p class=\"box_label\">Camera</p>")

camera_label = Div(text="")

camera_names = ["b", "r", "z"]
camera_label.text = camera_names[0]
selected_camera = dict()
selected_camera['id'] = 0

select_camera = row(GraphsHelper.create_previous_button(camera_label, camera_names, selected_camera), camera_label, GraphsHelper.create_next_button(camera_label, camera_names, selected_camera))

options_row = row(column(stage_title, select_stage, css_classes=['column_box']), column(spectrograph_title, select_spectrograph, css_classes=['column_box']), column(camera_title, select_camera, css_classes=['column_box']), css_classes=['top_controls'])

graphs_box = Div(text="<p class=\"graphs_box\"></p>")

right_side = column(header_row, options_row, graphs_box)

curdoc().add_root(row(metrics_box, right_side))