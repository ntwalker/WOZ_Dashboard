import dash_devices
from dash_devices.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_table as dt
import plotly.express as px
import pandas as pd
import numpy as np
import json
import collections
import zmq
import speech_recognition as sr
import numpy as np
import random
import copy
import os
import re
import base64

app = dash_devices.Dash(__name__)
#app = dash_devices.Dash()
app.config.suppress_callback_exceptions = True

r = sr.Recognizer()

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

people_table = pd.DataFrame(jp[people[0]['label']])
people_table = pd.DataFrame(columns=people_table.columns)
groups_table = pd.DataFrame(jg[groups[0]['label']])
groups_table = pd.DataFrame(columns=groups_table.columns)
rooms_table = pd.DataFrame(jr[rooms[0]['label']])
rooms_table = pd.DataFrame(columns=rooms_table.columns)

#Dialogue Templates:
agent_templates = ["Hello!", 
"Sorry, I didn't understand that.", 
"_Person_ is available!",
"_Person_ is available at _Time_!",
"_Person_ is available at _Time_ on _Date_!"]

##User Page Objects##
image_filename = os.path.join(os.getcwd(), 'chatbot.jpg')
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

# Feedback to know when button is listening
white_button_style = {'background-color': 'white',
                      'color': 'black',
                      'height': '50px',
                      'width': '200px',
                      'margin-top': '50px',
                      'margin-left': '50px'}

red_button_style = {'background-color': 'red',
                    'color': 'white',
                    'height': '50px',
                    'width': '200px',
                    'margin-top': '50px',
                    'margin-left': '50px'}

