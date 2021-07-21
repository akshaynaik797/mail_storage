import signal
from time import sleep

from mail_storage import gmail_api
from settings import hospital_data, time_out

hosp = "noble"
deferred = ""
data = hospital_data[hosp]
sleep_secs = 2

class TimeOutException(Exception):
    pass


def alarm_handler(signum, frame):
    print("ALARM signal received")
    raise TimeOutException()

while 1:
    try:
        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(time_out)
        gmail_api(data, hosp, deferred)
        sleep(sleep_secs)
        signal.alarm(0)
    except KeyboardInterrupt:
        break
    except:
        print('timeout')