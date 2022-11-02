from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, blue, red
from django.utils import timezone


def create_acknowledge_form(filename, context):
    documentTitle = 'Acknowledgement for Hostel Room Allocation'
    can = canvas.Canvas(filename, pagesize=letter, bottomup=1)
    can.setTitle(documentTitle)
    can.setFillColor(red)
    can.setFont('Times-Roman', 14)
    title = 'NATIONAL INSTITUTE OF TECHNOLOGY, ANDHRA PRADESH'
    can.drawCentredString(330, 740, title)
    place = 'TADEPALLIGUDEM - 534102, WEST GODAVARI DIST., ANDHRA PRADESH, INDIA'
    can.setFontSize(10)
    can.setFillColor(blue)
    can.drawCentredString(330,725, place)
    can.setFillColor(black)
    can.setFont('Times-Bold',12)
    can.drawCentredString(330,705, 'HOSTEL OFFICE')
    can.drawImage('logo.png', 60, 700, 65, 65, mask = [0,0,0,0,0,0])
    can.line(20,695,580,695)
    can.drawCentredString(300, 675, 'Acknowledgement for Hostel Room Allocation')
    date = 'Date: {}'.format(timezone.localdate().strftime('%d-%m-%Y'))
    can.drawString(460, 675, date)
    programme = '(B.Tech/M.Tech/MS(Research)/Ph.D/Project Staff/Interns/Others: {})'.format(context['room'].student.specialization)
    can.drawCentredString(300, 650, programme)
    can.line(20,640,580,640)
    can.setFont('Times-Roman', 12)
    can.drawString(40, 615, 'Hall of Residence: {}'.format(context['room'].block.short_name()))
    can.drawCentredString(300, 615, 'Room No.: {}'.format(context['room'].room()))
    can.drawString(400, 615, 'Cot No.: {}'.format(context['room'].bed))
    can.drawString(40, 590, "Name of the Student: {}".format(context['room'].student.name))
    can.drawString(400, 590, 'Reg No: {}'.format(context['room'].student.regd_no))
    can.drawString(40, 565, 'Contact No.: {}'.format(context['room'].student.phone))
    can.drawString(400, 565, "B.Tech Year: {}".format(context['room'].student.year))
    can.drawString(40, 540, "Mode Of Payment: {}".format(context['fee'].mode_of_payment))
    can.drawString(400, 540, "Amount Paid: {}".format(context['fee'].amount_paid))

    
   

    style = []
    style+=[('GRID',(0,0),(-1,-1),1,black),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONT', (0,0),(-1,-1), 'Times-Roman', 12)
            ]
    

    can.drawString(390, 445, "Signature & Office Seal")
    can.drawString(40, 445, "Signature of Student")
    can.drawCentredString(275, 410, "Signature of Warden/Caretaker")


    can.line(20,370,580,370)
    


    can.setFillColor(red)
    can.setFont('Times-Roman', 14)
    title = 'NATIONAL INSTITUTE OF TECHNOLOGY, ANDHRA PRADESH'
    can.drawCentredString(330, 340, title)
    place = 'TADEPALLIGUDEM - 534102, WEST GODAVARI DIST., ANDHRA PRADESH, INDIA'
    can.setFontSize(10)
    can.setFillColor(blue)
    can.drawCentredString(330,325, place)
    can.setFillColor(black)
    can.setFont('Times-Bold',12)
    can.drawCentredString(330,305, 'HOSTEL OFFICE')
    can.drawImage('logo.png', 60, 300, 65, 65, mask = [0,0,0,0,0,0])

    can.line(20,295,580,295)
    can.drawCentredString(300, 275, 'Acknowledgement for Hostel Room Allocation')
    date = 'Date: {}'.format(timezone.localdate().strftime('%d-%m-%Y'))
    can.drawString(460, 275, date)
    programme = '(B.Tech/M.Tech/MS(Research)/Ph.D/Project Staff/Interns/Others: {})'.format(context['room'].student.specialization)
    can.drawCentredString(300, 250, programme)
    can.line(20,240,580,240)
    can.setFont('Times-Roman', 12)
    can.drawString(40, 215, 'Hall of Residence: {}'.format(context['room'].block.short_name()))
    can.drawCentredString(300, 215, 'Room No.: {}'.format(context['room'].room()))
    can.drawString(400, 215, 'Cot No.: {}'.format(context['room'].bed))
    can.drawString(40, 190, "Name of the Student: {}".format(context['room'].student.name))
    can.drawString(400, 190, 'Reg No: {}'.format(context['room'].student.regd_no))
    can.drawString(40, 165, 'Contact No.: {}'.format(context['room'].student.phone))
    can.drawString(400, 165, "B.Tech Year: {}".format(context['room'].student.year))
    can.drawString(40, 140, "Mode Of Payment: {}".format(context['fee'].mode_of_payment))
    can.drawString(400, 140, "Amount Paid: {}".format(context['fee'].amount_paid))

    
   

    style = []
    style+=[('GRID',(0,0),(-1,-1),1,black),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONT', (0,0),(-1,-1), 'Times-Roman', 12)
            ]
    
    can.drawString(390, 45, "Signature & Office Seal")
    can.drawString(40, 45, "Signature of Student")
    can.drawCentredString(275, 10, "Signature of Warden/Caretaker")

    # can.line(20,20,580,20)

    can.save()
    return can
