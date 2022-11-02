import os, csv, traceback
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from students.models import FeeDetail, RoomDetail
from institute.models import Student, Block
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
    
    def handle(self, *args, **options):
        file_path = self.get_file_path(options["file_name"][0])
        try:
            with open(file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=",")
                self.stdout.write(self.style.SUCCESS("Reading: {}".format(file_path)))
                
                created, rejected = [0, 0]

                BLOCKS_DICT = {'Godavari':'4S-A', 'Sabari':'2S-A', 'Indravathi':'2S-B', 'Pranahita':'2S-C', 
                               'Banganga':'1S-A', 'Purna':'1S-B', 'Manjeera':'1S-C',
                               'Krishnaveni': '4S-FA', 'Bhima':'2S-FA', 'Tungabhadra':'2S-FB',
                               'Ghataprabha': '1S-FA', 'Munneru':'1S-FB',
                               'Vamsadhara-I': '4S-B1', 'Vamsadhara-II':'4S-B2', 'Nagavali-I':'2S-D1', 'Nagavali-II':'2S-D2',
                               'Swarnamukhi':'1S-D'
                            }
                for data in csv_reader:
                    try:
                        # TODO: Modify Model to hold null data for blood group, community, 
                        # Required values for roll_no, year, branch, institute email, 
                        regd_no = data["RegNo"]
                        student = Student.objects.get(regd_no=regd_no)
                        room = RoomDetail.objects.filter(student=student).first()
                        if not room:
                            room = RoomDetail()
                        room.student = student
                        
                        if data["Block"] == "Vamsadhara":
                            if data["Floor"] in ["Ground", "First", "Second"]:
                                block_id = BLOCKS_DICT["Vamsadhara-I"]
                            else:
                                block_id = BLOCKS_DICT["Vamsadhara-II"]
                        elif data['Block'] == 'Nagavali':
                            if data["Floor"] in ["Ground", "First", "Second", 'Third']:
                                block_id = BLOCKS_DICT["Nagavali-I"]
                            else:
                                block_id = BLOCKS_DICT["Nagavali-II"]
                        else:
                            block_id = BLOCKS_DICT[data["Block"]]
                        
                        block = Block.objects.get(block_id=block_id)
                        room.block = block
                        room.room_no = data["RoomNo"]
                        room.floor = data["Floor"]
                        valid_beds = [_+1 for _ in range(int(block.room_type[0]))]
                        if RoomDetail.objects.filter(block=block, room_no=data['RoomNo'], floor=data['Floor']).order_by('-bed').exists():
                            room_details = RoomDetail.objects.filter(block=block, room_no=data['RoomNo'], floor=data['Floor']).order_by('-bed')
                            valid_beds = list(set(valid_beds) - set(room_details.values_list('bed', flat=True)))
                            if valid_beds:
                                room.bed = valid_beds[0]
                        else:
                            room.bed = 1
                        room.allotted_on = self.convert_date(data["AllottedOn"])
                        room.save()
                        created += 1

                        FeeDetail.objects.filter(student=student).update(room_detail=room)

                    except Exception as e:
                        if data["RegNo"]:
                            print("Error while inserting room-detail {}".format(data["RegNo"]))
                            traceback.print_exc()
                            print()
                        else:
                            pass
                        rejected += 1 

        except Exception as e:
            raise CommandError("Error: {}".format(e))

        self.stdout.write(self.style.SUCCESS('Successfully imported {} room-details. Rejected {} room-details.'.format(created, rejected)))