from bokeh.models import Button
from functools import partial
from bokeh.layouts import widgetbox, row, column, gridplot, layout, Spacer
from bokeh.models import CustomJS, RadioGroup, Div, CheckboxGroup, Button
from dashboard.bokeh.helper import get_last_process

import logging
logger = logging.getLogger(__name__)

class GraphsHelper:
    def on_next_press(label, options, selected):
        selected['id'] = (selected['id'] + 1) % len(options)
        label.text = options[selected['id']]

    def on_previous_press(label, options, selected):
        selected['id'] = (selected['id'] - 1) % len(options)
        label.text = options[selected['id']]

    def create_next_button(label, options, selected):
        button_next = Button(label=">", button_type="success", css_classes=["nav_buttons"])
        button_next.on_click(partial(GraphsHelper.on_next_press, label=label, options=options, selected=selected))
        return button_next
    
    def create_previous_button(label, options, selected):
        button_previous = Button(label="<", button_type="success", css_classes=["nav_buttons"])
        button_previous.on_click(partial(GraphsHelper.on_previous_press, label=label, options=options, selected=selected))
        return button_previous

    def create_header(time_widget, date_widget, exposure):
        reduct_mode = widgetbox(Div(text="<b>Reduction Mode:</b>"))

        radio = RadioGroup(labels=['Manual', 'Automatic'], active=1)
        column_mode = column(reduct_mode, widgetbox(radio))

        process = get_last_process()

        exposure_label = Div(text="<b>Exposure Id</b>")
        column_exposure = column(exposure_label, exposure, css_classes=['column_exposure'])

        date_label = Div(text="<b>Date</b>")
        column_date = column(date_label, date_widget, css_classes=['column_date'])

        time_label = Div(text="<b>Time</b>")
        column_time = column(time_label, time_widget, css_classes=['column_time'])



        return row(column_exposure, column_date, column_time, sizing_mode='scale_height', css_classes=['top_controls'])