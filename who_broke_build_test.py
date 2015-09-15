import json
from mock import call, patch
import socket
import unittest

from who_broke_build import (
    wait_for_event,
    jenkins_wait_for_event
)
from settings import (
    AF_INET,
    SOCK_DGRAM,
    JENKINS_NOTIFICATION_UDP_PORT
)


class WhoBrokeBuildTest(unittest.TestCase):
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
            AF_INET,
            SOCK_DGRAM
        )
        mock_socket.socket.return_value.bind.assert_called_once_with(
            ('', JENKINS_NOTIFICATION_UDP_PORT)
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


if __name__ == '__main__':
    unittest.main()
