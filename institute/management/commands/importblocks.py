from django.core.management.base import BaseCommand, CommandError
from institute.models import Block
from django.conf import settings


class Command(BaseCommand):
    help = "Import Blocks to the system."

    BLOCKS = [
        {"name": "Godavari Hall of Residency",      "block_id": "4S-A", "gender": "Male", "room_type": "4S", "floor_count": 3, "capacity": 76},
        {"name": "Sabari Hall of Residency",        "block_id": "2S-A", "gender": "Male", "room_type": "2S", "floor_count": 3, "capacity": 100},
        {"name": "Indravathi Hall of Residency",    "block_id": "2S-B", "gender": "Male", "room_type": "2S", "floor_count": 3, "capacity": 100},
        {"name": "Pranahita Hall of Residency",    "block_id": "2S-C", "gender": "Male", "room_type": "2S", "floor_count": 3, "capacity": 100},
        {"name": "Banganga Hall of Residency",      "block_id": "1S-A", "gender": "Male", "room_type": "1S", "floor_count": 3, "capacity": 100},
        {"name": "Purna Hall of Residency",         "block_id": "1S-B", "gender": "Male", "room_type": "1S", "floor_count": 3, "capacity": 100},
        {"name": "Manjeera Hall of Residency",      "block_id": "1S-C", "gender": "Male", "room_type": "1S", "floor_count": 3, "capacity": 100},
        

        {"name": "Krishnaveni Hall of Residency",   "block_id": "4S-FA", "gender": "Female", "room_type": "4S", "floor_count": 3, "capacity": 50},
        {"name": "Bhima Hall of Residency",        "block_id": "2S-FA", "gender": "Female", "room_type": "2S", "floor_count": 3, "capacity": 100},
        {"name": "Tungabhadra Hall of Residency",   "block_id": "2S-FB", "gender": "Female", "room_type": "2S", "floor_count": 3, "capacity": 100},
        {"name": "Ghataprabha Hall of Residency",   "block_id": "1S-FA", "gender": "Female", "room_type": "1S", "floor_count": 3, "capacity": 100},
        {"name": "Munneru Hall of Residency",       "block_id": "1S-FB", "gender": "Female", "room_type": "1S", "floor_count": 3, "capacity": 100},
        
        {"name": "Vamsadhara-I Hall of Residency",          "block_id": "4S-B1", "gender": "Male", "room_type": "4S", "floor_count": 3, "capacity": 69},
        {"name": "Vamsadhara-II Hall of Residency",         "block_id": "4S-B2", "gender": "Male", "room_type": "4S", "floor_count": 2, "capacity": 46},
        {"name": "Nagavali-I Hall of Residency",          "block_id": "2S-D1", "gender": "Male", "room_type": "2S", "floor_count": 4, "capacity": 140},
        {"name": "Nagavali-II Hall of Residency",          "block_id": "2S-D2", "gender": "Male", "room_type": "2S", "floor_count": 1, "capacity": 35},
        {"name": "Swarnamukhi Hall of Residency",        "block_id": "1S-D", "gender": "Male", "room_type": "1S", "floor_count": 5, "capacity": 175},
    ]


    def handle(self, *args, **options):
        try:
            for block_info in self.BLOCKS:
                block, created = Block.objects.get_or_create(**block_info)
                if created:
                    self.stdout.write(self.style.NOTICE("Created Block: {}.".format(block.name)))
        except Exception as e:
            raise CommandError("Error: {}".format(e))
        
        block_names = Block.objects.all().values_list('name', flat=True)
        self.stdout.write(self.style.SUCCESS('Available blocks: {}.'.format(", ".join(block_names))))