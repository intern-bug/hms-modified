from reportlab.platypus.tables import Table
from reportlab.platypus.paragraph import Paragraph, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black, blue, red
from django.utils import timezone


def create_vacation_form(filename, context):
    documentTitle = 'Vacation Form'
    can = canvas.Canvas(filename, pagesize=letter, bottomup=1)
    can.setTitle(documentTitle)
    can.setFillColor(red)
    can.setFont('Times-Roman', 14)
    title = 'NATIONAL INSTITUTE OF TECHNOLOGY, ANDHRA PRADESH'
    can.drawCentredString(330, 740, title)
    place = 'TADEPALLIGUDEM - 534101, WEST GODAVARI DIST., ANDHRA PRADESH, INDIA'
    can.setFontSize(10)
    can.setFillColor(blue)
    can.drawCentredString(330,725, place)
    can.setFillColor(black)
    can.setFont('Times-Bold',12)
    can.drawCentredString(330,705, 'HOSTEL OFFICE')
    can.drawImage('logo.png', 60, 700, 65, 65, mask = [0,0,0,0,0,0])
    can.line(20,695,580,695)
    can.drawCentredString(300, 675, 'VACATION REPORT')
    date = 'Date: {}'.format(timezone.localdate().strftime('%d-%m-%Y'))
    can.drawString(460, 675, date)
    programme = '(B.Tech/M.Tech/MS(Research)/Ph.D/Project Staff/Interns/Others: {})'.format(context['vac'].room_detail.student.specialization)
    # programme = '(B.Tech/M.Tech/MS(Research)/Ph.D/Project Staff/Interns/Others: )'
    can.drawCentredString(300, 650, programme)
    can.line(20,640,580,640)
    can.setFont('Times-Roman', 12)
    can.drawString(40, 615, 'Department: {}'.format(context['vac'].room_detail.student.branch))
    can.drawCentredString(300, 615, 'Room No.: {}'.format(context['vac'].room_detail.room()))
    can.drawString(410, 615, 'Block: {}'.format(context['vac'].room_detail.block.short_name()))
    can.drawString(40, 590, "Name of the Student: {}".format(context['vac'].room_detail.student.name))
    can.drawString(400, 590, 'Roll No.: {}'.format(context['vac'].room_detail.student.roll_no))
    can.drawString(40, 565, "Personal Email ID: {}".format(context['vac'].room_detail.student.account_email))
    can.drawString(370, 565, 'Contact No.: {}'.format(context['vac'].room_detail.student.phone))
    iron_cot = context['vac'].iron_cot_status+', '+(context['vac'].iron_cot_remarks or '')
    tube_light = context['vac'].tube_light_status+', '+(context['vac'].tube_light_remarks or '')
    fan = context['vac'].fan_status+', '+(context['vac'].fan_remarks or '')
    fan_regulator = context['vac'].fan_regulator_status+', '+(context['vac'].fan_regulator_remarks or '')
    cupboards = context['vac'].cupboards_status+', '+(context['vac'].cupboards_remarks or '')
    switches = context['vac'].switches_status+', '+(context['vac'].switches_remarks or '')
    amperes_socket_15 = context['vac'].amperes_socket_15_status+', '+(context['vac'].amperes_socket_15_remarks or '')
    data = [
        ('S.No.', 'Name of the Item', 'Quantity', 'Remarks'),
        ('1', 'Iron Cot', 'One', iron_cot),
        ('2', 'Tube Light', 'One', tube_light),
        ('3', 'Fan', 'One', fan),
        ('4', 'Fan regulator', 'One', fan_regulator),
        ('5', 'Cupboards', 'One', cupboards),
        ('6', 'Switches', 'Four', switches),
        ('7', '15 amperes Socket', 'One', amperes_socket_15)
        ]
    style = []
    style+=[('GRID',(0,0),(-1,-1),1,black),
            ('ALIGN',(0,0),(-1,-1),'LEFT'),
            ('FONT', (0,0),(-1,-1), 'Times-Roman', 12)
            ]
    if context['vac'].iron_cot_status == 'Defective':
        style += [('FONT', (3,1), (-1,-7), 'Times-Bold', 12)]
    if context['vac'].tube_light_status == 'Defective':
        style += [('FONT', (3,2), (-1,-6), 'Times-Bold', 12)]
    if context['vac'].fan_status == 'Defective':
        style += [('FONT', (3,3), (-1,-5), 'Times-Bold', 12)]
    if context['vac'].fan_regulator_status == 'Defective':
        style += [('FONT', (3,4), (-1,-4), 'Times-Bold', 12)]
    if context['vac'].cupboards_status == 'Defective':
        style += [('FONT', (3,5), (-1,-3), 'Times-Bold', 12)]
    if context['vac'].switches_status == 'Defective':
        style += [('FONT', (3,6), (-1,-2), 'Times-Bold', 12)]
    if context['vac'].amperes_socket_15_status == 'Defective':
        style += [('FONT', (3,7), (-1,-1), 'Times-Bold', 12)]
    colWidths=[1.74*cm, 7.22*cm, 2.94*cm, 6.03*cm]
    rowHeights = [0.7*cm for row in data]
    tab = Table(data, colWidths=colWidths, rowHeights=rowHeights, style=style)
    tab.wrapOn(can, 40, 380)
    tab.drawOn(can, 40, 380)

    para_style = ParagraphStyle('Normal', fontName='Times-Roman', fontSize=12, alignment=TA_LEFT, leading=24)
    para = "Handing over the above-mentioned specific and common items in the room in good condition. Further\nstudent's mode of journey {} from NIT-Andhra Pradesh to {} on the date of\n {}".format(context['vac'].mode_of_journey, context['vac'].journey_destination, context['vac'].vacated_on.strftime('%d-%m-%Y'))
    para.replace('\n', '<br />')
    paragraph = Paragraph(para, style=para_style)
    paragraph.wrap(520, 40)
    paragraph.drawOn(can, 40, 310)

    can.drawString(40, 260, "Signature of Student")
    can.drawString(390, 260, "Signature of Caretaker/Warden")
    can.line(20,255,580,255)
    can.setFont('Times-Bold',12)
    can.drawCentredString(300, 235, "For Hostel Office Use")
    can.setFont('Times-Roman', 12)
    can.drawString(400, 200, "Checked & Verified by")
    can.drawString(40, 185, "Name & Designation:______________________")
    can.drawString(40, 155, "Date:___________")
    can.drawString(420, 155, "Signature:________________")
    can.drawString(40, 125, "Ref. Reg. No. (if any):______________")
    can.rect(320, 120, 20, 20, stroke=1, fill=0)
    can.drawString(350, 125, "Ok(No Fine)")
    can.rect(430, 120, 20, 20, stroke=1, fill=0)
    can.drawString(460, 125, "Not Ok")
    can.drawString(40, 100, "Remarks:")
    can.setFont('Times-Bold',12)
    can.drawString(400, 60, "Signature & Office seal")

    can.save()
    return can
