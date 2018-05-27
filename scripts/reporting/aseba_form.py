import time

class FormASEBA:
    def __init__(self):
        self.constant_fields = {}
        self.form = None
        self.form_field_regex = None
        self.set_generic_fields()
        self.set_specific_fields()

    def set_generic_fields(self):
        self.constant_fields["admver"] = 9.1
        self.constant_fields["datatype"] = 'raw'
        self.constant_fields["dfo"] = '//'
        self.constant_fields["enterdate"] = time.strftime("%m/%d/%Y")

    def set_specific_fields(self):
        pass

class FormASR(FormASEBA):
    def set_specific_fields(self):
        self.form = 'youth_report_1b'
        self.form_field_regex = r'^youthreport1_asr_section'

        self.constant_fields["formver"] = '2003'
        self.constant_fields["dataver"] = '2003'
        self.constant_fields["formno"] = '9'
        self.constant_fields["formid"] = '9'
        self.constant_fields["type"] = 'ASR'
        self.constant_fields["compitems"] = "'" + ('9' * 36)

class FormYSR(FormASEBA):
    def set_specific_fields(self):
        self.form = 'youth_report_1b'
        self.form_field_regex = r'^youthreport1_ysr_section'

        self.constant_fields["formver"] = '2001'
        self.constant_fields["dataver"] = '2001'
        self.constant_fields["formno"] = '13'
        self.constant_fields["formid"] = '13'
        self.constant_fields["type"] = 'YSR'
        self.constant_fields["compitems"] = "'" + ('9' * 36)

class FormCBC(FormASEBA):
    def set_specific_fields(self):
        self.form = 'parent_report'
        self.form_field_regex = r'^parentreport_cbcl_section'

        self.constant_fields["formver"] = '2001'
        self.constant_fields["dataver"] = '2001'
        self.constant_fields["formno"] = '9'
        self.constant_fields["formid"] = '9'
        self.constant_fields["type"] = 'CBC'
        self.constant_fields["compitems"] = "'" + ('9' * 40)
