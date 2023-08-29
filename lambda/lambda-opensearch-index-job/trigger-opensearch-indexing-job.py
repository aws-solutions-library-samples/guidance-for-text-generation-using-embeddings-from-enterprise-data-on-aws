import os
import sys
import json
import boto3
import logging
from datetime import datetime

aws_batch = boto3.client('batch')

def handler(event, context):
    batch_job_queue = os.environ.get("BATCH_JOB_QUEUE")
    batch_job_definition = os.environ.get("BATCH_JOB_DEF")

    print(f'batch_job_queue: { batch_job_queue }')
    print(f'batch_job_definition: { batch_job_definition }')
    date_time = datetime.now().strftime("%Y%m%d%H%M%S")

    batch_job_name = "aws-blog-batch-job-%s" % (date_time)
    
    response = aws_batch.submit_job(jobName=batch_job_name, jobQueue=batch_job_queue, jobDefinition=batch_job_definition)
    print(f'response: { response }')
    return "Job Triggered!!!"