wizard_page = html.Div([
            html.H3('GraphDial Dashboard', style={'text-align': 'center', 'color': 'white', 'background': 'green'}),
            html.Div("Last User Utterance:", id='utterance-label', style={'text-align': 'center', 'width': '25%', 'fontSize': 15,'background': 'tan'}),
            html.Div("Utterance", id='user-utterance', style={'text-align': 'center', 'width': '25%', 'fontSize': 20,'background': 'tan'}),
            #html.Div([
            #    html.Div(id='placeholder-utterance', style={'width': '4%', 'display': 'inline-block'})],
            #    id='screen',
            #    style={'width': '400px', 'margin': '0 auto'}),
            
            #html.Div(id='input-utterance', style={'width': '10%', 'display': 'inline-block'}),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            # placeholder
            #html.Div("Bot Response", id="update", style={'text-align': 'left', 'display': 'inline-block', 'fontSize': 30}),
            html.Div("[Template Here]", id="response-holder", style={'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'padding-left': '30%'}),
            html.Div(
                [dcc.Dropdown(
                    id = 'wizard-agent-response',
                    placeholder = "Select Template...",
                    options = [{'label': i, 'value': i} for i in agent_templates]
                )],
                style={'width': '30%', 'align-items': 'left', 'justify-content': 'left'}), #, 'padding-left': '40%'
            html.Div(
                [html.Button(
                    id='send-button', 
                    n_clicks=0, 
                    children='Send', 
                    style={'align': 'center', 'display': 'flex',  'justify': 'left'}
                )],
                style={'align-items': 'center', 'justify-content': 'center', 'padding-left': '40%'}),
            # placeholder
            html.Div(style={'width': '5%'}),
            html.Div([], id="selected-person", style={'text-align': 'center', 'fontSize': 15, 'display': 'inline-block'}),
            html.Div([
                html.Button(
                        id='add-person-button', 
                        n_clicks=0, 
                        children='compose', 
                        style={'align': 'left', 'display': 'inline-block',  'justify': 'left'}
                    ),
                html.Button(
                        id='clear-person-button', 
                        n_clicks=0, 
                        children='clear', 
                        style={'align': 'left', 'display': 'inline-block',  'justify': 'left'}
                    )], style={'width': '20%', 'align-items': 'left', 'justify-content': 'left'}),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            html.Div("Group Here", id="selected-group", style={'text-align': 'center', 'fontSize': 15, 'display': 'inline-block'}),
            html.Button(
                    id='add-group-button', 
                    n_clicks=0, 
                    children='add', 
                    style={'align': 'left', 'display': 'flex',  'justify': 'left'}
                ),
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            html.Div("Room Here", id="selected-room", style={'text-align': 'center', 'fontSize': 15, 'display': 'inline-block'}),
            html.Button(
                    id='add-room-button', 
                    n_clicks=0, 
                    children='add', 
                    style={'align': 'left', 'display': 'flex',  'justify': 'left'}
                ),
            html.Div(style={'width': '10%', 'display': 'inline-block'}),
            html.H5("People", style={'width': '5%'}),
            html.Div([dcc.Dropdown(
                id='people-dropdown',
                options=people,
                style={'width': '50%'}
            )]),
            dt.DataTable(
                id='person-tbl', data=people_table.to_dict('records'),
                columns=[{"name": i, "id": i} for i in people_table.columns],
                style_cell={'textAlign': 'left', "whiteSpace": "pre-line"},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                ),
            html.H5("Groups", style={'width': '5%'}),
            dcc.Dropdown(
                id='groups-dropdown',
                options=groups,
                style={'width': '50%'}
            ),
            dt.DataTable(
                id='groups-tbl', data=groups_table.to_dict('records'),
                columns=[{"name": i, "id": i} for i in groups_table.columns],
                style_cell={'textAlign': 'left', "whiteSpace": "pre-line"},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                ),
            html.H5("Rooms", style={'width': '5%'}),
            dcc.Dropdown(
                id='rooms-dropdown',
                options=rooms,
                style={'width': '50%'}
            ),
            dt.DataTable(
                id='rooms-tbl', data=rooms_table.to_dict('records'),
                columns=[{"name": i, "id": i} for i in rooms_table.columns],
                style_cell={'textAlign': 'left', "whiteSpace": "pre-line"},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                ),
            # placeholder
            html.Div(style={'width': '5%', 'display': 'inline-block'})
        ])

user_page = html.Div([
    html.H3('GraphDial User Dashboard', style={'text-align': 'center', 'color': 'white', 'background': 'green'}),
    #html.I("Bot Response", id="agent-label", style={'width': '20%', 'text-align': 'center', 'display': 'inline-block'}),
    html.Div("Recognized Speech", id="user-utt-label", style={'width': '30%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'background': 'gray'}),
    html.Div("Speak Into the Microphone", id="button-label", style={'width': '33%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'background': 'gray'}),
    html.Div("Bot Response", id="agent-label", style={'width': '33%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'background': 'gray'}),
    html.Br(),
    html.Div("", id="transcription", style={'width': '30%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 30, 'color': 'gray'}),
    html.Div([
            #dcc.Input(id="text-input", type="text", n_submit=1, placeholder="Say something..."),
            html.Button(id='listen-pause', n_clicks=0, children='Record Message', style=white_button_style)],
            style={'width': '30%', 'text-align': 'center', 'align-items': 'center', 'justify-content': 'center', 'display': 'inline-block'}
            ),
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width': '7%', 'display': 'inline-block', 'height': '100px'}),
    html.Div("Bot Response", id="user-agent-response", style={'display': 'inline-block', 'fontSize': 15}),
    html.Div("Please try again", id="warning", style={'text-align': 'center', 'color': 'red'})
    ])


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Input(id="access", type="text", value=''),
    html.Button(id='change', n_clicks=0, children='admin', style={'text-align': 'center'}),
    html.Div(user_page, id='user-content'),
    html.Div(wizard_page, id='wizard-content'),
])


# app.layout = html.Div([
#     html.Div("Shared slider"),
#     dcc.Slider(id='shared_slider', value=5, min=0, max=10, step=1, updatemode='drag'),
#     html.Div(id='shared_slider_output'),

#     html.Div("Regular slider"),
#     dcc.Slider(id='regular_slider', value=5, min=0, max=10, step=1, updatemode='drag'),
#     html.Div(id='regular_slider_output'),

#     html.Div("Shared input"),
#     dcc.Input(id="shared_input", type="text", value=''), 
#     html.Div(id='shared_input_output'),

#     html.Div("Regular input"),
#     dcc.Input(id="regular_input", type="text", value=''), 
#     html.Div(id='regular_input_output'),
# ])

# Page navigation callbacks
@app.callback([Output('wizard-content', 'children'),
                Output('user-content', 'children'),
                Output('access', 'value')],
              [Input('change', 'n_clicks')],
              [State('access', 'value')])
def display_page(n_clicks, password):
    if password == "wizard":
        return [html.Div(wizard_page, id='wizard'), html.Div(user_page, id='user', hidden='hidden'), ""]
    else:
        return [html.Div(wizard_page, id='wizard', hidden='hidden'), html.Div(user_page, id='user'), ""]

###WIZARD PAGE CALLBACKS###

@app.callback(
    [Output('person-tbl', 'data')],
    [Input('people-dropdown', 'value')]
)
def update_people_calendar(value):
    df = pd.DataFrame(jp[people[0]['label']])
    df = pd.DataFrame(columns=df.columns)
    if value == None:
        return [people_table.to_dict('records')]
    else:
        df = pd.DataFrame(jp[value])
        return [df.to_dict('records')]

@app.callback(
    [Output('groups-tbl', 'data')],
    [Input('groups-dropdown', 'value')]
)
def update_groups_calendar(value):
    df = pd.DataFrame(jg[groups[0]['label']])
    df = pd.DataFrame(columns=df.columns)
    if value == None:
        return [groups_table.to_dict('records')]
    else:
        df = pd.DataFrame(jg[value])
        return [df.to_dict('records')]

@app.callback(
    [Output('rooms-tbl', 'data')],
    [Input('rooms-dropdown', 'value')]
)
def update_rooms_calendar(value):
    df = pd.DataFrame(jr[rooms[0]['label']])
    df = pd.DataFrame(columns=df.columns)
    if value == None:
        return [rooms_table.to_dict('records')]
    else:
        df = pd.DataFrame(jr[value])
        return [df.to_dict('records')]

@app.callback(
    [Output('response-holder', 'children')],
    [Input('add-person-button', 'n_clicks'),
    Input('send-button', 'n_clicks')],
    [State('wizard-agent-response', 'value'),
    State('selected-person', 'children')]
)
def add_person_entity_to_template(_, __, template, entity_list):
    ctx = dash_devices.callback_context

    if ctx.triggered[0]['prop_id'] == "send-button.n_clicks":
        return [""]

    if entity_list == []:
        return [template]
    else:
        for item in entity_list:
            template = re.sub(r"_(Person|Time|Date)_", item, template, 1)
        return [template]

@app.callback(
    [Output('selected-person', 'children')],
    [Input('person-tbl', 'active_cell'),
    Input('clear-person-button', 'n_clicks'),
    Input('send-button', 'n_clicks')],
    [State('person-tbl', 'data'),
    State('selected-person', 'children')]
)
def select_entity(selected_entity, _, __, data, prev):

    ctx = dash_devices.callback_context

    if ctx.triggered[0]['prop_id'] == "clear-person-button.n_clicks":
        return [[]]
    if ctx.triggered[0]['prop_id'] == "send-button.n_clicks":
        return [[]]

    if selected_entity == None:
        return [prev]
    try:
        prev.append(data[selected_entity['row']][selected_entity['column_id']])
        return [prev]
    except:
        return [prev]


@app.callback(
    [Output('selected-group', 'children')],
    [Input('groups-tbl', 'active_cell')],
    [State('groups-tbl', 'data')]
)
def select_group(selected_entity, data):
    try:
        return [data[selected_entity['row']][selected_entity['column_id']]]
    except:
        return [""]

@app.callback(
    [Output('selected-room', 'children')],
    [Input('rooms-tbl', 'active_cell')],
    [State('rooms-tbl', 'data')]
)
def select_room(selected_entity, data):
    try:
        return [data[selected_entity['row']][selected_entity['column_id']]]
    except:
        return [""]

@app.callback_shared(
    [Output(component_id='user-agent-response', component_property='children'),
    Output(component_id='wizard-agent-response', component_property='value')],
    [Input(component_id='send-button', component_property='n_clicks')],
    [State(component_id='response-holder', component_property='children')]
)
def display_response(_, template):
    return template, ""

##User Side Callbacks##

@app.callback(
    Output(component_id='listen-pause', component_property='style'),
    [Input(component_id='listen-pause', component_property='n_clicks')],
)
def toggle_button(n_clicks):
    return white_button_style

@app.callback(
    [Output(component_id='transcription', component_property='children'),
    Output(component_id='listen-pause', component_property='children')],
    [Input(component_id='listen-pause', component_property='style')],
    [State(component_id='listen-pause', component_property='n_clicks')]
)
def transcribe_speech(_, n_clicks):
    if n_clicks == 0:
        return ["", "Record Message"]
    print("Recording Speech...")
    try:
        with sr.Microphone() as source:
            audio_text = r.listen(source)
            transcript = r.recognize_google(audio_text)
            return [r.recognize_google(audio_text), "Record Message"]
    except sr.UnknownValueError:
        return ["Could not parse input", "Record Message"]

@app.callback_shared(Output('user-utterance', 'children'), 
    [Input('transcription', 'children')])
def func(value):
    return value

# @app.callback_shared(Output('shared_slider_output', 'children'), [Input('shared_slider', 'value')])
# def func(value):
#     return value

# @app.callback(Output('regular_slider_output', 'children'), [Input('regular_slider', 'value')])
# def func(value):
#     return value

# @app.callback_shared(Output('shared_input_output', 'children'), [Input('shared_input', 'value')])
# def func(value):
#     return value

# @app.callback(Output('regular_input_output', 'children'), [Input('regular_input', 'value')])
# def func(value):
#     return value


if __name__ == '__main__':
    app.run_server(debug=True, port=5000, suppress_callback_exceptions=True)