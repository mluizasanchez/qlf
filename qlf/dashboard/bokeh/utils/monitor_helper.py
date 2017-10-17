from bokeh.plotting import figure, output_file, curdoc
from bokeh.models import ColumnDataSource, LabelSet, Label
from bokeh.driving import count
from dashboard.bokeh.helper import get_last_process
from bokeh.models import CustomJS, RadioGroup, Div, CheckboxGroup, Button
from bokeh.layouts import widgetbox, row, column, gridplot, layout, Spacer
import pandas as pd
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
import requests
from functools import partial

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


logger = logging.getLogger(__name__)

cams_stages_r = list()
for i in range(4):
    cams_stages_r.append(
            dict(
            camera=[i for i in range(10)],
        )
    )

cams_stages_b = copy.deepcopy(cams_stages_r)
cams_stages_z = copy.deepcopy(cams_stages_r)

class MonitorHelper():
    def open_stream(filename):
        qlf_root = os.getenv('QLF_ROOT')
        cfg = configparser.ConfigParser()
        try:
            cfg.read('%s/qlf/config/qlf.cfg' % qlf_root)
            desi_spectro_redux = cfg.get('namespace', 'desi_spectro_redux')
        except Exception as error:
            logger.error(error)
            logger.error("Error reading  %s/qlf/config/qlf.cfg" % qlf_root)
        try:
            logfile = cfg.get('main', filename)
            return subprocess.Popen(['tail', '+2','-F', logfile],\
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        except Exception as e:
            logger.warn(e)
    
    def update_stage(band, stage, camera, status):
        if band == 'r':
            cams_stages_r[stage]['camera'][camera] = status
        if band == 'z':
            cams_stages_z[stage]['camera'][camera] = status
        if band == 'b':
            cams_stages_b[stage]['camera'][camera] = status

    def create_table(cam_stage, header):
        column_names = ["Pre Processing", "Spectral Extraction", "Fiber Flattening", "Sky Subtraction"]
        table_text = "<table>"
        if header:
            table_text += "<tr>"
            for column in column_names:
                table_text += "<td>" + column + "</td>"
            table_text += "</tr>"
        for camera in range(10):
            table_text += "<tr>"
            for stage in range(4):
                table_text += "<td onclick=\"openDialog(event)\" class=\"" + str(cam_stage[stage]['camera'][camera]) + " camera_stage\"></td>"
            table_text += "<td><i class=\"fa fa-plus-circle\" aria-hidden=\"true\"></i></td>"
            table_text += "</tr>"
        table_text += "</table>"
        return table_text

    def create_stages():
        b_band = Div(text=MonitorHelper.create_table(cams_stages_b, True))
        r_band = Div(text=MonitorHelper.create_table(cams_stages_r, False))
        z_band = Div(text=MonitorHelper.create_table(cams_stages_z, False))

        b_label = Div(text="<b class=\"band_label\">b</b>")
        r_label = Div(text="<b class=\"band_label\">r</b>")
        z_label = Div(text="<b class=\"band_label\">z</b>")

        return [b_label, b_band, r_label, r_band, z_label, z_band]

    def dispatch_event(event):
        QLF_BASE_URL = os.environ.get('QLF_BASE_URL',
                            'http://localhost:8000')
        return requests.get(QLF_BASE_URL+event).json()

    def create_header(time_widget, date_widget, exposure, status):
        reduct_mode = widgetbox(Div(text="<b>Reduction Mode:</b>"))

        radio = RadioGroup(labels=['Manual', 'Automatic'], active=1)
        column_mode = column(reduct_mode, widgetbox(radio))

        process = get_last_process()

        exposure_label = Div(text="<b>Exposure Id</b>")
        column_exposure = column(exposure_label, exposure, css_classes=['column_exposure'])

        status_label = Div(text="<b>Status</b>")
        status_column = column(status_label, status, css_classes=['column_status'])

        date_label = Div(text="<b>Date</b>")
        column_date = column(date_label, date_widget, css_classes=['column_date'])

        time_label = Div(text="<b>Time</b>")
        column_time = column(time_label, time_widget, css_classes=['column_time'])



        return row(status_column, column_exposure, column_date, column_time, sizing_mode='scale_height', css_classes=['top_controls'])

    def create_controls():
        controls = []
        controls.append(Button(label='START', button_type="success", width=50))
        controls.append(Button(label='STOP', button_type="danger", width=50))
        controls.append(Button(label='RESET', button_type="warning", width=50))

        for index, event in enumerate(['/start', '/stop', '/restart']):
            controls[index].on_click(partial(MonitorHelper.dispatch_event, event=event))

        buttons = column(*controls, css_classes=["btn_group"])
        return row(buttons, sizing_mode='scale_height', css_classes=['top_controls'])

    def create_console(checkbox, console_name):
        main_log = widgetbox(Div(text="<textarea textarea class=\"general_console\" disabled></textarea>"), name=console_name)
        # return column(row(main_log), row(checkbox), css_classes=["main_console"])
        return column(row(main_log), css_classes=["main_console"])