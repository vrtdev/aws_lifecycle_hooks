#!/usr/bin/env python
'''
File managed by puppet in module aws_lifecycle_hooks
'''
import json
import functools
import urllib.request
import boto3


@functools.lru_cache(maxsize=1)
def get_instance_identity():
    instance_identity = urllib.request.urlopen(
        "http://169.254.169.254/2016-09-02/dynamic/instance-identity/document"
    ).read()
    instance_identity = json.loads(instance_identity.decode('utf-8'))
    return instance_identity


def get_instance_id():
    get_instance_identity()['instanceId']


def get_region():
    get_instance_identity()['region']


@functools.lru_cache(maxsize=1)
def get_user_data():
    user_data = urllib.request.urlopen(
        "http://169.254.169.254/2016-09-02/user-data"
    ).read()
    user_data = json.loads(user_data.decode('utf-8'))
    return user_data


@functools.lru_cache(maxsize=1)
def get_asg_data(region, instance_id):
    asg_c = boto3.client('autoscaling', region_name=region)
    """:type : pyboto3.autoscaling"""

    asg_info = asg_c.describe_auto_scaling_instances(InstanceIds=[instance_id])
    asg = asg_info[u'AutoScalingInstances'][0][u'AutoScalingGroupName']
    print("I am part of Auto Scaling Group {asg}".format(asg=asg))

    return asg_c, asg
