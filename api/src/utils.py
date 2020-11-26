import json

# Change these parameters as required 
PATH_TO_JSON = '/vagrant_data/artifacts/'
PAYLESS_JSON = 'payless.json'
POLLING_JSON = 'periodicpolling.json'

VALID_MONITOR_TYPES = ['periodic_polling', 'adaptive']
VALID_AGGREGATION_LEVELS = ['flow', 'switch']
VALID_METRICS = ['utilization', 'overhead']


def is_valid_input(monitor_type, metric, aggregation_level):
    """ True if the input of the monitoring request is valid.

    Parameters:
        - monitor_type (str): Monitoring type
        - metric (str):

    Returns:
        - True or False
    """
    return is_valid_monitor_type(monitor_type) and is_valid_metric(metric) and is_valid_aggregation_level(aggregation_level)


def is_valid_monitor_type(monitor_type):
    return monitor_type in VALID_MONITOR_TYPES

def is_valid_metric(metric):
    return metric in VALID_METRICS

def is_valid_aggregation_level(aggregation_level):
    return aggregation_level in VALID_AGGREGATION_LEVELS


def load_json_data(monitor_type):
    """ Loads and returns the requested json data that has been
    generated after running the experiments. 
    
    Params: 
        - monitor_type (str): Monitoring type
    
    Returns:
        - Returns the entire json data 
    """

    if monitor_type == 'adaptive':
        path = PATH_TO_JSON + PAYLESS_JSON
    else:
        path = PATH_TO_JSON + POLLING_JSON

    with open(path) as f:
        json_data = json.load(f) 

    return json_data


def select_requested_data(json_data, metric, aggregation_level):
    """ Retrieves the required data from the json data.
    
    Params:
        - json_data: The previously loaded json data.
        - metric (str): Specifies the metric that should be monitored.
        - aggregation_level (str): Specifies the level of aggregation for statstics collection.

    Returns:
        - The requested data.
    
    """

    if metric == 'overhead':
        return json_data['overhead']
    else:
        if aggregation_level == 'flow':
            return json_data['flow_stats']
        elif aggregation_level == 'switch':
            flow_stats = json_data['flow_stats']
            flow_info = json_data['flow_info']
            switches = [value['switch_id'] for value in flow_info.values()] 
            unique_switches = list(set(switches))

            result = {}
            for switch in unique_switches:
                result[str(switch)] = [flow_stats[str(value['flow_id'])] for value in flow_info.values() if value['switch_id'] == switch]
            return result














