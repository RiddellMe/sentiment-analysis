import logging
import time

logger = logging.getLogger(__name__)


class Timer:
    _start_time = None
    _end_time = None

    def start(self):
        if not self._start_time:
            self._start_time = time.perf_counter()
            logger.debug("Timer started.")
        else:
            raise TimerError(f"Timer is already running.")

    def get_elapsed_time(self):
        if self._start_time:
            if self._end_time:
                elapsed_time = self._end_time - self._start_time
                logger.debug(f"Timer completed in: {elapsed_time}.")
            else:
                elapsed_time = time.perf_counter() - self._start_time
                logger.debug(f"Current elapsed time: {elapsed_time}.")
        else:
            raise TimerError(f"Timer is not running.")

        return elapsed_time

    def end(self):
        if not self._end_time:
            self._end_time = time.perf_counter()
            logger.debug("Timer complete.")
        else:
            raise TimerError(f"Timer was previously stopped.")
        return self.get_elapsed_time()


class TimerError(Exception):
    pass
