import json
import boto3
import os
import urllib3
import requests
from requests.auth import HTTPBasicAuth

secrets_client = boto3.client(service_name='secretsmanager')
ssm_client = boto3.client('ssm')
sg_runtime = boto3.client('runtime.sagemaker')

TEXT_EMBEDDING_MODEL_ENDPOINT_NAME = ssm_client.get_parameter(Name="txt2emb_sm_endpoint")['Parameter']['Value']
print(f'TEXT_EMBEDDING_MODEL_ENDPOINT_NAME: { TEXT_EMBEDDING_MODEL_ENDPOINT_NAME }')

TEXT_GENERATION_MODEL_ENDPOINT_NAME = ssm_client.get_parameter(Name="txt2txt_sm_endpoint")['Parameter']['Value']
print(f'TEXT_GENERATION_MODEL_ENDPOINT_NAME: { TEXT_GENERATION_MODEL_ENDPOINT_NAME }')

def handler(event, context):
    # print('received event:')
    # print(event)
    data = json.loads(json.dumps(event))
    payload_body = json.loads(data['body'])
    http = urllib3.PoolManager()

    payload_body_split = payload_body['data'].splitlines(True)

    prompt = payload_body_split[0]
    payload = {'text_inputs': [prompt]}
    payload = json.dumps(payload).encode('utf-8')
    response = sg_runtime.invoke_endpoint(EndpointName=TEXT_EMBEDDING_MODEL_ENDPOINT_NAME, 
                                                ContentType='application/json', 
                                                Body=payload)
    body = json.loads(response['Body'].read())
    embedding = body['embedding'][0]

    K = 10
    query = {
        'size': K,
        'query': {
            'knn': {
            'embedding': {
                'vector': embedding,
                'k': K
            }
            }
        }
    }
    ES_DOMAIN_ENDPOINT_NAME  = 'https://' + ssm_client.get_parameter(Name="opensearch_domain_endpoint")["Parameter"]["Value"]
    ES_USER_NAME = ssm_client.get_parameter(Name="opensearch_master_user_name")["Parameter"]["Value"]
    ES_PASSWORD = secrets_client.get_secret_value(SecretId="opensearch_master_password")['SecretString']
    response = requests.post(f'{ES_DOMAIN_ENDPOINT_NAME}/legal-passages/_search', auth=HTTPBasicAuth(ES_USER_NAME, ES_PASSWORD), json=query)
    response_json = response.json()
    hits = response_json['hits']['hits']

    uniq_hits = []
    for hit in hits:
        res = list(filter(lambda uniq_hits: uniq_hits['_source']['passage_id'] == hit['_source']['passage_id'], uniq_hits))
        if len(res) == 0:
            uniq_hits.append(hit)

    parameters = {
        "max_length": 5000,
        "num_return_sequences": 1,
        "top_k": 50,
        "top_p": 0.95,
        "do_sample": True,
        "early_stopping": False,
        "num_beams": 1,
        "no_repeat_ngram_size": 3,        
        "temperature": 1
    }

    answers = []
    if len(payload_body_split) > 1 :
        question = payload_body_split[1]
    else :
        question = payload_body_split[0]

    for hit in uniq_hits:
        score = hit['_score']
        passage = hit['_source']['passage']
        passage = passage.replace("\n", "")
        doc_id = hit['_source']['doc_id']
        passage_id = hit['_source']['passage_id']
        qa_prompt = f'{passage}\n\n{question}\n'
        payload = {"text_inputs": qa_prompt, **parameters}
        encoded_payload = json.dumps(payload).encode("utf-8")        
        sg_response = sg_runtime.invoke_endpoint(EndpointName=TEXT_GENERATION_MODEL_ENDPOINT_NAME, ContentType='application/json', Body=encoded_payload)
        sg_result = json.loads(sg_response['Body'].read().decode())
        resp_obj = {
            "doc_id": doc_id,
            "passage_id": passage_id,
            "passage": passage,
            "ans": sg_result
        }
        answers.append(resp_obj)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(resp_obj)
    }
    