from collections import defaultdict
import copy
import folium
import flightradar24
import optimizer

fr = flightradar24.Api()

airports = fr.get_airports()['rows']
br_airports_se = list(filter(lambda airport: airport['country'] == 'Brazil', airports))


def _generate_color(index):
    color = 'red'
    if index == 2:
        color = 'blue'
    elif index == 3:
        color = 'yellow'
    next_index = index + 1 if index < 3 else 1
    return color, next_index


def _group_by_airplane(routes):
    routes_by_airplane = defaultdict(list)
    for route in routes:
        routes_by_airplane[route['airplane']].append(route)

    return routes_by_airplane


def _group_by_airport(routes):
    routes_by_airport = defaultdict(lambda: defaultdict(list))
    for route in routes:
        routes_by_airport[route['origin']['name']]['as_origin'].append(route)
        routes_by_airport[route['destine']['name']]['as_destine'].append(route)

    return routes_by_airport


def map_by_airplanes(optimization_data, map_file_name):
    routes_bkp = copy.deepcopy(optimization_data['rotas'])
    airplanes_bkp = copy.deepcopy(optimization_data['aeronaves'])
    fix_cost, fix_routes = optimizer.treat_failures(optimization_data['aeronaves'], br_airports_se)
    cost = 0
    routes = []
    if len(optimization_data['aeronaves']) > 0:
        cost, routes = optimizer.optimize(optimization_data, br_airports_se)
    routes.extend(fix_routes)

    routes_by_airplane = _group_by_airplane(routes)
    routes_by_airport = _group_by_airport(routes)

    airplane_vision_map = folium.Map(location=[-20.1234, -45.9408], zoom_start=5, min_zoom=4, tiles='Mapbox Bright')
    fg_airports = folium.FeatureGroup(name='Brazilian airports')

    for br_airport in br_airports_se:
        popup = br_airport['iata']
        if br_airport['iata'] in routes_by_airport:
            if 'as_origin' in routes_by_airport[br_airport['iata']]:
                popup = popup + '<br />Origem de:'
                for route in routes_by_airport[br_airport['iata']]['as_origin']:
                    popup = popup + '<br />' + route['airplane']
                    popup = popup + ' - ' + route['departure_time'].strftime('%4Y-%m-%d %H:%M:%S')

            if 'as_destine' in routes_by_airport[br_airport['iata']]:
                popup = popup + '<br />Destino de:'
                for route in routes_by_airport[br_airport['iata']]['as_destine']:
                    popup = popup + '<br />' + route['airplane']

        fg_airports.add_child(folium.CircleMarker(location=[float(br_airport['lat']), float(br_airport['lon'])], radius=6,
                                                  popup=popup, fill_color='green', color='grey',
                                                  fill=True, fill_opacity=0.7))
    airplane_vision_map.add_child(fg_airports)

    color_index = 1
    for (airplane, routes) in routes_by_airplane.items():
        route_color, color_index = _generate_color(color_index)
        fg = folium.FeatureGroup(name=airplane)

        for route in routes:
            points = [(float(route['origin']['lat']), float(route['origin']['lon'])),
                      (float(route['destine']['lat']), float(route['destine']['lon']))]
            popup = route['airplane'] + ' - ' + route['departure_time'].strftime('%4Y-%m-%d %H:%M:%S')
            fg.add_child(folium.PolyLine(locations=points, popup=popup, color=route_color))

        airplane_vision_map.add_child(fg)

    airplane_vision_map.add_child(folium.LayerControl())
    airplane_vision_map.save(map_file_name)

    optimization_data['rotas'] = routes_bkp
    optimization_data['aeronaves'] = airplanes_bkp

    return fix_cost + cost, routes
