import json
import pytz
from datetime import datetime
from datetime import timedelta
from geopy import distance
import pulp

configs_file = open('configs.json', 'r')
configs = json.loads(configs_file.read())

TIME_FIX_FAILURES = configs['failure_time_to_fix']
PLACE_FIX_FAILURES = configs['failure_treatment']

PRICE_PER_L = configs['price_per_l']
SCALE_TIME = 60
MIN_SPEED = None


def _pre_processing(data, airports):
    global MIN_SPEED

    routes = data['rotas']
    routes.insert(0, 'first')
    routes.append('last')
    airplanes = data['aeronaves']

    speeds = [airplane['veloc_max'] for airplane in airplanes]
    MIN_SPEED = min(speeds)

    airports_by_iata = {}
    for airport in airports:
        airports_by_iata[airport['iata']] = airport

    for airplane in airplanes:
        airplane['disponibilidade'] = datetime.strptime(airplane['disponibilidade'], '%Y-%m-%dT%H:%M:%S.%f')

    for route in routes:
        if route is not 'first' and route is not 'last':
            route['horario_decolagem'] = datetime.strptime(route['horario_decolagem'], '%Y-%m-%dT%H:%M:%S.%f')
            route['horario_pouso'] = datetime.strptime(route['horario_pouso'], '%Y-%m-%dT%H:%M:%S.%f')

            route['origem'] = airports_by_iata[route['origem']]
            route['destino'] = airports_by_iata[route['destino']]

            origin_coordinate = (route['origem']['lat'], route['origem']['lon'])
            destine_coordinate = (route['destino']['lat'], route['destino']['lon'])
            route['distancia'] = distance.vincenty(origin_coordinate, destine_coordinate).km

    schedule_restrictions = []
    airplane_restrictions = []
    cost = [[[9999999999 for x in range(len(airplanes))] for y in range(len(routes))] for z in range(len(routes))]
    for i in range(len(routes)):
        for j in range(len(routes)):
            if i == j or j == 0 or i == len(routes)-1:
                schedule_restrictions.append((i, j))
            elif i != 0 and j != len(routes)-1:
                if routes[i]['destino'] == routes[j]['origem']:
                    if _incompatible_times(routes[i], routes[j]):
                        schedule_restrictions.append((i, j))
                elif _incompatible_routes(routes[i], routes[j]):
                        schedule_restrictions.append((i, j))

            for k in range(len(airplanes)):
                if i != j and i != len(routes)-1 and j != 0:
                    km_by_l = airplanes[k]['autonomia']/airplanes[k]['consumo']

                    between_cost = 0
                    if i == 0 and j != len(routes)-1:
                        actual = airports_by_iata[airplanes[k]['localizacao']]
                        origin_coordinate = (actual['lat'], actual['lon'])
                        destine_coordinate = (routes[j]['origem']['lat'], routes[j]['origem']['lon'])
                        km_distance = distance.vincenty(origin_coordinate, destine_coordinate).km
                        between_cost = (km_distance / km_by_l) * PRICE_PER_L
                    elif i != 0 and j != len(routes)-1 and routes[i]['destino'] != routes[j]['origem']:
                        between_cost = _calculate_between_cost(km_by_l, routes[i], routes[j])

                    first_route_cost = 0
                    if j != len(routes) - 1:
                        first_route_cost = (routes[j]['distancia'] / km_by_l) * PRICE_PER_L

                    cost[i][j][k] = between_cost + first_route_cost# + second_route_cost

                if j != 0 and j != len(routes)-1:
                    actual = airports_by_iata[airplanes[k]['localizacao']]
                    origin_coordinate = (actual['lat'], actual['lon'])
                    destine_coordinate = (routes[j]['origem']['lat'], routes[j]['origem']['lon'])
                    km_distance = distance.vincenty(origin_coordinate, destine_coordinate).km
                    hours_to_travel = km_distance / airplanes[k]['veloc_max']
                    if (routes[j]['horario_decolagem'] < (airplanes[k]['disponibilidade'] + timedelta(hours=hours_to_travel))
                            or airplanes[k]['max_pas'] < routes[j]['num_passageiros'])\
                            and not airplane_restrictions.__contains__((k, j)):
                        airplane_restrictions.append((k, j))

    schedule_restrictions = list(filter(lambda sr: sr[0] != len(routes)-1 and sr[1] != 0, schedule_restrictions))

    return schedule_restrictions, airplane_restrictions, cost


def _incompatible_times(first_route, second_route):
    first_arrive_time = first_route['horario_pouso']
    second_departure_time = second_route['horario_decolagem']
    return first_arrive_time > (second_departure_time - timedelta(minutes=SCALE_TIME))


