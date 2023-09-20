try:
    import unzip_requirements
except ImportError:
    print("Import error during unzip requirements")

from datetime import date, datetime
import json
import psycopg2


def retrieve_credentials():
    credential = {}

    credential['username'] = 'hippy'
    credential['password'] = 'pippy'
    credential['host'] = 'db'
    credential['db'] = 'yippy'

    return credential


def credentials(event, context):
    credential = retrieve_credentials()
    res = {"statusCode": 200, "body": json.dumps(credential)}
    return res


def connect_with(credentials: dict):
    return psycopg2.connect(
        user=credentials['username'],
        password=credentials['password'],
        host=credentials['host'],
        database=credentials['db'],
        port="5432"
    )


def log_access(event, context):
    body = json.loads(event['body'])
    if 'event' not in body:
        return {
            'statusCode': 400,
            'body': 'Bad Request'
        }
    try:
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        cursor = connection.cursor()
        log(event=body['event'], cursor=cursor)
        cursor.close()
        connection.commit()
        return {
            'statusCode': 201,
            'body': ''
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": f"Houve um problema na conexão com o banco: {e.args}"}
        }


def get_logs(event, context):
    try:
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        cursor = connection.cursor()
        query = "SELECT * FROM accesslogs ORDER BY id::text DESC LIMIT 5;"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        connection.commit()
        if result == None or len(result) == 0:
            return {
                'statusCode': 404,
                'body': ''
            }
        return {
            'statusCode': 200,
            'body': { "result": json.dumps(result, default=json_date_serial) }
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": f"Houve um problema na conexão com o banco: {e.args}"}
        }


def json_date_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))
