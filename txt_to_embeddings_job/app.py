#!/bin/python3

from fileinput import filename
import boto3
import logging
import json
import shutil
import lzma
import tiktoken
from itertools import islice
import requests
from requests.auth import HTTPBasicAuth
import os
import sys

logger = logging.getLogger("txt_to_embeddings_job")
stdout = logging.StreamHandler(stream=sys.stdout)
fmt = logging.Formatter(
    "%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(process)d >>> %(message)s"
)
stdout.setLevel(logging.DEBUG)
stdout.setFormatter(fmt)
logger.addHandler(stdout)

sagemaker_client = boto3.client('runtime.sagemaker')
opensearch_client = boto3.client('opensearch')
s3_client = boto3.client('s3')
secrets_client = boto3.client(service_name='secretsmanager')
ssm_client = boto3.client('ssm')

ES_DOMAIN_ENDPOINT_NAME  = 'https://' + ssm_client.get_parameter(Name="opensearch_domain_endpoint")["Parameter"]["Value"]
ES_USER_NAME = ssm_client.get_parameter(Name="opensearch_master_user_name")["Parameter"]["Value"]
ES_PASSWORD = secrets_client.get_secret_value(SecretId="opensearch_master_password")['SecretString']
print(f'ES_DOMAIN_ENDPOINT_NAME: { ES_DOMAIN_ENDPOINT_NAME }')

TEXT_EMBEDDING_MODEL_ENDPOINT_NAME = ssm_client.get_parameter(Name="txt2emb_sm_endpoint")['Parameter']['Value']
print(f'TEXT_EMBEDDING_MODEL_ENDPOINT_NAME: { TEXT_EMBEDDING_MODEL_ENDPOINT_NAME }')

EMBEDDING_CTX_LENGTH = 768
EMBEDDING_ENCODING = 'cl100k_base'
encoding = tiktoken.get_encoding(EMBEDDING_ENCODING)

def batched(iterable, n):
    """Batch data into tuples of length n. The last batch may be shorter."""
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := tuple(islice(it, n))):
        yield batch

def chunked_tokens(text, chunk_length):
    tokens = encoding.encode(text)
    chunks_iterator = batched(tokens, chunk_length)
    yield from chunks_iterator

def len_safe_get_embedding(text, max_tokens=EMBEDDING_CTX_LENGTH, average=True):
    chunks = []
    for chunk in chunked_tokens(text, chunk_length=max_tokens):
        chunks.append(encoding.decode(chunk))
    return chunks

def get_embedding(chunk: str):
    payload = {'text_inputs': [chunk]}
    payload = json.dumps(payload).encode('utf-8')

    response = sagemaker_client.invoke_endpoint(EndpointName=TEXT_EMBEDDING_MODEL_ENDPOINT_NAME, 
                                    ContentType='application/json',  
                                    Body=payload)
    model_predictions = json.loads(response['Body'].read())
    embedding = model_predictions['embedding'][0]
    return embedding

def check_and_create_os_index():
    print('About to check and create OpenSearch Index')
    url = f'{ES_DOMAIN_ENDPOINT_NAME}/legal-passages/'
    response = requests.head(url, auth=HTTPBasicAuth(ES_USER_NAME, ES_PASSWORD))
    if response.status_code == 404:
        mapping = {
            'settings': {
                'index': {
                    'knn': True  # Enable k-NN search for this index
                }
            },
            'mappings': {
                'properties': {
                    'embedding': {  # k-NN vector field
                        'type': 'knn_vector',
                        'dimension': 4096  # Dimension of the vector
                    },
                    'passage_id': {
                        'type': 'long'
                    },
                    'passage': {
                        'type': 'text'
                    },
                    'doc_id': {
                        'type': 'keyword'
                    }
                }
            }
        }        
        response = requests.put(url, auth=HTTPBasicAuth(ES_USER_NAME, ES_PASSWORD), json=mapping)
        if response.status_code == 200:
            print(f'Index created: {response.text}')
            return True
        else:
            print(f'Index creation failed!!!')
            return False
    elif response.status_code == 200:
        print('OpenSearch Index already exists')
        return True
    elif response.status_code == 403:
        print('Forbidden Error!!!')
        return False
    else:
        print(f'Error occurred - response code - {response.status_code}')
        return False
if __name__ == "__main__":
    print('Starting to create OpenSearch Index')
    filename = './data/train.cc_casebooks.jsonl'
    logging.info(f'Reading data from {filename}.xz')

    with lzma.open(f"{filename}.xz", "rb") as fsrc:
        with open(filename, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)
    logging.info(f'Unzipped data to {filename}')

    with open(filename,  'r') as f: 
        data = [json.loads(line) for line in f]

    status = check_and_create_os_index()
    
    if status == True:
        for doc_id, ln in enumerate(data):
            passages = len_safe_get_embedding(ln['text'])
            print(f'Processed document: {doc_id}, number of passages {len(passages)}')        
            for passage_id, passage in enumerate(passages):
                embedding = get_embedding(passage)
                document = { 
                    'doc_id': doc_id, 
                    'passage_id': passage_id,
                    'passage': passage, 
                    'embedding': embedding
                }
                response = requests.post(f'{ES_DOMAIN_ENDPOINT_NAME}/legal-passages/_doc/{doc_id}_{passage_id}', auth=HTTPBasicAuth(ES_USER_NAME, ES_PASSWORD), json=document)
                if response.status_code == 200:
                    print(f'Posted to OpenSearch Index - { doc_id } for passage id - { passage_id }')
                else:
                    print(f'Error posting document { doc_id }  passage id - { passage_id } to Open Search')
                    print(f'response.status_code: {response.status_code}')
    os.remove(filename)
    os.remove(f'{filename}.xz')