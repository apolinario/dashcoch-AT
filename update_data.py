# -*- coding: utf-8 -*-
import os
import bs4
import pandas as pd
from urllib import request
from datetime import date
from bs4 import BeautifulSoup


URL = 'https://www.sozialministerium.at/Informationen-zum-Coronavirus/Neuartiges-Coronavirus-(2019-nCov).html'
STATES = {
    'Bgld.': 'B',
    'Ktn.': 'K',
    'NÖ': 'NÖ',
    'OÖ': 'OÖ',
    'Sbg.': 'S',
    'Stmk.': 'ST',
    'T': 'T',
    'Vbg.': 'V',
    'W': 'W',
    'Österreich gesamt': 'AT'
}
DISTRICTS = {
    'Amstetten': 'NÖ',
    'Baden': 'NÖ',
    'Bludenz': 'V',
    'Braunau am Inn': 'OÖ',
    'Bregenz': 'V',
    'Bruck an der Leitha': 'NÖ',
    'Bruck-Mürzzuschlag': 'ST',
    'Deutschlandsberg': 'ST',
    'Dornbirn': 'V',
    'Eferding': 'OÖ',
    'Eisenstadt(Stadt)': 'B',
    'Eisenstadt-Umgebung': 'B',
    'Feldkirch': 'V',
    'Feldkirchen': 'K',
    'Freistadt': 'OÖ',
    'Gänserndorf': 'NÖ',
    'Gmünd': 'NÖ',
    'Gmunden': 'OÖ',
    'Graz(Stadt)': 'ST',
    'Graz-Umgebung': 'ST',
    'Grieskirchen': 'OÖ',
    'Gröbming': 'ST',
    'Güssing': 'B',
    'Hallein': 'S',
    'Hartberg-Fürstenfeld': 'ST',
    'Hermagor': 'K',
    'Hollabrunn': 'NÖ',
    'Horn': 'NÖ',
    'Imst': 'T',
    'Innsbruck-Land': 'T',
    'Innsbruck-Stadt': 'T',
    'Jennersdorf': 'B',
    'Kirchdorf an der Krems': 'OÖ',
    'Kitzbühel': 'T',
    'Klagenfurt Land': 'K',
    'Klagenfurt Stadt': 'K',
    'Korneuburg': 'NÖ',
    'Krems an der Donau(Stadt)': 'NÖ',
    'Krems(Land)': 'NÖ',
    'Kufstein': 'T',
    'Landeck': 'T',
    'Leibnitz': 'ST',
    'Leoben': 'ST',
    'Lienz': 'T',
    'Liezen': 'ST',
    'Lilienfeld': 'NÖ',
    'Linz(Stadt)': 'OÖ',
    'Linz-Land': 'OÖ',
    'Mattersburg': 'B',
    'Melk': 'NÖ',
    'Mistelbach': 'NÖ',
    'Mödling': 'NÖ',
    'Murau': 'ST',
    'Murtal': 'ST',
    'Neunkirchen': 'NÖ',
    'Neusiedl am See': 'B',
    'Oberpullendorf': 'B',
    'Oberwart': 'B',
    'Perg': 'OÖ',
    'Reutte': 'T',
    'Ried im Innkreis': 'OÖ',
    'Rohrbach': 'B',
    'Salzburg(Stadt)': 'S',
    'Salzburg-Umgebung': 'S',
    'Sankt Johann im Pongau': 'S',
    'Sankt Pölten(Land)': 'NÖ',
    'Sankt Pölten(Stadt)': 'NÖ',
    'Sankt Veit an der Glan': 'K',
    'Schärding': 'OÖ',
    'Scheibbs': 'NÖ',
    'Schwaz': 'T',
    'Spittal an der Drau': 'K',
    'Steyr(Stadt)': 'OÖ',
    'Steyr-Land': 'OÖ',
    'Südoststeiermark': 'ST',
    'Tamsweg': 'S',
    'Tulln': 'NÖ',
    'Urfahr-Umgebung': 'OÖ',
    'Villach Land': 'K',
    'Villach Stadt': 'K',
    'Vöcklabruck': 'K',
    'Voitsberg': 'ST',
    'Völkermarkt': 'K',
    'Waidhofen an der Thaya': 'NÖ',
    'Waidhofen an der Ybbs(Stadt)': 'NÖ',
    'Weiz': 'ST',
    'Wels(Stadt)': 'OÖ',
    'Wels-Land': 'OÖ',
    'Wien(Stadt)': 'W',
    'Wiener Neustadt(Land)': 'NÖ',
    'Wiener Neustadt(Stadt)': 'NÖ',
    'Wolfsberg': 'K',
    'Zell am See': 'S',
    'Zwettl': 'NÖ'
}

FILE_CASES = 'data_AT/covid19_cases_austria.csv'
FILE_FATALITIES = 'data_AT/covid19_fatalities_austria.csv'
FILE_HOSPITALIZATIONS = 'data_AT/covid19_hospitalized_austria.csv'
FILE_ICUS = 'data_AT/covid19_icu_austria.csv'
FILE_RELEASES = 'data_AT/covid19_releases_austria.csv'


def retrieve():
    r = request.urlopen(URL).read().decode().replace('\n', '').replace('\t', '').replace('&nbsp;', '')
    soup = BeautifulSoup(r, 'html.parser')
    table = soup.find(attrs={'class': 'table-responsive'}).find_next()
    body = table.find('tbody')
    rows = body.find_all('tr')

    for row in rows:
        line = [c for c in row.contents if type(c) == bs4.element.Tag]
        date_string = line[0].text.split('(')[1].strip(')')

        line_head = line.pop(0)

        if line_head.text.startswith('Bestätigte Fälle'):
            cases = list(zip(STATES.keys(), [l.text for l in line]))
        elif line_head.text.startswith('Todesfälle'):
            fatalities = list(zip(STATES.keys(), [l.text for l in line]))
        elif line_head.text.startswith('Hospitalisierung'):
            hospitalizations = list(zip(STATES.keys(), [l.text for l in line]))
        elif line_head.text.startswith('Intensivstation'):
            icus = list(zip(STATES.keys(), [l.text for l in line]))
        elif line_head.text.startswith('Genesen'):
            releases = list(zip(STATES.keys(), [l.text for l in line]))

    return cases, fatalities, hospitalizations, icus, releases


def append_csv(filename, data):
    df = pd.read_csv(filename)

    values = {k[1]:0 for k in STATES.items()}
    for d in data: 
        values[STATES[d[0]]] = int(d[1].replace('.', ''))

    today_str = date.today().strftime('%Y-%m-%d')
    sum_at = sum([v for k, v in values.items() if k != 'AT'])
    if sum_at != values['AT']:
        print('Sum differs from numbers online for {} at {}'.format(os.path.basename(filename), today_str))

    values['Date'] = today_str

    if today_str in df['Date'].to_list():
        df.update([values])
    else:
        df = df.append([values])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    df.sort_index(inplace=True)
    df.to_csv(filename)


def update_data():
    cases, fatalities, hospitalizations, icus, releases = retrieve()
    append_csv(FILE_CASES, cases)
    append_csv(FILE_FATALITIES, fatalities)
    append_csv(FILE_HOSPITALIZATIONS, hospitalizations)
    append_csv(FILE_ICUS, icus)
    append_csv(FILE_RELEASES, releases)


if __name__ == "__main__":
    update_data()
