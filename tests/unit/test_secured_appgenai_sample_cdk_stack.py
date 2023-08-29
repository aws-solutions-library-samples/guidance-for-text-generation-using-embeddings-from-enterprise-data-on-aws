import aws_cdk as core
import aws_cdk.assertions as assertions

from secured_appgenai_sample_cdk.secured_appgenai_sample_cdk_stack import SageMakerLLMTxt2TxtEndpointStack

# example tests. To run these tests, uncomment this file along with the example
# resource in secured_appgenai_sample_cdk/secured_appgenai_sample_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SageMakerLLMTxt2TxtEndpointStack(app, "secured-appgenai-sample-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
