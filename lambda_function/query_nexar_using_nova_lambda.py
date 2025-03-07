import os
import boto3
import json
import requests
from datetime import datetime

def lambda_handler(event, context):

    print(f'event: {event}')

    ### Handing Preflight Request (for CORS)
    if event["requestContext"]["http"]["method"] == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "https://d3r9mhcj5ucoi7.cloudfront.net/", # Remember to replace this if I change the domain
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""
        }
    else:
        user_query = json.loads(event['body'])['user_query']
        print(f'user_query: {user_query}')

        # Create a Bedrock Runtime client in the AWS Region of your choice.
        client = boto3.client("bedrock-runtime", region_name="us-west-2")

        system = [{"text": "You are an expert in electronic circuit design. If appropriate, you may use the provided tool to respond \
            to the user's prompt, but if you do, ONLY USE PROPERTIES THAT THE TOOL HAS. If you use the tool, you do NOT need to fill \
            in a value for every property; only provide values for the property or properties that you can infer from the user's \
            prompt. The property values should not contain comparion operators such as less than (<) or greator than (>), because \
            the tool does not support them. Do not drop units such as the mA in 3mA or the u in 5uA (m stands for milli, u stands for micro, and A stand for amps). \
            If the user asks for a property value comparison of 'less than' or 'greater than', \
            treat it as 'equal to' instead. You can only use the tool one time to answer the user's request, so do not expect \
            to get follow-up requests. Property values should ALWAYS be in string format, not integer. Do not ask the user a follow-up question."}]

        # Define one or more messages using the "user" and "assistant" roles.
        message_list = [{"role": "user", "content": [{"text": user_query}]}]

        # Configure the inference parameters.
        inf_params = {"maxTokens": 500, "topP": 1, "temperature": 1}

        nexar_api_properties = {}
        with open("nexar_attributes.txt", "r") as file:
            next(file) # Skip the header line
            for line in file:
                shortname, name = line.strip().split("\t")
                nexar_api_properties[shortname] = {
                    "type": "string",
                    "description": name
                }

        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "search_electronic_parts_database",
                        "description": "Searches a database of electronic parts (for example, integrated circuits) and returns the \
                            manufacturer part number (MPN), URL, datasheet, and other specifications of the part that matches the given query.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": nexar_api_properties
                            }
                        }
                    }
                }
            ]
        }

        request_body = {
            "schemaVersion": "messages-v1",
            "messages": message_list,
            "toolConfig": tool_config,
            "system": system,
            "inferenceConfig": inf_params
        }

        print(f'request_body: {request_body}')

        try: 
            # Invoke the model with the response stream
            response = client.invoke_model(
                modelId='us.amazon.nova-pro-v1:0', body=json.dumps(request_body) # Other modelId options: us.amazon.nova-micro-v1:0
            )
        except Exception as e:
            if 'Try your request again.' in str(e):
                print('Trying request one more time...')
                response = client.invoke_model(
                    modelId='us.amazon.nova-pro-v1:', body=json.dumps(request_body) # Other modelId options: us.amazon.nova-micro-v1:0
                )
            else:
                raise e

        request_id = response.get("ResponseMetadata").get("RequestId")
        print(f"Request ID: {request_id}")
        print("Awaiting first token...")

        chunk_count = 0
        time_to_first_token = None

        response_body = response['body'].read().decode("utf-8")  # Decode the entire response body

        print(f'response_body: {response_body}')

        # Convert string to JSON
        response_json = json.loads(response_body)

        validated_properties_and_values = {}

        # Check if tool usage is required
        if "tool_use" in response_json["stopReason"]:
            for content_item in response_json["output"]["message"]["content"]:
                if 'toolUse' in content_item:
                    if content_item['toolUse']['name'] == 'search_electronic_parts_database':
                        properties_and_values_output_by_model = content_item['toolUse']['input']
                        print(f'properties_and_values_output_by_model: {properties_and_values_output_by_model}')
                        for prop, value in properties_and_values_output_by_model.items():
                            if prop not in nexar_api_properties:
                                print(f'Model recommended an unknown property; ignoring: {prop}')
                            else:
                                validated_properties_and_values[prop] = str(value).strip().replace('<', '').replace('>', '').replace('=', '').split(' ')[-1]
                        print(f'\n\nFinal properties and values that will be passed to Nexar: {validated_properties_and_values}\n\n')
                    else:
                        print(f"Unknown tool requested: {tool['name']}")
        else:
            raise('No tool usage detected')

        spec_attributes = []

        for prop, value in validated_properties_and_values.items():
            _filter = f'''    {{
                key: "{prop}",
                value: ["{value}"]
            }}'''
            spec_attributes.append(_filter)

        formatted_spec_attributes = "[\n" + ",\n".join(spec_attributes) + "\n]"
        #print(f'formatted_spec_attributes: {formatted_spec_attributes}')

        CLIENT_ID = '97c7cdb7-d24c-493a-9c36-fd4fd4467b08' # Evaluation App
        NEXAR_CLIENT_SECRET = os.getenv('NEXAR_CLIENT_SECRET')
        NEXAR_API_TOKEN = os.getenv('NEXAR_API_TOKEN')

        NEXAR_GRAPHQL_URL = 'https://api.nexar.com/graphql'

        # If you want to query other categories besides ICs, you'll need to stop hard-coding the category_id. See nexar_categories.txt for all categories.
        query = f'''
        query {{
            supSearch(sort: "quiescentcurrent", sortDir: desc, limit: 1,
                filters: {{
                    category_id: "4215"
                    specAttributes: {formatted_spec_attributes}
                }})
                {{
                    hits
                    results{{
                        part {{
                            mpn
                            manufacturer {{
                                name
                            }}
                            specs {{
                                attribute{{
                                    name
                                    id
                                }}
                            }}
                            octopartUrl
                        }}
                    }}
                }}
            }}
        '''        

        print(f'query: {query}')

        headers = {
            'Authorization': f'Bearer {NEXAR_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        full_query_results = requests.post(NEXAR_GRAPHQL_URL, json={'query': query}, headers=headers).json()

        print(f'\n\nfull_query_results: {full_query_results}\n\n')

        response_to_user = f'<p>Here\'s the info I found for your query: <br>'
        response_to_user += f'Manufacturer: {full_query_results["data"]["supSearch"]["results"][0]["part"]["manufacturer"]["name"]}<br>'
        response_to_user += f'MPN: {full_query_results["data"]["supSearch"]["results"][0]["part"]["mpn"]}<br>'
       
        if 'octopartUrl' in full_query_results['data']['supSearch']['results'][0]['part']:
            octopart_url = full_query_results['data']['supSearch']['results'][0]['part']['octopartUrl']
            response_to_user += f'Octopart URL: <a href="{octopart_url}" target="_blank" rel="noopener noreferrer">{octopart_url}</a></p>'
        elif 'datasheets' in full_query_results['data']['supSearch']['results'][0]['part']:
            datasheet_url = full_query_results['data']['supSearch']['results'][0]['part']['datasheets']['url']
            response_to_user += f'Datasheet URL: <a href="{datasheet_url}">{datasheet_url}</a></p>'
        else:
            response_to_user += 'I couldn\'t find a datasheet or URL for this part.</p>'
        
        print(f'response_to_user: {response_to_user}')

        return {
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Methods": "OPTIONS, GET, POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            'statusCode': 200,
            'body': json.dumps(response_to_user)
        }


        