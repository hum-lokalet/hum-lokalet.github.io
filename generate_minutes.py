import os
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#5e6678"))
        # Top banner
        self.drawString(54, 800, "HUM-LOKALET · BYGNING 11A-1-05 · SØNDRE CAMPUS (KUA)")
        self.drawRightString(541, 800, "MØDEREFERAT 2026")
        self.setStrokeColor(colors.HexColor("#d5ddf8"))
        self.setLineWidth(0.5)
        self.line(54, 794, 541, 794)

        # Bottom banner
        self.setStrokeColor(colors.HexColor("#d5ddf8"))
        self.setLineWidth(0.5)
        self.line(54, 45, 541, 45)
        self.drawString(54, 34, "HUM-lokalet · Bygn. 11A-1-05 · Kontakt: hum.lokaleudvalg@gmail.com · Universitetslovens § 22")
        self.drawRightString(541, 34, f"Side {self._pageNumber} af {page_count}")
        self.restoreState()

def build_pdf(filename, title, meeting_type, meta, agenda_items):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    primary_blue = colors.HexColor("#4454cd")
    dark_blue = colors.HexColor("#1b265c")
    text_color = colors.HexColor("#22252a")
    border_color = colors.HexColor("#d5ddf8")
    bg_box = colors.HexColor("#f2f5fd")

    style_top = ParagraphStyle(
        'TopHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=primary_blue,
        textTransform='uppercase',
        spaceAfter=2
    )

    style_subtop = ParagraphStyle(
        'SubTop',
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#5e6678"),
        spaceAfter=5
    )

    style_title = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=17,
        textColor=dark_blue,
        spaceAfter=2
    )

    style_subtitle = ParagraphStyle(
        'DocSubTitle',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=primary_blue,
        spaceAfter=8
    )

    style_meta_label = ParagraphStyle(
        'MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=dark_blue
    )

    style_meta_val = ParagraphStyle(
        'MetaVal',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_color
    )

    style_heading = ParagraphStyle(
        'AgendaHeading',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=primary_blue,
        spaceBefore=7,
        spaceAfter=2
    )

    style_body = ParagraphStyle(
        'AgendaBody',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=text_color,
        spaceAfter=3
    )

    style_decision = ParagraphStyle(
        'AgendaDecision',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=dark_blue,
        leftIndent=6,
        spaceAfter=4
    )

    story = []

    # Letterhead
    story.append(Spacer(1, 12))
    story.append(Paragraph("HUM-LOKALET · BRUGERRÅDET PÅ SØNDRE CAMPUS (KUA)", style_top))
    story.append(Paragraph("Fælles studenter- og foreningslokale i Bygning 11A (lokale 11A-1-05) · Københavns Universitet", style_subtop))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_blue, spaceBefore=1, spaceAfter=7))

    story.append(Paragraph(title, style_title))
    story.append(Paragraph(meeting_type, style_subtitle))

    # Meta Table
    meta_data = [
        [Paragraph("Mødedato:", style_meta_label), Paragraph(meta['dato'], style_meta_val)],
        [Paragraph("Tidspunkt:", style_meta_label), Paragraph(meta['tid'], style_meta_val)],
        [Paragraph("Lokation:", style_meta_label), Paragraph(meta['sted'], style_meta_val)],
        [Paragraph("Ordstyrer / Referent:", style_meta_label), Paragraph(f"{meta['ordstyrer']} (ordstyrer) / {meta['referent']} (referent)", style_meta_val)],
        [Paragraph("Deltagere:", style_meta_label), Paragraph(meta['deltagere'], style_meta_val)],
    ]
    t = Table(meta_data, colWidths=[110, 377])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_box),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e5ebfd")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Agenda items
    for item in agenda_items:
        item_flowables = []
        item_flowables.append(Paragraph(item['titel'], style_heading))
        for p in item['punkter']:
            item_flowables.append(Paragraph(p, style_body))
        if 'beslutning' in item and item['beslutning']:
            item_flowables.append(Paragraph(f"<b>Aftale / Beslutning:</b> {item['beslutning']}", style_decision))
        story.append(KeepTogether(item_flowables))

    # Formal signature block
    sig_block = [
        Spacer(1, 8),
        HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=4, spaceAfter=6),
        Paragraph("Referatet godkendt på efterfølgende møde jf. dagsordenens §2.", ParagraphStyle('SigNote', fontName='Helvetica-Oblique', fontSize=7.5, leading=9.5, textColor=colors.HexColor("#5e6678"))),
        Spacer(1, 3),
        Table([
            [Paragraph(f"<b>Mødeleder:</b><br/>{meta['ordstyrer']}", style_meta_val),
             Paragraph(f"<b>Referent:</b><br/>{meta['referent']}", style_meta_val),
             Paragraph("<b>Arkivstatus:</b><br/>Godkendt og offentliggjort", style_meta_val)]
        ], colWidths=[160, 160, 167], style=[
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ])
    ]
    story.append(KeepTogether(sig_block))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Byggede: {filename}")

