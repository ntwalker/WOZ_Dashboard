import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import json
import zmq
import speech_recognition as sr
import numpy as np
import random
import copy

r = sr.Recognizer()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:%s" % "5557")

# Feedback to know when button is listening
white_button_style = {'background-color': 'white',
                      'color': 'black',
                      'height': '50px',
                      'width': '100px',
                      'margin-top': '50px',
                      'margin-left': '50px'}

red_button_style = {'background-color': 'red',
                    'color': 'white',
                    'height': '50px',
                    'width': '100px',
                    'margin-top': '50px',
                    'margin-left': '50px'}

def create_zmq_socket(zmq_port="5556", topicfilter=b""):
    """ Create a ZMQ SUBSCRIBE socket """
    context = zmq.Context()
    zmq_socket = context.socket(zmq.SUB)
    zmq_socket.connect("tcp://localhost:%s" % "5556")
    zmq_socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
    return zmq_socket

def recv_zmq(topic='data'):
    with create_zmq_socket() as socket:
        msg = socket.recv()
    return msg.decode('utf-8')

def send_zmq(socket, d, topic='data'):
    return socket.send_string("%s" %d)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H3('Graphdial Dashboard V1', style={'text-align': 'center'}),
    html.H4(id='agent-response', style={'width': '20%', 'display': 'inline-block', 'fontSize': 30}),
    html.Div("Bot Response", id="update", style={'width': '20%', 'display': 'inline-block', 'fontSize': 30}),
    html.Div("User Utterance", id="transcription", style={'width': '20%', 'display': 'inline-block', 'fontSize': 30}),
    html.Div([
            dcc.Input(id="text-input", type="text", n_submit=1, placeholder="Say something..."),
            html.Button(id='listen-pause', n_clicks=0, children='Listen', style=white_button_style)],
            ),
    dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0 # MUST BE 0, FOR GOD KNOWS WHY, DO NOT CHANGE!!!!!!!
            ),
    dcc.Interval(
                id='socket-interval',
                interval=1*1000000, # in milliseconds
                n_intervals=0
            ),
    html.Div("", id="line-holder", style={'width': '20%', 'display': 'hidden', 'fontSize': 30})
    ])

@app.callback(
    Output(component_id='listen-pause', component_property='style'),
    [Input(component_id='listen-pause', component_property='n_clicks')]
)
def toggle_button(n_clicks):
    print(n_clicks)
    if n_clicks % 2 == 0:
        return white_button_style
    else:
        return red_button_style

# @app.callback(
#     [Output(component_id='agent-response', component_property='value'),
#     Output(component_id='update', component_property='children'),
#     Output(component_id='response-holder', component_property='children')],
#     [Input(component_id='send-button', component_property='n_clicks')],
#     [State(component_id='agent-response', component_property='value')]
# )
# def create_response(response, value):
#     send_zmq(pub_socket, value)
#     return '', "Last Response: ", str(value)

@app.callback(
    [Output(component_id='transcription', component_property='children'),
    Output(component_id='listen-pause', component_property='children'),
    Output(component_id='listen-pause', component_property='n_clicks')],
    [Input(component_id='listen-pause', component_property='n_clicks'),
    State(component_id='transcription', component_property='children')]
)
def transcribe_speech(n_clicks, prevtext):
    try:
        with sr.Microphone() as source:
            audio_text = r.listen(source)
            transcript = r.recognize_google(audio_text)
            return r.recognize_google(audio_text), "Listen", n_clicks + 1
    except sr.UnknownValueError:
        return "Could not parse input", "Listen", n_clicks + 1

@app.callback(
    Output(component_id='line-holder', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')],
    [State(component_id='transcription', component_property='children')]
)
def send_transcription(_, transcription):
    send_zmq(pub_socket, transcription)
    return ""

@app.callback(
    Output(component_id='update', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')],
    [State(component_id='update', component_property='children')]
)
def receive_response(n_intervals, old_response):
    #response = zmq_socket.recv()
    print("Listening...")
    response = recv_zmq()
    print(response)
    return response

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=8060)