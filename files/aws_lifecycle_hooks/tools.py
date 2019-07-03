#!/usr/bin/env python
'''
File managed by puppet in module aws_lifecycle_hooks
'''
import json
import functools
import urllib.request
import typing


@functools.lru_cache(maxsize=1)
def get_instance_identity() -> typing.Mapping[str, typing.Any]:
    instance_identity = urllib.request.urlopen(
        "http://169.254.169.254/2016-09-02/dynamic/instance-identity/document"
    ).read()
    instance_identity = json.loads(instance_identity.decode('utf-8'))
    return instance_identity


def get_instance_id() -> str:
    return get_instance_identity()['instanceId']


def get_instance_region() -> str:
    return get_instance_identity()['region']


@functools.lru_cache(maxsize=1)
def get_user_data() -> typing.Mapping[str, typing.Any]:
    user_data = urllib.request.urlopen(
        "http://169.254.169.254/2016-09-02/user-data"
    ).read()
    user_data = json.loads(user_data.decode('utf-8'))
    return user_data


@functools.lru_cache()
def get_asg_name(
        instance_id: str,
        asg_client
) -> str:
    asg_info = asg_client.describe_auto_scaling_instances(InstanceIds=[instance_id])
    asg_name = asg_info[u'AutoScalingInstances'][0][u'AutoScalingGroupName']
    print("I am part of Auto Scaling Group {asg_name}".format(asg_name=asg_name))

    return asg_name
