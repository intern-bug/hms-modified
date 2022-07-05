import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from students.views import send_birthday_mail

def start():
    scheduler=BackgroundScheduler()
    # scheduler.add_job(send_birthday_mail,"cron",second='*',replace_existing=True)

    scheduler.add_job(send_birthday_mail,"cron",hour='0',minute='0',replace_existing=True)
    
    # scheduler.add_job(send_birthday_mail,"interval",seconds=20,replace_existing=True)
    scheduler.start()

    