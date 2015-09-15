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


if __name__ == '__main__':
    unittest.main()
