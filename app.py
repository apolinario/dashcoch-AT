# -*- coding: utf-8 -*-
import time
import i18n
from dashcoch import DataLoader, StyleLoader
import math
from configparser import ConfigParser
from datetime import date, datetime, timedelta
from pytz import timezone
import geojson
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, ClientsideFunction
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

#external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
parser = ConfigParser()
parser.read("settings.ini")

meta_tags = [
    # {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    {"property": "og:title", "content": "COVID-19 Information Austria"},
    {"property": "og:type", "content": "website"},
    {
        "property": "og:description",
        "content": "Latest updates of COVID-19 virus development in Austria",
    },
    {"property": "og:url", "content": "http://dashcoch-at.herokuapp.com"},
]

app = dash.Dash(
    __name__,
#    external_scripts=external_scripts,
    # external_stylesheets=external_stylesheets,
    meta_tags=meta_tags,
)
server = app.server

style = StyleLoader()

# google-analytics
app.scripts.config.serve_locally = False
app.scripts.append_script({
    'external_url': 'http://dashcoch-at.herokuapp.com/assets/async_src.js'
})
app.scripts.append_script({
    'external_url': 'http://dashcoch-at.herokuapp.com/assets/gtag.js'
})

def get_data():
    global data
    data = DataLoader(parser)
    
get_data()

app.title = "Austria COVID19 Tracker"

