import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from students.views import send_birthday_mail

def start():
    scheduler=BackgroundScheduler()
    print(datetime.datetime.now())
    # scheduler.add_job(send_birthday_mail,"cron",second='*',replace_existing=True)

    scheduler.add_job(send_birthday_mail,"cron",hour='12',minute='26',replace_existing=True)
    
    # scheduler.add_job(send_birthday_mail,"interval",seconds=20,replace_existing=True)
    scheduler.start()

    