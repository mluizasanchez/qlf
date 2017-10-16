from bokeh.models import Button
from functools import partial
from bokeh.layouts import widgetbox, row, column, gridplot, layout, Spacer
from bokeh.models import CustomJS, RadioGroup, Div, CheckboxGroup, Button
from dashboard.bokeh.helper import get_last_process

import logging
logger = logging.getLogger(__name__)

class GraphsHelper:
    def render_step_buttons(id, buttons):
        buttons[0].label = "COUNTPIX"
        buttons[1].label = "GETBIAS"
        buttons[2].label = "GETRMS"
        buttons[3].label = "XWSIGMA"
        if id == 0:
            buttons[0].label = "COUNTPIX"
            buttons[1].label = "GETBIAS"
            buttons[2].label = "GETRMS"
            buttons[3].label = "XWSIGMA"
            buttons[1].button_type = "success"
            buttons[2].button_type = "success"
            buttons[3].button_type = "success"
        if id == 1:
            buttons[0].label = "COUNTBINS"
            buttons[1].button_type = "link"
            buttons[2].button_type = "link"
            buttons[3].button_type = "link"
            buttons[1].label = None
            buttons[2].label = None
            buttons[3].label = None
        if id == 2:
            buttons[0].label = "INTEG"
            buttons[1].label = "SKYCONT"
            buttons[2].label = "SKYPEAK"
            buttons[3].label = "SKYRESID"
            buttons[1].button_type = "success"
            buttons[2].button_type = "success"
            buttons[3].button_type = "success"
        if id == 3:
            buttons[0].label = "SNR"
            buttons[1].button_type = "link"
            buttons[2].button_type = "link"
            buttons[3].button_type = "link"
            buttons[1].label = None
            buttons[2].label = None
            buttons[3].label = None
        return buttons

    def on_next_press_step(label, options, selected, buttons):
        selected['id'] = (selected['id'] + 1) % len(options)
        label.text = options[selected['id']]
        GraphsHelper.render_step_buttons(selected['id'], buttons)

    def on_previous_press_step(label, options, selected, buttons):
        selected['id'] = (selected['id'] - 1) % len(options)
        label.text = options[selected['id']]
        GraphsHelper.render_step_buttons(selected['id'], buttons)

    def create_next_button_step(label, options, selected, buttons):
        button_next = Button(label=">", button_type="success", css_classes=["nav_buttons"])
        button_next.on_click(partial(GraphsHelper.on_next_press_step, label=label, options=options, selected=selected, buttons=buttons))
        return button_next
    
    def create_previous_button_step(label, options, selected, buttons):
        button_previous = Button(label="<", button_type="success", css_classes=["nav_buttons"])
        button_previous.on_click(partial(GraphsHelper.on_previous_press_step, label=label, options=options, selected=selected, buttons=buttons))
        return button_previous

    def on_next_press(label, select):
        logger.error(label)
        cur_index = select.options.index(select.value)
        next_index = (cur_index + 1) % len(select.options)
        label.text = select.options[next_index]
        select.value = select.options[next_index]

    def on_previous_press(label, select):
        cur_index = select.options.index(select.value)
        next_index = (cur_index - 1) % len(select.options)
        label.text = select.options[next_index]
        select.value = select.options[next_index]

    def create_next_button(label, select):
        button_next = Button(label=">", button_type="success", css_classes=["nav_buttons"])
        button_next.on_click(partial(GraphsHelper.on_next_press, label=label, select=select))
        return button_next
    
    def create_previous_button(label, select):
        button_previous = Button(label="<", button_type="success", css_classes=["nav_buttons"])
        button_previous.on_click(partial(GraphsHelper.on_previous_press, label=label, select=select))
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



        return row(column_exposure, column_date, column_time, width=600, css_classes=['top_controls'])