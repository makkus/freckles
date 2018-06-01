# -*- coding: utf-8 -*-


class FrecklesException(Exception):
    """Base exception class for nsbl."""

    def __init__(self, message):

        super(FrecklesException, self).__init__(message)

class FrecklesConfigException(FrecklesException):

    def __init__(self, message):

        super(FrecklesConfigException, self).__init__(message)

