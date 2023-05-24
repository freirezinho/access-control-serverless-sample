try:
    import unzip_requirements
except ImportError:
    print("Import error during unzip requirements")

import datetime
import json
import boto3
import psycopg2
import ulid
import uuid


def retrieve_credentials():
    credential = {}

    secret_name = "DBParams"
    region_name = "us-east-1"
    db_host = "xyz.rds.aws.amazon.com"
    db_name = "acckDB"

    # boto3.setup_default_session(profile_name='localstack')

    client = boto3.client(
        service_name='secretsmanager',
        endpoint_url="http://0.0.0.0:4566"
    )

    print(client)
    try:

        # get_secret_value_response = client.get_secret_value(
        #     SecretId=secret_name
        # )

        # print(get_secret_value_response)

        # secret = json.loads(get_secret_value_response['SecretString'])

        # credential['username'] = secret['username']
        # credential['password'] = secret['password']
        # credential['host'] = secret['host']
        # credential['db'] = secret['db']
        credential['username'] = 'hippy'
        credential['password'] = 'pippy'
        credential['host'] = 'db'
        credential['db'] = 'yippy'

    except Exception as e:
        credential['error'] = e.args

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
        query = "CREATE TABLE IF NOT EXISTS accesskeys (id TEXT NOT NULL, value TEXT NOT NULL, user_id TEXT NOT NULL, is_active BOOLEAN NOT NULL, created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL, PRIMARY KEY (id));"
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


def select_active_key(key_value, cursor):
    query = f"SELECT * FROM accesskeys WHERE value = '{key_value}' AND is_active = true;"
    cursor.execute(query)
    result = cursor.fetchall()
    return result


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
        result = select_active_key(key_value=params['value'], cursor=cursor)
        cursor.close()
        connection.commit()
        if result != None and len(result) > 0:
            return {
                "statusCode": 200,
                "body": ""
            }
        else:
            return {
                "statusCode": 404,
                "body": ""
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"Deu ruim no banco {e.args}"
        }


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
            "body": f"Deu ruim no banco {e.args}"
        }


def create_key(event, context):
    body = event['body']
    if 'user_id' not in body:
        return {
            'statusCode': 400,
            'body': 'Bad Request'
        }
    try:
        # return {
        #     'statusCode': 201,
        #     'body': json.dumps(event)
        # }
        jsonBody = json.loads(body)
        db_config = retrieve_credentials()
        connection = connect_with(credentials=db_config)
        user_id = jsonBody['user_id']

        cursor = connection.cursor()
        user_active_keys = select_active_keys(
            user_id=user_id, cursor=cursor)
        if user_active_keys != None or len(user_active_keys) > 0:
            print("Treating stuff..")
            for key in user_active_keys:
                key_id = key[0]
                deactivate_query = "UPDATE accesskeys SET is_active = %s WHERE id = %s"
                cursor.execute(deactivate_query, (False, key_id))
        query = "INSERT INTO accesskeys(id, value, user_id, is_active, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s);"
        values_tuple = (ulid.ulid(), str(uuid.uuid4(
        )), jsonBody['user_id'], True, datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query, values_tuple)
        cursor.close()

        connection.commit()
        return {
            "statusCode": 201,
            "body": ""
        }
    except Exception as e:
        return {
            "statusCode": 503,
            "body": f"Deu ruim no banco {e.args}"
        }


def hello(event, context):
    body = {
        "message": "It works!!",
        "pathParam": event['pathParameters']['id'],
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)}

    return response
