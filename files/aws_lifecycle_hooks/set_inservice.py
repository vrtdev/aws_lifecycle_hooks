#!/usr/bin/env python
'''
File managed by puppet in module profiles::service::ldap
'''
import enum
import json
import urllib.request
import boto3


class LifecycleActionResult(enum.Enum):
    CONTINUE = "CONTINUE"
    ABANDON = "ABANDON"


def mark_as_healthy(
        asg_client,
        asg_name: str,
        instance_id: str,
        result: LifecycleActionResult = LifecycleActionResult.CONTINUE,
) -> None:
    # Signal ASG that we're done
    # Figure out which hook to signal
    # BUG: this assumes only 1 LAUNCHING-hook is registered
    #      possible solution: look to the CloudFormation Stack that created us
    #      and read out the name of the hook there
    asg_hooks = asg_client.describe_lifecycle_hooks(
        AutoScalingGroupName=asg_name)

    # Filter for EC2_INSTANCE_LAUNCHING hook
    asg_hooks = [h for h in asg_hooks[u'LifecycleHooks']
                 if h[u'LifecycleTransition'] == "autoscaling:EC2_INSTANCE_LAUNCHING"]

    if len(asg_hooks) != 1:
        raise RuntimeError("Could not find Lifecycle hook to notify")

    asg_hooks = asg_hooks[0][u'LifecycleHookName']

    asg_client.complete_lifecycle_action(
        AutoScalingGroupName=asg_name,
        LifecycleHookName=asg_hooks,
        InstanceId=instance_id,
        LifecycleActionResult=result.value,
    )


def instance_data():
    instance_identity = urllib.request.urlopen(
            "http://169.254.169.254/2016-09-02/dynamic/instance-identity/document"
        ).read()
    instance_identity = json.loads(instance_identity.decode('utf-8'))

    instance_id = instance_identity['instanceId']
    region = instance_identity['region']
    print("I am {iid}, running in {r}".format(
        iid=instance_id,
        r=region,
    ))

    asg_c = boto3.client('autoscaling', region_name=region)
    """:type : pyboto3.autoscaling"""

    asg_info = asg_c.describe_auto_scaling_instances(InstanceIds=[instance_id])
    asg = asg_info[u'AutoScalingInstances'][0][u'AutoScalingGroupName']
    print("I am part of Auto Scaling Group {asg}".format(asg=asg))

    return asg_c, asg, instance_id


def state_dir_ok(state_dir):
    import os

    for r, d, f in os.walk(state_dir):
        for statefile in f:
            statefile_h = open(os.path.join(r + '/' + statefile), 'r')
            state = statefile_h.read()
            if state:
                return False

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--state-dir", type=str, default=None,
                        help="Directory to check for state files. "
                             "If set, this script will check the state files in this dir "
                             "and not send the lifecycle 'CONTINUE' status if any file is non-empty. "
                             "When not specified, no state will be checked")

    args = parser.parse_args()

    if args.state_dir:
        state_ok = state_dir_ok(args.state_dir)
    else:
        state_ok = True

    if state_ok:
        asg_c, asg, instance_id = instance_data()
        mark_as_healthy(asg_c, asg, instance_id)
