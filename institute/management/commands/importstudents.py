import os, csv, traceback
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from institute.models import Student
from django.conf import settings


class Command(BaseCommand):
    help = "Imports Students from given CSV file to Student Model."

    def get_file_path(self, file_name):
        return os.path.join(settings.BASE_DIR, "data", file_name)

    def convert_date(self, date):
        day, month, year = list(map(lambda x: int(x), date.split("-")))
        return timezone.datetime(year=year, month=month, day=day)

    def add_arguments(self, parser):
        parser.add_argument("file_name", nargs="+", type=str)

    def get_branch(self, branch):
        import re
        BRANCH_DICT = {
            'bio[-]*(t|tech)[nology]?' : 'BIOT',
            '(chemical(-| )*(engg|Engineering)|chem)': 'CHEM',
            '(civil(-| )*(engg|Engineering)|civil)': 'CIVIL',
            '(computer[ ]*science[ ]*(and|&)?[ ]*(Engineering|engg)|CSE)': 'CSE',
            '(electrical([ ]*(and|&)?[ ]*electronics)?[ ]*(Engineering|engg)|EEE)': 'EEE',
            '(electronics[ ]*(and|&)?[ ]*(communication|comm)[ ]*(Engineering|engg)|ECE)': 'ECE',
            'mech([anical]?[ ]*(Engineering|engg))?': 'MECH',
            '(metallurgical[ ]*(and|&)?[ ]*materials[ ]*(Engineering|engg)|MME)': 'MME'
        }
        for key in BRANCH_DICT.keys():
            if re.search(key, branch, re.IGNORECASE):
                return  BRANCH_DICT[key]
        raise Exception("Invalid Branch Name")

    def get_blood_group(self, bgroup):
        import re
        BGROUP_DICT = {
            '[\'\"]?a[\'\"]?[ ]*(\(?\+\)?[ ]*(ve)?[ ]*|po(s|ss)itive)': 'A+',
            '[\'\"]?a[\'\"]?[ ]*(\(?-\)?[ ]*(ve)?[ ]*|negative)': 'A-',
            '[\'\"]?b[\'\"]?[ ]*(\(?\+\)?[ ]*(ve)?[ ]*|po(s|ss)itive)': 'B+',
            '[\'\"]?b[\'\"]?[ ]*(\(?-\)?[ ]*(ve)?[ ]*|negative)': 'B-',
            '[\'\"]?(o|0)?[\'\"]?[ ]*(\(?\+\)?[ ]*(ve)?[ ]*|po(s|ss)itive)': 'O+',
            '[\'\"]?(o|0)?[\'\"]?[ ]*(\(?-\)?[ ]*(ve)?[ ]*|negative)': 'O-',
            '[\'\"]?ab[\'\"]?[ ]*(\(?\+\)?[ ]*(ve)?[ ]*|po(s|ss)itive)': 'AB+',
            '[\'\"]?ab[\'\"]?[ ]*(\(?-\)?[ ]*(ve)?[ ]*|negative)': 'AB-',
        }
        for key in BGROUP_DICT.keys():
            if re.search(key, bgroup, re.IGNORECASE):
                return BGROUP_DICT[key]
        raise Exception("Invalid Blood Group")            

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
                        student = Student()
                        student.regd_no = data["StudentID"]
                        student.roll_no = data["roll_no"]
                        student.name = ' '.join([n.capitalize() for n in data["FullName"].lower().split()])
                        student.year = data["year"]
                        student.branch = self.get_branch(data["branch"])
                        student.account_email = "{}@student.nitandhra.ac.in".format(student.roll_no)
                        student.email = data["StudentEmail"]
                        student.address = data["Address"]
                        student.phone = data["StudentMobile"]
                        student.parents_phone = data["ParentMobile"]
                        student.emergency_phone = data["EmergencyMobile"]
                        student.gender = data["Gender"]
                        student.community = data["Caste"].upper()
                        student.dob = self.convert_date(data["BirthDate"])
                        student.blood_group = self.get_blood_group(data["Bgroup"])
                        student.pwd = data["Disability"] == "1"
                        student.aadhar_number = data["AadharNumber"]
                        student.father_name = ' '.join([n.capitalize() for n in data["FatherName"].lower().split()])
                        student.mother_name = ' '.join([n.capitalize() for n in data["MotherName"].lower().split()])
                        student.specialization = 'B.Tech.'
                        student.is_hosteller = True
                        student.photo = data['photo']
                        student.save()
                        created += 1

                    except Exception as e:
                        if data["StudentID"]:
                            print("Error while inserting student {} - {}".format(data["StudentID"], data["FullName"]))
                            traceback.print_exc()
                            print()
                        else:
                            pass
                        rejected += 1 

        except Exception as e:
            raise CommandError("Error: {}".format(e))

        self.stdout.write(self.style.SUCCESS('Successfully imported {} students. Rejected {} students.'.format(created, rejected)))