#
# Show the data
#
def get_layout():
    return html.Div(
        id="main",
        children=[
            dcc.Location(id="url", refresh=False),
            html.Div(
            id="header",
            children=[
                html.H4(children="COVID-19 Information for Austria"),
                html.P(
                    id="description",
                    children=[
                        dcc.Markdown(
                            """Number of COVID-19 cases in Austria.
                        Public data from [Bundesministerium für Soziales, Gesundheit, Pflege und Konsumentenschutz](https://www.sozialministerium.at). No data has been taken from news websites, newspapers, etc. Software by [@skepteis](https://twitter.com/skepteis), adapted to and for Austria by [@osaukh](https://twitter.com/osaukh). This page uses [Google Analytics](https://analytics.google.com).
                        """
                        )
                    ],
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="twelve columns",
                    children=[
                        html.Div(
                            className="total-container",
                            children=[
                                html.P(
                                    className="total-title",
                                    children="Total Cases",
                                ),
                                html.Div(
                                    className="total-content",
                                    children=str(int(data.total_swiss_cases)),
                                ),
                            ],
                        ),
                        html.Div(
                            className="total-container",
                            children=[
                                html.P(
                                    className="total-title",
                                    children="Reported Today",
                                ),
                                html.Div(
                                    className="total-content",
                                    children="+" + str(int(data.new_swiss_cases)),
                                ),
                            ],
                        ),
                        html.Div(
                            className="total-container",
                            children=[
                                html.P(
                                    className="total-title",
                                    children="Total Fatalities"
                                ),
                                html.Div(
                                    className="total-content",
                                    children=str(int(data.total_swiss_fatalities)),
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(className="six columns"),
                html.Div(className="six columns"),
            ],
        ),
        html.Div(
            className="slider-container",
            children=[
                dcc.RadioItems(
                    id="radio-prevalence",
                    options=[
                        {"label": "Total Reported Cases", "value": "number"},
                        {"label": "Newly Reported Cases", "value": "new"},
                        {
                            "label": "Cumulative Prevalence (per 10,000)",
                            "value": "prevalence",
                        },
                        {
                            "label": "New Hospitalizations",
                            "value": "new_hospitalizations",
                        },
                        {
                            "label": "Total Reported Hospitalizations",
                            "value": "hospitalizations",
                        },
                        {"label": "New Fatalities", "value": "new_fatalities"},
                        {"label": "Total Fatalities", "value": "fatalities"},
                    ],
                    value="number",
                    labelStyle={
                        "display": "inline-block",
                        "color": style.theme["foreground"],
                    },
                ),
            ],
        ),
        html.Div(id="date-container", className="slider-container"),
        html.Div(children=[dcc.Graph(id="graph-map", config={"staticPlot": True},),]),
        html.Div(
            className="slider-container",
            children=[
                html.P(
                    id="slider-text", children="Drag the slider to change the date:",
                ),
                dcc.Slider(
                    id="slider-date",
                    min=0,
                    max=len(data.swiss_cases["Date"]) - 1,
                    marks={
                        i: date.fromisoformat(d).strftime("%d.")
                        for i, d in enumerate(data.swiss_cases["Date"])
                    },
                    value=len(data.swiss_cases["Date"]) - 1,
                ),
            ],
        ),
        html.Br(),
        html.H4(
            children="Data for Austria", style={"color": style.theme["accent"]}
        ),
        html.Div(
            className="info-container",
            children=[
                html.P(
                    children="Bitte beachten Sie, dass die Abflachung der Kurven irreführend sein kann, da die heutigen Daten noch nicht vollständig aktualisiert sind. / Please be aware, that the flattening of the curves can be misleading, as today's data is not yet completely updated."
                )
            ],
        ),
        html.Div(
            className="slider-container",
            children=[
                dcc.RadioItems(
                    id="radio-scale-switzerland",
                    options=[
                        {"label": "Linear Scale", "value": "linear"},
                        {"label": "Logarithmic Scale", "value": "log"},
                    ],
                    value="linear",
                    labelStyle={
                        "display": "inline-block",
                        "color": style.theme["foreground"],
                    },
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-ch-graph")]
                ),
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="fatalities-ch-graph")],
                ),
            ],
        ),
        html.Br(),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="hospitalizations-ch-graph")],
                ),
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="releases-ch-graph")],
                ),
            ],
        ),
        html.Br(),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="case-world-graph")],
                ),
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="fatalities-world-graph")],
                ),
            ],
        ),
        html.Br(),
        html.Div(
            className="info-container",
            children=[
                html.P(
                    children="Dieses Diagramm zeigt die Entwicklung neuer Fälle basierend auf der Gesamtzahl der Fälle. Die täglichen Neuerkrankungen werden als gelbe Linie angezeigt, variieren jedoch stark zwischen den Tagen. Um eine reibungslosere Entwicklung zu zeigen, zeigt die grüne Linie die Gesamtzahl der Fälle während einer Woche bis zu jedem Tag. / This plot shows the development of new cases based on total cases. The daily new cases are shown as the yellow line, however, they vary strongly between days. To show a smoother development, the green line shows the total number of cases during a week to each day."
                )
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="twelve columns",
                    children=[dcc.Graph(id="caseincrease-ch-graph")],
                ),
            ],
        ),
        html.Br(),
        html.H4(children="Data per State", style={"color": style.theme["accent"]}),
        html.Div(
            className="info-container",
            children=[
                html.P(
                    children="Bitte beachten Sie, dass die Abflachung der Kurven irreführend sein kann, da die heutigen Daten noch nicht vollständig aktualisiert sind. / Please be aware, that the flattening of the curves can be misleading, as today's data is not yet completely updated."
                )
            ],
        ),
        html.Div(
            id="plot-settings-container",
            children=[
                dcc.RadioItems(
                    id="radio-scale-cantons",
                    options=[
                        {"label": "Linear Scale", "value": "linear"},
                        {"label": "Logarithmic Scale", "value": "log"},
                    ],
                    value="linear",
                    labelStyle={
                        "display": "inline-block",
                        "color": style.theme["foreground"],
                    },
                ),
                html.Br(),
                dcc.Dropdown(
                    id="dropdown-cantons",
                    options=[
                        {"label": canton, "value": canton}
                        for canton in data.canton_labels
                    ],
                    value=data.canton_labels,
                    multi=True,
                ),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-graph")]
                ),
                html.Div(
                    className="six columns", children=[dcc.Graph(id="case-pc-graph"),],
                ),
            ],
        ),
        html.Br(),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="twelve columns",
                    children=[dcc.Graph(id="case-graph-diff")],
                ),
            ],
        ),
        html.Br(),
        html.Div(
            className="info-container",
            children=[
                html.P(
                    children="Dieses Diagramm zeigt die Entwicklung neuer Fälle basierend auf der Gesamtzahl der Fälle. Die täglichen Neuerkrankungen variieren jedoch stark zwischen den Tagen. Um eine reibungslosere Entwicklung zu zeigen, zeigen die Linien die Gesamtzahl der Fälle während einer Woche bis zu jedem Tag. / This plot shows the development of new cases based on total cases. The daily new cases, however, vary strongly between days. To show a smoother development, the lines show the total number of cases during a week to each day."
                )
            ],
        ),
        html.Div(id="date-container-cantonal", className="slider-container"),
        html.Div(id="caseincrease-cantonal-data", style={"display": "none"}),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="twelve columns",
                    children=[dcc.Graph(id="caseincrease-cantonal-graph")],
                ),
            ],
        ),
        html.Div(
            className="slider-container",
            children=[
                html.P(
                    className="slider-text",
                    children="Drag the slider to change the date:",
                ),
                dcc.Slider(
                    id="slider-date-cantonal",
                    min=0,
                    max=len(data.swiss_cases["Date"]) - 1,
                    step=1,
                    value=len(data.moving_total) - 1,
                    updatemode="drag",
                ),
            ],
        ),
        html.Br(),
        html.H4(
            children="Demographic Correlations",
            style={"color": style.theme["accent"]},
        ),
        html.Div(
            className="info-container",
            children=[
                html.P(
                    children='Die gestrichelte weiße Linie zeigt die Korrelation zwischen den Daten der beiden Achsen. Der Wert "r" beschreibt die Stärke der Korrelation, während ein p-Wert von mehr als 0,05 bedeutet, dass die Korrelation nicht signifikant ist. / The dashed white line shows the correlation between the data of the two axes. The value "r" describes the strength of the correlation, while a p-value of more than 0.05 means that the correlation is not significant.'
                )
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="six columns",
                    children=[dcc.Graph(id="prevalence-density-graph")],
                ),
                html.Div(
                    className="six columns", children=[dcc.Graph(id="cfr-age-graph")]
                ),
            ],
        ),
        html.Br(),
        html.H4(children="Raw Data", style={"color": style.theme["accent"]}),
        html.P(
#            id="footer",
            children=[
                dcc.Markdown(
                    """The data is available on [GitHub](https://github.com/osaukh/dashcoch-AT/tree/master/data_AT).
                    The numbers of confirmed infected and fatality cases are from [Bundesministerium für Soziales, Gesundheit, Pflege und Konsumentenschutz](https://www.sozialministerium.at). No data has been taken from news websites, newspapers, etc. Software by [@skepteis](https://twitter.com/skepteis), adapted to and for Austria by [@osaukh](https://twitter.com/osaukh).
                    Austrian map from [@ginseng666](https://github.com/ginseng666/GeoJSON-TopoJSON-Austria).
                    Austrian demographic information from [Statistik Austria](http://www.statistik.at/web_de/statistiken/menschen_und_gesellschaft/bevoelkerung/bevoelkerungsstruktur/bevoelkerung_nach_alter_geschlecht/index.html).
                    Austrian bed information from [Bundesministerium für Soziales, Gesundheit, Pflege und Konsumentenschutz](http://www.kaz.bmgf.gv.at/ressourcen-inanspruchnahme/betten.html).
                    Dashboards for other countries: [Switzerland](http://www.corona-data.ch), [Ukraine](http://dashcoch-ua.herokuapp.com).
                    """
                )
            ],
        ),
    ],
)

