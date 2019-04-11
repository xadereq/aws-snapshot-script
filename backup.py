import datetime
import socket

import boto3
import requests

"""
Script to make daily/monthly or whatever backup of volume using AWS API
"""

VOLUME_ID = ""
"""ID of volume"""
REGION_NAME = ""
"""AWS region name containing above volume (eu-central-1, eu-west-1 etc)"""
RETENTION_DAYS = 3
"""How many days should the snapshots last before deletion (integer)"""
INTERVAL_TYPE = "daily"
"""Interval type: daily/weekly/monthly etc"""
DRY_RUN = False
"""Dry run switch for testing purposes"""

EMOJI = ""
HOOK_URL = ""
"""
Notifier variables:

EMOJI: used to set rocket.chat bot avatar
HOOK_URL: URL to API of notifications
"""


class Host:
    def __init__(self):
        self.today = datetime.date.today().strftime('%Y-%m-%d')
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.name = socket.gethostname()

    def get_hostname(self):
        """Return hostname of machine running script"""
        return self.name

    def get_today(self):
        """Return today's date"""
        return self.today

    def get_retention_time(self):
        """Return date of retention"""
        return self.now - datetime.timedelta(days=int(RETENTION_DAYS)) + datetime.timedelta(seconds=int(10))


class Snapshot:
    def __init__(self):
        self.resource = boto3.client('ec2', region_name=REGION_NAME)
        self.created_id = None
        self.deleted_ids = []

    @staticmethod
    def _get_snapshot_description():
        """Return new snapshot description"""
        return '{}-{}-backup-{}'.format(Host().get_hostname(), INTERVAL_TYPE, Host().get_today())

    def _list_snapshots(self):
        """Return all snapshots tagged as CreatedBy with value AutomatedBackupDaily"""
        return self.resource.describe_snapshots(
            Filters=[
                {
                    'Name': 'tag:CreatedBy',
                    'Values': [
                        'AutomatedBackup{}'.format(INTERVAL_TYPE.capitalize())
                    ]
                }
            ]
        )

    def create(self):
        """Creates new snapshot of volume"""
        snap = self.resource.create_snapshot(
            Description=self._get_snapshot_description(),
            VolumeId=VOLUME_ID,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {
                            'Key': 'CreatedBy',
                            'Value': 'AutomatedBackup{}'.format(INTERVAL_TYPE.capitalize())
                        },
                    ]
                },
            ],
            DryRun=DRY_RUN
        )
        self.created_id = snap['SnapshotId']

    def delete_old(self):
        """Delete old snapshots of volume if retention time exceeded, send notify after all"""
        retention_time = Host().get_retention_time()
        snapshots = self._list_snapshots()

        for snap in snapshots['Snapshots']:
            snapshot_id = snap['SnapshotId']
            start_time = snap['StartTime']
            if start_time <= retention_time:
                self.resource.delete_snapshot(
                    SnapshotId=snapshot_id,
                    DryRun=DRY_RUN
                )
                self.deleted_ids.append(snapshot_id)

        notify = Notifier()
        notify.send(self.created_id, self.deleted_ids)


class Notifier:
    def __init__(self):
        self.url = HOOK_URL
        self.emoji = EMOJI

    def send(self, created_id, deleted_ids):
        """
        Send notification with json data.
        :param created_id
        :type created_id str
        :param deleted_ids
        :type deleted_ids list
        """
        if deleted_ids:
            deleted_ids = "\n".join(deleted_ids)
        else:
            deleted_ids = 'none'

        data = {
            'username': '{} {} Backup'.format(INTERVAL_TYPE.capitalize(), Host().get_hostname().capitalize()),
            'icon_emoji': '{}'.format(self.emoji),
            'text': '[{}] Created snapshot of {} (snapshot id: {})\n'
                    'Deleted old snapshots with IDs:\n{}'.format(INTERVAL_TYPE.upper(), VOLUME_ID, created_id,
                                                                 deleted_ids)
        }

        requests.post(self.url, json=data)


if __name__ == '__main__':
    backup = Snapshot()
    backup.create()
    backup.delete_old()