def _incompatible_routes(first_route, second_route):
    first_coordinate = (first_route['destino']['lat'], first_route['destino']['lon'])
    second_coordinate = (second_route['origem']['lat'], second_route['origem']['lon'])
    distance_km = distance.vincenty(first_coordinate, second_coordinate).km
    mins_to_travel = (distance_km / MIN_SPEED) * 60

    first_arrive_time = first_route['horario_pouso']
    second_departure_time = second_route['horario_decolagem']
    return first_arrive_time > (second_departure_time - timedelta(minutes=SCALE_TIME + mins_to_travel))


def _calculate_between_cost(km_by_l, first_route, second_route):
    first_coordinate = (first_route['destino']['lat'], first_route['destino']['lon'])
    second_coordinate = (second_route['origem']['lat'], second_route['origem']['lon'])
    distance_km = distance.vincenty(first_coordinate, second_coordinate).km
    return (distance_km / km_by_l) * PRICE_PER_L


def _prepare_data(data, c):
    routes = data['rotas']
    airplanes = data['aeronaves']

    arcs = []
    arc_data = {}

    for i in range(len(routes)):
        for j in range(len(routes)):
            for k in range(len(airplanes)):
                arc = (i, j, airplanes[k]['tail'])
                arc_data[arc] = [c[i][j][k], 0, 1]
                arcs.append(arc)

    return arcs, arc_data


def optimize(data, airports):
    sr, ar, c = _pre_processing(data, airports)
    arcs, arc_data = _prepare_data(data, c)

    routes = data['rotas']
    airplanes = data['aeronaves']
    allocation = []

    costs, mins, maxs = pulp.splitDict(arc_data)

    # cria os limites das variaveis
    x = pulp.LpVariable.dicts("Route", arcs, 0, 1, pulp.LpInteger)
    for arc in arcs:
        x[arc].bounds(mins[arc], maxs[arc])

    # variavel com estrutura do problema
    prob = pulp.LpProblem("Min Routes", pulp.LpMinimize)

    # funcao objetivo
    prob += pulp.lpSum([x[arc] * costs[arc] for arc in arcs]), ""

    # restricao 1: voos que nao podem ser feitos seguidamente
    for i, j in sr:
        prob += pulp.lpSum([x[(i, j, k['tail'])] for k in airplanes]) == 0, ""

    # restricao 2: todos os voos devem ser feitos
    for j in range(1, len(routes)-1):
        prob += pulp.lpSum([x[(i, j, k['tail'])] for i in range(len(routes)) for k in airplanes]) == 1, ""

    # restricao 3: todas as naves que chegam em um no, saem desse no
    for i in range(1, len(routes) - 1):
        for k in airplanes:
            prob += pulp.lpSum([x[(i, j, k['tail'])] for j in range(len(routes))]) == \
                    pulp.lpSum([x[(j, i, k['tail'])] for j in range(len(routes))]), ""

    # restricao 4: todas as naves devem sair do no inicial
    for k in airplanes:
        prob += pulp.lpSum([x[(0, j, k['tail'])] for j in range(len(routes))]) == 1, ""

    # restricao 5: todas as naves devem chegar no no final
    for k in airplanes:
        prob += pulp.lpSum([x[(i, (len(routes)-1), k['tail'])] for i in range(len(routes))]) == 1, ""

    # restricao 6: naves que nao podem fazer certos voos
    for k, j in ar:
        prob += pulp.lpSum([x[(i, j, airplanes[k]['tail'])] for i in range(len(routes))]) == 0, ""

    # restricao 7: nenhuma nave deve chegar no no inicial
    for k in airplanes:
        prob += pulp.lpSum([x[(i, 0, k['tail'])] for i in range(len(routes))]) == 0, ""

    # restricao 8: nenhuma nave deve sair do no final
    for k in airplanes:
        prob += pulp.lpSum([x[((len(routes)-1), j, k['tail'])] for j in range(len(routes))]) == 0, ""

    # resolvendo
    prob.writeLP("min_routes.lp")
    prob.solve()
    print("Status:", pulp.LpStatus[prob.status])
    for v in prob.variables():
        if v.varValue == 1:
            print(v.name, "=", v.varValue)
            name = v.name.replace(')', '')
            chars = name.split('(')[1].split(',_')
            route = int(chars[1])
            tail = chars[-1].replace('\'', '')
            flight = routes[route]
            if flight != 'last':
                allocation.append({
                    'airplane': tail,
                    'origin': {
                        'name': flight['origem']['iata'],
                        'lat': flight['origem']['lat'],
                        'lon': flight['origem']['lon']
                    },
                    'destine': {
                        'name': flight['destino']['iata'],
                        'lat': flight['destino']['lat'],
                        'lon': flight['destino']['lon']
                    },
                    'departure_time': flight['horario_decolagem']
                })

    print("Cost = ", pulp.value(prob.objective))

    cost = pulp.value(prob.objective)
    return cost, allocation


