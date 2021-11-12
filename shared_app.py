import dash_devices
from dash_devices.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_table as dt
import plotly.express as px
import speech_recognition as sr
import pyttsx3
import pandas as pd
import numpy as np
import json
import collections
import numpy as np
import random
import os
import re
import base64
import time
from time import strftime
from datetime import date
from faker import Faker

# Functions to filter the datatable
def to_string(filter):
    operator_type = filter.get('type')
    operator_subtype = filter.get('subType')

    if operator_type == 'relational-operator':
        if operator_subtype == '=':
            return '=='
        else:
            return operator_subtype
    elif operator_type == 'logical-operator':
        if operator_subtype == '&&':
            return '&'
        else:
            return '|'
    elif operator_type == 'expression' and operator_subtype == 'value' and type(filter.get('value')) == str:
        return '"{}"'.format(filter.get('value'))
    else:
        return filter.get('value')

def construct_filter(derived_query_structure, df, complexOperator=None):

    # there is no query; return an empty filter string and the
    # original dataframe
    if derived_query_structure is None:
        return ('', df)

    # the operator typed in by the user; can be both word-based or
    # symbol-based
    operator_type = derived_query_structure.get('type')

    # the symbol-based representation of the operator
    operator_subtype = derived_query_structure.get('subType')

    # the LHS and RHS of the query, which are both queries themselves
    left = derived_query_structure.get('left', None)
    right = derived_query_structure.get('right', None)

    # the base case
    if left is None and right is None:
        return (to_string(derived_query_structure), df)

    # recursively apply the filter on the LHS of the query to the
    # dataframe to generate a new dataframe
    (left_query, left_df) = construct_filter(left, df)

    # apply the filter on the RHS of the query to this new dataframe
    (right_query, right_df) = construct_filter(right, left_df)

    # 'datestartswith' and 'contains' can't be used within a pandas
    # filter string, so we have to do this filtering ourselves
    if complexOperator is not None:
        right_query = right.get('value')
        # perform the filtering to generate a new dataframe
        if complexOperator == 'datestartswith':
            return ('', right_df[right_df[left_query].astype(str).str.startswith(right_query)])
        elif complexOperator == 'contains':
            return ('', right_df[right_df[left_query].astype(str).str.contains(right_query)])

    if operator_type == 'relational-operator' and operator_subtype in ['contains', 'datestartswith']:
        return construct_filter(derived_query_structure, df, complexOperator=operator_subtype)

    # construct the query string; return it and the filtered dataframe
    return ('{} {} {}'.format(
        left_query,
        to_string(derived_query_structure) if left_query != '' and right_query != '' else '',
        right_query
    ).strip(), right_df)

def text_to_speech(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id) 
    engine.setProperty('rate',175)
    engine.say(text)
    engine.runAndWait()

fake = Faker()

app = dash_devices.Dash(__name__)
#app = dash_devices.Dash()
app.config.suppress_callback_exceptions = True

# Speech recognition
r = sr.Recognizer()

with open("event_calendars.json", "r") as file:
    je = json.load(file)
    file.close()

#One table of all events instead of the above three
events_table = pd.DataFrame(je)
events_table['attendees'] = events_table['attendees'].apply(lambda x: ", ".join(x))

#Dialogue Templates:
agent_templates = ["Hello!", 
"Sorry, I didn't understand that.", 
"_Person_ is available!",
"_Person_ is available at _Time_!",
"_Person_ is available at _Time_ on _Date_!"]

