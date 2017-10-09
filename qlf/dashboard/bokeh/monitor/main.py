from bokeh.plotting import figure, output_file, curdoc
from bokeh.models import ColumnDataSource, LabelSet, Label
from bokeh.driving import count
from dashboard.bokeh.helper import get_last_process
from bokeh.models import CustomJS, RadioGroup, Div, CheckboxGroup, Button
from bokeh.layouts import widgetbox, row, column, gridplot, layout, Spacer
import pandas as pd
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
from bokeh import events

import configparser
import os
import logging

import time
import subprocess
import select
import fcntl, os
import datetime
import time
import copy
from dashboard.bokeh.utils.outputs import Outputs

logger = logging.getLogger(__name__)

qlf_root = os.getenv('QLF_ROOT')
cfg = configparser.ConfigParser()

try:
    cfg.read('%s/qlf/config/qlf.cfg' % qlf_root)
    desi_spectro_redux = cfg.get('namespace', 'desi_spectro_redux')
except Exception as error:
    logger.error(error)
    logger.error("Error reading  %s/qlf/config/qlf.cfg" % qlf_root)

PROCESS = dict()

label_name = list()

for num in range(30):
    if 'z9' not in label_name:
        label_name.append('z' + str(num))
    elif 'r9' not in label_name:
        label_name.append('r' + str(num - 10))
    elif 'b9' not in label_name:
        label_name.append('b' + str(num - 20))

# Header Variables
time_widget = Div(text="")
date_widget = Div(text="")
exposure = Div(text="")

curdoc().add_root(Outputs.create_header(time_widget, date_widget, exposure))

# Main console widget
activate_main_console = CheckboxGroup(labels=['Scroll End'], active=[0])
main_console = Outputs.create_console(activate_main_console, "main_log")

# Injection console widget
activate_inject_console = CheckboxGroup(labels=['Scroll End'], active=[0])
inject_console = Outputs.create_console(activate_inject_console, "inject")

consoles = column(main_console, inject_console, css_classes=["consoles"])
curdoc().add_root(consoles)

# Stages tables
stages = Outputs.create_stages()
stage_columns = column(widgetbox(stages[0], stages[1], name="stage_table_r", css_classes=["stages"]),widgetbox(stages[2], stages[3], name="stage_table_b", css_classes=["stages"]),widgetbox(stages[4], stages[5], name="stage_table_z", css_classes=["stages"]), css_classes=["stage_columns"])
curdoc().add_root(stage_columns)

r = curdoc().session_context._document

f = Outputs.open_stream('logfile')
fcntl.fcntl(f.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

console_html = []

@count()
def update(t):
    date_widget.text = datetime.datetime.now().strftime("%Y-%m-%d")
    time_widget.text = datetime.datetime.now().strftime("%H:%M:%S")
    log_messages = ""
    while True:
        new_line = ''
        try:
            new_line = f.stdout.read()
            line_array = new_line.strip().decode('utf-8').split('\n')
            for eacharray in line_array:
                console_html.append("<p>"+ eacharray +"</p>")
        except:
            break
    for line in reversed(console_html):
        log_messages += line

    new_child = [Div(text="<div class=\"general_console\">" + log_messages + "</div>")]

    if activate_main_console._property_values['active'] != []:
        curdoc().set_select({"name": "main_log"}, {"children": new_child})

    new_child = [Div(text="<div class=\"general_console\"></div>")]

    if activate_inject_console._property_values['active'] != []:
        curdoc().set_select({"name": "inject"}, {"children": new_child})

    barsRight = list()

    for num in range(30):
        barsRight.append(0)

    proc_finished = False

    global PROCESS

    process = get_last_process()


    if process:
        process = process.pop()

        if PROCESS.get("id") != process.get("id"):
            proc_finished = True

        PROCESS = process
        exp_id = PROCESS.get("exposure")
        exposure.text = str(exp_id)
    stages = Outputs.create_stages()
    curdoc().set_select({"name": "stage_table_r"}, {"children": [stages[0], stages[1]]})
    curdoc().set_select({"name": "stage_table_b"}, {"children": [stages[2], stages[3]]})
    curdoc().set_select({"name": "stage_table_z"}, {"children": [stages[4], stages[5]]})
    
    for cam in label_name:
        cameralog = None
        log = str()
        try:
            for item in PROCESS.get("jobs", list()):
                if cam == item.get("camera"):
                    cameralog = os.path.join(desi_spectro_redux, item.get('logname'))
                    break
            if cameralog:
                arq = open(cameralog, 'r')
                log = arq.readlines()

        except Exception as e:
            logger.warn(e)

        if "Running Preproc" in ''.join(log):
            Outputs.update_stage(cam[:1], 0, int(cam[1:]), 'processing_stage')
        if "Checking version SIM" in ''.join(log):
            Outputs.update_stage(cam[:1], 1, int(cam[1:]), 'error_stage')
        if "Subtracting average overscan" in ''.join(log):
            Outputs.update_stage(cam[:1], 2, int(cam[1:]), 'success_stage')
        if "Median rdnoise and overscan" in ''.join(log):
            Outputs.update_stage(cam[:1], 3, int(cam[1:]), 'success_stage')
            

curdoc().add_periodic_callback(update, 1000)
