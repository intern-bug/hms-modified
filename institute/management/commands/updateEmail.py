import os, csv, traceback
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from institute.models import Student
from django.conf import settings


class Command(BaseCommand):
    help = "Update Student rows from given CSV file to Student Model."

    def get_file_path(self, file_name):
        return os.path.join(settings.BASE_DIR, "data", file_name)

    def add_arguments(self, parser):
        parser.add_argument("file_name", nargs="+", type=str)         

    def handle(self, *args, **options):
        file_path = self.get_file_path(options["file_name"][0])
        try:
            with open(file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                self.stdout.write(self.style.SUCCESS("Reading: {}".format(file_path)))
                
                created, rejected = [0, 0]
                for data in csv_reader:
                    try:
                        # TODO: Modify Model to hold null data for blood group, community, 
                        # Required values for roll_no, year, branch, institute email, 
                        if Student.objects.filter(regd_no=data['RegNo']).exists():
                            student = Student.objects.filter(regd_no=data['RegNo']).first()
                        elif Student.objects.filter(roll_no=data['RollNo']).exists():
                            student = Student.objects.filter(roll_no=data['RollNo']).first()
                        else:
                            student = Student()

                        student.account_email = data["Institute email"]
                        student.save()
                        created += 1

                    except Exception as e:
                        if data["RegNo"]:
                            print("Error while inserting student {} - {}".format(data["RegNo"], data["Name"]))
                            traceback.print_exc()
                            print()
                        else:
                            pass
                        rejected += 1 

        except Exception as e:
            raise CommandError("Error: {}".format(e))

        self.stdout.write(self.style.SUCCESS('Successfully imported {} students. Rejected {} students.'.format(created, rejected)))