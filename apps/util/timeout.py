import signal


class TimeoutError(Exception):
    pass


class Timeout():
    def __init__(self, minutes=1, error_message='Timeout'):
        self.minutes = minutes
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.minutes * 60)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)
