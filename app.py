# # Run this app with `python app.py` and
# # visit http://127.0.0.1:8050/ in your web browser.
#
#
from dash import Dash, html, dcc, Input, Output, callback
import dash
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import sheets_api
import plotly.graph_objects as go
def get_club_values():
    clubs_spread = "11_AhmjJIgkGi6JGtYYKehpC1UJ2ET1Ag4oV76mO5RCM"
    client = sheets_api.GoogleSheetsClient(clubs_spread)

    # Check if the client is authorized before proceeding
    if not client.authorized:
        print("Client not authorized yet. Skipping data fetch.")
        return [], [], [], []  # Return empty lists or handle as appropriate for your application

    range_data = client.get_values("A3:E")  # This line now runs only if authorized

    # Initialize lists to hold column data
    clubs = []
    days = []
    members = []
    magnitude = []

    # Parse through fetched data to extract and convert specific columns
    for row in range_data:
        # Extract and append club names (column A)
        clubs.append(row[0] if len(row) > 0 else "")

        # Extract and append days (column B)
        days.append(row[1] if len(row) > 1 else "")

        # Extract, convert to int, and append member counts (column D)
        # Using a try-except block to handle conversion errors
        try:
            members.append(int(row[3]) if len(row) > 3 and row[3] else 0)
        except ValueError:
            members.append(0)  # Default to 0 in case of conversion error

        # Extract, convert to float, and append magnitude (column E)
        # Using a try-except block to handle conversion errors
        try:
            magnitude.append(float(row[4]) if len(row) > 4 and row[4] else 0.0)
        except ValueError:
            magnitude.append(0.0)  # Default to 0.0 in case of conversion error

    # Calculate value_weight using list comprehension
    value_weight = [members[i] * magnitude[i] for i in range(len(members))]

    return clubs, days, members, value_weight
# Initialize your Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
load_figure_template('DARKLY')
app.layout = html.Div(children=[
    dbc.Row([
        dbc.Col(),
        dbc.Col(html.H1('AISA Visualization Tool', style={'textAlign': 'center'}), width=12),
    ]),
    dbc.Row([
        dcc.Graph(id='example-graph'),
        dcc.Graph(id='example-graph-weighted'),

        ], justify="center"),
        dcc.Interval(
            id='interval-component',
            interval=15*1000,  # 10 seconds in milliseconds
            n_intervals=0
        )
])

# Callback to update the first graph
@app.callback(
    Output('example-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    clubs, days, members, value_weight = get_club_values()
    df = pd.DataFrame({
        "Days": days,
        "Members": members,
        "Club": clubs
    })
    fig = px.bar(df, x="Days", y="Members", color="Club", barmode="group")
    return fig

# Callback to update the weighted graph
@app.callback(
    Output('example-graph-weighted', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph_weighted_live(n):
    clubs, days, members, value_weight = get_club_values()
    weighted_df = pd.DataFrame({
        "Days": days,
        "Membership Value": value_weight,
        "Club": clubs
    })
    fig_weighted = px.bar(weighted_df, x="Days", y="Membership Value", color="Club", barmode="group")
    return fig_weighted

if __name__ == '__main__':
    app.run_server(debug=True)
