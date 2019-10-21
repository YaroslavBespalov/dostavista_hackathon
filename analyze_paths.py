import pandas as pd
import numpy as np

cols = ['x', 'y', 't0', 't1', 'payment']


def prepare_picks_drops(orders):
    picks = orders[['pickup_location_x', 'pickup_location_y', 'pickup_from', 'pickup_to', 'payment']]
    picks.columns = cols
    picks['type'] = 'P'

    drops = orders[['dropoff_location_x', 'dropoff_location_y', 'dropoff_from', 'dropoff_to', 'payment']]
    drops.columns = cols
    drops['type'] = 'D'

    picks_drops = pd.concat([picks, drops])

    return picks_drops


def path_to_frame(path, picks_drops):
    path_df_pick = pd.DataFrame(path, columns=cols[:-1])
    res = pd.merge(path_df_pick, picks_drops)
    return res


def get_zero_payments_mask(paths, picks_drops):
    payments = [
        path_to_frame(p['path'], picks_drops)['payment'].sum() / 2
        for p in paths
    ]
    return np.array(payments) == 0


def get_all_orders(paths):
    all_orders = []
    for p in paths:
        all_orders.extend(p['orders'])

    print(all_orders)
    return all_orders

