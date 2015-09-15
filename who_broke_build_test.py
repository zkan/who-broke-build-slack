from mock import patch
import socket
import unittest

from who_broke_build import jenkins_wait_for_event
from settings import (
    AF_INET,
    SOCK_DGRAM,
    JENKINS_NOTIFICATION_UDP_PORT
)


class WhoBrokeBuildTest(unittest.TestCase):
    @patch('who_broke_build.socket')
    def test_jenkins_wait_for_event_should_listen_to_udp_port_22222(
        self,
        mock
    ):
        jenkins_wait_for_event()

        mock.socket.assert_called_once_with(
            AF_INET,
            SOCK_DGRAM
        )
        mock.socket.return_value.bind.assert_called_once_with(
            ('', JENKINS_NOTIFICATION_UDP_PORT)
        )


if __name__ == '__main__':
    unittest.main()
