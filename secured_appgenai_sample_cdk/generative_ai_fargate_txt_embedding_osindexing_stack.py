from distutils.sysconfig import project_base
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_batch_alpha as batch,
    aws_lambda as _lambda,
    App, 
    CfnOutput,
    Stack,
    Size,
    aws_ecr_assets,
)
from aws_solutions_constructs.aws_fargate_opensearch import FargateToOpenSearch, FargateToOpenSearchProps
import os
from constructs import Construct

class Docs2EmbeddingsOSIndexingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc_stack: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        private_vpc_subnets=ec2.SubnetSelection(
            subnets=[vpc_stack.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets[0]],
        )

        self.batch_queue = batch.JobQueue(self, "GenAIServiceTxt2EmbeddingsOSIndexingQueue")
        fargate_spot_env = batch.FargateComputeEnvironment(self, "GenAIServiceTxt2EmbeddingsOSIndexingEnv",
                                                           vpc_subnets=private_vpc_subnets,
                                                           vpc=vpc_stack)
        
        fargate_spot_env.connections.allow_internally(ec2.Port.tcp(443))

        self.batch_queue.add_compute_environment(fargate_spot_env, 0)

        sagemaker_endpoint_policy_stmt = iam.PolicyStatement(
                actions=["sagemaker:InvokeEndpoint"],
                resources=["*"]
            )

        task_execution_role = iam.Role(self, "TaskExecutionRole",
                                  assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                                  managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"),
                                                    iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                                                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                                                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
                                                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                                                    iam.ManagedPolicy.from_aws_managed_policy_name("AmazonOpenSearchServiceFullAccess")])
        
        task_execution_role.add_to_policy(sagemaker_endpoint_policy_stmt)
    
        job_source_path = os.path.join(os.getcwd(), "txt_to_embeddings_job")
        logging = ecs.AwsLogDriver(stream_prefix="GenAIServiceTxt2EmbeddingsOSIndexing")

        docker_image_asset = aws_ecr_assets.DockerImageAsset(self, "GenAIServiceTxt2EmbeddingsOSIndexingDockerImage",
                                                                directory=job_source_path,
                                                                platform=aws_ecr_assets.Platform.LINUX_AMD64)
        docker_container_image = ecs.ContainerImage.from_docker_image_asset(docker_image_asset)
        
        fargate_job_image = batch.EcsFargateContainerDefinition(self, "GenAIServiceTxt2EmbeddingsOSIndexingContainerDef",
                                                                image=docker_container_image,
                                                                memory=Size.mebibytes(512),
                                                                cpu=0.25,
                                                                execution_role=task_execution_role,
                                                                assign_public_ip=False,
                                                                logging=logging,
                                                                job_role=task_execution_role,
                                                                )
        
        batch_job_definition = batch.EcsJobDefinition(self, "GenAIServiceTxt2EmbeddingsOSIndexingJobDef",
                                                      container=fargate_job_image)
        
        
        lamda_batch_role = iam.Role(self, "GenAIServiceTxt2EmbeddingsOSIndexingLambdaRole", 
                                    assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                    managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AWSBatchFullAccess")])

        _lambda.Function(self, "GenAIServiceTxt2EmbeddingsOSIndexingLambda", function_name="GenAIServiceTxt2EmbeddingsOSIndexingLambda",
                         runtime=_lambda.Runtime.PYTHON_3_9,
                         handler="trigger-opensearch-indexing-job.handler",
                         code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda/lambda-opensearch-index-job")),
                         environment={
                             "BATCH_JOB_QUEUE": self.batch_queue.job_queue_name,
                             "BATCH_JOB_DEF": batch_job_definition.job_definition_name
                         },
                         role=lamda_batch_role)