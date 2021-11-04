import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
import dash_table as dt
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
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
            html.H3('GraphDial Dashboard', style={'text-align': 'center', 'color': 'white', 'background': 'green'}),
            html.Div("Last User Utterance:", id='utterance-label', style={'text-align': 'center', 'width': '25%', 'fontSize': 15,'background': 'tan'}),
            html.Div("Utterance", id='user-utterance', style={'text-align': 'center', 'width': '25%', 'fontSize': 20,'background': 'tan'}),
            #html.Div([
            #    html.Div(id='placeholder-utterance', style={'width': '4%', 'display': 'inline-block'})],
            #    id='screen',
            #    style={'width': '400px', 'margin': '0 auto'}),
            
            #html.Div(id='input-utterance', style={'width': '10%', 'display': 'inline-block'}),
            dcc.Interval(
                id='interval-component',
                interval=1*1000, # in milliseconds
                n_intervals=0
            ),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            # placeholder
            html.Div("Bot Response", id="update", style={'text-align': 'center', 'fontSize': 30}),
            html.Div("", id="response-holder", style={'text-align': 'center', 'fontSize': 30}),
            html.Div("", id="line-holder", style={'width': '20%', 'hidden': 'hidden', 'fontSize': 30}),
            html.Div(
                [dcc.Dropdown(
                    id = 'agent-response',
                    placeholder = "Select Template...",
                    options = [{'label': i, 'value': i} for i in ["Hello!", "Sorry, I didn't understand that.", "_Person_ is available!"]]
                )],
                style={'width': '20%', 'align-items': 'center', 'justify-content': 'center', 'padding-left': '40%'}),
            html.Div(
                [html.Button(
                    id='send-button', 
                    n_clicks=0, 
                    children='Send', 
                    style={'align': 'center', 'display': 'flex',  'justify': 'center'}
                )],
                style={'align-items': 'center', 'justify-content': 'center', 'padding-left': '40%'}),
            # placeholder
            html.Div("Person Here", id="selected-person", style={'text-align': 'center', 'fontSize': 15, 'display': 'inline-block'}),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            html.Div("Group Here", id="selected-group", style={'text-align': 'center', 'fontSize': 15, 'display': 'inline-block'}),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            html.Div("Room Here", id="selected-room", style={'text-align': 'center', 'fontSize': 15, 'display': 'inline-block'}),
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
                style={'width': '50%'}
            ),
            html.Div(id='groups-output-container'),
            html.H5("Rooms", style={'width': '5%'}),
            dcc.Dropdown(
                id='rooms-dropdown',
                options=rooms,
                style={'width': '50%'}
            ),
            html.Div(id='rooms-output-container'),
            # placeholder
            html.Div(style={'width': '5%', 'display': 'inline-block'}),
            dcc.Interval(
                id='socket-interval',
                interval=1*1000000, # in milliseconds
                n_intervals=0 #MUST BE 0
            )
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
        #return [html.P(str(item)) for item in jp[value]]
        df = pd.DataFrame(jp[value])
        df["attendees"] = df["attendees"].apply(lambda x: ", ".join(x))
        return dt.DataTable(
                id='person-tbl', data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                )
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
        #return [html.P(str(item)) for item in jg[value]]
        df = pd.DataFrame(jg[value])
        df["attendees"] = df["attendees"].apply(lambda x: ", ".join(x))
        return dt.DataTable(
                id='group-tbl', data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                )

@app.callback(
    Output('rooms-output-container', 'children'),
    Input('rooms-dropdown', 'value')
)
def update_rooms_calendar(value):
    if value == None:
        return html.P("No Events to Display")
    if len(jr[value]) == 0:
        return html.P("No Events to Display")
    else:
        #return [html.P(str(item)) for item in jr[value]]
        df = pd.DataFrame(jr[value])
        df["attendees"] = df["attendees"].apply(lambda x: ", ".join(x))
        return dt.DataTable(
                id='room-tbl', data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={'textAlign': 'left'},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                )

@app.callback(
    Output('selected-person', 'children'),
    Input('person-tbl', 'active_cell'),
    State('person-tbl', 'data')
)
def fill_person(selected_entity, data):
    try:
        return data[selected_entity['row']][selected_entity['column_id']]
    except:
        return ""

@app.callback(
    Output('selected-group', 'children'),
    Input('group-tbl', 'active_cell'),
    State('group-tbl', 'data')
)
def fill_group(selected_entity, data):
    try:
        return data[selected_entity['row']][selected_entity['column_id']]
    except:
        return ""

@app.callback(
    Output('selected-room', 'children'),
    Input('room-tbl', 'active_cell'),
    State('room-tbl', 'data')
)
def fill_room(selected_entity, data):
    try:
        return data[selected_entity['row']][selected_entity['column_id']]
    except:
        return ""

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