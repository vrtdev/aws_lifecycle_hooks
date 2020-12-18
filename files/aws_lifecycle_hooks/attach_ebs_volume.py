#!/usr/bin/env python
"""File managed by puppet in module aws_lifecycle_hooks."""
import glob
import time
import typing
import boto3
import botocore.exceptions

import tools
from exceptions import VolumeInUseError


def volume_id_attached(volume_id: str) -> bool:
    """Check if a volume_id is attached."""
    nvme_devices_list = glob.glob('/dev/nvme[0-9]')
    for nvme_device in nvme_devices_list:
        if tools.nvme_device_volume_id(nvme_device) == volume_id:
            return True
    return False


def attach_volume(
        volume_id: str,
        region_name: typing.Optional[str] = None,
        instance_id: typing.Optional[str] = None,
        device_name: str = "/dev/sdf",
) -> None:
    """
    Try to attach volume `volume_id` to instance `instance_id` in region.

    `region_name` as device `device_name`.
    :param volume_id: The volume-id to attach
    :param region_name: The region to perform the call in. Default: the region
                        of this instance
    :param instance_id: The instance to attach the volume to. Default: this
                        instance
    :param device_name: Device name to attach under. Default: /dev/sdf
    :raises: VolumeInUseError: if the volume is already attached somewhere (possibly
                          the requested instance)
    """
    if instance_id is None:
        instance_id = tools.get_instance_id()

    if region_name is None:
        region_name = tools.get_instance_region()

    ec2_client = boto3.client('ec2', region_name=region_name)
    """:type: pyboto3.ec2"""

    try:
        ec2_client.attach_volume(
            VolumeId=volume_id,
            InstanceId=instance_id,
            Device=device_name,
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "VolumeInUse":
            raise VolumeInUseError(e) from e
        else:
            raise


def get_volume_information_from_user_data() -> list:
    """
    Get the volume id and device name from the user data.

    For this we assume that:
        - the user_data is parsable (yaml or json)
        - it contains the following config

    ```yaml
    ---
    attach_volumes:
      - volume_id: volume_id
        device_name: device_name
    ```

    :return: A List of VolumeAttachment objects with volume id and device name
    """
    volumes = []
    user_data = tools.get_parsed_user_data()
    if user_data:
        attach_volumes = user_data.get('attach_volumes', [])
        for i, volume in enumerate(attach_volumes):
            try:
                v = tools.VolumeAttachment(volume_id=volume['volume_id'], device_name=volume['device_name'])
            except KeyError as e:
                raise RuntimeError("While parsing 'attach_volumes' index {i}".format(i=i)) from e
            volumes.append(v)

    return volumes


def try_attach(
        volume_id: str,
        device_name: str,
        instance_id: str,
        region: str,
        retry_limit: int,
        retry_interval: int,
) -> None:
    print("""\
        volume_id {volume_id}
        device_name {device_name}
        instance_id {instance_id}
        region {region}
        retry_limit {retry_limit}
        retry_interval {retry_interval}
    """.format(
        volume_id=volume_id,
        device_name=device_name,
        instance_id=instance_id,
        region=region,
        retry_limit=retry_limit,
        retry_interval=retry_interval,
    ))

    if volume_id_attached(volume_id):
        print(f"Requested volume '{volume_id}' is already attached.")
        return

    attached = False
    retry = 0
    while not attached:
        try:
            retry += 1
            attach_volume(
                volume_id=volume_id,
                device_name=device_name,
                region_name=region,
                instance_id=instance_id,
            )
            attached = True
        except VolumeInUseError:
            # 0 is used to signal unlimited retries
            if retry_limit != 0 and retry >= retry_limit:
                raise

            time.sleep(retry_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--volume-id", type=str, default=None,
                        help="Volume ID to attach")
    parser.add_argument("--device-name", type=str, default="/dev/sdf",
                        help="Device name to present the attached volume as")

    parser.add_argument("--region", type=str, default=None,
                        help="Region to perform API calls in. When not "
                             "specified, use the region of the instance this is "
                             "running on")
    parser.add_argument("--instance-id", type=str, default=None,
                        help="Instance ID to attach volume to. When not "
                             "specified, use the instance this is running on")

    parser.add_argument("--retry-limit",
                        type=int, metavar="TRIES", default=1,
                        help="Stop after trying this many times. A setting of 0 "
                             "is interpreted as no limit.")
    parser.add_argument("--retry-interval",
                        type=int, metavar="SECONDS", default=5,
                        help="Interval in seconds after which to retry")

    args = parser.parse_args()

    args = vars(args)

    if not args['volume_id']:
        volume_data = get_volume_information_from_user_data()
        for volume in volume_data:
            args['volume_id'] = volume.volume_id
            args['device_name'] = volume.device_name
            try_attach(**args)
    else:
        try_attach(**args)
