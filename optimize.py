from .optimizer import routes


def optimize(airports):
    return routes.get_routes(airports)
