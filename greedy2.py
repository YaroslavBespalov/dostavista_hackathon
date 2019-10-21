import json
import random


DEBUG = False
DEBUG_COURIERS = 50
DEBUG_ORDERS = 1000

START_TIME = 360
INF = 1e9
MAX_ITERATIONS = 15
MAX_DIST_TO_ORDER = 100


class TCourier:

    def __init__(self, _id, x, y):
        self.id = _id
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y


class TOrder:

    def __init__(self, _id, payment,
                 pickup_id, pickup_x, pickup_y, pickup_from, pickup_to,
                 dropoff_id, dropoff_x, dropoff_y, dropoff_from, dropoff_to):
        self.id = _id
        self.payment = payment

        self.pickup_id = pickup_id
        self.pickup_x = pickup_x
        self.pickup_y = pickup_y
        self.pickup_from = pickup_from
        self.pickup_to = pickup_to

        self.dropoff_id = dropoff_id
        self.dropoff_x = dropoff_x
        self.dropoff_y = dropoff_y
        self.dropoff_from = dropoff_from
        self.dropoff_to = dropoff_to

        self.distance = abs(dropoff_x - pickup_x) + abs(dropoff_y - pickup_y) + 10


class TDepot:

    def __init__(self, _id, point_id, x, y):
        self.id = _id
        self.point_id = point_id
        self.x = x
        self.y = y


class TEvent:

    def __init__(self, courier, action, order, timestamp=None):
        self.courier = courier
        self.action = action
        self.order = order
        self.timestamp = timestamp

    def to_output_dict(self):
        return {
            "courier_id": self.courier.id,
            "action": self.action,
            "order_id": self.order.id,
            "point_id": self.order.pickup_id if self.action == "pickup" else self.order.dropoff_id
        }


class TCourierPath:

    def __init__(self, courier):
        self.courier = courier

        self.money = 0
        self.orders = set()
        self.end_time = START_TIME
        self.path = []

        self.cur_money = 0
        self.cur_orders = set()
        self.cur_end_time = START_TIME
        self.cur_path = []


def read_data(filename):
    with open(filename, "r") as f:
        raw_data = json.load(f)

    couriers = [
        TCourier(
            courier["courier_id"],
            courier["location_x"],
            courier["location_y"]
        )
        for courier in raw_data["couriers"]
    ]

    orders = [
        TOrder(
            order["order_id"],
            order["payment"],
            order["pickup_point_id"],
            order["pickup_location_x"],
            order["pickup_location_y"],
            order["pickup_from"],
            order["pickup_to"],
            order["dropoff_point_id"],
            order["dropoff_location_x"],
            order["dropoff_location_y"],
            order["dropoff_from"],
            order["dropoff_to"]
        )
        for order in raw_data["orders"]
    ]

    depots = [
        TDepot(
            i,
            depot["point_id"],
            depot["location_x"],
            depot["location_y"]
        )
        for i, depot in enumerate(raw_data["depots"])
    ]

    if DEBUG:
        random.seed(117)
        random.shuffle(couriers)
        random.shuffle(orders)
        couriers = couriers[:DEBUG_COURIERS]
        orders = orders[:DEBUG_ORDERS]

    return couriers, orders, depots


def distance(x1, y1, x2, y2):
    return abs(x2 - x1) + abs(y2 - y1) + 10


def check_path(path, start_time=START_TIME):
    if not path:
        return True, start_time

    cur_x, cur_y, cur_time = path[0].courier.start_x, path[0].courier.start_y, start_time
    for event in path:
        if event.action == "pickup":
            to_x, to_y, t_from, t_to = event.order.pickup_x, event.order.pickup_y, event.order.pickup_from, event.order.pickup_to
        else:
            to_x, to_y, t_from, t_to = event.order.dropoff_x, event.order.dropoff_y, event.order.dropoff_from, event.order.dropoff_to
        t_arrive = cur_time + distance(cur_x, cur_y, to_x, to_y)
        if t_arrive < t_from:
            t_arrive = t_from
        if t_arrive > t_to:
            return False, None
        event.timestamp = t_arrive
        cur_x, cur_y, cur_time = to_x, to_y, t_arrive

    return True, cur_time


