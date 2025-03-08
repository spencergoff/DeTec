import aws_cdk as core
import aws_cdk.assertions as assertions

from search_infra.search_infra_stack import SearchInfraStack

# example tests. To run these tests, uncomment this file along with the example
# resource in search_infra/search_infra_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SearchInfraStack(app, "search-infra")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
