import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_callback_conglomerate import Router
from dash.dependencies import Input, Output, State
import dash.exceptions
from threading import Thread
import pandas as pd
from dash.exceptions import PreventUpdate
from adafruit_servokit import ServoKit
import time
import webbrowser
import sys, signal

kit = ServoKit(channels=16)
sys.path.append('./SDL_Adafruit_ADS1x15')
import SDL_Adafruit_ADS1x15

ADS1115 = 0x01  # 16-bit ADC
gain = 4096  # +/- 4.096V
sps = 250  # 250 samples per second
adc = SDL_Adafruit_ADS1x15.ADS1x15(ic=ADS1115)

for i in range(6):
    kit.servo[i + 10].angle = 90


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    for i in range(6):
        kit.servo[i + 10].angle = 90
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

df = pd.read_csv('log.csv')
real_voltz = []
sim_voltz = []
befores = []
afters = []
current = 0

running = False
app = dash.Dash(__name__)
router = Router(app, False)

app.layout = html.Div([
    html.H1('Battery Simulator'),
    html.H4('Press button to start simulator', id='indicator'),
    html.H4('Total Current: 0 Amps', id='current'),
    html.Button('Start', id='button'),
    dcc.Graph(id='graph0', figure={
        'layout': {
            'clickmode': 'event+select'
        }
    }),
    dcc.Graph(id='graph1', figure={
        'layout': {
            'clickmode': 'event+select'
        }
    }),
    dcc.Interval(id='update', interval=300, n_intervals=0)
])


@router.callback([Output('current', 'children'),
                  Output('graph0', 'figure'),
                  Output('graph1', 'figure'),
                  Output('indicator', 'children'),
                  Output('button', 'children')],
                 Input('update', 'n_intervals'))
def update(updates):
    if not updates:
        raise PreventUpdate
    return ['Total Current: {} Amps'.format(current), {
        'data': [{
            'type': 'scatter',
            'y': real_voltz,
        }, {
            'type': 'scatter',
            'y': sim_voltz,
        }],
        'layout': {
            'clickmode': 'event+select'
        }
    },
            {
                'data': [{
                    'type': 'scatter',
                    'y': befores,
                    'x': [24, 48, 72, 96, 120, 144]
                }, {
                    'type': 'scatter',
                    'y': afters,
                    'x': [24, 48, 72, 96, 120, 144]
                }],
                'layout': {
                    'clickmode': 'event+select'
                }
            }, 'Press button to start simulator' if not running else 'Press button to stop simulator',
            'Stop' if running else 'Start']


@router.callback([Output('indicator', 'children'),
                  Output('button', 'children')],
                 Input('button', 'n_clicks'))
def start(clicks):
    if not clicks:
        raise PreventUpdate
    global running
    if running:
        global current
        current = 0
        running = False
        return ['Press button to start simulator', 'Start']
    else:
        global real_voltz
        global sim_voltz
        real_voltz = []
        sim_voltz = []
        running = True
        Thread(target=simulate).start()
        return ['Running...', 'Stop']


def simulate():
    global befores
    global afters
    for j in range(6):
        if not running:
            return
        for i in range(6):
            kit.servo[i + 10].angle = 90 - 90 / 6 * (j + 1)
        time.sleep(1)
        befores.append(adc.readADCSingleEnded(0, gain, sps) / 1000)
    for i, j in df.iterrows():
        if not running:
            return
        global current
        global real_voltz
        global sim_voltz
        real_voltz.append(j.get('Voltage'))
        sim_voltz.append(adc.readADCSingleEnded(0, gain, sps) / 1000)
        current = j.get('Total Current')
        for i in range(6):
            kit.servo[i + 10].angle = 90 - 90 * current / 144
        time.sleep(.1)
    for j in range(6):
        if not running:
            return
        for i in range(6):
            kit.servo[i + 10].angle = 90 - 90 / 6 * (j + 1)
        time.sleep(1)
        afters.append(adc.readADCSingleEnded(0, gain, sps) / 1000)
    for i in range(6):
        kit.servo[i + 10].angle = 90


# Call when you are done assigning callbacks
router.register_callbacks()


def open_browser():
    webbrowser.open('http://localhost:8050')


if __name__ == '__main__':
    Thread(target=open_browser).start()
    app.run_server(debug=False, port=8050, use_reloader=False)
