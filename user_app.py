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
import os
import base64

r = sr.Recognizer()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://*:%s" % "5557")

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

image_filename = os.path.join(os.getcwd(), 'chatbot.jpg')
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

app.layout = html.Div([
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
    dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0 # MUST BE 0
            ),
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'width': '7%', 'display': 'inline-block', 'height': '100px'}),
    html.Div("Bot Response", id="agent-response", style={'display': 'inline-block', 'fontSize': 30}),
    dcc.Interval(
                id='socket-interval',
                interval=1*1000000, # in milliseconds
                n_intervals=0
            ),
    html.Div("", id="line-holder", style={'width': '5%', 'visibility': 'hidden', 'fontSize': 30}),
    html.Div("Please try again", id="warning", style={'text-align': 'center', 'color': 'red'})
    ])

@app.callback(
    Output(component_id='listen-pause', component_property='style'),
    [Input(component_id='listen-pause', component_property='n_clicks')],
)
def toggle_button(n_clicks):
    print(n_clicks)
    return white_button_style

@app.callback(
    [Output(component_id='transcription', component_property='children'),
    Output(component_id='listen-pause', component_property='children')],
    [Input(component_id='listen-pause', component_property='style')],
    [State(component_id='transcription', component_property='children'),
    State(component_id='listen-pause', component_property='n_clicks')]
)
def transcribe_speech(_, prevtext, n_clicks):
    if n_clicks == 0:
        return prevtext, "Record Message"
    try:
        with sr.Microphone() as source:
            audio_text = r.listen(source)
            transcript = r.recognize_google(audio_text)
            return r.recognize_google(audio_text), "Record Message"
    except sr.UnknownValueError:
        return "Could not parse input", "Record Message"

@app.callback(
    Output(component_id='line-holder', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')],
    [State(component_id='transcription', component_property='children')]
)
def send_transcription(_, transcription):
    send_zmq(pub_socket, transcription)
    return ""

@app.callback(
    Output(component_id='agent-response', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')],
    [State(component_id='agent-response', component_property='children')]
)
def receive_response(n_intervals, old_response):
    #response = zmq_socket.recv()
    #print("Listening...")
    response = recv_zmq()
    if response == old_response:
        return old_response
    #print(response)
    return response

@app.callback(
    Output(component_id='warning', component_property='children'),
    [Input(component_id='transcription', component_property='children')]
)
def display_warning(transcription):
    if transcription == "Could not parse input": 
        return "Please try again"
    else:
        return ""

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=8060)