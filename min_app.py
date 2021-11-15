import dash_devices
from dash_devices.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

app = dash_devices.Dash(__name__)
app.config.suppress_callback_exceptions = True


app.layout = html.Div([
    html.Div("Shared slider"),
    dcc.Slider(id='shared_slider', value=5, min=0, max=10, step=1, updatemode='drag'),
    html.Div(id='shared_slider_output'),

    html.Div("Regular slider"),
    dcc.Slider(id='regular_slider', value=5, min=0, max=10, step=1, updatemode='drag'),
    html.Div(id='regular_slider_output'),

    html.Div("Shared input"),
    dcc.Input(id="shared_input", type="text", value=''), 
    html.Div(id='shared_input_output'),

    html.Div("Regular input"),
    dcc.Input(id="regular_input", type="text", value=''), 
    html.Div(id='regular_input_output'),
])

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=5000)