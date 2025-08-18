"""Simple examples showing how to mock S3 and RDS (via boto3 and moto).
Run as a script or import into tests. Requires `boto3` and `moto` (best-effort compatibility across moto versions).
"""
import boto3

from moto import mock_aws

@mock_aws
def test_s3_operations():
    s3_client = boto3.client("s3", region_name="us-east-1")
    bucket_name = "my-test-bucket"
    s3_client.create_bucket(Bucket=bucket_name)

    # Now you can perform S3 operations like putting objects, getting objects, etc.
    s3_client.put_object(Bucket=bucket_name, Key="test_file.txt", Body="Hello, Moto!")
    response = s3_client.get_object(Bucket=bucket_name, Key="test_file.txt")
    assert response["Body"].read().decode("utf-8") == "Hello, Moto!"

@mock_aws
def test_rds_operations():
    rds_client = boto3.client("rds", region_name="us-east-1")
    db_instance_identifier = "my-test-db"

    # You can simulate creating DB instances, modifying them, etc.
    rds_client.create_db_instance(
        DBInstanceIdentifier=db_instance_identifier,
        DBInstanceClass="db.t2.micro",
        Engine="mysql",
        MasterUsername="admin",
        MasterUserPassword="password",
        AllocatedStorage=20
    )

    response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
    assert response["DBInstances"][0]["DBInstanceStatus"] == "available"
    # Moto simulates this
# moto has changed layout across releases; try multiple import paths and provide
# safe fallbacks so the module can be imported even if a particular decorator is
# not available in the installed moto version.
try:
    # preferred simple import (works on many moto versions)
    from moto import mock_s3, mock_rds2
except Exception:
    mock_s3 = None
    mock_rds2 = None
    try:
        from moto.s3 import mock_s3
    except Exception:
        mock_s3 = None
    
    # fall back to mock_rds if available; assign to mock_rds2 name for compatibility
    try:
        from moto.rds import mock_rds as mock_rds2
    except Exception:
        mock_rds2 = None


if mock_s3 is None:
    def example_s3():
        print("mock_s3 decorator not available in installed moto version; skipping S3 mock example")
else:
    @mock_s3
    def example_s3():
        s3 = boto3.client('s3', region_name='us-east-1')
        bucket_name = 'my-test-bucket'
        s3.create_bucket(Bucket=bucket_name)
        s3.put_object(Bucket=bucket_name, Key='hello.txt', Body=b'hello world')
        resp = s3.get_object(Bucket=bucket_name, Key='hello.txt')
        body = resp['Body'].read()
        print('S3 object body:', body)


if mock_rds2 is None:
    def example_rds():
        print('mock_rds2 decorator not available in installed moto version; skipping RDS mock example')
else:
    @mock_rds2
    def example_rds():
        # moto's RDS support is limited; this demonstrates creating an instance placeholder
        rds = boto3.client('rds', region_name='us-east-1')
        try:
            resp = rds.create_db_instance(DBInstanceIdentifier='test-db', DBInstanceClass='db.t2.micro', Engine='postgres')
            print('Created RDS instance:', resp)
        except Exception as e:
            print('RDS create error (expected in moto limited support):', e)


if __name__ == '__main__':
    example_s3()
    example_rds()
