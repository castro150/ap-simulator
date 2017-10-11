import folium
import flightradar24
import optimizer

fr = flightradar24.Api()
DESIRED_IATA = ['VIX', 'CDI', 'GUZ', 'SBJ', 'QAK', 'POJ', 'CNF', 'DIQ', 'GVR', 'JDF', 'MOC', 'PLU', 'POO', 'JDR', 'UDI',
                'UBA', 'IZA', 'SNZ', 'CAW', 'CFB', 'GIG', 'ITP', 'MEA', 'QRZ', 'SDU', 'ARU', 'AQA', 'AIF', 'QVP', 'BAT',
                'JTC', 'QCP', 'BJP', 'CPQ', 'CGH', 'QDC', 'GUJ', 'GRU', 'FRC', 'QDV', 'QGC', 'LIP', 'MII', 'OUS', 'QHB',
                'PPB', 'RAO', 'QSC', 'SJP', 'SJK', 'SOD', 'UBT', 'VCP', 'VOT']

airports = fr.get_airports()['rows']
br_airports_se = list(filter(lambda airport: airport['iata'] in DESIRED_IATA, airports))


def _generate_color(index):
    color = 'red'
    if index == 2:
        color = 'blue'
    elif index == 3:
        color = 'yellow'
    next_index = index + 1 if index < 3 else 1
    return color, next_index


# TODO olhar o defaultdict
def _group_by_airplane(routes):
    routes_by_airplane = dict()
    for route in routes:
        routes_by_airplane[route['airplane']] = list() if route['airplane'] not in routes_by_airplane \
            else routes_by_airplane[route['airplane']]
        routes_by_airplane[route['airplane']].append(route)

    return routes_by_airplane


def _group_by_airport(routes):
    routes_by_airport = dict()
    for route in routes:
        routes_by_airport[route['origin']['name']] = dict() if route['origin']['name'] not in routes_by_airport\
            else routes_by_airport[route['origin']['name']]
        routes_by_airport[route['origin']['name']]['as_origin'] = list() if 'as_origin'\
            not in routes_by_airport[route['origin']['name']] else routes_by_airport[route['origin']['name']]['as_origin']
        routes_by_airport[route['origin']['name']]['as_origin'].append(route)

        routes_by_airport[route['destine']['name']] = dict() if route['destine']['name'] not in routes_by_airport\
            else routes_by_airport[route['destine']['name']]
        routes_by_airport[route['destine']['name']]['as_destine'] = list() if 'as_destine'\
            not in routes_by_airport[route['origin']['name']] else routes_by_airport[route['origin']['name']]['as_destine']
        routes_by_airport[route['destine']['name']]['as_destine'].append(route)

    return routes_by_airport


class MapGenerator:
    def __init__(self):
        self.routes = optimizer.optimize(br_airports_se)

    def map_by_airplanes(self, map_file_name):
        routes_by_airplane = _group_by_airplane(self.routes)
        routes_by_airport = _group_by_airport(self.routes)

        # TODO informações de voos nos aeroportos (popup)
        airplane_vision_map = folium.Map(location=[-20.5934, -46.9408], zoom_start=7, min_zoom=7, tiles='Mapbox Bright')
        fg_airports = folium.FeatureGroup(name='Brazilian airports')

        for br_airport in br_airports_se:
            fg_airports.add_child(folium.CircleMarker(location=[br_airport['lat'], br_airport['lon']], radius=6,
                                              popup=br_airport['iata'], fill_color='green', color='grey',
                                              fill=True, fill_opacity=0.7))
        airplane_vision_map.add_child(fg_airports)

        # TODO informações de origem e destino com horário na rota (popup)
        color_index = 1
        for (airplane, routes) in routes_by_airplane.items():
            route_color, color_index = _generate_color(color_index)
            fg = folium.FeatureGroup(name=airplane)

            for route in routes:
                points = [(route['origin']['lat'], route['origin']['lon']), (route['destine']['lat'], route['destine']['lon'])]
                fg.add_child(folium.PolyLine(locations=points, popup=route['airplane'] + ' - ' + str(route['departure_time']), color=route_color))

            airplane_vision_map.add_child(fg)

        airplane_vision_map.add_child(folium.LayerControl())
        airplane_vision_map.save(map_file_name)
