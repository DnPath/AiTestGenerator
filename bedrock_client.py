import json
import os
import boto3

def call_bedrock_model(prompt: str, model_id: str, max_tokens: int, temperature: float) -> str:
    region = os.getenv("AWS_REGION", "us-east-1")
    client = boto3.client('bedrock-runtime', region_name=region)

    if model_id.startswith("anthropic.claude-3"):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        })
    elif model_id.startswith("anthropic."):
        anthropic_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
        body = json.dumps({
            "prompt": anthropic_prompt,
            "max_tokens_to_sample": max_tokens,
            "temperature": temperature,
            "stop_sequences": ["\n\nHuman:"]
        })
    elif model_id.startswith("amazon.titan"):
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "stopSequences": []
            }
        })
    else:
        raise ValueError(f"Unsupported model schema for {model_id}")

    response = client.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json"
    )

    resp_body = json.loads(response["body"].read())
    if model_id.startswith("anthropic.claude-3"):
        return resp_body["content"][0]["text"]
    elif model_id.startswith("anthropic."):
        return resp_body.get("completion", "")
    elif model_id.startswith("amazon.titan"):
        return resp_body.get("results", [{}])[0].get("outputText", "")
    return str(resp_body)


# def call_bedrock_model(prompt: str, model_id: str, max_tokens: int = 1500, temperature: float = 0.0) -> str:
#     client = boto3.client('bedrock-runtime')

#     if model_id.startswith("anthropic.claude-3"):
#         body = json.dumps({
#             "anthropic_version": "bedrock-2023-05-31",
#             "messages": [
#                 {"role": "user", "content": [{"type": "text", "text": prompt}]}
#             ],
#             "max_tokens": max_tokens,
#             "temperature": temperature
#         })
#     elif model_id.startswith("anthropic."):
#         anthropic_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
#         body = json.dumps({
#             "prompt": anthropic_prompt,
#             "max_tokens_to_sample": max_tokens,
#             "temperature": temperature,
#             "stop_sequences": ["\n\nHuman:"]
#         })
#     elif model_id.startswith("amazon.titan"):
#         body = json.dumps({
#             "inputText": prompt,
#             "textGenerationConfig": {
#                 "maxTokenCount": max_tokens,
#                 "temperature": temperature,
#                 "stopSequences": []
#             }
#         })
#     else:
#         raise ValueError(f"Unsupported model schema for {model_id}")

#     response = client.invoke_model(
#         modelId=model_id,
#         body=body,
#         contentType="application/json",
#         accept="application/json"
#     )

#     resp_body = json.loads(response["body"].read())
#     if model_id.startswith("anthropic.claude-3"):
#         return resp_body["content"][0]["text"]
#     elif model_id.startswith("anthropic."):
#         return resp_body.get("completion", "")
#     elif model_id.startswith("amazon.titan"):
#         return resp_body.get("results", [{}])[0].get("outputText", "")
#     return str(resp_body)