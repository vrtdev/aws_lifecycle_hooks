#!/usr/bin/env python
"""File managed by puppet in module aws_lifecycle_hooks."""
import json
import functools
import urllib.request
import urllib.error
import typing
import yaml
import attr
import re

from exceptions import ParsingError

metadata_version = '2020-10-27'


@attr.s
class VolumeAttachment:
    """Utility class."""

    volume_id = attr.ib()
    device_name = attr.ib()


@functools.lru_cache(maxsize=1)
def get_metadata_token() -> str:
    """
    Instance Metadata Service Version 2 (IMDSv2).

    https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html
    Token fetching does not seem to work with versioned requests. Gives HTTP 403
    """
    headers = {'X-aws-ec2-metadata-token-ttl-seconds': 60}
    req = urllib.request.Request(
        url='http://169.254.169.254/latest/api/token',
        headers=headers,
        method='PUT',
    )
    with urllib.request.urlopen(req) as resp:
        response_data = resp.read().decode("utf-8")
    return response_data


@functools.lru_cache()
def get_metadata(key: str) -> typing.Union[None, str]:
    """Fetch meta-data with latest version by key."""
    headers = {'X-aws-ec2-metadata-token': get_metadata_token()}
    req = urllib.request.Request(
        url="http://169.254.169.254/{version}/{key}".format(
            version=metadata_version,
            key=key,
        ),
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            response_data = resp.read().decode("utf-8")
        return response_data
    except urllib.error.HTTPError as e:
        if e.status == 404:
            print("Key '{key}' not found in meta-data service.".format(key=key))
        else:
            raise


@functools.lru_cache(maxsize=1)
def get_instance_identity() -> typing.Mapping[str, typing.Any]:
    """Query instance identity."""
    instance_identity = get_metadata('dynamic/instance-identity/document')
    instance_identity = json.loads(instance_identity)
    return instance_identity


def get_instance_id() -> str:
    """Query instance id."""
    instance_id = get_instance_identity()['instanceId']
    print("My instance_id is {instance_id}".format(instance_id=instance_id))
    return instance_id


def get_instance_region() -> str:
    """Query instance region."""
    instance_region = get_instance_identity()['region']
    print("My region is {instance_region}".format(instance_region=instance_region))
    return instance_region


@functools.lru_cache(maxsize=1)
def get_user_data() -> str:
    """Get user data."""
    user_data = get_metadata('user-data')
    print("My raw user-data is {user_data}".format(user_data=user_data))
    return user_data


@functools.lru_cache(maxsize=1)
def get_parsed_user_data() -> typing.Mapping[str, typing.Any]:
    """Get parsed user data."""
    user_data = get_user_data()
    if user_data:
        try:
            # every JSON file is also valid YAML, so we only need to parse YAML.
            user_data = yaml.safe_load(user_data)
            print("My parsed user-data is {user_data}".format(user_data=user_data))
        except yaml.YAMLError as e:
            raise ParsingError("Failed to parse User Data") from e

        return user_data


@functools.lru_cache()
def get_asg_name(
        instance_id: str,
        asg_client,
) -> typing.Optional[str]:
    """Use describe asg to get asg group name."""
    import botocore.exceptions
    asg_name = None
    try:
        asg_info = asg_client.describe_auto_scaling_instances(InstanceIds=[instance_id])
        asg_name = asg_info[u'AutoScalingInstances'][0][u'AutoScalingGroupName']
        print("I am part of Auto Scaling Group {asg_name}".format(asg_name=asg_name))
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "AccessDenied":
            print('This instance/user has no permission to query autoscaling.')
        else:
            raise

    return asg_name


@functools.lru_cache(maxsize=1)
def get_block_device_mapping() -> list:
    """Get meta-data Block device mapping."""
    block_device_mapping = get_metadata('meta-data/block-device-mapping')
    print("My raw block-device-mapping is\n{block_device_mapping}".format(block_device_mapping=block_device_mapping))
    block_device_mapping_list = block_device_mapping.splitlines()
    return block_device_mapping_list


def get_block_device_mapping_filtered(regex: re.Pattern) -> list:
    """Apply filter to get_block_device_mapping() result."""
    block_device_mapping_list = get_block_device_mapping()

    block_device_mapping_list_filtered = [s for s in block_device_mapping_list if regex.match(s)]
    return block_device_mapping_list_filtered


def get_block_device_mountpoint(regex: re.Pattern) -> list:
    devices = get_block_device_mapping_filtered(regex)
    mountpoints = []
    for device in devices:
        mountpoint = get_metadata("meta-data/block-device-mapping/{device}".format(device=device))
        mountpoints.append(mountpoint)

    return mountpoints


def test_tools():
    """Test all these methods."""
    get_metadata_token()

    get_metadata('user-data')

    get_instance_identity()

    get_user_data()

    get_parsed_user_data()

    instance_id = get_instance_id()
    region = get_instance_region()
    import boto3
    asg_client = boto3.client('autoscaling', region_name=region)
    """:type : pyboto3.autoscaling"""
    get_asg_name(instance_id, asg_client)

    print("Test get_block_device_mapping()")
    print(get_block_device_mapping())

    print("Test get_block_device_mapping_filtered('')")
    r1 = re.compile('')
    print(get_block_device_mapping_filtered(r1))

    print("Test get_block_device_mapping_filtered('root')")
    r2 = re.compile('root')
    print(get_block_device_mapping_filtered(r2))

    print("Test get_block_device_mapping_filtered('ebs*')")
    r3 = re.compile('ebs*')
    print(get_block_device_mapping_filtered(r3))

    print("Test get_block_device_mapping_filtered('ebs[0-9]+')")
    r4 = re.compile('ebs[0-9]+')
    print(get_block_device_mapping_filtered(r4))

    print("Test get_block_device_mountpoint('')")
    r5 = re.compile('')
    print(get_block_device_mountpoint(r5))

    print("Test get_block_device_mountpoint('root')")
    r6 = re.compile('root')
    print(get_block_device_mountpoint(r6))

    print("Test get_block_device_mountpoint('ebs[0-9]+')")
    r7 = re.compile('ebs[0-9]+')
    print(get_block_device_mountpoint(r7))

    get_metadata('user-data-x')

# Python 3.7.3 (default, Jul 25 2020, 13:03:44)
# [GCC 8.3.0] on linux
# Type "help", "copyright", "credits" or "license" for more information.
# >>> import t
# >>> t.test_tools()
# My raw user-data is
#         #cloud-config
#         attach_volumes:
#         - volume_id: vol-0f4e30092431fa402
#           device_name: /dev/xvdm
#
# My parsed user-data is {'attach_volumes': [{'volume_id': 'vol-0f4e30092431fa402', 'device_name': '/dev/xvdm'}]}
# My instance_id is i-07ba9e6f1d7d9eb0f
# My region is eu-west-1
# This instance/user has no permission to query autoscaling.
# Test get_block_device_mapping()
# My raw block-device-mapping is ami
# ebs2
# ebs3
# root
# ['ami', 'ebs2', 'ebs3', 'root']
# Test get_block_device_mapping_filtered('')
# ['ami', 'ebs2', 'ebs3', 'root']
# Test get_block_device_mapping_filtered('root')
# ['root']
# Test get_block_device_mapping_filtered('ebs*')
# ['ebs2', 'ebs3']
# Test get_block_device_mapping_filtered('ebs[0-9]+')
# ['ebs2', 'ebs3']
# Test get_block_device_mountpoint('')
# ['xvda', 'xvdf', 'xvdm', '/dev/xvda']
# Test get_block_device_mountpoint('root')
# ['/dev/xvda']
# Test get_block_device_mountpoint('ebs[0-9]+')
# ['xvdf', 'xvdm']
# Key 'user-data-x' not found in meta-data service.
