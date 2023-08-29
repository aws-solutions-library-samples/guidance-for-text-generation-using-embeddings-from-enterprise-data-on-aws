from distutils.sysconfig import project_base
from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ec2 as ec2,
)
from constructs import Construct
from construct.sagemaker_endpoint_construct import SageMakerEndpointConstruct

class SageMakerLLMTxt2TxtEndpointStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, model_info, vpc_stack: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = iam.Role(self, "SecureApp-Txt2Txt-SageMaker-Role",
                        assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"))
        
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"))

        txt2txt_endpoint_construct = SageMakerEndpointConstruct(self, "SageMaker-Txt2Txt-Endpoint",
                                                                project_prefix="SecureAppGenAISample",
                                                                role_arn=role.role_arn,
                                                                model_name="HuggingfaceText2TextFlanT5XL",
                                                                model_bucket_name = model_info['model_bucket_name'],
                                                                model_bucket_key = model_info['model_bucket_key'],
                                                                model_docker_image = model_info['model_docker_image'],
                                                                variant_name = "AllTraffic",
                                                                variant_weight = 1,
                                                                instance_count = 1,
                                                                instance_type = model_info['instance_type'],

                                                                environment = {
                                                                    "MODEL_CACHE_ROOT": "/opt/ml/model",
                                                                    "SAGEMAKER_ENV": "1",
                                                                    "SAGEMAKER_MODEL_SERVER_TIMEOUT": "3600",
                                                                    "SAGEMAKER_MODEL_SERVER_WORKERS": "1",
                                                                    "SAGEMAKER_PROGRAM": "inference.py",
                                                                    "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code/",
                                                                    "TS_DEFAULT_WORKERS_PER_MODEL": "1"
                                                                },

                                                                deploy_enable = True,
                                                                subnetIds=vpc_stack.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnet_ids,
                                                                security_group_ids=[vpc_stack.vpc_default_security_group]
        )

        ssm.StringParameter(self, 'txt2txt_sm_endpoint', parameter_name='txt2txt_sm_endpoint', string_value=txt2txt_endpoint_construct.endpoint_name)