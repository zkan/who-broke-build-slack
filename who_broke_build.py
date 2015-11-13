import json
import re
import requests
import socket
import subprocess

from firebase import firebase

import settings


def put_breaker_to_firebase(name):
    firebase_app = firebase.FirebaseApplication(
        settings.FIREBASE_STORAGE_URL,
        None
    )
    result = firebase_app.get(settings.FIREBASE_OBJECT_URL, name)
    if result is None:
        result = firebase_app.put(settings.FIREBASE_OBJECT_URL, name, 1)
    else:
        result = firebase_app.put(
            settings.FIREBASE_OBJECT_URL,
            name,
            result + 1
        )

    return result


# http://love-python.blogspot.com/2008/07/strip-html-tags-using-python.html
def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def yell_at(name):
    command = 'echo "Hey <!channel>! <@%s> just broke the build!" | ' % name
    command += 'slacker -c %s -t %s -i :bear:' % (
        settings.SLACK_CHANNEL,
        settings.SLACK_TOKEN
    )

    subprocess.call(command, shell=True)

    if settings.FIREBASE_STORAGE_URL:
        put_breaker_to_firebase(name)


def get_responsible_user(full_url):
    members = settings.JENKINS_USERS_TO_SLACK_USERS
    response = requests.get(
        full_url,
        auth=(
            settings.JENKINS_USERNAME,
            settings.JENKINS_PASSWORD
        )
    )

    content = remove_html_tags(response.content)
    for each, _ in members.iteritems():
        if ('Started by GitHub push by ' + each in content or \
                'Started by user ' + each in content):
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
