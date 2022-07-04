from django.apps import AppConfig


class StudentsConfig(AppConfig):
    name = 'students'

    def ready(self):
        from .birthday_scheduler import check_birthday
        check_birthday.start()
