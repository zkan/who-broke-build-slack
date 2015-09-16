import json
from mock import call, patch
import socket
import unittest

from who_broke_build import (
    get_responsible_user,
    jenkins_wait_for_event,
    remove_html_tags,
    wait_for_event,
    yell_at
)
import settings


class WhoBrokeBuildTest(unittest.TestCase):
    def setUp(self):
        settings.AF_INET = 2
        settings.SOCK_DGRAM = 2
        settings.JENKINS_USERNAME = 'zkan'
        settings.JENKINS_PASSWORD = 'who_broke_the_build!?'
        settings.JENKINS_NOTIFICATION_UDP_PORT = 22222
        settings.JENKINS_USERS_TO_SLACK_USERS = {
            'Sandy S': 'sandy',
            'zkan': 'zkan'
        }
        settings.SLACK_TOKEN = 'slack-token'

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

    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_response_with_no_status_should_keep_running_with_no_error(
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
                'url': 'job/00-Prontoworld-Checkin%20-%2010.3.0.20/1992/',
                'scm': {},
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
        content = '<span>'
        content += 'Started by user <a href="/user/sandy/">Sandy S</a>'
        content += '</span>'
        mock.return_value.content = content

        full_url = 'https://ci.prontomarketing.com/job/'
        full_url += '04-Prontoworld-Deploy-Dev%20-%2010.3.0.20/734/'

        user = get_responsible_user(full_url)

        expected = 'Sandy S'
        self.assertEqual(user, expected)

        mock.assert_called_once_with(
            full_url,
            auth=(
                settings.JENKINS_USERNAME,
                settings.JENKINS_PASSWORD
            )
        )

    @patch('who_broke_build.remove_html_tags')
    @patch('who_broke_build.requests.get')
    def test_get_responsible_user_should_remove_all_html_tags(
        self,
        mock,
        mock_remove_html_tags
    ):
        content = '<span>'
        content += 'Started by user <a href="/user/sandy/">Sandy S</a>'
        content += '</span>'
        mock.return_value.content = content

        full_url = 'https://ci.prontomarketing.com/job/'
        full_url += '04-Prontoworld-Deploy-Dev%20-%2010.3.0.20/734/'

        get_responsible_user(full_url)

        mock_remove_html_tags.assert_called_once_with(content)

    @patch('who_broke_build.yell_at')
    @patch('who_broke_build.get_responsible_user')
    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_when_build_fails_it_should_get_responsible_user(
        self,
        mock_socket,
        mock_wait_for_event,
        mock_get_responsible_user,
        mock_yell_at
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
        mock_get_responsible_user.return_value = 'zkan'

        jenkins_wait_for_event()

        self.assertEqual(mock_wait_for_event.call_count, 2)
        mock_socket.socket.return_value.recvfrom.assert_called_once_with(
            8 * 1024
        )
        mock_get_responsible_user.assert_called_once_with(full_url)

    @patch('who_broke_build.get_responsible_user')
    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_when_build_passes_it_should_not_get_any_responsible_user(
        self,
        mock_socket,
        mock_wait_for_event,
        mock_get_responsible_user
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

        mock_socket.socket.return_value.recvfrom.return_value = data
        mock_wait_for_event.side_effect = [True, False]

        jenkins_wait_for_event()

        self.assertEqual(mock_wait_for_event.call_count, 2)
        mock_socket.socket.return_value.recvfrom.assert_called_once_with(
            8 * 1024
        )
        self.assertEqual(mock_get_responsible_user.call_count, 0)

    @patch('who_broke_build.subprocess.call')
    def test_yell_at_build_breaker_should_execute_slacker_cli(self, mock):
        yell_at('zkan')

        command = 'echo "Hey <!channel>! <@zkan> just broke the build! | '
        command += 'slacker -c main '
        command += '-t %s -i :bear:' % settings.SLACK_TOKEN
        mock.assert_called_once_with(command, shell=True)

    @patch('who_broke_build.yell_at')
    @patch('who_broke_build.get_responsible_user')
    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_when_build_fails_it_should_yell_at_responsible_user(
        self,
        mock_socket,
        mock_wait_for_event,
        mock_get_responsible_user,
        mock_yell_at
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
        mock_get_responsible_user.return_value = 'zkan'

        jenkins_wait_for_event()

        mock_yell_at.assert_called_once_with('zkan')

    @patch('who_broke_build.yell_at')
    @patch('who_broke_build.get_responsible_user')
    @patch('who_broke_build.wait_for_event')
    @patch('who_broke_build.socket')
    def test_when_build_fails_yell_at_should_take_slack_username(
        self,
        mock_socket,
        mock_wait_for_event,
        mock_get_responsible_user,
        mock_yell_at
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
        mock_get_responsible_user.return_value = 'Sandy S'

        jenkins_wait_for_event()

        mock_yell_at.assert_called_once_with('sandy')

    def test_remove_all_html_tags(self):
        html = '<span>'
        html += 'Started by user <a href="/user/zkan">Kan Ouivirach</a>'
        html += '</span>'

        result = remove_html_tags(html)

        expected = 'Started by user Kan Ouivirach'
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