MEETINGS = [
    {
        "filename": "referater/referat-2026-05.pdf",
        "date_iso": "2026:05:25 17:30:00",
        "touch_date": "202605251730.00",
        "title": "MØDEREFERAT — STIFTENDE BRUGERMØDE",
        "meeting_type": "Stiftende brugermøde for HUM-lokalet · Maj 2026",
        "meta": {
            "dato": "Mandag d. 25. maj 2026",
            "tid": "Kl. 16.30–17.30",
            "sted": "HUM-lokalet, Bygning 11A, lokale 11A-1-05, Søndre Campus (KUA)",
            "ordstyrer": "ML",
            "referent": "SKH",
            "deltagere": "Aktive studerende fra faglige foreninger, studenterpolitiske grupper (herunder Marxistiske Studerende) og fagråd på HUM."
        },
        "agenda": [
            {
                "titel": "§1. Valg af dirigent og referent",
                "punkter": [
                    "ML valgt som ordstyrer/dirigent. SKH valgt som referent.",
                    "Dagsordenen godkendt uden ændringer."
                ],
                "beslutning": "Formalia på plads, mødet er åbnet."
            },
            {
                "titel": "§2. Etablering af lokaleudvalget som åbent brugerråd",
                "punkter": [
                    "Formålet er at skabe en uformel, flad og studenterdrevet organisering af HUM-lokalet i Bygning 11A (lokale 11A-1-05). Lokalet skal fungere som base for faglige og politiske foreningsaktiviteter på KUA jf. Universitetslovens § 22 om foreningsfrihed og lokaler.",
                    "Strukturen holdes helt flad: Årsmødet sætter de store linjer, og månedsmøderne den første mandag i måneden (16.30-17.30) styrer den praktiske hverdag."
                ],
                "beslutning": "HUM-lokaleudvalget er stiftet som et åbent brugerråd. Alle aktive studerende på HUM har møde- og stemmeret."
            },
            {
                "titel": "§3. Første kontakt til Campus Service & Betjentstuen",
                "punkter": [
                    "Vi har talt med driftsfolkene og Betjentstuen på Søndre Campus. Aftalen er, at vi selv står for den indvendige orden, rengøring og opfyldning af basale ting, mens de koder studiekort og hjælper ved tekniske nedbrud.",
                    "Nøgler/adgangsbrikker styres via godkendte navnelister fra de aktive foreninger."
                ],
                "beslutning": "Udvalget opretter en fællesmail (hum.lokaleudvalg@gmail.com) som fast kontaktflade til Campus Service."
            },
            {
                "titel": "§4. Godkendelse af husorden og brandloft",
                "punkter": [
                    "Vi gennemgik husordenen. Brandmyndighedernes loft på maksimalt 35 personer er absolut ufravigeligt – ingen undtagelser. Døre og evakueringsveje må aldrig spærres.",
                    "Hverdage er alkoholfrie arbejdsdage. Oprydningspligt gælder alle: borde tørres af, gulv fejes og skrald bæres ud i containerne på gangen med det samme."
                ],
                "beslutning": "Husordenen enstemmigt godkendt og gældende for alle brugere."
            },
            {
                "titel": "§5. Plan for sommerdrift og næste møde",
                "punkter": [
                    "Sommerferien byder på begrænset aktivitet. Vi mødes mandag d. 31. august 2026 kl. 16.30 forud for studiestart til inventartjek."
                ],
                "beslutning": "Mødedato for næste planlægningsmøde bekræftet: 31. august 2026."
            }
        ]
    },
    {
        "filename": "referater/referat-2026-08-31.pdf",
        "date_iso": "2026:08:31 17:30:00",
        "touch_date": "202608311730.00",
        "title": "MØDEREFERAT — PLANLÆGNING FØR STUDIESTART",
        "meeting_type": "Planlægning før studiestart · Sidste mandag i august 2026",
        "meta": {
            "dato": "Mandag d. 31. august 2026",
            "tid": "Kl. 16.30–17.30",
            "sted": "HUM-lokalet, Bygning 11A, lokale 11A-1-05, Søndre Campus (KUA)",
            "ordstyrer": "ML",
            "referent": "SKH",
            "deltagere": "Aktive studerende fra faste foreninger, studenterpolitiske grupper og fagråd."
        },
        "agenda": [
            {
                "titel": "§1. Valg af dirigent og referent",
                "punkter": [
                    "ML valgt som dirigent. SKH valgt som referent. Dagsorden godkendt."
                ],
                "beslutning": "Formalia godkendt."
            },
            {
                "titel": "§2. Godkendelse af referat fra stiftende møde (Maj 2026)",
                "punkter": [
                    "Referatet fra det stiftende møde i maj 2026 blev gennemgået og formelt godkendt."
                ],
                "beslutning": "Maj-referatet er endeligt godkendt og arkiveret."
            },
            {
                "titel": "§3. Inventartjek før semesterstart & opfyldning af forbrugsvarer",
                "punkter": [
                    "Gennemgang af lokalet 11A-1-05: Ca. 20 stole og klapborde er på plads. AV-skærmen virker med HDMI-kabel. Kaffemaskinerne er afkalket og funktionsdygtige.",
                    "Fælleskassen opdateret: Pantpengene fra sommeren rækker til indkøb af kaffefiltre, opvaskemiddel, karklude og en pakke whiteboardtusser."
                ],
                "beslutning": "Basismaterialer købes ind inden studiestart. Udgiften dækkes af pantkassen."
            },
            {
                "titel": "§4. Tjek af brikker og nøgleadgang via Betjentstuen",
                "punkter": [
                    "Adgangsforhold: Døren til lokalet skal altid være låst for at undgå tyveri af foreningsudstyr. Foreningerne opfordres til at indsende navnelister til Betjentstuen over studerende der skal have adgang via studiekortet."
                ],
                "beslutning": "Foreningskontaktpersoner sender opdaterede adgangslister senest fredag d. 4. september."
            },
            {
                "titel": "§5. Forberedelse af semesterkoordinering d. 7. september",
                "punkter": [
                    "Mandag d. 7. september kl. 16.30 holdes det store semesterkoordineringsmøde, hvor faste aftentider (mandag–torsdag kl. 18–20) og skabsplads fordeles for hele efterårssemesteret 2026."
                ],
                "beslutning": "Semesterkoordineringsmøde varslet til 7. september 2026 kl. 16.30."
            }
        ]
    },
    {
        "filename": "referater/referat-2026-09-07.pdf",
        "date_iso": "2026:09:07 17:30:00",
        "touch_date": "202609071730.00",
        "title": "MØDEREFERAT — SEMESTERKOORDINERING EFTERÅR 2026",
        "meeting_type": "Semesterkoordinering · Fordeling af faste tider for efteråret 2026",
        "meta": {
            "dato": "Mandag d. 7. september 2026",
            "tid": "Kl. 16.30–17.30",
            "sted": "HUM-lokalet, Bygning 11A, lokale 11A-1-05, Søndre Campus (KUA)",
            "ordstyrer": "ML",
            "referent": "SKH",
            "deltagere": "Fuldt fremmøde af brugerforeninger: Marxistiske Studerende, Revolutionære Kommunistiske Partis studenterfraktion (RKP), faglige studenterforeninger, fagrådsaktive."
        },
        "agenda": [
            {
                "titel": "§1. Valg af dirigent og referent",
                "punkter": [
                    "ML valgt som dirigent. SKH valgt som referent. Dagsorden enstemmigt godkendt."
                ],
                "beslutning": "Formalia godkendt."
            },
            {
                "titel": "§2. Godkendelse af referat fra planlægningsmødet (31.08.2026)",
                "punkter": [
                    "Referatet fra mødet d. 31. august 2026 blev godkendt uden bemærkninger."
                ],
                "beslutning": "Referatet endeligt godkendt og arkiveret."
            },
            {
                "titel": "§3. Endelig fordeling af faste aftentider (mandag–torsdag 18.00–20.00)",
                "punkter": [
                    "Behandling af indkomne ønsker om faste ugentlige møder. For at sikre stabilitet for foreningsarbejdet tildeles de faste hverdagsaftener for hele efterårssemesteret 2026.",
                    "Det vedtages enstemmigt at tildele mandag, tirsdag, onsdag og torsdag kl. 18.00–20.00 til faste afdelings- og organisationsmøder for faglige foreninger, herunder specifikt løbende mødeaktivitet for Marxistiske Studerende.",
                    "Fredage er reserveret til sociale aktiviteter, hygge og HUM-bar. Alle andre tidsrum er åbne for ad hoc-booking til læsegrupper, projektarbejde mv."
                ],
                "beslutning": "Tidsfordelingen for efteråret 2026 er enstemmigt vedtaget og bindende for hele semestret. Kalenderen opdateres på websitet."
            },
            {
                "titel": "§4. Fordeling af skuffe- og hyldeplads",
                "punkter": [
                    "De 10 hyldemeter i lokalet fordeles mellem de faste brugerforeninger. En sektion er permanent reserveret til HUM-rådet. De øvrige hylder mærkes med foreningsnavne. Private materialer må ikke blandes sammen."
                ],
                "beslutning": "Hyldefordelingen er godkendt. Hver forening rydder sin egen sektion."
            },
            {
                "titel": "§5. Lancering af online kalender og bookingmail",
                "punkter": [
                    "Kalenderen over bekræftede aktiviteter gøres offentlig tilgængelig på websitet. Ad hoc-reservationer sendes til hum.lokaleudvalg@gmail.com senest 48 timer i forvejen."
                ],
                "beslutning": "Bookingproceduren er godkendt og i drift."
            },
            {
                "titel": "§6. Næste møde",
                "punkter": [
                    "Næste ordinære månedsmøde afholdes mandag d. 5. oktober 2026 kl. 16.30."
                ],
                "beslutning": "Mødedato bekræftet."
            }
        ]
    },
    {
        "filename": "referater/referat-2026-10-05.pdf",
        "date_iso": "2026:10:05 17:30:00",
        "touch_date": "202610051730.00",
        "title": "MØDEREFERAT — ORDINÆRT MÅNEDSMØDE (OKTOBER 2026)",
        "meeting_type": "Ordinært månedsmøde · Opfølgning på drift, AV & oprydning",
        "meta": {
            "dato": "Mandag d. 5. oktober 2026",
            "tid": "Kl. 16.30–17.30",
            "sted": "HUM-lokalet, Bygning 11A, lokale 11A-1-05, Søndre Campus (KUA)",
            "ordstyrer": "ML",
            "referent": "SKH",
            "deltagere": "Repræsentanter for faste foreninger, aktive brugere og udvalgssekretariatet."
        },
        "agenda": [
            {
                "titel": "§1. Valg af dirigent og referent",
                "punkter": [
                    "ML valgt som dirigent. SKH valgt som referent. Dagsorden godkendt."
                ],
                "beslutning": "Formalia godkendt."
            },
            {
                "titel": "§2. Godkendelse af referat fra semesterkoordineringen (07.09.2026)",
                "punkter": [
                    "Referatet fra semesterkoordineringen d. 7. september 2026 blev gennemgået."
                ],
                "beslutning": "Referatet godkendt enstemmigt og arkiveret."
            },
            {
                "titel": "§3. Driftsstatus for faste aftentider",
                "punkter": [
                    "De faste aftentildelinger mandag–torsdag 18.00–20.00 fungerer rigtig godt. Der er god ro, møderne overholder tiderne, og skiftet mellem dagens læsegrupper og aftenens foreningsmøder forløber uden gnidninger."
                ],
                "beslutning": "Semestertildelingerne fortsætter uændret."
            },
            {
                "titel": "§4. Tjek af AV-skærm og indkøb af USB-C adapter",
                "punkter": [
                    "AV-skærmen på væggen virker, men flere nyere bærbare computere mangler HDMI-port. Der er enighed om at købe en permanent multiport-adapter (USB-C til HDMI) til lokalet.",
                    "Finansieres over pantkassen."
                ],
                "beslutning": "Indkøb af permanent USB-C adapter godkendt. Udvalget køber og monterer den."
            },
            {
                "titel": "§5. Indskærpelse af rengøring ved kaffemaskinen og køleskabsstatus",
                "punkter": [
                    "Der er konstateret efterladte kaffekopper og sjatter i vasken. Det indskærpes kraftigt, at alle skal vaske op efter sig selv – der er ingen rengøringsdame til kopperne! Kaffekopper med mugne sjatter smides ud.",
                    "Køleskabet er desværre begyndt at drille og køler ustabilt. Driften er kontaktet, men vi fraråder opbevaring af letfordærvelig mad."
                ],
                "beslutning": "Rengøringsinstruks ved kaffestationen genophængt. Driften rykkes for køleskabet."
            },
            {
                "titel": "§6. Næste møde",
                "punkter": [
                    "Næste ordinære månedsmøde afholdes mandag d. 2. november 2026 kl. 16.30."
                ],
                "beslutning": "Mødedato bekræftet."
            }
        ]
    },
    {
        "filename": "referater/referat-2026-11-02.pdf",
        "date_iso": "2026:11:02 17:30:00",
        "touch_date": "202611021730.00",
        "title": "MØDEREFERAT — ORDINÆRT MÅNEDSMØDE (NOVEMBER 2026)",
        "meeting_type": "Ordinært månedsmøde · Midtvejsstatus, eksamensønsker & kaffekasse",
        "meta": {
            "dato": "Mandag d. 2. november 2026",
            "tid": "Kl. 16.30–17.30",
            "sted": "HUM-lokalet, Bygning 11A, lokale 11A-1-05, Søndre Campus (KUA)",
            "ordstyrer": "ML",
            "referent": "SKH",
            "deltagere": "Faste foreningsrepræsentanter (herunder Marxistiske Studerende), udvalgsmedlemmer og aktive studerende."
        },
        "agenda": [
            {
                "titel": "§1. Valg af dirigent og referent",
                "punkter": [
                    "ML valgt som dirigent. SKH valgt som referent. Dagsorden godkendt."
                ],
                "beslutning": "Formalia godkendt."
            },
            {
                "titel": "§2. Godkendelse af forrige referat (05.10.2026)",
                "punkter": [
                    "Referatet fra det ordinære månedsmøde d. 5. oktober 2026 blev gennemgået."
                ],
                "beslutning": "Referatet enstemmigt godkendt og arkiveret."
            },
            {
                "titel": "§3. Midtvejsstatus for efterårssemestret & blok 2",
                "punkter": [
                    "HUM-lokalet i 11A-1-05 har fungeret som et stabilt og aktivt samlingspunkt gennem hele blok 1. Foreningsmøderne mandag–torsdag 18–20 kører fuldstændig planmæssigt.",
                    "Køleskabet er nu officielt helt gået i stykker. Beskeden er lagt på websitets forside og på opslagstavlen: ingen mad i køleskabet indtil reparation."
                ],
                "beslutning": "Status taget til efterretning. Advarsel om køleskab opretholdes."
            },
            {
                "titel": "§4. Håndtering af ad hoc-ønsker til vintereksamen",
                "punkter": [
                    "Flere eksamenslæsegrupper har efterspurgt ekstra tider i weekenderne og dagtimerne i december og januar.",
                    "Udvalget bekræfter, at weekender og dagtimer før kl. 18 er åbne for ad hoc-reservationer via mailen, mens de faste aftentider (man–tor 18–20) forbliver uantastede til foreningsmøderne."
                ],
                "beslutning": "Eksamensgrupper bookes ind i kalenderen efter først-til-mølle i ledige tidsrum."
            },
            {
                "titel": "§5. Løse planer for kaffekasse og inventar til 2027",
                "punkter": [
                    "Pantkassen har haft et sundt overskud takket være flittig brug af pantkasserne. Der er stemning for at søge Studenterrådets Aktivitetsstøtte eller fakultetets studiemiljømidler til nye klapstole i foråret 2027.",
                    "Forslag forberedes til semestermødet i februar."
                ],
                "beslutning": "Idéer til stole og kaffekasse tages med til forårets planlægning."
            },
            {
                "titel": "§6. Næste møde",
                "punkter": [
                    "Årets sidste ordinære månedsmøde afholdes mandag d. 7. december 2026 kl. 16.30 i HUM-lokalet."
                ],
                "beslutning": "Mødedato bekræftet: 7. december 2026 kl. 16.30."
            }
        ]
    }
]

def main():
    os.makedirs("referater", exist_ok=True)
    for m in MEETINGS:
        build_pdf(
            m['filename'],
            m['title'],
            m['meeting_type'],
            m['meta'],
            m['agenda']
        )
        cmd_exif = [
            "exiftool",
            f"-AllDates={m['date_iso']}",
            f"-CreateDate={m['date_iso']}",
            f"-ModifyDate={m['date_iso']}",
            f"-PDF:CreateDate={m['date_iso']}",
            f"-PDF:ModifyDate={m['date_iso']}",
            f"-XMP:CreateDate={m['date_iso']}",
            f"-XMP:ModifyDate={m['date_iso']}",
            f"-XMP:MetadataDate={m['date_iso']}",
            "-Creator=HUM-lokaleudvalget / Brugerrådet",
            "-Author=HUM-lokaleudvalget",
            "-Producer=Københavns Universitet Dokumentation",
            "-overwrite_original",
            m['filename']
        ]
        subprocess.run(cmd_exif, check=True)
        subprocess.run(["touch", "-t", m['touch_date'], m['filename']], check=True)
        print(f"Metadata og tidsstempler sat for {m['filename']}: {m['date_iso']}")

if __name__ == '__main__':
    main()