previous_response = ""

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
            
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            # placeholder
            html.Div("[Template Here]", id="composed-response", style={'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'padding-left': '30%'}),
            html.Div("[Template Here]", id="response-holder", hidden='hidden'),
            html.Div(
                [dcc.Dropdown(
                    id = 'wizard-response-template',
                    placeholder = "Select Template...",
                    options = [{'label': i, 'value': i} for i in agent_templates]
                ),
                html.Button(
                    id='clear-button', 
                    n_clicks=0, 
                    children='Clear Entities', 
                    style={'align': 'center', 'display': 'flex',  'justify': 'left'}
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
            html.Div(style={'width': '5%', 'display': 'inline-block'}), 
            html.H5("Events", style={'width': '5%'}),
            dt.DataTable(
                id='event-tbl', data=events_table.to_dict('records'),
                columns=[{"name": i, "id": i} for i in events_table.columns],
                style_cell={'textAlign': 'left', "whiteSpace": "pre-line"},
                sort_action="native",
                sort_mode="single",
                column_selectable="single",
                row_selectable="multi",
                filter_action='native'
                ),
            # placeholder
            html.Div(style={'width': '5%', 'display': 'inline-block'})
        ])

user_page = html.Div([
    html.H3('GraphDial User Dashboard', style={'text-align': 'center', 'color': 'white', 'background': 'green'}),
    html.Div("Task", id="task-label", style={'width': '20%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'background': 'gray'}),
    html.Div("Speak Into the Microphone", id="button-label", style={'width': '40%', 'text-align': 'center', 'display': 'inline-block', 'fontSize': 20, 'background': 'gray'}),
    html.Div("Bot Response", id="agent-label", style={'width': '40%', 'text-align': 'left', 'display': 'inline-block', 'fontSize': 20, 'background': 'gray'}),
    html.Br(),
    html.Div(
        [html.Div([
            html.Button(id='task-button', n_clicks=0, children='Complete', style={'align': 'center'}),
            html.Div(style={'height':'10px'}),
            html.Div("Task Description Here", id="task-desc", style={'text-align': 'left', 'fontSize': 20, "verticalAlign": "top"})
            ], style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
            #dcc.Input(id="text-input", type="text", n_submit=1, placeholder="Say something..."),
            html.Button(id='listen-pause', n_clicks=0, children='Record Message', style=white_button_style)],
            style={'width': '30%', 'text-align': 'center', 'align-items': 'center', 'justify-content': 'center', 'display': 'inline-block', "verticalAlign": "top"}
            ),
        html.Div([
        html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width': '7%', 'display': 'inline-block', 'height': '100px', 'width': '100px', "verticalAlign": "top"}),
        html.Div("[Template Here]", 
            id="user-agent-response", 
            style={'display': 'inline-block', 'width': '70%', 'fontSize': 25, 'background': 'lightcyan'}),
        ], id="agent-display", style={'width': '50%', 'display': 'inline-block'})]),
    html.Div("", id="transcription", hidden='hidden'),
    # White space below hides the wizard dashboard at the bottom if it momentarily appears on refresh
    html.Div("", id="whitespace", style={'height': '1500px', 'width': '100%', 'clear': 'both'})])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Input(id="access", type="text", value=''),
    html.Button(id='change', n_clicks=0, children='admin', style={'text-align': 'center'}),
    html.Div(user_page, id='user-content'),
    html.Div(wizard_page, id='wizard-content'),
    #html.Div("", id='last-response', hidden='hidden'),
    html.Div("Misc", id='miscellaneous', hidden='hidden'),
])

# Page navigation callbacks
@app.callback([Output('wizard-content', 'children'),
                Output('user-content', 'children'),
                Output('access', 'value')],
              [Input('change', 'n_clicks')],
              [State('access', 'value')])
def display_page(n_clicks, password):
    if password != "wizard":
        return [html.Div(wizard_page, id='wizard'), html.Div(user_page, id='user', hidden='hidden'), ""]
    else:
        return [html.Div(wizard_page, id='wizard', hidden='hidden'), html.Div(user_page, id='user'), ""]

###WIZARD PAGE CALLBACKS###

@app.callback(
    Output("event-tbl", "data"),
    [Input("event-tbl", "derived_filter_query_structure")]
)
def filter_table(derived_query_structure):
    (pd_query_string, df_filtered) = construct_filter(derived_query_structure, events_table)

    if pd_query_string != '':
        df_filtered = df_filtered.query(pd_query_string)

    return df_filtered.to_dict('records')

@app.callback(
    [Output('composed-response', 'children'),
    Output('response-holder', 'children')],
    [Input('wizard-response-template', 'value'),
    Input('event-tbl', 'active_cell'),
    Input('send-button', 'n_clicks'),
    Input('clear-button', 'n_clicks')],
    [State('event-tbl', 'data'),
    State('composed-response', 'children'),
    State('response-holder', 'children')]
)
def update_template(selected_template, selected_cell, _, __, data, current_template, prev_response):
    ctx = dash_devices.callback_context

    try:
        if ctx.triggered[0]['prop_id'] == "wizard-response-template.value":
            #New Template Selected, no entities added
            return [selected_template, prev_response]
        if ctx.triggered[0]['prop_id'] == "event-tbl.active_cell":
            print(ctx.triggered)
            entity = data[selected_cell['row']][selected_cell['column_id']]

            if 'time' in selected_cell['column_id']:
                time_entity = time.strptime(entity, "%H:%M:%S")
                entity = strftime("%H:%M", time_entity)

            if selected_cell['column_id'] == 'date':
                date_entity = date.fromisoformat(entity)
                entity = str(date_entity.strftime("%A, %B %d"))

            new_template = re.sub(r"_(Person|Time|Date)_", entity, current_template, 1)
            return [new_template, prev_response]
        if ctx.triggered[0]['prop_id'] == "clear-button.n_clicks":
            return [selected_template, prev_response]
        if ctx.triggered[0]['prop_id'] == "send-button.n_clicks":
            return ["", current_template]
    except:
        return [current_template, prev_response]

@app.callback(
    Output(component_id='wizard-response-template', component_property='value'),
    [Input(component_id='clear-button', component_property='n_clicks')],
    #[Input(component_id='send-button', component_property='n_clicks')],
)
def clear_template_selector(n_clicks):
    return ""

@app.callback_shared(
    Output('user-agent-response', 'children'), 
    [Input('response-holder', 'children')])
def display_agent_response(value):
    if value == "[Template Here]":
        return ""
    return value

@app.callback_shared(
    Output('whitespace', 'children'), 
    [Input('user-agent-response', 'children')])
def say_agent_response(value):
    global previous_response

    if value == previous_response:
        return ""
    else:
        text_to_speech(value)
        previous_response = value
        return ""

##User Related Callbacks##

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
            audio_text = r.listen(source, 10, 3)
            transcript = r.recognize_google(audio_text)
            return [r.recognize_google(audio_text), "Record Message"]
    except sr.UnknownValueError:
        return ["Could not parse input", "Record Message"]

@app.callback_shared(Output('user-utterance', 'children'), 
    [Input('transcription', 'children')])
def display_transcription(value):
    return value

##Data Saving Function(s)##

@app.callback_shared(Output('miscellaneous', 'children'), 
    [Input('user-agent-response', 'children')])
def save_interaction(_):
    #Save functions here to output data
    return _


if __name__ == '__main__':
    app.run_server(debug=True, port=5000, suppress_callback_exceptions=True)
    #app.run_server(debug=False, host='0.0.0.0', port=8050, suppress_callback_exceptions=True)