app.layout = get_layout

# -------------------------------------------------------------------------------
# Callbacks
# -------------------------------------------------------------------------------
@app.callback(
    dash.dependencies.Output("date-container", "children"),
    [dash.dependencies.Input("slider-date", "value")],
)
def update_map_date(selected_date_index):
    d = date.fromisoformat(data.swiss_cases["Date"].iloc[selected_date_index])
    return d.strftime("%d. %m. %Y")


@app.callback(
    Output("graph-map", "figure"),
    [Input("slider-date", "value"), Input("radio-prevalence", "value")],
)
def update_graph_map(selected_date_index, mode):
    d = data.swiss_cases["Date"].iloc[selected_date_index]
    date = data.swiss_cases["Date"].iloc[selected_date_index]

    map_data = data.swiss_cases_by_date_filled
    labels = [
        canton + ": " + str(int(map_data[canton][d]))
        if not math.isnan(float(map_data[canton][d]))
        else ""
        for canton in data.cantonal_centres
    ]

    if mode == "prevalence":
        map_data = data.swiss_cases_by_date_filled_per_capita
        labels = [
            canton + ": " + str(round((map_data[canton][d]), 1))
            if not math.isnan(float(map_data[canton][d]))
            else ""
            for canton in data.cantonal_centres
        ]
    elif mode == "fatalities":
        map_data = data.swiss_fatalities_by_date_filled
        labels = [
            canton + ": " + str(int(map_data[canton][d]))
            if not math.isnan(float(map_data[canton][d]))
            else ""
            for canton in data.cantonal_centres
        ]
    elif mode == "new":
        map_data = data.swiss_cases_by_date_diff
        labels = [
            canton + ": " + str(int(map_data[canton][d]))
            if not math.isnan(float(map_data[canton][d]))
            else ""
            for canton in data.cantonal_centres
        ]
    elif mode == "new_fatalities":
        map_data = data.swiss_fatalities_by_date_diff
        labels = [
            canton + ": " + str(int(map_data[canton][d]))
            if not math.isnan(float(map_data[canton][d]))
            else ""
            for canton in data.cantonal_centres
        ]
    elif mode == "new_hospitalizations":
        map_data = data.swiss_hospitalizations_by_date_diff
        labels = [
            canton + ": " + str(int(map_data[canton][d]))
            if not math.isnan(float(map_data[canton][d]))
            else ""
            for canton in data.cantonal_centres
        ]
    elif mode == "hospitalizations":
        map_data = data.swiss_hospitalizations_by_date_filled
        labels = [
            canton + ": " + str(int(map_data[canton][d]))
            if not math.isnan(float(map_data[canton][d]))
            else ""
            for canton in data.cantonal_centres
        ]

    return {
        "data": [
            {
                "lat": [
                    data.cantonal_centres[canton]["lat"]
                    for canton in data.cantonal_centres
                ],
                "lon": [
                    data.cantonal_centres[canton]["lon"]
                    for canton in data.cantonal_centres
                ],
                "text": labels,
                "mode": "text",
                "type": "scattergeo",
                "textfont": {
                    "family": "Arial, sans-serif",
                    "size": 16,
                    "color": "white",
                    "weight": "bold",
                },
            },
            {
                "type": "choropleth",
                "showscale": False,
                "locations": data.canton_labels,
                "z": [map_data[canton][d] for canton in map_data if canton != "AT"],
                "colorscale": style.turbo,
                "geojson": "/assets/austria.geojson",
                "marker": {"line": {"width": 0.0, "color": "#08302A"}},
#                "colorbar": {
#                    "thickness": 10,
#                    "bgcolor": "#252e3f",
#                    "tickfont": {"color": "white"},
#                },
            },
        ],
        "layout": {
            "geo": {
                "visible": False,
                "center": {"lat": 47.700033, "lon": 13.263449},
                "lataxis": {"range": [46.2845, 49.6406]},
                "lonaxis": {"range": [9.5223, 17.363449]},
                # "fitbounds": "geojson",
                "projection": {"type": "transverse mercator"},
                # "landcolor": "#1f2630",
                # "showland": True,
                # "showcountries": True,
            },
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            "height": 600,
            "plot_bgcolor": "#252e3f",
            "paper_bgcolor": "#252e3f",
        },
    }


