import random
from datetime import datetime, timedelta


def generate_random_datetime(start_hour_int: int = 5, end_hour_int: int = 23):

    random_datetime = (datetime.now() - timedelta(days=random.randint(0, 730)) - timedelta(microseconds=random.randint(0, 1000*60*60*24)))

    random_hour = random.randint(start_hour_int, end_hour_int)

    random_datetime = random_datetime.replace(hour=random_hour)

    return random_datetime


def convert_datetime_to_str(cr_datetime: datetime, cr_format: str = "%d-%m-%Y %H:%M:%S.%f"):

    return cr_datetime.strftime(format=cr_format)[:-3]

