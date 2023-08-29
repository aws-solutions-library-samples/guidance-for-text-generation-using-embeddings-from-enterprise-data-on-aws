from distutils.sysconfig import project_base
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    SecretValue,
    Stack,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_opensearchservice as os,
    aws_ec2 as ec2,
    aws_secretsmanager as secrets
)
from constructs import Construct

class OpenSearchEmbeddingDomainStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc_stack: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        private_vpc_subnets=ec2.SubnetSelection(
            subnets=[vpc_stack.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS).subnets[0]],
        )

        domain_acc_policy = iam.PolicyStatement(actions=["es:*"], principals=[iam.AnyPrincipal()])
        domain = os.Domain(self, "Domain",
            version=os.EngineVersion.OPENSEARCH_2_3,
            ebs=os.EbsOptions(
                volume_size=100,
                volume_type=ec2.EbsDeviceVolumeType.GP3
            ),
            access_policies=[domain_acc_policy],
            enforce_https=True,
            capacity=os.CapacityConfig(data_node_instance_type="t3.medium.search", data_nodes=1, master_node_instance_type="t3.small.search", master_nodes=2),
            fine_grained_access_control=os.AdvancedSecurityOptions(
                master_user_name="genai-opensearch-master-user"
            ),            
            node_to_node_encryption=True,
            encryption_at_rest=os.EncryptionAtRestOptions(
                enabled=True
            ),
            vpc=vpc_stack,
            vpc_subnets=[private_vpc_subnets],
            removal_policy=RemovalPolicy.DESTROY,         
        )

        domain.connections.allow_internally(ec2.Port.tcp(443), "Allow HTTPS Access")
        domain.connections.allow_from_any_ipv4(ec2.Port.tcp(443), "Allow HTTPS Access from anywhere")

        sec_gp_ids = []
        for sec_gp in domain.connections.security_groups:
            sec_gp_ids.append(sec_gp.security_group_id)

        ssm.StringParameter(self, 'opensearch_domain_endpoint', parameter_name='opensearch_domain_endpoint', string_value=domain.domain_endpoint)
        ssm.StringParameter(self, 'opensearch_master_user_name', parameter_name='opensearch_master_user_name', string_value='genai-opensearch-master-user')
        ssm.StringParameter(self, 'opensearch_domain_sec_group', parameter_name='opensearch_domain_sec_group', string_value=','.join(sec_gp_ids))

        os_secret_pwd = secrets.Secret(self, "Secret", secret_name="opensearch_master_password",
            secret_string_value=domain.master_user_password
        )