#
# Total cases Austria
#
@app.callback(
    Output("case-ch-graph", "figure"), [Input("radio-scale-switzerland", "value")],
)
def update_case_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases["Date"],
                "y": data.swiss_cases["AT"],
                "name": "AT",
                "type": "bar",
                "marker": {"color": style.theme["foreground"]},
                "showlegend": False,
            },
        ],
        "layout": {
            "title": "Total Reported Cases Austria",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
                "title": "Reported Cases",
            },
            "hovermode": "closest",
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }

@app.callback(
    Output("caseincrease-ch-graph", "figure"),
    [Input("radio-scale-switzerland", "value")],
)
def update_caseincrease_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases.iloc[6:-1]["AT"],
                "y": data.moving_total["AT"][6:-1],
                "mode": "lines+markers",
                "name": "New Cases During<br>the Last Week",
                "marker": {"color": style.theme["foreground"]},
                "text": data.moving_total["date_label"][6:-1],
                "hovertemplate": "<br><span style='font-size:2.0em'><b>%{y:.0f}</b></span> new cases<br>"
                + "between <b>%{text}</b><br>"
                + "<extra></extra>",
            },
            {
                "x": data.swiss_cases.iloc[6:-1]["AT"],
                "y": data.swiss_cases_by_date_diff["AT"][6:-1],
                "mode": "lines+markers",
                "name": "Daily new Cases",
                "marker": {"color": style.theme["yellow"]},
                "text": data.swiss_cases_by_date_diff["date_label"][6:-1],
                "hovertemplate": "<br><span style='font-size:2.0em'><b>%{y:.0f}</b></span> new cases<br>"
                + "on <b>%{text}</b><br>"
                + "<extra></extra>",
            },
        ],
        "layout": {
            "title": "Newly Reported Cases",
            "height": 400,
            "xaxis": {
                "showgrid": True,
                "color": "#ffffff",
                "title": "Total Cases",
                "type": "log",
            },
            "yaxis": {
                "type": "log",
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
                "title": "Newly Reported Cases",
            },
            "legend": {
                "x": 0.015,
                "y": 1,
                "traceorder": "normal",
                "font": {"family": "sans-serif", "color": "white"},
                "bgcolor": style.theme["background"],
                "bordercolor": style.theme["accent"],
                "borderwidth": 1,
            },
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }

