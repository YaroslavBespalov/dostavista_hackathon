import json

import tqdm
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

from analyze_paths import prepare_picks_drops, get_zero_payments_mask, get_all_orders
from utils import Order, MIN, distance


def order_cost_fn(curr_x, curr_y, curr_time, order: Order):
    order_pickup_distance = distance(curr_x, curr_y, order.pickup_x, order.pickup_y)
    pickup_time = max(curr_time + order_pickup_distance, order.pickup_from)
    dropoff_time = max(pickup_time + order.distance, order.dropoff_from)
    # print(pickup_time, dropoff_time, order.dropoff_to)
    if pickup_time > order.pickup_to:
        rv = MIN
    if dropoff_time > order.dropoff_to:
        rv = MIN

    else:
        rv = order.payment / (dropoff_time - curr_time)

    return rv, dropoff_time


def get_nearest_orders(x, y, neighbors):
    return neighbors.kneighbors([[x, y]])[1][0]


def greedy(start_x, start_y, start_time, all_orders, amask, neighbors):
    curr_x, curr_y, curr_time = start_x, start_y, start_time
    money = 0
    money_max = 0
    cur_mask = np.copy(amask)
    while True:
        nearest_orders = [order for order in get_nearest_orders(curr_x, curr_y, neighbors) if not cur_mask[order]]
        if not nearest_orders:
            break

        order_scores = [order_cost_fn(curr_x, curr_y, curr_time, all_orders[oid])[0] for oid in nearest_orders]
        min_score_id = np.argmax(order_scores)
        if order_scores[min_score_id] < 0:
            break

        best_order_id = nearest_orders[min_score_id]
        best_order = all_orders[best_order_id]
        cur_mask[best_order_id] = 1

        dropoff_time = order_cost_fn(curr_x, curr_y, curr_time, best_order)[1]
        money += best_order.payment
        curr_x, curr_y, curr_time = best_order.dropoff_x, best_order.dropoff_y, dropoff_time

        cur_money = money - 2 * (curr_time - start_time)
        if cur_money > money_max:
            money_max = cur_money
            amask[:] = cur_mask

    return money_max


if __name__ == '__main__':
    with open('../phystech/data/contest_input.json', 'r') as f:
        data = json.load(f)

    with open('kamenshikov2.json', 'r') as f:
        paths = json.load(f)

    couriers = pd.DataFrame(data['couriers'])
    depots = pd.DataFrame(data['depots'])
    orders = pd.DataFrame(data['orders'])
    # orders = orders[orders['payment'] > 0]
    orders['distance'] = distance(
        orders['pickup_location_x'],
        orders['pickup_location_y'],
        orders['dropoff_location_x'],
        orders['dropoff_location_y']
    )
    orders['price_per_min'] = orders['payment'] / orders['distance']

    picks_drops = prepare_picks_drops(orders)
    zero_couriers = get_zero_payments_mask(paths, picks_drops)
    couriers = couriers.iloc[zero_couriers]
    amask = np.where(get_all_orders(paths))[0]
    ## orders = orders.iloc[~()]

    nn = NearestNeighbors(n_neighbors=1000, p=1)
    nn.fit(orders[['pickup_location_x', 'pickup_location_y']])
    all_orders = [Order(order) for order in orders.to_dict('records')]

    amask = np.zeros(len(all_orders))

    money = []
    for start_x, start_y in tqdm.tqdm(zip(couriers.location_x, couriers.location_y), total=len(couriers)):
        money.append(greedy(start_x, start_y, 360, all_orders, amask, nn))

    print(sum(money))
    print(sum(amask))
