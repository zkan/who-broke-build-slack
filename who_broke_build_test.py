import json
from mock import call, patch
import socket
import unittest

from who_broke_build import (
    get_responsible_user,
    jenkins_wait_for_event,
    wait_for_event
)
import settings


class WhoBrokeBuildTest(unittest.TestCase):
    def setUp(self):
        settings.AF_INET = 2
        settings.SOCK_DGRAM = 2
        settings.JENKINS_USERNAME = 'zkan'
        settings.JENKINS_PASSWORD = 'who_broke_the_build!?'
        settings.JENKINS_NOTIFICATION_UDP_PORT = 22222
        settings.TEAM_MEMBERS = [
            'zkan',
            'sandy',
        ]

    def test_wait_for_event_should_just_return_true(self):
        self.assertTrue(wait_for_event())

    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_jenkins_wait_for_event_should_listen_to_udp_port_22222(
        self,
        mock_socket,
        mock_wait_for_event
    ):
        mock_wait_for_event.side_effect = [False]

        jenkins_wait_for_event()

        mock_socket.socket.assert_called_once_with(
            settings.AF_INET,
            settings.SOCK_DGRAM
        )
        mock_socket.socket.return_value.bind.assert_called_once_with(
            ('', settings.JENKINS_NOTIFICATION_UDP_PORT)
        )

    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_jenkins_wait_for_event_should_always_try_to_receive_data(
        self,
        mock_socket,
        mock_wait_for_event
    ):
        full_url = 'https://ci.prontomarketing.com/job/04-Prontoworld-Deploy-'
        full_url += 'Dev%20-%2010.3.0.20/731/'
        response = {
            'name': '00-Prontoworld-Checkin - 10.3.0.20',
            'url': 'job/00-Prontoworld-Checkin%20-%2010.3.0.20/',
            'build': {
                'full_url': full_url,
                'number': 1992,
                'phase': 'COMPLETED',
                'status': 'SUCCESS',
                'url': 'job/00-Prontoworld-Checkin%20-%2010.3.0.20/1992/',
                'scm': {
                    'url': 'git@github.com:prontodev/pronto-dashboard.git',
                    'branch': 'origin/develop',
                    'commit': '067169c64bfe4cfe203537ccf05c9e71e7378921'
                },
                'log': '',
                'artifacts': {}
            }
        }
        data = (
            json.dumps(response),
            ('10.3.0.20', 44450)
        )

        mock_socket.socket.return_value.recvfrom.side_effect = [
            data,
            data
        ]
        mock_wait_for_event.side_effect = [True, True, False]

        jenkins_wait_for_event()

        self.assertEqual(mock_wait_for_event.call_count, 3)
        expected_calls = [
            call(8 * 1024),
            call(8 * 1024)
        ]
        mock_socket.socket.return_value.recvfrom.assert_has_calls(
            expected_calls
        )

    @patch('who_broke_build.requests.get')
    def test_get_responsible_user_should_return_user_who_pushed(self, mock):
        mock.return_value.content = 'Started by GitHub push by zkan'

        full_url = 'https://ci.prontomarketing.com/job/'
        full_url += '04-Prontoworld-Deploy-Dev%20-%2010.3.0.20/734/'

        user = get_responsible_user(full_url)

        expected = 'zkan'
        self.assertEqual(user, expected)

        mock.assert_called_once_with(
            full_url,
            auth=(
                settings.JENKINS_USERNAME,
                settings.JENKINS_PASSWORD
            )
        )

    @patch('who_broke_build.requests.get')
    def test_get_responsible_user_should_return_user_who_ran_manually(
        self,
        mock
    ):
        mock.return_value.content = 'Started by user sandy'

        full_url = 'https://ci.prontomarketing.com/job/'
        full_url += '04-Prontoworld-Deploy-Dev%20-%2010.3.0.20/734/'

        user = get_responsible_user(full_url)

        expected = 'sandy'
        self.assertEqual(user, expected)

        mock.assert_called_once_with(
            full_url,
            auth=(
                settings.JENKINS_USERNAME,
                settings.JENKINS_PASSWORD
            )
        )

    @patch('who_broke_build.get_responsible_user')
    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_when_build_fails_it_should_get_responsible_user(
        self,
        mock_socket,
        mock_wait_for_event,
        mock_get_responsible_user
    ):
        full_url = 'https://ci.prontomarketing.com/job/03-Prontoworld-'
        full_url += 'AcceptanceTests-Group/193/'
        response = {
            'name': '03-Prontoworld-AcceptanceTests-Group',
            'url': 'job/03-Prontoworld-AcceptanceTests-Group/',
            'build': {
                'full_url': full_url,
                'number': 193,
                'phase': 'COMPLETED',
                'status': 'FAILURE',
                'url': 'job/03-Prontoworld-AcceptanceTests-Group/193/',
                'scm': {},
                'log': '',
                'artifacts':{}
            }
        }
        data = (
            json.dumps(response),
            ('10.3.0.20', 48580)
        )

        mock_socket.socket.return_value.recvfrom.return_value = data
        mock_wait_for_event.side_effect = [True, False]

        jenkins_wait_for_event()

        self.assertEqual(mock_wait_for_event.call_count, 2)
        mock_socket.socket.return_value.recvfrom.assert_called_once_with(
            8 * 1024
        )
        mock_get_responsible_user.assert_called_once_with(full_url)


if __name__ == '__main__':
    unittest.main()
