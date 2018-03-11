import boto3

Clients = {}


def client(service, config):
    global Clients
    if service not in Clients:
        print '# Initializing boto3 client for AWS {}'.format(service)
        Clients[service] = boto3.client(
            service,
            region_name='us-east-1',
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key
        )
    return Clients[service]
