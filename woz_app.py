import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import json
import collections
import zmq

def create_zmq_socket(zmq_port="5557", topicfilter=b""):
    """ Create a ZMQ SUBSCRIBE socket """
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://localhost:%s" % "5557")
    sub_socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    return sub_socket

def recv_zmq(topic='data'):
    with create_zmq_socket() as socket:
        msg = socket.recv()
    return msg.decode('utf-8')

def send_zmq(socket, d, topic='data'):
    return socket.send_string("%s" %d)

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:%s" % "5556")

with open("people_calendars.json", "r") as file:
    jp = json.load(file)
    file.close()

with open("group_calendars.json", "r") as file:
    jg = json.load(file)
    file.close()

with open("room_calendars.json", "r") as file:
    jr = json.load(file)
    file.close()

people = [{'label': key, 'value': key} for key, value in sorted(jp.items())]
groups = [{'label': key, 'value': key} for key, value in sorted(jg.items())]
rooms = [{'label': key, 'value': key} for key, value in sorted(jr.items())]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

app.layout = html.Div([
            html.H3('Graphdial Dashboard V1', style={'text-align': 'center'}),
            html.Div([
                #html.Div([
                    #dcc.Input(id="text-input", type="text", n_submit=1, placeholder="Say something...")]
                    #html.Button(id='listen-pause', n_clicks=0, children='Submit', style={'text-align': 'center'})]
                    #),
                #html.Br(),
                html.Div(id='placeholder-utterance', style={'width': '4%', 'display': 'inline-block'})],
                id='screen',
                style={'width': '400px', 'margin': '0 auto'}),
            
            #html.Div(id='input-utterance', style={'width': '10%', 'display': 'inline-block'}),
            html.Div("Utterance", id='user-utterance', style={'width': '10%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 30}),
            dcc.Interval(
                id='interval-component',
                interval=1*1000, # in milliseconds
                n_intervals=0
            ),
            # placeholder
            html.Div(style={'width': '10%', 'display': 'inline-block'}),
            html.H5("People", style={'width': '5%'}),
            dcc.Dropdown(
                id='people-dropdown',
                options=people,
                style={'width': '50%'}
            ),
            html.Div(id='people-output-container'),
            html.H5("Groups", style={'width': '5%'}),
            dcc.Dropdown(
                id='groups-dropdown',
                options=groups,
                style={'width': '50%', 'display': 'inline-block'}
            ),
            html.Div(id='groups-output-container'),
            html.H5("Rooms", style={'width': '5%'}),
            dcc.Dropdown(
                id='rooms-dropdown',
                options=rooms,
                style={'width': '50%', 'display': 'inline-block'}
            ),
            html.Div(id='rooms-output-container'),
            # placeholder
            html.Div(style={'width': '5%', 'display': 'inline-block'}),
            html.Div("Bot Response", id="update", style={'width': '20%', 'display': 'inline-block', 'fontSize': 30}),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            html.Div(
                dcc.Dropdown(
                    id = 'agent-response',
                    options = [{'label': i, 'value': i} for i in ["Hello!", "Sorry, I didn't understand that."]], 
            ), style={'width': '20%', 'display': 'inline-block'}),
            html.Button(id='send-button', n_clicks=0, children='Send', style={'text-align': 'center'}),
            # placeholder
            html.Div(style={'width': '5%', 'display': 'inline-block'}),
            dcc.Interval(
                id='socket-interval',
                interval=1*1000000, # in milliseconds
                n_intervals=0
            ),
            html.Div("NONE", id="response-holder", style={'width': '20%', 'display': 'hidden', 'fontSize': 30}),
            html.Div("", id="line-holder", style={'width': '20%', 'display': 'hidden', 'fontSize': 30})
        ])

@app.callback(
    Output('people-output-container', 'children'),
    Input('people-dropdown', 'value')
)
def update_people_calendar(value):
    if value == None:
        return html.P("No Events to Display")
    if len(jp[value]) == 0:
        return html.P("No Events to Display")
    else:
        return [html.P(str(item)) for item in jp[value]]

@app.callback(
    Output('groups-output-container', 'children'),
    Input('groups-dropdown', 'value')
)
def update_groups_calendar(value):
    if value == None:
        return html.P("No Events to Display")
    if len(jg[value]) == 0:
        return html.P("No Events to Display")
    else:
        return [html.P(str(item)) for item in jg[value]]

@app.callback(
    Output('rooms-output-container', 'children'),
    Input('rooms-dropdown', 'value')
)
def update_events_calendar(value):
    if value == None:
        return html.P("No Events to Display")
    if len(jr[value]) == 0:
        return html.P("No Events to Display")
    else:
        return [html.P(str(item)) for item in jr[value]]

@app.callback(
    Output(component_id='user-utterance', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')]
)
def receive_utterance(n_intervals):
    print("Listening...")
    response = recv_zmq()
    print(response)
    return response

@app.callback(
    [Output(component_id='agent-response', component_property='value'),
    Output(component_id='update', component_property='children'),
    Output(component_id='response-holder', component_property='children')],
    [Input(component_id='send-button', component_property='n_clicks')],
    [State(component_id='agent-response', component_property='value')]
)
def create_response(response, value):
    send_zmq(pub_socket, value)
    return '', "Last Response: ", str(value)

@app.callback(
    Output(component_id='line-holder', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')],
    [State(component_id='response-holder', component_property='children')]
)
def send_response(_, response):
    send_zmq(pub_socket, response)
    return ""

if __name__ == '__main__':  
    #app.run_server(debug=True)
    app.run_server(debug=True, use_reloader=False)