@app.callback(
    Output("fatalities-ch-graph", "figure"),
    [Input("radio-scale-switzerland", "value")],
)
def update_fatalities_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_fatalities["Date"],
                "y": data.swiss_fatalities["AT"],
                "name": "AT",
                "type": "bar",
                "marker": {"color": style.theme["blue"]},
                "showlegend": False,
            },
        ],
        "layout": {
            "title": "Total Reported Fatalities Austria",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
                "title": "Fatalities",
            },
            "hovermode": "closest",
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }

@app.callback(
    Output("hospitalizations-ch-graph", "figure"),
    [Input("radio-scale-switzerland", "value")],
)
def update_hospitalizations_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_hospitalizations[:-1]["Date"],
                "y": data.swiss_hospitalizations[:-1]["AT"],
                "name": "Regular",
                "mode": "lines",
                "marker": {"color": style.theme["yellow"]},
                "showlegend": True,
            },
            {
                "x": data.swiss_icu[:-1]["Date"],
                "y": data.swiss_icu[:-1]["AT"],
                "name": "Intensive",
                "mode": "lines",
                "marker": {"color": style.theme["red"]},
                "showlegend": True,
            },
            {
                "x": data.swiss_hospitalizations.iloc[-2:]["Date"],
                "y": data.swiss_hospitalizations.iloc[-2:]["AT"],
                "name": "Regular",
                "mode": "lines",
                "line": {"dash": "dot"},
                "marker": {"color": style.theme["yellow"]},
                "showlegend": False,
            },
            {
                "x": data.swiss_icu.iloc[-2:]["Date"],
                "y": data.swiss_icu.iloc[-2:]["AT"],
                "name": "Intensive",
                "mode": "lines",
                "line": {"dash": "dot"},
                "marker": {"color": style.theme["red"]},
                "showlegend": False,
            },
        ],
        "layout": {
            "title": "Total Reported Hospitalizations Austria",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
                "title": "Hospitalizations",
            },
            "hovermode": "closest",
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("releases-ch-graph", "figure"), [Input("radio-scale-switzerland", "value")],
)
def update_releases_ch_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_releases[:-1]["Date"],
                "y": data.swiss_releases[:-1]["AT"],
                "name": "Regular",
                "mode": "lines",
                "marker": {"color": style.theme["foreground"]},
                "showlegend": False,
            },
            {
                "x": data.swiss_releases.iloc[-2:]["Date"],
                "y": data.swiss_releases.iloc[-2:]["AT"],
                "name": "Regular",
                "mode": "lines",
                "line": {"dash": "dot"},
                "marker": {"color": style.theme["foreground"]},
                "showlegend": False,
            },
        ],
        "layout": {
            "title": "Total Reported Recoveries Austria",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
                "title": "Releases",
            },
            "hovermode": "closest",
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


