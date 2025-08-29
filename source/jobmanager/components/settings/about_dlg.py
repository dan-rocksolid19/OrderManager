from librepy.pybrex import dialog

class AboutDialog(dialog.DialogBase):
    POS_SIZE = 0, 0, 400, 200
    MARGIN = 10
    LABEL_HEIGHT = 12
    TITLE_COLOR = 0x2B579A

    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = 'About'
        props['BackgroundColor'] = 0xFFFFFF
        self.ctx = ctx
        self.parent = parent
        self.logger = logger
        super().__init__(ctx, self.parent, **props)

    def _create(self):
        try:
            x = self.MARGIN
            y = self.MARGIN
            width = self.POS_SIZE[2] - self.MARGIN * 2

            self.add_label(
                'LblTitle',
                x, y,
                width,
                self.LABEL_HEIGHT + 4,
                Label='Job Manager',
                FontHeight=14,
                FontWeight=150,
                TextColor=self.TITLE_COLOR,
                Align=1
            )

            y += self.LABEL_HEIGHT + 8

            description = 'Job Manager streamlines job tracking, documents and reporting within LibreOffice.'
            self.add_label(
                'LblDescription',
                x, y,
                width,
                self.LABEL_HEIGHT * 3,
                Label=description,
                MultiLine=True,
                FontHeight=11,
                Align=0
            )

            y += self.LABEL_HEIGHT * 3 + 8
            credits = 'Developed by RockSolid Data Solutions\nFor Farview Concrete\nContact: sales@rocksoliddata.solutions | 620-888-7050'
            self.add_label(
                'LblCredits',
                x, y,
                width,
                self.LABEL_HEIGHT * 4,
                Label=credits,
                MultiLine=True,
                FontHeight=11,
                Align=0
            )

            y = self.POS_SIZE[3] - 35
            btn_width = 60
            self.add_button(
                'OkButton',
                int(self.POS_SIZE[2] / 2 - btn_width / 2),
                y,
                btn_width,
                20,
                Label='OK',
                PushButtonType=1,
                DefaultButton=True
            )
        except Exception as e:
            error_msg = f"Error creating about dialog: {str(e)}"
            self.logger.error(error_msg)
            MsgBox(error_msg, 16, 'UI Creation Error')
            raise

    def _prepare(self):
        pass

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret 