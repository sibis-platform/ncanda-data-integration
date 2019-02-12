##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Helper file storing all information that the different ASEBA forms require.

Data shared between forms is defined in the top-level FormASEBA class, as are
the data structures and function methods that populate each instance.

The only reason classes are used are for easy inheritance of ASEBA *metadata*.
Data processing is done separately in aseba_prep.py and aseba_reformat.py.
"""


from builtins import object
import time
from collections import OrderedDict

# TODO: Might be cleaner for this to be a @staticmethod of FormASEBA?
def get_aseba_form(form_type):
    """
    Given form_type, returns an instance of the FormASEBA of that form type.
    """
    if form_type == "asr":
        return FormASR()
    elif form_type == "ysr":
        return FormYSR()
    elif form_type == "cbc":
        return FormCBC()
    else:
        raise NotImplementedError("Form type %s not implemented!" % form_type)

class FormASEBA(object):
    """
    Base class for ASEBA forms. Should never be instantiated on its own.
    
    Its only purpose is to allow child classes to inherit generic fields, as
    well as the __init__ method (which populates generic fields, specific
    fields, and post-processing rename lookup dict.)
    """
    def __init__(self):
        """
        Set up variables and invoke methods that child classes will define.
        """
        self.constant_fields = {}
        self.post_score_renames = {}
        self.form = None
        self.form_field_regex = None
        self.field_count = None

        self.set_generic_fields()
        self.set_specific_fields()
        self.set_post_score_renames()

    def set_generic_fields(self):
        """
        Fields that are shared between all ASEBA / ADM forms.
        """
        self.constant_fields["admver"] = 9.1
        self.constant_fields["datatype"] = 'raw'
        self.constant_fields["dfo"] = '//'
        self.constant_fields["enterdate"] = time.strftime("%m/%d/%Y")

    def set_specific_fields(self):
        """
        Fields specific to a form. Not implemented in base class.
        """
        raise NotImplementedError("Must be defined by subclass!")

    def set_post_score_renames(self):
        """
        Lookup of scored variable names -> NCANDA release names.

        Currently, this is an OrderedDict of 60+ name mappings for each form.

        In principle, it should be possible to derive the renames by:

        A. Extracting the identification embedded in <form>_*name
        B. Form-specific scores (that nonetheless overlap in content)
            1. Extract from each variable whether it
                a. ends in _Total, _TScore, or _Percentile
                b. the string preceding that
            2. Look up both components of the name in a shorter lookup table
                (e.g. {'Anxious__Depressed': 'anxdep'})

        However, extracting out the large rename tables from
        *_output_reformat.py files is sufficient progress for now.
        """
        raise NotImplementedError("Must be defined by subclass!")

class FormASR(FormASEBA):
    """
    Properties for the ASR (Adult Self-Report) form.
    """

    def set_specific_fields(self):
        self.form = 'youth_report_1b'
        self.form_field_regex = r'^youthreport1_asr_section.+(?<!label)$'
        self.field_count = 131

        self.constant_fields["formver"] = '2003'
        self.constant_fields["dataver"] = '2003'
        self.constant_fields["formno"] = '9'
        self.constant_fields["formid"] = '9'
        self.constant_fields["type"] = 'ASR'
        self.constant_fields["compitems"] = "'" + ('9' * 36)

    def set_post_score_renames(self):
        self.post_score_renames = OrderedDict([
            ('asr_middlename', 'subject'),
            ('asr_othername', 'arm'),
            ('asr_lastname', 'visit'),
            # ('asr_firstname', 'study_id'),
            ('Personal_Strengths_Total', 'asr_strength_raw'),
            ('Personal_Strengths_TScore', 'asr_strength_t'),
            ('Personal_Strengths_Percentile', 'asr_strength_pct'),
            ('Anxious__Depressed_Total', 'asr_anxdep_raw'),
            ('Anxious__Depressed_TScore', 'asr_anxdep_t'),
            ('Anxious__Depressed_Percentile', 'asr_anxdep_pct'),
            ('Withdrawn_Total', 'asr_withdrawn_raw'),
            ('Withdrawn_TScore', 'asr_withdrawn_t'),
            ('Withdrawn_Percentile', 'asr_withdrawn_pct'),
            ('Somatic_Complaints_Total', 'asr_somatic_raw'),
            ('Somatic_Complaints_TScore', 'asr_somatic_t'),
            ('Somatic_Complaints_Percentile', 'asr_somatic_pct'),
            ('Thought_Problems_Total', 'asr_thought_raw'),
            ('Thought_Problems_TScore', 'asr_thought_t'),
            ('Thought_Problems_Percentile', 'asr_thought_pct'),
            ('Attention_Problems_Total', 'asr_attention_raw'),
            ('Attention_Problems_TScore', 'asr_attention_t'),
            ('Attention_Problems_Percentile', 'asr_attention_pct'),
            ('Aggressive_Behavior_Total', 'asr_aggressive_raw'),
            ('Aggressive_Behavior_TScore', 'asr_aggressive_t'),
            ('Aggressive_Behavior_Percentile', 'asr_aggressive_pct'),
            ('Rule_Breaking_Behavior_Total', 'asr_rulebreak_raw'),
            ('Rule_Breaking_Behavior_TScore', 'asr_rulebreak_t'),
            ('Rule_Breaking_Behavior_Percentile', 'asr_rulebreak_pct'),
            ('Intrusive_Total', 'asr_intrusive_raw'),
            ('Intrusive_TScore', 'asr_intrusive_t'),
            ('Intrusive_Percentile', 'asr_intrusive_pct'),
            ('Internalizing_Problems_Total', 'asr_internal_raw'),
            ('Internalizing_Problems_TScore', 'asr_internal_t'),
            ('Internalizing_Problems_Percentile', 'asr_internal_pct'),
            ('Externalizing_Problems_Total', 'asr_external_raw'),
            ('Externalizing_Problems_TScore', 'asr_external_t'),
            ('Externalizing_Problems_Percentile', 'asr_external_pct'),
            ('Total_Problems_Total', 'asr_totprob_raw'),
            ('Total_Problems_TScore', 'asr_totprob_t'),
            ('Total_Problems_Percentile', 'asr_totprob_pct'),
            ('Depressive_Problems_Total', 'asr_dep_dsm_raw'),
            ('Depressive_Problems_TScore', 'asr_dep_dsm_t'),
            ('Depressive_Problems_Percentile', 'asr_dep_dsm_pct'),
            ('Anxiety_Problems_Total', 'asr_anx_dsm_raw'),
            ('Anxiety_Problems_TScore', 'asr_anx_dsm_t'),
            ('Anxiety_Problems_Percentile', 'asr_anx_dsm_pct'),
            ('Somatic_Problems_Total', 'asr_somat_dsm_raw'),
            ('Somatic_Problems_TScore', 'asr_somat_dsm_t'),
            ('Somatic_Problems_Percentile', 'asr_somat_dsm_pct'),
            ('Avoidant_Personality_Problems_Total', 'asr_avoid_dsm_raw'),
            ('Avoidant_Personality_Problems_TScore', 'asr_avoid_dsm_t'),
            ('Avoidant_Personality_Problems_Percentile', 'asr_avoid_dsm_pct'),
            ('AD_H_Problems_Total', 'asr_adhd_dsm_raw'),
            ('AD_H_Problems_TScore', 'asr_adhd_dsm_t'),
            ('AD_H_Problems_Percentile', 'asr_adhd_dsm_pct'),
            ('Antisocial_Personality_Total', 'asr_antisoc_dsm_raw'),
            ('Antisocial_Personality_TScore', 'asr_antisoc_dsm_t'),
            ('Antisocial_Personality_Percentile', 'asr_antisoc_dsm_pct'),
            ('Inattention_Problems_Subscale_Total', 'asr_inatten_raw'),
            ('Inattention_Problems_Subscale_TScore', 'asr_inatten_t'),
            ('Inattention_Problems_Subscale_Percentile', 'asr_inatten_pct'),
            ('Hyperactivity_Impulsivity_Problems_Subscale_Total',
             'asr_hyper_raw'),
            ('Hyperactivity_Impulsivity_Problems_Subscale_TScore',
             'asr_hyper_t'),
            ('Hyperactivity_Impulsivity_Problems_Subscale_Percentile',
             'asr_hyper_pct'),
            ('Sluggish_Cognitive_Tempo_Total', 'asr_slugcog_raw'),
            ('Sluggish_Cognitive_Tempo_TScore', 'asr_slugcog_t'),
            ('Sluggish_Cognitive_Tempo_Percentile', 'asr_slugcog_pct'),
            ('Obsessive_Compulsive_Problems_Total', 'asr_ocd_raw'),
            ('Obsessive_Compulsive_Problems_TScore', 'asr_ocd_t'),
            ('Obsessive_Compulsive_Problems_Percentile', 'asr_ocd_pct'),
        ])


class FormYSR(FormASEBA):
    """
    Properties for the YSR (Youth Self-Report) form.
    """
    def set_specific_fields(self):
        self.form = 'youth_report_1b'
        self.form_field_regex = r'^youthreport1_ysr_section.+(?<!label)$'
        self.field_count = 119

        self.constant_fields["formver"] = '2001'
        self.constant_fields["dataver"] = '2001'
        self.constant_fields["formno"] = '13'
        self.constant_fields["formid"] = '13'
        self.constant_fields["type"] = 'YSR'
        self.constant_fields["compitems"] = "'" + ('9' * 36)

    def set_post_score_renames(self):
        self.post_score_renames = OrderedDict([
            ('ysr_middlename', 'subject'),
            ('ysr_othername', 'arm'),
            ('ysr_lastname', 'visit'),
            ('Anxious__Depressed_Total', 'ysr_anxdep_raw'),
            ('Anxious__Depressed_TScore', 'ysr_anxdep_t'),
            ('Anxious__Depressed_Percentile', 'ysr_anxdep_pct'),
            ('Withdrawn__Depressed_Total', 'ysr_withdep_raw'),
            ('Withdrawn__Depressed_TScore', 'ysr_withdep_t'),
            ('Withdrawn__Depressed_Percentile', 'ysr_withdep_pct'),
            ('Somatic_Complaints_Total', 'ysr_somatic_raw'),
            ('Somatic_Complaints_TScore', 'ysr_somatic_t'),
            ('Somatic_Complaints_Percentile', 'ysr_somatic_pct'),
            ('Social_Problems_Total', 'ysr_social_raw'),
            ('Social_Problems_TScore', 'ysr_social_t'),
            ('Social_Problems_Percentile', 'ysr_social_pct'),
            ('Thought_Problems_Total', 'ysr_thought_raw'),
            ('Thought_Problems_TScore', 'ysr_thought_t'),
            ('Thought_Problems_Percentile', 'ysr_thought_pct'),
            ('Attention_Problems_Total', 'ysr_attention_raw'),
            ('Attention_Problems_TScore', 'ysr_attention_t'),
            ('Attention_Problems_Percentile', 'ysr_attention_pct'),
            ('Rule_Breaking_Behavior_Total', 'ysr_rulebrk_raw'),
            ('Rule_Breaking_Behavior_TScore', 'ysr_rulebrk_t'),
            ('Rule_Breaking_Behavior_Percentile', 'ysr_rulebrk_pct'),
            ('Aggressive_Behavior_Total', 'ysr_aggress_raw'),
            ('Aggressive_Behavior_TScore', 'ysr_aggress_t'),
            ('Aggressive_Behavior_Percentile', 'ysr_aggress_pct'),
            ('Internalizing_Problems_Total', 'ysr_internal_raw'),
            ('Internalizing_Problems_TScore', 'ysr_internal_t'),
            ('Internalizing_Problems_Percentile', 'ysr_internal_pct'),
            ('Externalizing_Problems_Total', 'ysr_external_raw'),
            ('Externalizing_Problems_TScore', 'ysr_external_t'),
            ('Externalizing_Problems_Percentile', 'ysr_external_pct'),
            ('Total_Problems_Total', 'ysr_totprob_raw'),
            ('Total_Problems_TScore', 'ysr_totprob_t'),
            ('Total_Problems_Percentile', 'ysr_totprob_pct'),
            ('Depressive_Problems_Total', 'ysr_dep_dsm_raw'),
            ('Depressive_Problems_TScore', 'ysr_dep_dsm_t'),
            ('Depressive_Problems_Percentile', 'ysr_dep_dsm_pct'),
            ('Anxiety_Problems_Total', 'ysr_anx_dsm_raw'),
            ('Anxiety_Problems_TScore', 'ysr_anx_dsm_t'),
            ('Anxiety_Problems_Percentile', 'ysr_anx_dsm_pct'),
            ('Somatic_Problems_Total', 'ysr_somat_dsm_raw'),
            ('Somatic_Problems_TScore', 'ysr_somat_dsm_t'),
            ('Somatic_Problems_Percentile', 'ysr_somat_dsm_pct'),
            ('Attention_Deficit__Hyperactivity_Problems_Total',
             'ysr_adhd_dsm_raw'),
            ('Attention_Deficit__Hyperactivity_Problems_TScore',
             'ysr_adhd_dsm_t'),
            ('Attention_Deficit__Hyperactivity_Problems_Percentile',
             'ysr_adhd_dsm_pct'),
            ('Oppositional_Defiant_Problems_Total', 'ysr_odd_dsm_raw'),
            ('Oppositional_Defiant_Problems_TScore', 'ysr_odd_dsm_t'),
            ('Oppositional_Defiant_Problems_Percentile', 'ysr_odd_dsm_pct'),
            ('Conduct_Problems_Total', 'ysr_cd_dsm_raw'),
            ('Conduct_Problems_TScore', 'ysr_cd_dsm_t'),
            ('Conduct_Problems_Percentile', 'ysr_cd_dsm_pct'),
            ('Obsessive_Compulsive_Problems_Total', 'ysr_ocd_raw'),
            ('Obsessive_Compulsive_Problems_TScore', 'ysr_ocd_t'),
            ('Obsessive_Compulsive_Problems_Percentile', 'ysr_ocd_pct'),
            ('Stress_Problems_Total', 'ysr_stress_raw'),
            ('Stress_Problems_TScore', 'ysr_stress_t'),
            ('Stress_Problems_Percentile', 'ysr_stress_pct'),
            ('Positive_Qualities_Total', 'ysr_positive_raw'),
            ('Positive_Qualities_TScore', 'ysr_positive_t'),
            ('Positive_Qualities_Percentile', 'ysr_positive_pct')
        ])


class FormCBC(FormASEBA):
    """
    Properties for the CBCL (Child Behavior Checklist) form.
    """
    def set_specific_fields(self):
        self.form = 'parent_report'
        self.form_field_regex = r'^parentreport_cbcl_section.+(?<!label)$'
        self.field_count = 119

        self.constant_fields["formver"] = '2001'
        self.constant_fields["dataver"] = '2001'
        self.constant_fields["formno"] = '9'
        self.constant_fields["formid"] = '9'
        self.constant_fields["type"] = 'CBC'
        self.constant_fields["compitems"] = "'" + ('9' * 40)

    def set_post_score_renames(self):
        self.post_score_renames = OrderedDict([ 
            ('cbc_middlename', 'subject'),
            ('cbc_othername', 'arm'),
            ('cbc_lastname', 'visit'),
            ('Anxious__Depressed_Total', 'cbcl_anxdep_raw'),
            ('Anxious__Depressed_TScore', 'cbcl_anxdep_t'),
            ('Anxious__Depressed_Percentile', 'cbcl_anxdep_pct'),
            ('Withdrawn__Depressed_Total', 'cbcl_withdep_raw'),
            ('Withdrawn__Depressed_TScore', 'cbcl_withdep_t'),
            ('Withdrawn__Depressed_Percentile', 'cbcl_withdep_pct'),
            ('Somatic_Complaints_Total', 'cbcl_somatic_raw'),
            ('Somatic_Complaints_TScore', 'cbcl_somatic_t'),
            ('Somatic_Complaints_Percentile', 'cbcl_somatic_pct'),
            ('Social_Problems_Total', 'cbcl_social_raw'),
            ('Social_Problems_TScore', 'cbcl_social_t'),
            ('Social_Problems_Percentile', 'cbcl_social_pct'),
            ('Thought_Problems_Total', 'cbcl_thought_raw'),
            ('Thought_Problems_TScore', 'cbcl_thought_t'),
            ('Thought_Problems_Percentile', 'cbcl_thought_pct'),
            ('Attention_Problems_Total', 'cbcl_atten_raw'),
            ('Attention_Problems_TScore', 'cbcl_atten_t'),
            ('Attention_Problems_Percentile', 'cbcl_atten_pct'),
            ('Rule_Breaking_Behavior_Total', 'cbcl_rulebrk_raw'),
            ('Rule_Breaking_Behavior_TScore', 'cbcl_rulebrk_t'),
            ('Rule_Breaking_Behavior_Percentile', 'cbcl_rulebrk_pct'),
            ('Aggressive_Behavior_Total', 'cbcl_aggress_raw'),
            ('Aggressive_Behavior_TScore', 'cbcl_aggress_t'),
            ('Aggressive_Behavior_Percentile', 'cbcl_aggress_pct'),
            ('Internalizing_Problems_Total', 'cbcl_internal_raw'),
            ('Internalizing_Problems_TScore', 'cbcl_internal_t'),
            ('Internalizing_Problems_Percentile', 'cbcl_internal_pct'),
            ('Externalizing_Problems_Total', 'cbcl_external_raw'),
            ('Externalizing_Problems_TScore', 'cbcl_external_t'),
            ('Externalizing_Problems_Percentile', 'cbcl_external_pct'),
            ('Total_Problems_Total', 'cbcl_totprob_raw'),
            ('Total_Problems_TScore', 'cbcl_totprob_t'),
            ('Total_Problems_Percentile', 'cbcl_totprob_pct'),
            ('Depressive_Problems_Total', 'cbcl_dep_dsm_raw'),
            ('Depressive_Problems_TScore', 'cbcl_dep_dsm_t'),
            ('Depressive_Problems_Percentile', 'cbcl_dep_dsm_pct'),
            ('Anxiety_Problems_Total', 'cbcl_anx_dsm_raw'),
            ('Anxiety_Problems_TScore', 'cbcl_anx_dsm_t'),
            ('Anxiety_Problems_Percentile', 'cbcl_anx_dsm_pct'),
            ('Somatic_Problems_Total', 'cbcl_somat_dsm_raw'),
            ('Somatic_Problems_TScore', 'cbcl_somat_dsm_t'),
            ('Somatic_Problems_Percentile', 'cbcl_somat_dsm_pct'),
            ('Attention_Deficit__Hyperactivity_Problems_Total',
             'cbcl_adhd_dsm_raw'),
            ('Attention_Deficit__Hyperactivity_Problems_TScore',
             'cbcl_adhd_dsm_t'),
            ('Attention_Deficit__Hyperactivity_Problems_Percentile',
             'cbcl_adhd_dsm_pct'),
            ('Oppositional_Defiant_Problems_Total', 'cbcl_odd_dsm_raw'),
            ('Oppositional_Defiant_Problems_TScore', 'cbcl_odd_dsm_t'),
            ('Oppositional_Defiant_Problems_Percentile', 'cbcl_odd_dsm_pct'),
            ('Conduct_Problems_Total', 'cbcl_cd_dsm_raw'),
            ('Conduct_Problems_TScore', 'cbcl_cd_dsm_t'),
            ('Conduct_Problems_Percentile', 'cbcl_cd_dsm_pct'),
            ('Sluggish_Cognitive_Tempo_Total', 'cbcl_slugcog_raw'),
            ('Sluggish_Cognitive_Tempo_TScore', 'cbcl_slugcog_t'),
            ('Sluggish_Cognitive_Tempo_Percentile', 'cbcl_slugcog_pct'),
            ('Obsessive_Compulsive_Problems_Total', 'cbcl_ocd_raw'),
            ('Obsessive_Compulsive_Problems_TScore', 'cbcl_ocd_t'),
            ('Obsessive_Compulsive_Problems_Percentile', 'cbcl_ocd_pct'),
            ('Stress_Problems_Total', 'cbcl_stress_raw'),
            ('Stress_Problems_TScore', 'cbcl_stress_t'),
            ('Stress_Problems_Percentile', 'cbcl_stress_pct'),
        ])