def treat_failures(airplanes, airports):
    airports_by_iata = {}
    for airport in airports:
        airports_by_iata[airport['iata']] = airport

    routes = []
    cost = 0
    to_remove = []
    for airplane in airplanes:
        km_by_l = airplane['autonomia']/airplane['consumo']

        if len(airplane['falhas']['3']) > 0:
            last_3 = datetime.strptime(airplane['falhas']['3'][-1], '%Y-%m-%dT%H:%M:%S.%f')
            last_3 = last_3.astimezone(pytz.timezone('America/Sao_Paulo'))
            if (last_3 + timedelta(hours=TIME_FIX_FAILURES[2])) <= datetime.now(pytz.timezone('America/Sao_Paulo')):
                final_fix = None
                final_distance = 999999999
                actual = airports_by_iata[airplane['localizacao']]
                for place in PLACE_FIX_FAILURES[2]:
                    place_to_fix = airports_by_iata[place]
                    origin_coordinate = (actual['lat'], actual['lon'])
                    destine_coordinate = (place_to_fix['lat'], place_to_fix['lon'])
                    km_distance = distance.vincenty(origin_coordinate, destine_coordinate).km
                    if km_distance < final_distance:
                        final_distance = km_distance
                        final_fix = place_to_fix
                cost += (final_distance / km_by_l) * PRICE_PER_L
                routes.append({
                    'airplane': airplane['tail'],
                    'origin': {
                        'name': actual['iata'],
                        'lat': actual['lat'],
                        'lon': actual['lon']
                    },
                    'destine': {
                        'name': final_fix['iata'],
                        'lat': final_fix['lat'],
                        'lon': final_fix['lon']
                    },
                    'departure_time': last_3
                })
                to_remove.append(airplane)

        elif len(airplane['falhas']['2']) > 0:
            last_2 = datetime.strptime(airplane['falhas']['2'][-1], '%Y-%m-%dT%H:%M:%S.%f')
            last_2 = last_2.astimezone(pytz.timezone('America/Sao_Paulo'))
            if (last_2 + timedelta(hours=TIME_FIX_FAILURES[1])) <= datetime.now(pytz.timezone('America/Sao_Paulo')):
                final_fix = None
                final_distance = 999999999
                actual = airports_by_iata[airplane['localizacao']]
                for place in PLACE_FIX_FAILURES[1]:
                    place_to_fix = airports_by_iata[place]
                    origin_coordinate = (actual['lat'], actual['lon'])
                    destine_coordinate = (place_to_fix['lat'], place_to_fix['lon'])
                    km_distance = distance.vincenty(origin_coordinate, destine_coordinate).km
                    if km_distance < final_distance:
                        final_distance = km_distance
                        final_fix = place_to_fix
                cost += (final_distance / km_by_l) * PRICE_PER_L
                routes.append({
                    'airplane': airplane['tail'],
                    'origin': {
                        'name': actual['iata'],
                        'lat': actual['lat'],
                        'lon': actual['lon']
                    },
                    'destine': {
                        'name': final_fix['iata'],
                        'lat': final_fix['lat'],
                        'lon': final_fix['lon']
                    },
                    'departure_time': last_2
                })
                to_remove.append(airplane)

        elif len(airplane['falhas']['1']) > 0:
            last_1 = datetime.strptime(airplane['falhas']['1'][-1], '%Y-%m-%dT%H:%M:%S.%f')
            last_1 = last_1.astimezone(pytz.timezone('America/Sao_Paulo'))
            if (last_1 + timedelta(hours=TIME_FIX_FAILURES[0])) <= datetime.now(pytz.timezone('America/Sao_Paulo')):
                final_fix = None
                final_distance = 999999999
                actual = airports_by_iata[airplane['localizacao']]
                for place in PLACE_FIX_FAILURES[0]:
                    place_to_fix = airports_by_iata[place]
                    origin_coordinate = (actual['lat'], actual['lon'])
                    destine_coordinate = (place_to_fix['lat'], place_to_fix['lon'])
                    km_distance = distance.vincenty(origin_coordinate, destine_coordinate).km
                    if km_distance < final_distance:
                        final_distance = km_distance
                        final_fix = place_to_fix
                cost += (final_distance / km_by_l) * PRICE_PER_L
                routes.append({
                    'airplane': airplane['tail'],
                    'origin': {
                        'name': actual['iata'],
                        'lat': actual['lat'],
                        'lon': actual['lon']
                    },
                    'destine': {
                        'name': final_fix['iata'],
                        'lat': final_fix['lat'],
                        'lon': final_fix['lon']
                    },
                    'departure_time': last_1
                })
                to_remove.append(airplane)

    for airplane in to_remove:
        airplanes.remove(airplane)

    return cost, routes
