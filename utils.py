import numpy as np
from matplotlib import pyplot as plt


MIN = -9999999


class Order:

    def __init__(self, order_data):
        self.pickup_x = order_data['pickup_location_x']
        self.pickup_y = order_data['pickup_location_y']
        self.pickup_from = order_data['pickup_from']
        self.pickup_to = order_data['pickup_to']
        self.dropoff_x = order_data['dropoff_location_x']
        self.dropoff_y = order_data['dropoff_location_y']
        self.dropoff_from = order_data['dropoff_from']
        self.dropoff_to = order_data['dropoff_to']
        self.payment = order_data['payment']
        self.distance = order_data['distance']
        self.price_per_min = order_data['price_per_min']


def distance(x1, y1, x2, y2):
    return np.abs(x1 - x2) + np.abs(y1 - y2) + 10


def plot_data(couriers, depots, orders):
    fig, ax = plt.subplots(figsize=(20, 20))
    ax.scatter(x=couriers['location_x'], y=couriers['location_y'], marker='o', color='black', s=50)
    ax.scatter(x=orders['pickup_location_x'], y=orders['pickup_location_y'], marker='>', color='green', alpha=0.5, s=5)
    ax.scatter(x=orders['dropoff_location_x'], y=orders['dropoff_location_y'], marker='s', color='red', alpha=0.5, s=5)
    ax.scatter(x=depots['location_x'], y=depots['location_y'], marker='^', color='blue', s=300)
