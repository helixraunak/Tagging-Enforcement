# Tagging-Enforcement

1. Project Overview

The AWS Tag Enforcement Project ensures that AWS resources comply with specific tagging
policies. A Lambda function validates EC2 instance tags against a predefined set of allowed values
stored in DynamoDB. If an instance lacks the required tags or contains incorrect values, it is
automatically terminated.

2. Architecture & Components

- **AWS Lambda**: Processes EC2 instance creation events and enforces tagging rules.
- **AWS DynamoDB**: Stores predefined tag keys and allowed values.
- **AWS EventBridge**: Captures instance creation events and triggers Lambda.
- **AWS EC2**: The target resource that must comply with tag requirements.
- **AWS CloudWatch**: Logs Lambda execution details and errors for debugging.

3. Setting Up AWS Lambda Function

1. Open the AWS Lambda Console.
2. Click 'Create Function'.
3. Select 'Author from Scratch'.
4. Enter function name: `TagEnforcementLambda`.
5. Select runtime: Python 3.x.
6. Under 'Permissions', attach a policy with DynamoDB Read and EC2 Terminate permissions.
7. Deploy the Lambda function with the provided code.
8. Configure environment variables if necessary.
4. Creating an EventBridge Rule
1. Open the AWS EventBridge Console.
2. Click 'Rules' and then 'Create Rule'.
3. Enter a name for the rule (e.g., `EC2TagValidation`).
4. Under 'Define pattern', choose 'Event Pattern'.
5. Select 'AWS events' and 'EC2 Instance State-change Notification'.
6. Choose 'Specific detail type': `AWS API Call via CloudTrail`.
7. Under 'Target', select the Lambda function `TagEnforcementLambda`.
8. Click 'Create'.
