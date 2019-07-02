import time
import typing
import functools
import urllib.request
import json

import boto3
import botocore.exceptions


class VolumeInUse(botocore.exceptions.ClientError):
    def __init__(self, client_error: botocore.exceptions.ClientError):
        super().__init__(
            operation_name=client_error.operation_name,
            error_response=client_error.response,
        )


@functools.lru_cache(maxsize=1)
def get_instance_identity():
    instance_identity = urllib.request.urlopen(
        "http://169.254.169.254/2016-09-02/dynamic/instance-identity/document"
    ).read()
    instance_identity = json.loads(instance_identity.decode('utf-8'))
    return instance_identity


def attach_volume(
        volume_id: str,
        region_name: typing.Optional[str] = None,
        instance_id: typing.Optional[str] = None,
        device_name: str = "/dev/sdf",
) -> None:
    """
    Try to attach volume `volume_id` to instance `instance_id` in region
    `region_name` as device `device_name`.
    :param volume_id: The volume-id to attach
    :param region_name: The region to perform the call in. Default: the region
                        of this instance
    :param instance_id: The instance to attach the volume to. Default: this
                        instance
    :param device_name: Device name to attach under. Default: /dev/sdf
    :rtype: None
    :raises: VolumeInUse: if the volume is already attached somewhere (possibly
                          the requested instance)
    """
    if instance_id is None:
        instance_id = get_instance_identity()['instanceId']

    if region_name is None:
        region_name = get_instance_identity()['region']

    ec2_client = boto3.client('ec2', region_name=region_name)
    """:type: pyboto3.ec2"""

    try:
        result = ec2_client.attach_volume(
            VolumeId=volume_id,
            InstanceId=instance_id,
            Device=device_name,
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "VolumeInUse":
            raise VolumeInUse(e)
        else:
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("volume_id", type=str,
                        help="Volume ID to attach")
    parser.add_argument("--region", type=str, default=None,
                        help="Region to perform API calls in. When not "
                             "specified, use the region of the instance this is "
                             "running on")
    parser.add_argument("--instance-id", type=str, default=None,
                        help="Instance ID to attach volume to. When not "
                             "specified, use the instance this is running on")
    parser.add_argument("--device-name", type=str, default="/dev/sdf",
                        help="Device name to present the attached volume as")

    parser.add_argument("--retry-limit",
                        type=int, metavar="TRIES", default=1,
                        help="Stop after trying this many times. A setting of 0 "
                             "is interpreted as no limit.")
    parser.add_argument("--retry-interval",
                        type=int, metavar="SECONDS", default=5,
                        help="Interval in seconds after which to retry")

    args = parser.parse_args()

    attached = False
    retry = 0
    while not attached:
        try:
            retry = retry + 1
            attach_volume(
                volume_id=args.volume_id,
                region_name=args.region,
                instance_id=args.instance_id,
                device_name=args.device_name,
            )
            attached = True
        except VolumeInUse:
            if args.retry_limit != 0 and retry >= args.retry_limit:
                raise

            time.sleep(args.retry_interval)
