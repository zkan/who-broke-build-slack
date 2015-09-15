import socket

from settings import (
    AF_INET,
    SOCK_DGRAM,
    JENKINS_NOTIFICATION_UDP_PORT
)


def jenkins_wait_for_event():
    sock = socket.socket(AF_INET, SOCK_DGRAM)
    sock.bind(('', JENKINS_NOTIFICATION_UDP_PORT))
