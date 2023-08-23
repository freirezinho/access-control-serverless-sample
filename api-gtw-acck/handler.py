try:
    import unzip_requirements
except ImportError:
    print("Import error during unzip requirements")

from datetime import date, datetime
import json
import psycopg2
import ulid
import uuid


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


def migration(event, context):
    try:
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        cursor = connection.cursor()
        query = """CREATE TABLE IF NOT EXISTS accesskeys (
            id TEXT NOT NULL,
            value TEXT NOT NULL,
            user_id TEXT NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (id)
            );
            CREATE TABLE IF NOT EXISTS accesslogs (
                id TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                PRIMARY KEY (id)
            );"""
        cursor.execute(query)
        cursor.close()
        connection.commit()
        return {
            "statusCode": 200,
            "body": ""
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Migration not successful: {e.args}"
        }


def select_active_keys(user_id, cursor):
    query = f"SELECT * FROM accesskeys WHERE user_id = '{user_id}' AND is_active = true;"
    cursor.execute(query)
    result = cursor.fetchall()
    return result


def select_active_key_by(key_value, cursor):
    query = f"SELECT * FROM accesskeys WHERE value = '{key_value}' AND is_active = true;"
    cursor.execute(query)
    result = cursor.fetchall()
    return result


def select_active_key(id, cursor):
    query = f"SELECT * FROM accesskeys WHERE id = '{id}' AND is_active = true;"
    cursor.execute(query)
    result = cursor.fetchall()
    return result


def log(event, cursor):
    current_fdate = datetime.now().strftime("%m-%d-%YT%H:%M:%SZ")
    query = "INSERT INTO accesslogs(id, message, created_at, updated_at) VALUES (%s, %s, %s, %s);"
    cursor.execute(query,
                   (
                       ulid.ulid(),
                       f'[{ current_fdate }]: {event}',
                       datetime.now(),
                       datetime.now()
                   )
                   )
    return


def validate_key(event, context):
    params = event['pathParameters']
    if 'value' not in params:
        return {
            'statusCode': 400,
            'body': 'Bad Request'
        }
    try:
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        cursor = connection.cursor()
        result = select_active_key_by(key_value=params['value'], cursor=cursor)
        log(
            event=f"Foi solicitada a validação da chave com valor {params['value']}",
            cursor=cursor
        )
        if result != None and len(result) > 0:
            log(
                event=f"Verificamos e validamos a chave com valor {params['value']}",
                cursor=cursor
            )
            return {
                "statusCode": 200,
                "body": ""
            }
        else:
            log(
                event=f"Verificamos e negamos a existência de chave ativa com valor {params['value']}",
                cursor=cursor
            )
            return {
                "statusCode": 404,
                "body": ""
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": f"Houve um problema na conexão com o banco: {e.args}"}
        }
    finally:
        cursor.close()
        connection.commit()


def json_date_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def get_key(event, context):
    params = event['pathParameters']
    if 'id' not in params:
        return {
            'statusCode': 400,
            'body': 'Bad Request'
        }
    try:
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        cursor = connection.cursor()
        result = select_active_keys(
            cursor=cursor,
            user_id=params['id'])
        cursor.close()
        connection.commit()
        if result != None:
            record = result[0]
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        'id': record[0],
                        'value': record[1],
                        'user_id': record[2],
                        'is_active': record[3],
                        'created_at': record[4].strftime("%m-%d-%YT%H:%M:%SZ"),
                        'updated_at': record[5].strftime("%m-%d-%YT%H:%M:%SZ")
                    }
                )
            }
        else:
            return {
                'statusCode': 404,
                'body': ''
            }
    except Exception as e:
        return {
            "statusCode": 404,
            "body": {"error": f"Houve um problema na conexão com o banco: {e.args}"}
        }


def create_key(event, context):
    body = event['body']
    if 'user_id' not in body:
        return {
            'statusCode': 400,
            'body': 'Bad Request'
        }
    try:
        jsonBody = json.loads(body)
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        user_id = jsonBody['user_id']
        cursor = connection.cursor()
        user_active_keys = select_active_keys(
            user_id=user_id, cursor=cursor)

        if user_active_keys != None or len(user_active_keys) > 0:
            for key in user_active_keys:
                key_id = key[0]
                deactivate_query = "UPDATE accesskeys SET is_active = %s WHERE id = %s"
                cursor.execute(deactivate_query, (False, key_id))
                log(event=f"Chave {key_id}, do usuário {user_id} foi colocada na fila para invalidação", cursor=cursor)

        query = "INSERT INTO accesskeys(id, value, user_id, is_active, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s);"
        new_key_id = ulid.ulid()
        new_key_value = str(uuid.uuid4())
        values_tuple = (new_key_id, new_key_value,
                        jsonBody['user_id'], True, datetime.now(), datetime.now())
        cursor.execute(query, values_tuple)
        log(
            event=f"Nova chave {new_key_id} foi colocada na fila para criação para o usuário {user_id}",
            cursor=cursor
        )
        cursor.close()
        connection.commit()
        return {
            "statusCode": 201,
            "body": {
                "id": new_key_id,
                "value": new_key_value
            }
        }
    except Exception as e:
        return {
            "statusCode": 503,
            "body": {"error": f"Houve um problema na conexão com o banco: {e.args}"}
        }


def cancel_key(event, context):
    params = event['pathParameters']
    if 'id' not in params:
        return {
            'statusCode': 400,
            'body': 'Bad Request'
        }
    try:
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        cursor = connection.cursor()
        key_id = params['id']

        log(
            event=f"Foi solicitado o cancelamento da chave com id {key_id}",
            cursor=cursor
        )

        result = select_active_key(id=key_id, cursor=cursor)

        if result == None or len(result) == 0:
            log(
                event=f"Não havia chave ativa com id ${key_id}, por isso o cancelamento não foi concluído",
                cursor=cursor
            )
            return {
                'statusCode': 406,
                'body': 'Not Acceptable'
            }

        deactivate_query = "UPDATE accesskeys SET is_active = %s WHERE id = %s"
        cursor.execute(deactivate_query, (False, key_id))

        log(event=f"Chave {key_id} foi colocada na fila para invalidação", cursor=cursor)

        return {
            'statusCode': 200,
            'body': ''
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": {"error": f"Houve um problema na conexão com o banco: {e.args}"}
        }
    finally:
        cursor.close()
        connection.commit()


def hello(event, context):
    body = {
        "message": "It works!!",
        "pathParam": event['pathParameters']['id'],
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
