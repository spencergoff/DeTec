from aws_cdk import (
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_wafv2 as wafv2,
    aws_s3_deployment as s3deploy,
    CfnOutput,
    Duration,
    Stack
)
from constructs import Construct

class SearchInfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get environment context
        environment = self.node.try_get_context("environment")

        # Define resource names based on environment
        bucket_name = f"detec-search-{environment}"
        function_name = f"get_component_results_{environment}"

        website_bucket = s3.Bucket(
            self, "DetecSearchBucket",
            bucket_name=bucket_name,
            website_index_document="index.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            )
        )

        s3deploy.BucketDeployment(
            self, "DeployWebsite",
            sources=[s3deploy.Source.asset("../../")],
            destination_bucket=website_bucket,
            retain_on_delete=False,
            include=["index.html"]
        )

        waf = wafv2.CfnWebACL(
            self, "DetecWAF",
            default_action={"allow": {}},
            scope="CLOUDFRONT",
            visibility_config={
                "cloudWatchMetricsEnabled": False,
                "metricName": f"DetecWAFMetrics-{environment}",
                "sampledRequestsEnabled": True
            },
            rules=[
                {
                    "name": "AWSManagedRulesAmazonIpReputationList",
                    "priority": 0,
                    "statement": {
                        "managedRuleGroupStatement": {
                            "vendorName": "AWS",
                            "name": "AWSManagedRulesAmazonIpReputationList"
                        }
                    },
                    "overrideAction": {"none": {}},
                    "visibilityConfig": {
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": False,
                        "metricName": f"AWSManagedRulesAmazonIPReputationListMetric-{environment}"
                    }
                },
                {
                    "name": "AWSManagedRulesCommonRuleSet",
                    "priority": 1,
                    "statement": {
                        "managedRuleGroupStatement": {
                            "vendorName": "AWS",
                            "name": "AWSManagedRulesCommonRuleSet"
                        }
                    },
                    "overrideAction": {"none": {}},
                    "visibilityConfig": {
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": False,
                        "metricName": f"AWSManagedRulesCommonRuleSetMetric-{environment}"
                    }
                },
                {
                    "name": "AWSManagedRulesKnownBadInputsRuleSet",
                    "priority": 2,
                    "statement": {
                        "managedRuleGroupStatement": {
                            "vendorName": "AWS",
                            "name": "AWSManagedRulesKnownBadInputsRuleSet"
                        }
                    },
                    "overrideAction": {"none": {}},
                    "visibilityConfig": {
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": False,
                        "metricName": f"AWSManagedRulesKnownBadInputsRuleSetMetric-{environment}"
                    }
                },
                {
                    "name": "RateLimit",
                    "priority": 3,
                    "statement": {
                        "rateBasedStatement": {
                            "limit": 20,
                            "aggregateKeyType": "IP"
                        }
                    },
                    "action": {"block": {}},
                    "visibilityConfig": {
                        "sampledRequestsEnabled": True,
                        "cloudWatchMetricsEnabled": True,
                        "metricName": f"RateLimitMetric-{environment}"
                    }
                }
            ]
        )

        distribution = cloudfront.Distribution(
            self, "DetecSearchDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(website_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            web_acl_id=waf.attr_arn
        )

        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=[
                    "arn:aws:bedrock:*:621544995223:inference-profile/us.amazon.nova*",
                    "arn:aws:bedrock:*::foundation-model/amazon.nova*"
                ]
            )
        )

        function = lambda_.Function(
            self, "GetComponentResults",
            function_name=function_name,
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="query_nexar_using_nova_lambda.lambda_handler",
            code=lambda_.Code.from_asset("../lambda_function"),
            timeout=Duration.seconds(30),
            role=lambda_role,
            environment={
                "NEXAR_API_TOKEN": "",  # Set this via AWS Console
                "NEXAR_CLIENT_SECRET": ""  # Set this via AWS Console
            }
        )

        fn_url = function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_origins=[f"https://{distribution.distribution_domain_name}"],
                allowed_methods=[lambda_.HttpMethod.ALL],
                allowed_headers=["content-type"],
                exposed_headers=[
                    "access-control-allow-origin",
                    "access-control-allow-methods",
                    "access-control-allow-headers",
                    "content-type"
                ]
            )
        )

        # Output the CloudFront URL and Function URL
        CfnOutput(self, "DistributionUrl",
                 value=f"https://{distribution.distribution_domain_name}")
        CfnOutput(self, "FunctionUrl",
                 value=fn_url.url)