from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Slider, CheckboxGroup, RadioButtonGroup, Div, LabelSet,\
    OpenURL, TapTool, HoverTool, Button
from bokeh.models.widgets import Select, Slider

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
from dashboard.bokeh.graphs.bias import Bias
from dashboard.bokeh.graphs.snr import SNR
from dashboard.bokeh.helper import get_arms_and_spectrographs
from functools import partial

logger = logging.getLogger(__name__)

# Header Variables
time_widget = Div(text="")
date_widget = Div(text="")
exposure = Div(text="4")

date_widget.text = "<p class=\"date_label\">" + datetime.datetime.now().strftime("%Y-%m-%d") + "</p>"
time_widget.text = "<p class=\"time_label\">" + datetime.datetime.now().strftime("%H:%M:%S") + "</p>"

header_row = row(GraphsHelper.create_header(time_widget, date_widget, exposure), width=130)

step_title = Div(text="<p class=\"box_label\">Step</p>")

step_label = Div(text="", css_classes=["step_label"])

step_names = ["Pre Processing", "Spectral Extraction", "Fiber Flattening", "Sky Subtraction"]
step_label.text = step_names[0]
selected_step = dict()
selected_step['id'] = 0

cameras = get_arms_and_spectrographs()

# we can filter by spectrograph
spectrograph_select = Select(
    title="Spectrograph:",
    value="0",
    options=cameras["spectrographs"],
    width=100)

# and arm
arm_select = Select(
    title="Arm:",
    options=cameras['arms'],
    value="b",
    width=100)

# Metrics Box
metrics_box = Div(text="<p class=\"metric_box\">Metrics</p>")

snr_graph = SNR.get_snr("4", arm_select, spectrograph_select)
bias_graph = Bias.get_bias("4", arm_select, spectrograph_select)

graphs_box = Div(text="<p class=\"graphs_box\"></p>")

# Metric Buttons
def handle_button(button):
    logger.error(vars(button))
    logger.error(button.label == "SNR")
    if button.label == "SNR":
        curdoc().set_select({"name": "graphs"}, {"children": [row(snr_graph, name="graphs")]})
    if button.label == "GETBIAS":
        curdoc().set_select({"name": "graphs"}, {"children": [row(bias_graph, name="graphs")]})
        
buttons = list()
for i in range(4):
    new_button = Button(label='init', button_type="success")
    new_button.on_click(partial(handle_button, button=new_button))
    buttons.append(new_button)

buttons[0].label = "COUNTPIX"
buttons[1].label = "GETBIAS"
buttons[2].label = "GETRMS"
buttons[3].label = "XWSIGMA"

render_buttons = column(*buttons, css_classes=["metric_box"])

select_step = row(GraphsHelper.create_previous_button_step(step_label, step_names, selected_step, buttons), step_label, GraphsHelper.create_next_button_step(step_label, step_names, selected_step, buttons))

spectrograph_title = Div(text="<p class=\"box_label\">Spectrograph</p>")

spectrograph_label = Div(text="")

spectrograph_names = [str(i) for i in range(10)]
spectrograph_label.text = spectrograph_names[0]
selected_spectrograph = dict()
selected_spectrograph['id'] = 0


select_spectrograph = row(GraphsHelper.create_previous_button(spectrograph_label, spectrograph_select), spectrograph_label, GraphsHelper.create_next_button(spectrograph_label, spectrograph_select), width=500)

camera_title = Div(text="<p class=\"box_label\">Arm</p>")

camera_label = Div(text="")

camera_names = ["b", "r", "z"]
camera_label.text = camera_names[0]

select_camera = row(GraphsHelper.create_previous_button(camera_label, arm_select), camera_label, GraphsHelper.create_next_button(camera_label, arm_select))

options_row = row(column(step_title, select_step, css_classes=['column_box']), column(spectrograph_title, select_spectrograph, css_classes=['column_box']), column(camera_title, select_camera, css_classes=['column_box']), css_classes=['top_controls'])

graphs_box = row(graphs_box, name="graphs")

right_side = column(header_row, options_row, graphs_box, css_classes=["right_side"])
curdoc().add_root(row(render_buttons, right_side))      

# item = curdoc().select({"name": "graphs"})
# logger.error(item)
# curdoc().set_select({"name": "graphs"}, {"children": [row(bias_graph, name="graphs")]})

