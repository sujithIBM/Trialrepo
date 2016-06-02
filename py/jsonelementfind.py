import json

jsonData = """{"from": {"id": "8", "name": "Mary Pinter"},
"message": "How ARE you?", "comments": {"count": 0},
"updated_time": "2012-05-01", "created_time": "2012-05-01",
"to": {"data": [{"id": "1543", "name": "Honey Pinter"}]},
"type": "status", "id": "id_7"}"""

def getTargetIds(jsonData):
    data = json.loads(jsonData)
    if 'to' not in data:
        raise ValueError("No target in given data")
    if 'data' not in data['to']:
        raise ValueError("No data for target")

    for dest in data:
        if 'id' not in dest:
            continue
        targetId = dest['id']
        print("to_id:", targetId)
getTargetIds(jsonData)
