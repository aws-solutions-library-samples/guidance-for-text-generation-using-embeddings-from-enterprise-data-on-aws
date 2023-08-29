import os
import json
import boto3

ssm_client = boto3.client('ssm')

ENDPOINT_NAME = ssm_client.get_parameter(Name="txt2txt_sm_endpoint")['Parameter']['Value']
print(f'ENDPOINT_NAME: { ENDPOINT_NAME }')
runtime= boto3.client('runtime.sagemaker')

def handler(event, context):
  print('received event:' + json.dumps(event, indent=2))  
  data = json.loads(json.dumps(event))
  if data['requestContext']['http']['method'] == 'OPTIONS':
    result = '{"message": "Proxy works!!!"}'
  elif data['requestContext']['http']['method'] == 'POST':
    payload_body = json.loads(data['body'])
    parameters = {
      "max_length": 5000,
      "num_return_sequences": 1,
      "top_k": 50,
      "top_p": 0.95,
      "do_sample": True,
    }

    payload = {"text_inputs": payload_body['data'], **parameters}
    encoded_payload = json.dumps(payload).encode("utf-8")
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME, ContentType='application/json', Body=encoded_payload)
    result = json.loads(response['Body'].read().decode())

  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps(result),
      "isBase64Encoded": False
  }