import json
import boto3

ssm_client = boto3.client('ssm')

ENDPOINT_NAME = ssm_client.get_parameter(Name="txt2img_sm_endpoint")['Parameter']['Value']
print(f'ENDPOINT_NAME: { ENDPOINT_NAME }')
runtime= boto3.client('runtime.sagemaker')

def handler(event, context):
  #print('received event:' + json.dumps(event, indent=2))
  data = json.loads(json.dumps(event))
  payload_body = json.loads(data['body'])
  #print(payload_body)

  payload = {
    "prompt": payload_body['data'],
    "width": 512,
    "height": 512,
    "num_images_per_prompt": 1,
    "num_inference_steps": 10,
    "guidance_scale": 7.5,
  }
  encoded_payload = json.dumps(payload).encode("utf-8")
  response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME, ContentType='application/json', Accept="application/json;jpeg", Body=encoded_payload)
  result = json.load(response['Body'])

  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
          'Content-Type': 'application/json;jpeg'
      },
      'body': json.dumps(result),
      "isBase64Encoded": False
  }