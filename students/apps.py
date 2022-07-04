from django.apps import AppConfig


class StudentsConfig(AppConfig):
    name = 'students'

    def ready(self):
        print('Starting Scheduler ...')
        from .birthday_scheduler import check_birthday
        check_birthday.start()
