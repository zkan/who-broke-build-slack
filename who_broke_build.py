import json
import re
import requests
import socket
import subprocess

import settings


def yell_at(name):
    command = 'echo "Hey <!channel>! <@%s> just broke the build! ' % name
    command += 'Let\'s fix it!" | '
    command += 'slacker -c main -t %s -i :bear:' % settings.SLACK_TOKEN

    subprocess.call(command, shell=True)


def get_responsible_user(full_url):
    members = settings.JENKINS_USERS_TO_SLACK_USERS
    response = requests.get(
        full_url,
        auth=(
            settings.JENKINS_USERNAME,
            settings.JENKINS_PASSWORD
        )
    )

    for each, _ in members.iteritems():
        if ('Started by GitHub push by ' + each in response.content or \
                'Started by user ' + each in response.content):
            return each


def wait_for_event():
    return True


def jenkins_wait_for_event():
    sock = socket.socket(settings.AF_INET, settings.SOCK_DGRAM)
    sock.bind(('', settings.JENKINS_NOTIFICATION_UDP_PORT))

    while wait_for_event():
        data, _ = sock.recvfrom(8 * 1024)

        try:
            notification_data = json.loads(data)
            status = notification_data['build']['status'].upper()
            phase = notification_data['build']['phase'].upper()

            if phase == 'COMPLETED' and status.startswith('FAIL'):
                target = get_responsible_user(
                    notification_data['build']['full_url']
                )
                yell_at(settings.JENKINS_USERS_TO_SLACK_USERS[target])
        except:
            pass


if __name__ == '__main__':
    jenkins_wait_for_event()
