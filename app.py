#!/usr/bin/env python3
import os
from pyexpat import model

import aws_cdk as cdk

import boto3

from script.sagemaker_uri import get_sagemaker_uris
from sagemaker.instance_types import retrieve_default, retrieve
from secured_appgenai_sample_cdk.generative_ai_api_for_lambda_smendpoints import GenAIAmplifyAppAPILambdaStack
from secured_appgenai_sample_cdk.generative_ai_fargate_txt_embedding_osindexing_stack import Docs2EmbeddingsOSIndexingStack
from secured_appgenai_sample_cdk.generative_ai_opensearch_stack import OpenSearchEmbeddingDomainStack
from secured_appgenai_sample_cdk.generative_ai_txt2emb_sagemaker_stack import SageMakerLLMTxt2EmbEndpointStack
from secured_appgenai_sample_cdk.generative_ai_txt2img_sagemaker_stack import SageMakerLLMTxt2ImgEndpointStack
from secured_appgenai_sample_cdk.generative_ai_txt2txt_sagemaker_stack import SageMakerLLMTxt2TxtEndpointStack
from secured_appgenai_sample_cdk.generative_ai_vpc_network_stack import GenerativeAiVpcNetworkStack

region_name = boto3.Session().region_name
env={'region': region_name}

TXT2TXT_MODEL_ID = 'huggingface-text2text-flan-t5-xl'
TXT2TXT_MODEL_VERSION = '*'
TXT2TXT_INFERENCE_INSTANCE_TYPE = retrieve_default(
    model_id=TXT2TXT_MODEL_ID, model_version=TXT2TXT_MODEL_VERSION, scope="inference"
)

TXT2TXT_MODEL_TASK_TYPE = 'text2text'
TXT2TXT_MODEL_INFO = get_sagemaker_uris(model_id=TXT2TXT_MODEL_ID,
                                        model_task_type=TXT2TXT_MODEL_TASK_TYPE,
                                        instance_type=TXT2TXT_INFERENCE_INSTANCE_TYPE,
                                        region_name=region_name)

TXT2IMG_MODEL_ID = 'model-txt2img-stabilityai-stable-diffusion-v2-1-base'
TXT2IMG_MODEL_VERSION = '*'
TXT2IMG_INFERENCE_INSTANCE_TYPE_ALL = retrieve(
    model_id=TXT2IMG_MODEL_ID, model_version=TXT2IMG_MODEL_VERSION, scope="inference"
)
TXT2IMG_MODEL_TASK_TYPE = 'text2img'
TXT2IMG_INFERENCE_INSTANCE_TYPE = ""
if 'ml.g5.2xlarge' in TXT2IMG_INFERENCE_INSTANCE_TYPE_ALL:
    TXT2IMG_INFERENCE_INSTANCE_TYPE = 'ml.g5.2xlarge'
else:
    print(f'ml.g5.2xlarge is not supported for {TXT2IMG_MODEL_TASK_TYPE}, going with default')
    TXT2IMG_INFERENCE_INSTANCE_TYPE = retrieve_default(
        model_id=TXT2IMG_MODEL_ID, model_version=TXT2IMG_MODEL_VERSION, scope="inference")
   
TXT2IMG_MODEL_INFO = get_sagemaker_uris(model_id=TXT2IMG_MODEL_ID,
                                    model_task_type=TXT2IMG_MODEL_TASK_TYPE,
                                    instance_type=TXT2IMG_INFERENCE_INSTANCE_TYPE,
                                    region_name=region_name)


TXT2EMB_MODEL_ID = 'huggingface-textembedding-gpt-j-6b-fp16'
TXT2EMB_MODEL_VERSION = '*'
TXT2EMB_INFERENCE_INSTANCE_TYPE_ALL = retrieve(
    model_id=TXT2EMB_MODEL_ID, model_version=TXT2IMG_MODEL_VERSION, scope="inference"
)

TXT2EMB_INFERENCE_INSTANCE_TYPE = retrieve_default(
    model_id=TXT2EMB_MODEL_ID, model_version=TXT2EMB_MODEL_VERSION, scope="inference"
)

TXT2EMB_MODEL_TASK_TYPE = 'text2emb'
TXT2EMB_MODEL_INFO = get_sagemaker_uris(model_id=TXT2EMB_MODEL_ID,
                                        model_task_type=TXT2EMB_MODEL_TASK_TYPE,
                                        instance_type=TXT2EMB_INFERENCE_INSTANCE_TYPE,
                                        region_name=region_name)

app = cdk.App()
description = "Guidance for Text Generation using Embeddings from Enterprise Data on AWS (SO9319)"
sagemaker_vpc_stack = GenerativeAiVpcNetworkStack(app, "SecureGenAIAppVpcStack", description=description, env=env)
sagemaker_txt2txt_stack = SageMakerLLMTxt2TxtEndpointStack(app, "GenerativeAITxt2TxtStack", description=description, env=env, model_info=TXT2TXT_MODEL_INFO, vpc_stack=sagemaker_vpc_stack.vpc)

sagemaker_txt2img_stack = SageMakerLLMTxt2ImgEndpointStack(app, "GenerativeAITxt2ImgStack", description=description, env=env, model_info=TXT2IMG_MODEL_INFO, vpc_stack=sagemaker_vpc_stack.vpc)
sagemaker_txt2emb_stack = SageMakerLLMTxt2EmbEndpointStack(app, "GenerativeAITxt2EmbStack", description=description, env=env, model_info=TXT2EMB_MODEL_INFO, vpc_stack=sagemaker_vpc_stack.vpc)

opensearch_embeddings_stack = OpenSearchEmbeddingDomainStack(app, "OpenSearchEmbeddingDomainStack", description=description, env=env, vpc_stack=sagemaker_vpc_stack.vpc, cross_region_references=True)
docs_2_embeddings_os_indexing_stack = Docs2EmbeddingsOSIndexingStack(app, "Docs2EmbeddingsOSIndexingStack", description=description, env=env, vpc_stack=sagemaker_vpc_stack.vpc, cross_region_references=True)

genai_amplify_app_api_lambda_stack = GenAIAmplifyAppAPILambdaStack(app, "GenAIAmplifyAppAPILambdaStack", description=description, env=env, vpc_stack=sagemaker_vpc_stack.vpc, cross_region_references=True)

sagemaker_txt2img_stack.add_dependency(sagemaker_vpc_stack)
sagemaker_txt2emb_stack.add_dependency(sagemaker_vpc_stack)
sagemaker_txt2txt_stack.add_dependency(sagemaker_vpc_stack)

opensearch_embeddings_stack.add_dependency(sagemaker_vpc_stack)

docs_2_embeddings_os_indexing_stack.add_dependency(opensearch_embeddings_stack)
docs_2_embeddings_os_indexing_stack.add_dependency(sagemaker_txt2emb_stack)
docs_2_embeddings_os_indexing_stack.add_dependency(sagemaker_vpc_stack)

genai_amplify_app_api_lambda_stack.add_dependency(docs_2_embeddings_os_indexing_stack)
genai_amplify_app_api_lambda_stack.add_dependency(sagemaker_vpc_stack)
genai_amplify_app_api_lambda_stack.add_dependency(sagemaker_txt2emb_stack)
genai_amplify_app_api_lambda_stack.add_dependency(sagemaker_txt2img_stack)
genai_amplify_app_api_lambda_stack.add_dependency(sagemaker_txt2txt_stack)

cdk.CfnOutput(genai_amplify_app_api_lambda_stack, id="app-region", value=region_name)

app.synth()
