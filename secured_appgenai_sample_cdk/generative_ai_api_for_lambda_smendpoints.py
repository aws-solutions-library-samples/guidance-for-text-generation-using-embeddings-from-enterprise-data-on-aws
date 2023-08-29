import http
from constructs import Construct
from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_amplify_alpha as amplify,
    aws_iam as iam,
    aws_lambda as _lambda, 
    aws_apigatewayv2_alpha as gtwy,
    aws_apigatewayv2_integrations_alpha as gtwy_int,
    aws_cognito as cognito,
    aws_apigatewayv2_authorizers_alpha as gtwy_auth,
    aws_amplify as amplify,
    CfnOutput,
    Stack
)
import os

class GenAIAmplifyAppAPILambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc_stack: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        private_vpc_subnets=ec2.SubnetSelection(
            subnets=[vpc_stack.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets[0]],
        )
        
        user_pool = cognito.UserPool(self, "GenAIAppUserPool", self_sign_up_enabled=False)

        sagemaker_endpoint_policy_stmt = iam.PolicyStatement(
                actions=["sagemaker:InvokeEndpoint"],
                resources=["*"]
            )
        
        lambda_network_vpc_policy_stmt = iam.PolicyStatement(
            actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface", "ec2:AssignPrivateIpAddresses", "ec2:UnassignPrivateIpAddresses"],
            resources=["*"]            
        )

        lambda_opensearch_policy_stmt = iam.PolicyStatement(
            actions=["es:ESHttpGet","es:ESHttpPut", "es:ESHttpHead"],
            resources=["*"]
        )
        genai_lambda_role = iam.Role(self, "genai_lambda_role", 
                                    assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                    managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
                                                      iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"),
                                                      iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                                                      iam.ManagedPolicy.from_aws_managed_policy_name("AmazonOpenSearchServiceFullAccess"),
                                                      iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")])
        genai_lambda_role.add_to_policy(sagemaker_endpoint_policy_stmt)
        genai_lambda_role.add_to_policy(lambda_network_vpc_policy_stmt)
        genai_lambda_role.add_to_policy(lambda_opensearch_policy_stmt)

        gen_ai_llm_rag_func = _lambda.Function(self, "GenAIDemoAppLLMRAGFunc", function_name="GenAIDemoAppLLMRAGFunc",
                         runtime=_lambda.Runtime.PYTHON_3_9,
                         handler="app.handler",
                         code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda/lambda-llmrag_func")),
                         role=genai_lambda_role,
                         timeout= Duration.seconds(30),
                         vpc=vpc_stack,
                         vpc_subnets=private_vpc_subnets)
        
        gen_ai_txt_2_img_func = _lambda.Function(self, "GenAIDemoAppTxt2ImgFunc", function_name="GenAIDemoAppTxt2ImgFunc",
                         runtime=_lambda.Runtime.PYTHON_3_9,
                         handler="app.handler",
                         code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda/lambda-txt2img_sm_inf_func")),
                         role=genai_lambda_role,
                         timeout= Duration.seconds(90),
                         vpc=vpc_stack,
                         vpc_subnets=private_vpc_subnets)

        gen_ai_txt_2_txt_func = _lambda.Function(self, "GenAIDemoAppTxt2TxtFunc", function_name="GenAIDemoAppTxt2TxtFunc",
                         runtime=_lambda.Runtime.PYTHON_3_9,
                         handler="app.handler",
                         code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda/lambda-txt2txt_sm_inf_func")),
                         role=genai_lambda_role,
                         timeout= Duration.seconds(30),
                         vpc=vpc_stack,
                         vpc_subnets=private_vpc_subnets)
        
        gen_ai_proxy_func = _lambda.Function(self, "GenAIDemoAppProxyFunc", function_name="GenAIDemoAppProxyFunc",
                         runtime=_lambda.Runtime.PYTHON_3_9,
                         handler="app.handler",
                         code=_lambda.Code.from_asset(os.path.join(os.getcwd(), "lambda/lambda-proxy_func")),
                         role=genai_lambda_role,
                         vpc=vpc_stack,
                         vpc_subnets=private_vpc_subnets)                                             
        cognito_app_client = cognito.UserPoolClient(self, "GenAIReactAmplifyClntId", user_pool=user_pool, generate_secret=False)
        cognito_iden_pool_prop = cognito.CfnIdentityPool.CognitoIdentityProviderProperty( client_id=cognito_app_client.user_pool_client_id, 
                                                                                         provider_name=user_pool.user_pool_provider_name)
        cognito_iden_pool = cognito.CfnIdentityPool(self, "GenAIReactAmplifyIdentityPool",
                                                    allow_unauthenticated_identities=False,
                                                    cognito_identity_providers=[cognito_iden_pool_prop])
        
        cognito_http_authorizer = gtwy_auth.HttpUserPoolAuthorizer("GenAIApiAuthorizer", user_pool, user_pool_clients=[cognito_app_client])

        http_api_gtwy = gtwy.HttpApi(self, "GenAIAPIGatwy", 
                                     cors_preflight=gtwy.CorsPreflightOptions(
                                        allow_methods=[gtwy.CorsHttpMethod.GET, gtwy.CorsHttpMethod.POST, gtwy.CorsHttpMethod.HEAD, gtwy.CorsHttpMethod.OPTIONS],
                                        allow_origins=["*"],
                                        max_age=Duration.days(10),
                                        allow_headers=['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key',],
                                     ))
        client_metric = http_api_gtwy.metric_count()

        http_gtwy_link = gtwy.VpcLink(self, "genaihttpgtwylink", vpc=vpc_stack, subnets=private_vpc_subnets)

        options_api_gtwy = http_api_gtwy.add_routes(path="/{proxy+}",
                                                    methods=[gtwy.HttpMethod.OPTIONS],
                                                    integration=gtwy_int.HttpLambdaIntegration("gen_ai_proxy_func", gen_ai_proxy_func))
        http_api_gtwy.add_routes(path="/txt2txt/{proxy+}",
                                                    methods=[gtwy.HttpMethod.OPTIONS],
                                                    integration=gtwy_int.HttpLambdaIntegration("gen_ai_proxy_func", gen_ai_proxy_func))
        llmrag_api_gtwy = http_api_gtwy.add_routes(path="/llmrag", 
                                    methods=[gtwy.HttpMethod.POST, gtwy.HttpMethod.GET], 
                                    integration=gtwy_int.HttpLambdaIntegration("gen_ai_llm_rag_func", gen_ai_llm_rag_func),
                                    authorizer=cognito_http_authorizer)
        txt2img_api_gtwy = http_api_gtwy.add_routes(path="/txt2img", 
                                    methods=[gtwy.HttpMethod.POST, gtwy.HttpMethod.GET], 
                                    integration=gtwy_int.HttpLambdaIntegration("gen_ai_txt_2_img_func", gen_ai_txt_2_img_func),
                                    authorizer=cognito_http_authorizer)
        txt2txt_api_gtwy = http_api_gtwy.add_routes(path="/txt2txt", 
                                    methods=[gtwy.HttpMethod.POST, gtwy.HttpMethod.GET], 
                                    integration=gtwy_int.HttpLambdaIntegration("gen_ai_txt_2_txt_func", gen_ai_txt_2_txt_func),
                                    authorizer=cognito_http_authorizer)

        CfnOutput(self, "CognitoUserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "GenAIReactAmplifyClientId", value=cognito_app_client.user_pool_client_id)
        CfnOutput(self, "CognitoIdentityPoolId", value=cognito_iden_pool.ref)
        CfnOutput(self, "llmrag_api_name", value="llmrag")
        CfnOutput(self, "llmrag_api_endpoint", value=http_api_gtwy.api_endpoint)
        CfnOutput(self, "txt2img_api_name", value="txt2img")
        CfnOutput(self, "txt2img_api_endpoint", value=http_api_gtwy.api_endpoint)
        CfnOutput(self, "txt2txt_api_name", value="txt2txt")
        CfnOutput(self, "txt2txt_api_endpoint", value=http_api_gtwy.api_endpoint)