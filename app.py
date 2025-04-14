from flask import Flask, render_template
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
import os
import math

app = Flask(__name__)

@app.route('/')
def index():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_directory, 'data', 'villes_carte.csv')
    df = pd.read_csv(csv_file_path, sep=";", encoding='utf-8')

    df['log_papa'] = df['papa'].apply(lambda x: math.floor(math.log(x, 2)) if x > 0 else 0)
    df['log_maman'] = df['maman'].apply(lambda x: math.floor(math.log(x, 2)) if x > 0 else 0)

    max_log_papa = df['log_papa'].max()
    max_log_maman = df['log_maman'].max()

    max_log_sosa = max(max_log_papa, max_log_maman)

    # Convertir la colonne coord_json en dictionnaire JSON
    df['coordinates'] = df['coord_json'].apply(json.loads)
    code_insee_counts = df['insee'].value_counts()
    max_ancetre_ville = code_insee_counts.max()
    df['count_code_insee'] = df['insee'].map(code_insee_counts)
    nb = max_log_sosa

    # Créer une carte centrée sur la France avec des marqueurs pour chaque ville
    fig = go.Figure()

    color_scale = [
        [0, 'rgb(0, 0, 255)'],   # Bleu
        [1, 'rgb(255, 0, 0)']    # Rouge
    ]

    def get_color(value):
         # Si la valeur dépasse le maximum de l'échelle, retourner la couleur maximale
        if value >= color_scale[-1][0]:
            return color_scale[-1][1]

        for i in range(len(color_scale) - 1):
            if color_scale[i][0] <= value <= color_scale[i + 1][0]:
                min_val, max_val = color_scale[i][0], color_scale[i + 1][0]
                color1, color2 = color_scale[i][1], color_scale[i + 1][1]
                ratio = (value - min_val) / (max_val - min_val)
                
                # Diviser la chaîne "rgb(...)" pour obtenir les valeurs r, g, b
                r1, g1, b1 = map(int, color1[4:-1].split(','))
                r2, g2, b2 = map(int, color2[4:-1].split(','))
                
                r = int((1 - ratio) * r1 + ratio * r2)
                g = int((1 - ratio) * g1 + ratio * g2)
                b = int((1 - ratio) * b1 + ratio * b2)
                
                return f'rgb({r}, {g}, {b})'

    # Ajouter les lignes entre chaque point
    for i in df['sosa']:
        papa_sosa = df.loc[df['sosa'] == i, 'papa'].values[0]
        maman_sosa = df.loc[df['sosa'] == i, 'maman'].values[0]
        point1 = json.loads(df.loc[df['sosa'] == i, 'coord_json'].values[0])
        test = df.loc[df['sosa'] == papa_sosa, 'coord_json']
        log_papa = math.floor(math.log(papa_sosa, 2)) if papa_sosa > 0 else 0  # Calcul de la partie entière du log base 2
        if not test.empty:
            point2 = json.loads(test.values[0])
            fig.add_trace(go.Scattermapbox(
                mode="lines+markers",
                lon=[point1['longitude'], point2['longitude']],
                lat=[point1['latitude'], point2['latitude']],
                marker=dict(
                    colorscale='Bluered',
                    colorbar=dict(
                        title='Echelle de couleur <br>(génération)',
                        tickvals=[1, nb//3, (nb*2)//3, nb],  # Les valeurs de l'échelle de couleur
                        ticktext=['1', nb//3, (nb*2)//3,  nb],  # Les libellés de l'échelle de couleur
                    ),
                    cmin=1,  # La valeur minimale de l'échelle de couleur
                    cmax=nb,  # La valeur maximale de l'échelle de couleur
                ),
                line = go.scattermapbox.Line(color = get_color(round(log_papa/max_log_sosa,1))),

                hoverinfo='text',
                hovertext='test',
                showlegend=False,
            ))

        log_maman = math.floor(math.log(maman_sosa, 2)) if maman_sosa > 0 else 0
        test_m = df.loc[df['sosa'] == maman_sosa, 'coord_json']
        if not test_m.empty:
            point2 = json.loads(test_m.values[0])
            fig.add_trace(go.Scattermapbox(
                mode="lines",
                lon=[point1['longitude'], point2['longitude']],
                lat=[point1['latitude'], point2['latitude']],
                line = go.scattermapbox.Line(color = get_color(round(log_maman/max_log_sosa,1))),
                hoverinfo='none',  # Ne pas afficher les informations au survol pour ces lignes
                showlegend=False,
            ))

    # Ajouter les marqueurs pour chaque ville avec leurs informations de survol
    for i, row in df.iterrows():
        fig.add_trace(go.Scattermapbox(
            lat=[row['coordinates']['latitude']],
            lon=[row['coordinates']['longitude']],
            mode='markers',
            marker=go.scattermapbox.Marker(color = get_color(round((row['count_code_insee'] / max_ancetre_ville),1))),
            hoverinfo='text',
            hovertext=f"<b>{row['count_code_insee']}</b> <i>{str(row['Commune']).capitalize()}</i>",
            showlegend=False,
        ))

    fig.update_layout(
        mapbox_style= "open-street-map",   #"carto-positron",
        mapbox_center={"lat": 46.603354, "lon": 1.888334}, 
        margin = {'l':120, 'r':100, 'b':10, 't':70},
        mapbox_zoom=4.5
    )

    fig.update_layout(
        title="<b>Arbre Généalogique des ancêtres de JP selon le sosa &#127968;</b>",
        title_x=0.12,  # Ajuster la position horizontale du titre
        title_y=0.95,  # Ajuster la position verticale du titre
        title_font=dict(size=20),  # Ajuster la taille du titre

        width=1300,  # Ajuster la largeur de la page
        height=660,  # Ajuster la hauteur de la page
    )


    # Convertir la figure en HTML
    graph_html = pio.to_html(fig, full_html=False)

    return render_template('index.html', graph_html=graph_html)

if __name__ == '__main__':
    app.run(debug=True)
