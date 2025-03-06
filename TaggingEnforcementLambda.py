import boto3
import traceback
import json

# AWS Clients
dynamodb = boto3.resource('dynamodb')
ec2 = boto3.client('ec2')

DYNAMODB_TABLE_NAME = "Pre-definedTags"

def lambda_handler(event, context):
    instance_id = None
    mandatory_tag_valid = False
    try:
        # Log the full event for debugging
        print(f"[DEBUG] Full event: {json.dumps(event, indent=2)}")

        # Parse instance ID
        detail = event.get('detail', {})
        instance_id = detail.get('responseElements', {}).get('instancesSet', {}).get('items', [{}])[0].get('instanceId')
        print(f"[INFO] Processing instance: {instance_id}")

        # Extract tags from tagSpecificationSet or tagSet
        tag_specifications = detail.get('requestParameters', {}).get('tagSpecificationSet', [])
        tag_set = detail.get('responseElements', {}).get('instancesSet', {}).get('items', [{}])[0].get('tagSet', {}).get('items', [])
        
        print(f"[DEBUG] Raw tagSpecificationSet: {json.dumps(tag_specifications, indent=2)}")
        print(f"[DEBUG] Raw tagSet: {json.dumps(tag_set, indent=2)}")
        
        resource_tags = {}
        
        # Extract from tagSpecificationSet
        if isinstance(tag_specifications, list):
            for tag_spec in tag_specifications:
                if isinstance(tag_spec, dict) and 'tags' in tag_spec and isinstance(tag_spec['tags'], list):
                    for tag in tag_spec['tags']:
                        if isinstance(tag, dict) and 'key' in tag and 'value' in tag:
                            resource_tags[tag['key'].strip()] = tag['value'].strip()
        
        # Extract from tagSet (Ensure it's always checked)
        if isinstance(tag_set, list):
            for tag in tag_set:
                if isinstance(tag, dict) and 'key' in tag and 'value' in tag:
                    resource_tags[tag['key'].strip()] = tag['value'].strip()
        
        print(f"[DEBUG] Final Extracted Tags: {json.dumps(resource_tags, indent=2)}")
        
        if not resource_tags:
            print(f"[ERROR] No tags found for Instance ID: {instance_id}. Full event: {json.dumps(event, indent=2)}")
            terminate_instance(instance_id, "No tags found in the event.")
            return {"statusCode": 400, "body": "No tags found. Instance terminated."}
        
        # Validate tags against DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)

        for tag_key, tag_value in resource_tags.items():
            print(f"[DEBUG] Checking tag: {tag_key} = {tag_value}")
            
            # Query DynamoDB for the tag key
            response = table.scan(
                FilterExpression="#key = :key_value",
                ExpressionAttributeNames={"#key": "Key"},
                ExpressionAttributeValues={":key_value": tag_key}
            )
            print(f"[DEBUG] DynamoDB response for '{tag_key}': {response}")

            if response['Items']:
                allowed_values = [item.get('Value', '').strip() for item in response['Items']]
                if tag_value in allowed_values:
                    mandatory_tag_valid = True
                    print(f"[INFO] Valid mandatory tag: {tag_key} = {tag_value}")
                    break
            else:
                print(f"[WARNING] Tag key '{tag_key}' not found in DynamoDB.")

        # Check compliance
        if not mandatory_tag_valid:
            print(f"[ERROR] No valid mandatory tags found for Instance ID: {instance_id}. Marking as non-compliant.")
            terminate_instance(instance_id, "No valid mandatory tags found.")
            return {"statusCode": 400, "body": "Non-compliant instance terminated."}

        print(f"[INFO] Instance {instance_id} is compliant with at least one mandatory tag. No termination required.")
        return {"statusCode": 200, "body": "Instance is compliant."}

    except Exception as e:
        error_message = str(e).lower()
        print(f"[ERROR] Exception occurred: {e}")
        print(traceback.format_exc())
        
        # Ignore "error 0 unknown error" if the instance has compliant tags
        if "error 0" in error_message and mandatory_tag_valid:
            print(f"[INFO] Ignoring 'error 0 unknown error' as the instance {instance_id} is compliant.")
            return {"statusCode": 200, "body": "Instance is compliant. Ignored error 0."}

        if instance_id:
            terminate_instance(instance_id, f"Unexpected error: {e}")
        return {"statusCode": 500, "body": f"Error: {e}"}

def terminate_instance(instance_id, reason):
    try:
        terminate_response = ec2.terminate_instances(InstanceIds=[instance_id])
        print(f"[INFO] Terminated instance {instance_id} due to: {reason}. Termination response: {terminate_response}")
    except Exception as e:
        print(f"[ERROR] Failed to terminate instance: {e}")
        print(traceback.format_exc())