#
# Total cases world
#
@app.callback(
    Output("case-world-graph", "figure"), [Input("radio-scale-switzerland", "value")],
)
def update_case_world_graph(selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_world_cases_normalized.index.values,
                "y": data.swiss_world_cases_normalized[country],
                "name": country,
                # "marker": {"color": theme["foreground"]},
                # "type": "bar",
            }
            for country in data.swiss_world_cases_normalized
            if country != "Day"
        ],
        "layout": {
            "title": "Cumulative Prevalence per 10,000 Inhabitants",
            "height": 400,
            "xaxis": {
                "showgrid": True,
                "color": "#ffffff",
                "title": "Days Since Prevalence >0.4 per 10,000",
            },
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "title": "Reported Cases / Population * 10,000",
            },
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("fatalities-world-graph", "figure"),
    [Input("radio-scale-switzerland", "value")],
)
def update_fatalities_world_graph(selected_scale):
    return {
        "data": [
            {
                "x": ["Austria"]
                + data.world_case_fatality_rate.index.values.tolist(),
                "y": [data.swiss_case_fatality_rate]
                + [val for val in data.world_case_fatality_rate],
                "name": "AT",
                "marker": {"color": style.theme["foreground"]},
                "type": "bar",
            }
        ],
        "layout": {
            "title": "Case Fatality Ratios (Fatalities / Reported Cases)",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Country"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "rangemode": "tozero",
                "title": "Fatalities / Reported Cases",
            },
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


#
# Cantonal Data
#
@app.callback(
    Output("case-graph", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale-cantons", "value")],
)
def update_case_graph(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases_as_dict["Date"],
                "y": data.swiss_cases_as_dict[canton],
                "name": canton,
                "marker": {"color": style.canton_colors[canton]},
            }
            for _, canton in enumerate(data.swiss_cases_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Reported Cases per Canton",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "title": "Reported Cases",
            },
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("case-pc-graph", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale-cantons", "value")],
)
def update_case_pc_graph(selected_cantons, selected_scale):
    return {
        "data": [
            {
                "x": data.swiss_cases_normalized_as_dict["Date"],
                "y": data.swiss_cases_normalized_as_dict[canton],
                "name": canton,
                "marker": {"color": style.canton_colors[canton]},
            }
            for _, canton in enumerate(data.swiss_cases_normalized_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Reported Cases per Canton (per 10,000 Inhabitants)",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": selected_scale,
                "showgrid": True,
                "color": "#ffffff",
                "title": "Reported Cases / Population * 10,000",
            },
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("case-graph-diff", "figure"),
    [Input("dropdown-cantons", "value"), Input("radio-scale-cantons", "value")],
)
def update_case_graph_diff(selected_cantons, selected_scale):
    data_non_nan = {}
    data_non_nan["Date"] = data.swiss_cases_as_dict["Date"]

    for canton in data.swiss_cases_as_dict:
        if canton == "Date":
            continue
        values = []
        last_value = 0
        for _, v in enumerate(data.swiss_cases_as_dict[canton]):
            if math.isnan(float(v)):
                values.append(last_value)
            else:
                last_value = v
                values.append(v)
        data_non_nan[canton] = values

    return {
        "data": [
            {
                "x": data_non_nan["Date"],
                "y": [0]
                + [
                    j - i
                    for i, j in zip(data_non_nan[canton][:-1], data_non_nan[canton][1:])
                ],
                "name": canton,
                "marker": {"color": style.canton_colors[canton]},
                "type": "bar",
            }
            for i, canton in enumerate(data.swiss_cases_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Newly Reported Cases per State",
            "height": 400,
            "xaxis": {"showgrid": True, "color": "#ffffff", "title": "Date"},
            "yaxis": {
                "type": "linear",
                "showgrid": True,
                "color": "#ffffff",
                "title": "Reported Cases",
            },
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
            "barmode": "stack",
        },
    }

app.clientside_callback(
    ClientsideFunction(
        namespace="clientside", function_name="update_caseincrease_cantonal_graph"
    ),
    Output("caseincrease-cantonal-graph", "figure"),
    [
        Input("dropdown-cantons", "value"),
        Input("radio-scale-cantons", "value"),
        Input("slider-date-cantonal", "value"),
        Input("caseincrease-cantonal-graph", "hoverData"),
    ],
)


@app.callback(
    Output("caseincrease-cantonal-data", "children"), [Input("url", "pathname")]
)
def store_caseincrease_cantona_data(value):
    return (
        '{"swiss_cases_by_date_filled": '
        + data.swiss_cases_by_date_filled.to_json(date_format="iso", orient="columns")
        + ', "moving_total":'
        + data.moving_total.to_json(date_format="iso", orient="columns")
        + "}"
    )

#
# Demographic Correlations
#
@app.callback(
    Output("prevalence-density-graph", "figure"), [Input("dropdown-cantons", "value")],
)
def update_prevalence_density_graph(selected_cantons):
    return {
        "data": [
            {
                "x": data.prevalence_density_regression["x"],
                "y": data.prevalence_density_regression["y"],
                "mode": "lines",
                "hoverinfo": "skip",
                "showlegend": False,
                "line": {"dash": "dash", "width": 2.0, "color": "#ffffff",},
            }
        ]
        + [
            {
                "x": [data.swiss_demography["Density"][canton]],
                "y": [data.swiss_cases_by_date_filled_per_capita.iloc[-1][canton]],
                "name": canton,
                "mode": "markers",
                "text": canton,
                "marker": {
                    "color": style.canton_colors[canton],
                    "size": data.scaled_cases[canton],
                },
                "hoverinfo": "text",
                "hovertext": f"<span style='font-size:2.0em'><b>{canton}</b></span><br>"
                + f"Prevalence: <b>{data.swiss_cases_by_date_filled_per_capita.iloc[-1][canton]:.3f}</b><br>"
                + f"Population Density: <b>{data.swiss_demography['Density'][canton]:.0f}</b> Inhabitants / km<sup>2</sup><br>"
                + f"Cases: <b>{data.swiss_cases_by_date_filled.iloc[-1][canton]:.0f}</b>",
            }
            for _, canton in enumerate(data.swiss_cases_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Prevalence vs Population Density",
            "hovermode": "closest",
            "height": 400,
            "xaxis": {
                "showgrid": True,
                "color": "#ffffff",
                "title": "Population Density [Inhabitants/km2 Settlement Area]",
            },
            "yaxis": {"showgrid": True, "color": "#ffffff", "title": "Prevalence",},
            "annotations": [
                {
                    "x": data.prevalence_density_regression["x"][1],
                    "y": data.prevalence_density_regression["y"][1],
                    "xref": "x",
                    "yref": "y",
                    "text": "r: "
                    + str(round(data.prevalence_density_regression["r_value"], 2))
                    + "<br>"
                    + "p-value: "
                    + str(round(data.prevalence_density_regression["p_value"], 2)),
                    "showarrow": True,
                    "arrowhead": 4,
                    "ax": 50,
                    "ay": 50,
                    "font": {"size": 12, "color": "#ffffff",},
                    "arrowcolor": "#ffffff",
                    "align": "left",
                }
            ],
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


@app.callback(
    Output("cfr-age-graph", "figure"), [Input("dropdown-cantons", "value")],
)
def update_cfr_age_graph(selected_cantons):
    return {
        "data": [
            {
                "x": [v * 100 for v in data.cfr_age_regression["x"]],
                "y": data.cfr_age_regression["y"],
                "mode": "lines",
                "hoverinfo": "skip",
                "showlegend": False,
                "line": {"dash": "dash", "width": 2.0, "color": "#ffffff",},
            }
        ]
        + [
            {
                "x": [data.swiss_demography["O65"][canton] * 100],
                "y": [data.swiss_case_fatality_rates.iloc[-1][canton]],
                "name": canton,
                "mode": "markers",
                "marker": {
                    "color": style.canton_colors[canton],
                    "size": data.scaled_cases[canton],
                },
                "hoverinfo": "text",
                "hovertext": f"<span style='font-size:2.0em'><b>{canton}</b></span><br>"
                + f"Population over 65: <b>{data.swiss_demography['O65'][canton] * 100:.0f}%</b><br>"
                + f"Case Fatality Ratio: <b>{data.swiss_case_fatality_rates.iloc[-1][canton]:.3f}</b><br>"
                + f"Cases: <b>{data.swiss_cases_by_date_filled.iloc[-1][canton]:.0f}</b>",
            }
            for _, canton in enumerate(data.swiss_cases_normalized_as_dict)
            if canton in selected_cantons
        ],
        "layout": {
            "title": "Case Fatality Ratio vs Population over 65",
            "hovermode": "closest",
            "height": 400,
            "xaxis": {
                "showgrid": True,
                "color": "#ffffff",
                "title": "Population over 65 [%]",
            },
            "yaxis": {
                "type": "linear",
                "showgrid": True,
                "color": "#ffffff",
                "title": "Case Fatality Ratio",
            },
            "annotations": [
                {
                    "x": data.cfr_age_regression["x"][1] * 100,
                    "y": data.cfr_age_regression["y"][1],
                    "xref": "x",
                    "yref": "y",
                    "text": "r: "
                    + str(round(data.cfr_age_regression["r_value"], 2))
                    + "<br>"
                    + "p-value: "
                    + str(round(data.cfr_age_regression["p_value"], 2)),
                    "showarrow": True,
                    "arrowhead": 4,
                    "ax": -50,
                    "ay": -50,
                    "font": {"size": 12, "color": "#ffffff",},
                    "arrowcolor": "#ffffff",
                    "align": "left",
                }
            ],
            "dragmode": False,
            "margin": {"l": 60, "r": 20, "t": 60, "b": 70},
            "plot_bgcolor": style.theme["background"],
            "paper_bgcolor": style.theme["background"],
            "font": {"color": style.theme["foreground"]},
        },
    }


if __name__ == "__main__":
    app.run_server(
        # debug=True,
        # dev_tools_hot_reload=True,
        # dev_tools_hot_reload_interval=50,
        # dev_tools_hot_reload_max_retry=30,
    )