def add_point_generator(path, point, start_pos=0):
    for pos in range(start_pos, len(path) + 1):
        yield path[:pos] + [point] + path[pos:], pos


def try_add_order(courier_path, orders, orders_mask, max_dist_to_order, use_bomzhes=True):
    cur_payment = 0
    for i in courier_path.cur_orders:
        cur_payment += orders[i].payment

    max_money = -INF if use_bomzhes else courier_path.cur_money
    max_orders = courier_path.cur_orders
    max_end_time = courier_path.cur_end_time
    max_path = courier_path.cur_path

    for i, order in enumerate(orders):
        if orders_mask[i] or i in courier_path.cur_orders:
            continue

        dist_to_path = distance(courier_path.courier.start_x, courier_path.courier.start_y, order.pickup_x, order.pickup_y)
        for event in courier_path.cur_path:
            if event.action == "pickup":
                x, y = event.order.pickup_x, event.order.pickup_y
            else:
                x, y = event.order.dropoff_x, event.order.dropoff_y
            dist_to_path = min(dist_to_path, distance(x, y, order.pickup_x, order.pickup_y))
        if courier_path.cur_path and dist_to_path > max_dist_to_order:
            continue

        point1 = TEvent(courier_path.courier, "pickup", order)
        point2 = TEvent(courier_path.courier, "dropoff", order)

        for path1, pos1 in add_point_generator(courier_path.cur_path, point1):
            for path2, _ in add_point_generator(path1, point2, pos1 + 1):
                is_correct, end_time = check_path(path2)
                if is_correct:
                    money = cur_payment + order.payment - 2 * (end_time - START_TIME)
                    if money > max_money:
                        max_money = money
                        max_orders = courier_path.cur_orders | {i}
                        max_end_time = end_time
                        max_path = path2

    courier_path.cur_money = max_money
    courier_path.cur_orders = max_orders
    courier_path.cur_end_time = max_end_time
    courier_path.cur_path = max_path

    if courier_path.cur_money > courier_path.money:
        courier_path.money = courier_path.cur_money
        courier_path.orders = courier_path.cur_orders
        courier_path.end_time = courier_path.cur_end_time
        courier_path.path = courier_path.cur_path


def greedy_iteration(couriers_paths, orders, max_dist_to_order, use_bomzhes=True):
    orders_mask = [False for _ in range(len(orders))]
    for courier_path in couriers_paths:
        for i in courier_path.cur_orders:
            orders_mask[i] = True

    money_sum = 0
    for courier_path in couriers_paths:
        try_add_order(
            courier_path,
            orders,
            orders_mask,
            max_dist_to_order,
            use_bomzhes
        )
        for i in courier_path.cur_orders:
            orders_mask[i] = True
        money_sum += courier_path.money

    return money_sum


def clean_bomzhes(couriers_paths):
    for courier_path in couriers_paths:
        courier_path.cur_money = courier_path.money
        courier_path.cur_orders = courier_path.orders
        courier_path.cur_end_time = courier_path.end_time
        courier_path.cur_path = courier_path.path


def print_output(couriers_paths, filename):
    for courier_path in couriers_paths:
        assert check_path(courier_path.path)[0]
    events = sum((courier_path.path for courier_path in couriers_paths), [])
    output = [event.to_output_dict() for event in sorted(events, key=lambda event: (event.timestamp, 0 if event.action == "pickup" else 1))]
    with open(filename, "w") as f:
        json.dump(output, f, indent=4)


if __name__ == "__main__":
    couriers, orders, depots = read_data("./data/contest_input.json")
    couriers_paths = [TCourierPath(courier) for courier in couriers]

    money = 0
    for i in range(MAX_ITERATIONS):
        new_money = greedy_iteration(couriers_paths, orders, MAX_DIST_TO_ORDER, use_bomzhes=True)
        print("Iter {}: {}".format(i, new_money))
        if money == new_money:
            break
        money = new_money
        print_output(couriers_paths, "./output.json")

    clean_bomzhes(couriers_paths)
    for i in range(MAX_ITERATIONS):
        new_money = greedy_iteration(couriers_paths, orders, INF, use_bomzhes=False)
        print("Iter {}: {}".format(i, new_money))
        if money == new_money:
            break
        money = new_money
        print_output(couriers_paths, "./output.json")
