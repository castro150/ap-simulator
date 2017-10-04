import folium
import flightradar24
import optimizer

fr = flightradar24.Api()
DESIRED_IATA = ['VIX', 'CDI', 'GUZ', 'SBJ', 'QAK', 'POJ', 'CNF', 'DIQ', 'GVR', 'JDF', 'MOC', 'PLU', 'POO', 'JDR', 'UDI',
                'UBA', 'IZA', 'SNZ', 'CAW', 'CFB', 'GIG', 'ITP', 'MEA', 'QRZ', 'SDU', 'ARU', 'AQA', 'AIF', 'QVP', 'BAT',
                'JTC', 'QCP', 'BJP', 'CPQ', 'CGH', 'QDC', 'GUJ', 'GRU', 'FRC', 'QDV', 'QGC', 'LIP', 'MII', 'OUS', 'QHB',
                'PPB', 'RAO', 'QSC', 'SJP', 'SJK', 'SOD', 'UBT', 'VCP', 'VOT']


def main():
    airports = fr.get_airports()['rows']
    br_airports_se = list(filter(lambda airport: airport['iata'] in DESIRED_IATA, airports))

    map_f = folium.Map(location=[-20.5934, -46.9408], zoom_start=7, min_zoom=7, tiles='Mapbox Bright')
    fga = folium.FeatureGroup(name='Brazilian airports')

    for br_airport in br_airports_se:
        fga.add_child(folium.CircleMarker(location=[br_airport['lat'], br_airport['lon']], radius=6,
                                          popup=br_airport['iata'], fill_color='green', color='grey',
                                          fill=True, fill_opacity=0.7))

    routes = optimizer.optimize(br_airports_se)
    fgb = folium.FeatureGroup(name='TN001')
    points1 = [(br_airports_se[0]['lat'], br_airports_se[0]['lon']),
              (br_airports_se[1]['lat'], br_airports_se[1]['lon'])]
    fgb.add_child(folium.PolyLine(locations=points1, popup='Test popup1', color='red'))

    fgc = folium.FeatureGroup(name='TN002')
    points2 = [(br_airports_se[2]['lat'], br_airports_se[2]['lon']),
              (br_airports_se[3]['lat'], br_airports_se[3]['lon'])]
    fgc.add_child(folium.PolyLine(locations=points2, popup='Test popup2', color='blue'))

    map_f.add_child(fga)
    map_f.add_child(fgb)
    map_f.add_child(fgc)
    map_f.add_child(folium.LayerControl())
    map_f.save('Map1.html')


main()
