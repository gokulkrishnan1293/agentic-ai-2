docker tag agentic-ai:latest 967255022802.dkr.ecr.us-east-1.amazonaws.com/agentic-ai:latest


docker push 967255022802.dkr.ecr.us-east-1.amazonaws.com/agentic-ai:latest


aws lambda create-function \
  --function-name agentic-ai-lambda \
  --package-type Image \
  --code ImageUri=967255022802.dkr.ecr.us-east-1.amazonaws.com/agentic-ai:latest \
  --role arn:aws:iam::967255022802:role/<your-lambda-execution-role>