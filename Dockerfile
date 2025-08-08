# Use the official AWS Lambda Python 3.11 base image.
# This image includes the Lambda Runtime Interface Client (RIC).
FROM public.ecr.aws/lambda/python:3.11

# Copy the requirements file into the container at /var/task/
COPY app/requirements.txt ./

# Install the Python dependencies from the requirements file.
# No need for --target, as we are installing directly into the image's environment.
RUN pip install -r requirements.txt

# Copy the rest of your application code from the 'app' directory to /var/task/
COPY app/ ./

# Set the CMD to your handler.
# The format is "<filename>.<handler_function_name>".
# This tells the Lambda RIC what function to run when the container starts.
CMD [ "lambda_function.lambda_handler" ]


