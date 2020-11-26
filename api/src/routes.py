from flask import current_app as app
from flask import request
from flask import jsonify
from sqlalchemy.orm.exc import NoResultFound

from . import db
from utils import load_json_data
from utils import select_requested_data
from utils import is_valid_input
from models import Access


@app.route('/payless/object/monitor_request/register', methods=['GET', 'POST'])
def register():
    """ Register the a monitoring request at the server.

    Returns:
        - access_id (int): access-id (key) to access the entry in the table
    """
    
    content = request.json

    metric = ''
    aggregation_level = ''
    monitor = ''

    if 'metric' in content['MonitoringRequest']:
        metric = content['MonitoringRequest']['metric']

    if 'aggregation_level' in content['MonitoringRequest']:
        aggregation_level = content['MonitoringRequest']['aggregation_level']   
    
    if 'monitor' in content['MonitoringRequest']:
        monitor = content['MonitoringRequest']['monitor']  
    
    # Check whether input is valid
    if not is_valid_input(monitor, metric, aggregation_level):
        return 'Error: Invalid or Incomplete Parameter Input'

    new_access = Access(metric=metric, aggregation_level=aggregation_level, monitor=monitor) 

    try: 
        db.session.add(new_access)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return 'Database Error: ' + str(e)
    else:
        return 'Successfully registered the request with access-id: ' + str(new_access.id)
    

@app.route('/payless/object/monitor_request/delete/<access_id>', methods=['POST'])
def delete(access_id):
    """ Delete the monitoring request from the table.

    Params:
        - access_id (int): access-id (key) to access the entry in the table
    """

    access = Access.query.filter_by(id=access_id).first()
    
    if access is None:
        return 'Error: No monitoring request found with the access-id: ' + str(access_id)
    
    db.session.delete(access)
    db.session.commit()

    return 'Successfully deleted the request with access-id: ' + str(access_id)


@app.route('/payless/object/monitor_request/update/<access_id>', methods=['GET', 'POST'])
def update(access_id):
    """ Updates an existing monitoring request in the table.

    Params:
        - access_id (int): access-id (key) to access the entry in the table
    """
    content = request.json

    access = Access.query.filter_by(id=access_id).first()
    
    if access is None:
        return 'Error: No monitoring request found with the access-id: ' + str(access_id)

    metric = ''
    aggregation_level = ''
    monitor = ''

    if 'metric' in content['MonitoringRequest']:
        metric = content['MonitoringRequest']['metric']

    if 'aggregation_level' in content['MonitoringRequest']:
        aggregation_level = content['MonitoringRequest']['aggregation_level']   
    
    if 'monitor' in content['MonitoringRequest']:
        monitor = content['MonitoringRequest']['monitor'] 

    # Check whether input is valid
    if not is_valid_input(monitor, metric, aggregation_level):
        return 'Error: Invalid or Incomplete Parameter Input' 

    # Update the monitoring request
    access.metric = metric
    access.aggregation_level = aggregation_level
    access.monitor = monitor

    return 'Successfully updated the request with access-id: ' + str(access_id) 


@app.route('/payless/log/retrieve/<access_id>', methods=['GET'])
def retrieve(access_id):
    """ Retrieves the requested data as specified in the monitoring request.

    Params:
        - access_id (int): access-id (key) to access the entry in the table

    Return:
        - Requested data in json format
    """

    access = Access.query.filter_by(id=access_id).first()
    
    if access is None:
        return 'Error: No monitoring request found with the access-id: ' + str(access_id)

    json_data = load_json_data(access.monitor)
    requested_data = select_requested_data(json_data, access.metric, access.aggregation_level)
    return jsonify(requested_data)







