import datetime

from sqlalchemy import (
    Column,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UnicodeText,
    event)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from rdr_service.model.base import Base, model_insert_listener, model_update_listener
from rdr_service.model.utils import Enum, EnumZeroBased, UTCDateTime, UTCDateTime6
from rdr_service.participant_enums import (
    EhrStatus,
    EnrollmentStatus,
    GenderIdentity,
    OrderStatus,
    PhysicalMeasurementsStatus,
    QuestionnaireStatus,
    Race,
    SampleStatus,
    SuspensionStatus,
    WithdrawalReason,
    WithdrawalStatus,
    ParticipantCohort,
    ParticipantCohortPilotFlag,
    ConsentExpireStatus,
    DeceasedStatus,
    RetentionStatus)


# The only fields that can be returned, queried on, or ordered by for queries for withdrawn
# participants.
WITHDRAWN_PARTICIPANT_FIELDS = [
    "withdrawalStatus",
    "withdrawalTime",
    "withdrawalAuthored",
    "withdrawalReason",
    "withdrawalReasonJustification",
    "participantId",
    "hpoId",
    "organizationId",
    "siteId",
    "biobankId",
    "firstName",
    "middleName",
    "lastName",
    "dateOfBirth",
    "consentForStudyEnrollment",
    "consentForStudyEnrollmentAuthored",
    "consentForElectronicHealthRecords",
    "consentForElectronicHealthRecordsAuthored",
]

# The period of time for which withdrawn participants will still be returned in results for
# queries that don't ask for withdrawn participants.
WITHDRAWN_PARTICIPANT_VISIBILITY_TIME = datetime.timedelta(days=2)

# suspended or deceased participants don't allow contact but can still use samples. These fields
# will not be returned when queried on suspended participant.
SUSPENDED_OR_DECEASED_PARTICIPANT_FIELDS = ["zipCode", "city", "streetAddress", "streetAddress2", "phoneNumber",
                                            "loginPhoneNumber", "email"]

# SQL Conditional for participant's retention eligibility computed column (1 = NOT_ELIGIBLE, 2 = ELIGIBLE)
_COMPUTE_RETENTION_ELIGIBLE_SQL = """
    CASE WHEN
      consent_for_study_enrollment = 1
      AND (consent_for_electronic_health_records = 1 OR consent_for_dv_electronic_health_records_sharing = 1)
      AND questionnaire_on_the_basics = 1
      AND questionnaire_on_overall_health = 1
      AND questionnaire_on_lifestyle = 1
      AND samples_to_isolate_dna = 1
      AND withdrawal_status = 1
      AND suspension_status = 1
      AND deceased_status = 0
    THEN 2 ELSE 1
    END
"""

# SQL for calculating the date when a participant gained retention eligibility
# Null unless the participant meets the retention-eligible requirements (above) and a qualifying test sample time
# is present.  Otherwise, find the last of the consent / module authored dates and the earliest of the qualifying
# DNA test samples.  The retention eligibility date is the later of those two
_COMPUTE_RETENTION_ELIGIBLE_TIME_SQL = """
     CASE WHEN retention_eligible_status = 2 AND
          COALESCE(sample_status_1ed10_time, sample_status_2ed10_time, sample_status_1ed04_time,
                 sample_status_1sal_time, sample_status_1sal2_time, 0) != 0
        THEN GREATEST(
            GREATEST (consent_for_study_enrollment_authored,
             questionnaire_on_the_basics_authored,
             questionnaire_on_overall_health_authored,
             questionnaire_on_lifestyle_authored,
             COALESCE(consent_for_electronic_health_records_authored, consent_for_study_enrollment_authored),
             COALESCE(consent_for_dv_electronic_health_records_sharing_authored, consent_for_study_enrollment_authored)
            ),
            LEAST(COALESCE(sample_status_1ed10_time, '9999-01-01'),
                COALESCE(sample_status_2ed10_time, '9999-01-01'),
                COALESCE(sample_status_1ed04_time, '9999-01-01'),
                COALESCE(sample_status_1sal_time, '9999-01-01'),
                COALESCE(sample_status_1sal2_time, '9999-01-01')
            )
        )
        ELSE NULL
     END
"""


class ParticipantSummary(Base):
    """Summary fields extracted from participant data (combined from multiple tables).
  Consented participants only."""

    __tablename__ = "participant_summary"
    participantId = Column(
        "participant_id", Integer, ForeignKey("participant.participant_id"), primary_key=True, autoincrement=False
    )
    biobankId = Column("biobank_id", Integer, nullable=False)
    lastModified = Column("last_modified", UTCDateTime6)
    # PTC string fields will generally be limited to 255 chars; set our field lengths accordingly to
    # ensure that long values can be inserted.
    firstName = Column("first_name", String(255), nullable=False)
    middleName = Column("middle_name", String(255))
    lastName = Column("last_name", String(255), nullable=False)
    zipCode = Column("zip_code", String(10))
    stateId = Column("state_id", Integer, ForeignKey("code.code_id"))
    city = Column("city", String(255))
    streetAddress = Column("street_address", String(255))
    streetAddress2 = Column("street_address2", String(255))
    phoneNumber = Column("phone_number", String(80))
    loginPhoneNumber = Column("login_phone_number", String(80))
    email = Column("email", String(255))
    primaryLanguage = Column("primary_language", String(80))
    recontactMethodId = Column("recontact_method_id", Integer, ForeignKey("code.code_id"))
    # deprecated - will remove languageId in the future
    languageId = Column("language_id", Integer, ForeignKey("code.code_id"))
    dateOfBirth = Column("date_of_birth", Date)
    genderIdentityId = Column("gender_identity_id", Integer, ForeignKey("code.code_id"))
    genderIdentity = Column("gender_identity", Enum(GenderIdentity))
    sexId = Column("sex_id", Integer, ForeignKey("code.code_id"))
    sexualOrientationId = Column("sexual_orientation_id", Integer, ForeignKey("code.code_id"))
    educationId = Column("education_id", Integer, ForeignKey("code.code_id"))
    incomeId = Column("income_id", Integer, ForeignKey("code.code_id"))
    enrollmentStatus = Column("enrollment_status", Enum(EnrollmentStatus), default=EnrollmentStatus.INTERESTED)
    race = Column("race", Enum(Race), default=Race.UNSET)
    physicalMeasurementsStatus = Column(
        "physical_measurements_status", Enum(PhysicalMeasurementsStatus), default=PhysicalMeasurementsStatus.UNSET
    )
    # The first time that physical measurements were submitted for the participant.
    physicalMeasurementsTime = Column("physical_measurements_time", UTCDateTime)
    # The time that physical measurements were finalized (before submission to the RDR)
    physicalMeasurementsFinalizedTime = Column("physical_measurements_finalized_time", UTCDateTime)
    physicalMeasurementsCreatedSiteId = Column(
        "physical_measurements_created_site_id", Integer, ForeignKey("site.site_id")
    )
    physicalMeasurementsFinalizedSiteId = Column(
        "physical_measurements_finalized_site_id", Integer, ForeignKey("site.site_id")
    )
    numberDistinctVisits = Column("number_distinct_visits", Integer, default=0)
    signUpTime = Column("sign_up_time", UTCDateTime)

    # The time that this participant become a member
    enrollmentStatusMemberTime = Column("enrollment_status_member_time", UTCDateTime)
    # The time when we get the first stored sample
    enrollmentStatusCoreStoredSampleTime = Column("enrollment_status_core_stored_sample_time", UTCDateTime)
    # The time when we get a DNA order
    enrollmentStatusCoreOrderedSampleTime = Column("enrollment_status_core_ordered_sample_time", UTCDateTime)

    # Fields for which questionnaires have been submitted, and at what times.
    consentForStudyEnrollment = Column(
        "consent_for_study_enrollment", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    consentForStudyEnrollmentTime = Column("consent_for_study_enrollment_time", UTCDateTime)
    consentForStudyEnrollmentAuthored = Column("consent_for_study_enrollment_authored", UTCDateTime)
    consentForStudyEnrollmentFirstYesAuthored = Column("consent_for_study_enrollment_first_yes_authored", UTCDateTime)
    semanticVersionForPrimaryConsent = Column("semantic_version_for_primary_consent", String(100))
    consentForGenomicsROR = Column("consent_for_genomics_ror", Enum(QuestionnaireStatus),
                                   default=QuestionnaireStatus.UNSET)
    consentForGenomicsRORTime = Column("consent_for_genomics_ror_time", UTCDateTime)
    consentForGenomicsRORAuthored = Column("consent_for_genomics_ror_authored", UTCDateTime)
    consentForElectronicHealthRecords = Column(
        "consent_for_electronic_health_records", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    consentForElectronicHealthRecordsTime = Column("consent_for_electronic_health_records_time", UTCDateTime)
    consentForElectronicHealthRecordsAuthored = Column("consent_for_electronic_health_records_authored", UTCDateTime)
    consentForElectronicHealthRecordsFirstYesAuthored = Column(
        "consent_for_electronic_health_records_first_yes_authored",
        UTCDateTime
    )
    consentForDvElectronicHealthRecordsSharing = Column(
        "consent_for_dv_electronic_health_records_sharing",
        Enum(QuestionnaireStatus),
        default=QuestionnaireStatus.UNSET,
    )
    consentForDvElectronicHealthRecordsSharingTime = Column(
        "consent_for_dv_electronic_health_records_sharing_time", UTCDateTime
    )
    consentForDvElectronicHealthRecordsSharingAuthored = Column(
        "consent_for_dv_electronic_health_records_sharing_authored", UTCDateTime
    )
    consentForCABoR = Column("consent_for_cabor", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET)
    consentForCABoRTime = Column("consent_for_cabor_time", UTCDateTime)
    consentForCABoRAuthored = Column("consent_for_cabor_authored", UTCDateTime)
    questionnaireOnOverallHealth = Column(
        "questionnaire_on_overall_health", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnOverallHealthTime = Column("questionnaire_on_overall_health_time", UTCDateTime)
    questionnaireOnOverallHealthAuthored = Column("questionnaire_on_overall_health_authored", UTCDateTime)
    questionnaireOnLifestyle = Column(
        "questionnaire_on_lifestyle", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnLifestyleTime = Column("questionnaire_on_lifestyle_time", UTCDateTime)
    questionnaireOnLifestyleAuthored = Column("questionnaire_on_lifestyle_authored", UTCDateTime)
    questionnaireOnTheBasics = Column(
        "questionnaire_on_the_basics", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnTheBasicsTime = Column("questionnaire_on_the_basics_time", UTCDateTime)
    questionnaireOnTheBasicsAuthored = Column("questionnaire_on_the_basics_authored", UTCDateTime)
    questionnaireOnHealthcareAccess = Column(
        "questionnaire_on_healthcare_access", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnHealthcareAccessTime = Column("questionnaire_on_healthcare_access_time", UTCDateTime)
    questionnaireOnHealthcareAccessAuthored = Column("questionnaire_on_healthcare_access_authored", UTCDateTime)
    questionnaireOnMedicalHistory = Column(
        "questionnaire_on_medical_history", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnMedicalHistoryTime = Column("questionnaire_on_medical_history_time", UTCDateTime)
    questionnaireOnMedicalHistoryAuthored = Column("questionnaire_on_medical_history_authored", UTCDateTime)
    questionnaireOnMedications = Column(
        "questionnaire_on_medications", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnMedicationsTime = Column("questionnaire_on_medications_time", UTCDateTime)
    questionnaireOnMedicationsAuthored = Column("questionnaire_on_medications_authored", UTCDateTime)
    questionnaireOnFamilyHealth = Column(
        "questionnaire_on_family_health", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnFamilyHealthTime = Column("questionnaire_on_family_health_time", UTCDateTime)
    questionnaireOnFamilyHealthAuthored = Column("questionnaire_on_family_health_authored", UTCDateTime)
    questionnaireOnCopeMay = Column(
        "questionnaire_on_cope_may", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnCopeMayTime = Column("questionnaire_on_cope_may_time", UTCDateTime)
    questionnaireOnCopeMayAuthored = Column("questionnaire_on_cope_may_authored", UTCDateTime)
    questionnaireOnCopeJune = Column(
        "questionnaire_on_cope_june", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnCopeJuneTime = Column("questionnaire_on_cope_june_time", UTCDateTime)
    questionnaireOnCopeJuneAuthored = Column("questionnaire_on_cope_june_authored", UTCDateTime)
    questionnaireOnCopeJuly = Column(
        "questionnaire_on_cope_july", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnCopeJulyTime = Column("questionnaire_on_cope_july_time", UTCDateTime)
    questionnaireOnCopeJulyAuthored = Column("questionnaire_on_cope_july_authored", UTCDateTime)
    questionnaireOnDnaProgram = Column(
        "questionnaire_on_dna_program", Enum(QuestionnaireStatus), default=QuestionnaireStatus.UNSET
    )
    questionnaireOnDnaProgramAuthored = Column("questionnaire_on_dna_program_authored", UTCDateTime)

    # Fields for which samples have been received, and at what times.
    sampleStatus1SST8 = Column("sample_status_1sst8", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1SST8Time = Column("sample_status_1sst8_time", UTCDateTime)
    sampleStatus2SST8 = Column("sample_status_2sst8", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus2SST8Time = Column("sample_status_2sst8_time", UTCDateTime)
    sampleStatus1SS08 = Column("sample_status_1ss08", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1SS08Time = Column("sample_status_1ss08_time", UTCDateTime)
    sampleStatus1PST8 = Column("sample_status_1pst8", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1PST8Time = Column("sample_status_1pst8_time", UTCDateTime)
    sampleStatus2PST8 = Column("sample_status_2pst8", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus2PST8Time = Column("sample_status_2pst8_time", UTCDateTime)
    sampleStatus1PS08 = Column("sample_status_1ps08", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1PS08Time = Column("sample_status_1ps08_time", UTCDateTime)
    sampleStatus1HEP4 = Column("sample_status_1hep4", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1HEP4Time = Column("sample_status_1hep4_time", UTCDateTime)
    sampleStatus1ED04 = Column("sample_status_1ed04", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1ED04Time = Column("sample_status_1ed04_time", UTCDateTime)
    sampleStatus1ED10 = Column("sample_status_1ed10", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1ED10Time = Column("sample_status_1ed10_time", UTCDateTime)
    sampleStatus2ED10 = Column("sample_status_2ed10", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus2ED10Time = Column("sample_status_2ed10_time", UTCDateTime)
    sampleStatus1UR10 = Column("sample_status_1ur10", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1UR10Time = Column("sample_status_1ur10_time", UTCDateTime)
    sampleStatus1UR90 = Column("sample_status_1ur90", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1UR90Time = Column("sample_status_1ur90_time", UTCDateTime)
    sampleStatus1SAL = Column("sample_status_1sal", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1SALTime = Column("sample_status_1sal_time", UTCDateTime)
    sampleStatus1SAL2 = Column("sample_status_1sal2", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1SAL2Time = Column("sample_status_1sal2_time", UTCDateTime)
    sampleStatus1ED02 = Column("sample_status_1ed02", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1ED02Time = Column("sample_status_1ed02_time", UTCDateTime)
    sampleStatus1CFD9 = Column("sample_status_1cfd9", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1CFD9Time = Column("sample_status_1cfd9_time", UTCDateTime)
    sampleStatus1PXR2 = Column("sample_status_1pxr2", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatus1PXR2Time = Column("sample_status_1pxr2_time", UTCDateTime)

    # Sample fields for Direct Volunteers
    # These are deprecated in favor of using the standard samplestatus2sal2, etc.
    sampleStatusDV1SAL2 = Column("sample_status_dv_1sal2", Enum(SampleStatus), default=SampleStatus.UNSET)
    sampleStatusDV1SAL2Time = Column("sample_status_dv_1sal2_time", UTCDateTime)

    sampleOrderStatusDV1SAL2 = Column("sample_order_status_dv_1sal2", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatusDV1SAL2Time = Column("sample_order_status_dv_1sal2_time", UTCDateTime)

    # Fields for which samples have been ordered, and at what times.
    sampleOrderStatus1SST8 = Column("sample_order_status_1sst8", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1SST8Time = Column("sample_order_status_1sst8_time", UTCDateTime)
    sampleOrderStatus2SST8 = Column("sample_order_status_2sst8", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus2SST8Time = Column("sample_order_status_2sst8_time", UTCDateTime)
    sampleOrderStatus1SS08 = Column("sample_order_status_1ss08", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1SS08Time = Column("sample_order_status_1ss08_time", UTCDateTime)
    sampleOrderStatus1PST8 = Column("sample_order_status_1pst8", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1PST8Time = Column("sample_order_status_1pst8_time", UTCDateTime)
    sampleOrderStatus2PST8 = Column("sample_order_status_2pst8", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus2PST8Time = Column("sample_order_status_2pst8_time", UTCDateTime)
    sampleOrderStatus1PS08 = Column("sample_order_status_1ps08", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1PS08Time = Column("sample_order_status_1ps08_time", UTCDateTime)
    sampleOrderStatus1HEP4 = Column("sample_order_status_1hep4", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1HEP4Time = Column("sample_order_status_1hep4_time", UTCDateTime)
    sampleOrderStatus1ED04 = Column("sample_order_status_1ed04", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1ED04Time = Column("sample_order_status_1ed04_time", UTCDateTime)
    sampleOrderStatus1ED10 = Column("sample_order_status_1ed10", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1ED10Time = Column("sample_order_status_1ed10_time", UTCDateTime)
    sampleOrderStatus2ED10 = Column("sample_order_status_2ed10", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus2ED10Time = Column("sample_order_status_2ed10_time", UTCDateTime)
    sampleOrderStatus1UR10 = Column("sample_order_status_1ur10", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1UR10Time = Column("sample_order_status_1ur10_time", UTCDateTime)
    sampleOrderStatus1UR90 = Column("sample_order_status_1ur90", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1UR90Time = Column("sample_order_status_1ur90_time", UTCDateTime)
    sampleOrderStatus1SAL = Column("sample_order_status_1sal", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1SALTime = Column("sample_order_status_1sal_time", UTCDateTime)
    sampleOrderStatus1SAL2 = Column("sample_order_status_1sal2", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1SAL2Time = Column("sample_order_status_1sal2_time", UTCDateTime)

    sampleOrderStatus1ED02 = Column("sample_order_status_1ed02", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1ED02Time = Column("sample_order_status_1ed02_time", UTCDateTime)
    sampleOrderStatus1CFD9 = Column("sample_order_status_1cfd9", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1CFD9Time = Column("sample_order_status_1cfd9_time", UTCDateTime)
    sampleOrderStatus1PXR2 = Column("sample_order_status_1pxr2", Enum(OrderStatus), default=OrderStatus.UNSET)
    sampleOrderStatus1PXR2Time = Column("sample_order_status_1pxr2_time", UTCDateTime)

    numCompletedBaselinePPIModules = Column("num_completed_baseline_ppi_modules", SmallInteger, default=0)
    numCompletedPPIModules = Column("num_completed_ppi_modules", SmallInteger, default=0)

    # The number of BiobankStoredSamples recorded for this participant, limited to those samples
    # where testCode is one of the baseline tests (listed in the config).
    numBaselineSamplesArrived = Column("num_baseline_samples_arrived", SmallInteger, default=0)
    samplesToIsolateDNA = Column("samples_to_isolate_dna", Enum(SampleStatus), default=SampleStatus.UNSET)
    # Whether biospecimens have been finalized or not, and the time at which they were
    # finalized.
    biospecimenStatus = Column("biospecimen_status", Enum(OrderStatus), default=OrderStatus.UNSET)
    biospecimenOrderTime = Column("biospecimen_order_time", UTCDateTime)
    biospecimenSourceSiteId = Column("biospecimen_source_site_id", Integer, ForeignKey("site.site_id"))
    biospecimenCollectedSiteId = Column("biospecimen_collected_site_id", Integer, ForeignKey("site.site_id"))
    biospecimenProcessedSiteId = Column("biospecimen_processed_site_id", Integer, ForeignKey("site.site_id"))
    biospecimenFinalizedSiteId = Column("biospecimen_finalized_site_id", Integer, ForeignKey("site.site_id"))

    # EHR status related columns
    ehrStatus = Column("ehr_status", Enum(EhrStatus), default=EhrStatus.NOT_PRESENT)
    ehrReceiptTime = Column("ehr_receipt_time", UTCDateTime)
    ehrUpdateTime = Column("ehr_update_time", UTCDateTime)

    ehrConsentExpireStatus = Column("ehr_consent_expire_status", Enum(ConsentExpireStatus),
                                    default=ConsentExpireStatus.UNSET)
    ehrConsentExpireTime = Column("ehr_consent_expire_time", UTCDateTime)
    ehrConsentExpireAuthored = Column("ehr_consent_expire_authored", UTCDateTime)

    # Withdrawal from the study of the participant's own accord.
    withdrawalStatus = Column("withdrawal_status", Enum(WithdrawalStatus), nullable=False)
    withdrawalReason = Column("withdrawal_reason", Enum(WithdrawalReason))
    withdrawalTime = Column("withdrawal_time", UTCDateTime)
    withdrawalAuthored = Column("withdrawal_authored", UTCDateTime)
    withdrawalReasonJustification = Column("withdrawal_reason_justification", UnicodeText)

    suspensionStatus = Column("suspension_status", Enum(SuspensionStatus), nullable=False)
    suspensionTime = Column("suspension_time", UTCDateTime)
    # The originating resource for participant, this (unlike clientId) will not change.
    participantOrigin = Column("participant_origin", String(80), nullable=False)

    participant = relationship("Participant", back_populates="participantSummary")
    # Note: leaving for future use if we go back to using a relationship to PatientStatus table.
    # # patientStatuses = relationship("PatientStatus", back_populates="participantSummary")
    # patientStatus = relationship(
    #   "PatientStatus",
    #   primaryjoin="PatientStatus.participantId == ParticipantSummary.participantId",
    #   foreign_keys=participantId,
    #   remote_side="PatientStatus.participantId",
    #   viewonly=True,
    #   uselist=True
    # )
    patientStatus = Column("patient_status", JSON, nullable=True, default=list())

    deceasedStatus = Column(
        "deceased_status",
        EnumZeroBased(DeceasedStatus),
        nullable=False,
        default=DeceasedStatus.UNSET
    )
    deceasedAuthored = Column("deceased_authored", UTCDateTime)
    dateOfDeath = Column("date_of_death", Date)

    @declared_attr
    def hpoId(cls):
        return Column("hpo_id", Integer, ForeignKey("hpo.hpo_id"), nullable=False)

    @declared_attr
    def organizationId(cls):
        return Column("organization_id", Integer, ForeignKey("organization.organization_id"))

    @declared_attr
    def siteId(cls):
        return Column("site_id", Integer, ForeignKey("site.site_id"))

    consentCohort = Column("consent_cohort", Enum(ParticipantCohort), default=ParticipantCohort.UNSET)
    cohort2PilotFlag = Column(
        "cohort_2_pilot_flag", Enum(ParticipantCohortPilotFlag), default=ParticipantCohortPilotFlag.UNSET
    )

    retentionEligibleStatus = Column(
        "retention_eligible_status",
        Enum(RetentionStatus),
        Computed(_COMPUTE_RETENTION_ELIGIBLE_SQL, persisted=True)
    )

    retentionEligibleTime = Column(
        "retention_eligible_time", UTCDateTime, Computed(_COMPUTE_RETENTION_ELIGIBLE_TIME_SQL, persisted=True)
    )


Index("participant_summary_biobank_id", ParticipantSummary.biobankId)
Index("participant_summary_ln_dob", ParticipantSummary.lastName, ParticipantSummary.dateOfBirth)
Index(
    "participant_summary_ln_dob_zip",
    ParticipantSummary.lastName,
    ParticipantSummary.dateOfBirth,
    ParticipantSummary.zipCode,
)
Index(
    "participant_summary_ln_dob_fn",
    ParticipantSummary.lastName,
    ParticipantSummary.dateOfBirth,
    ParticipantSummary.firstName,
)
Index("participant_summary_hpo", ParticipantSummary.hpoId)
Index("participant_summary_hpo_fn", ParticipantSummary.hpoId, ParticipantSummary.firstName)
Index("participant_summary_hpo_ln", ParticipantSummary.hpoId, ParticipantSummary.lastName)
Index("participant_summary_hpo_dob", ParticipantSummary.hpoId, ParticipantSummary.dateOfBirth)
Index("participant_summary_hpo_race", ParticipantSummary.hpoId, ParticipantSummary.race)
Index("participant_summary_hpo_zip", ParticipantSummary.hpoId, ParticipantSummary.zipCode)
Index("participant_summary_hpo_status", ParticipantSummary.hpoId, ParticipantSummary.enrollmentStatus)
Index("participant_summary_hpo_consent", ParticipantSummary.hpoId, ParticipantSummary.consentForStudyEnrollment)
Index(
    "participant_summary_hpo_num_baseline_ppi",
    ParticipantSummary.hpoId,
    ParticipantSummary.numCompletedBaselinePPIModules,
)
Index(
    "participant_summary_hpo_num_baseline_samples",
    ParticipantSummary.hpoId,
    ParticipantSummary.numBaselineSamplesArrived,
)
Index(
    "participant_summary_hpo_withdrawal_status_time",
    ParticipantSummary.hpoId,
    ParticipantSummary.withdrawalStatus,
    ParticipantSummary.withdrawalTime,
)
Index("participant_summary_last_modified", ParticipantSummary.hpoId, ParticipantSummary.lastModified)


class ParticipantGenderAnswers(Base):
    __tablename__ = "participant_gender_answers"
    id = Column("id", Integer, primary_key=True, autoincrement=True, nullable=False)
    participantId = Column("participant_id", Integer, ForeignKey("participant.participant_id"), autoincrement=False)
    created = Column("created", DateTime, nullable=True)
    modified = Column("modified", DateTime, nullable=True)
    codeId = Column("code_id", Integer, ForeignKey("code.code_id"), nullable=False)


event.listen(ParticipantGenderAnswers, "before_insert", model_insert_listener)
event.listen(ParticipantGenderAnswers, "before_update", model_update_listener)


class ParticipantRaceAnswers(Base):
    __tablename__ = "participant_race_answers"
    id = Column("id", Integer, primary_key=True, autoincrement=True, nullable=False)
    participantId = Column("participant_id", Integer, ForeignKey("participant.participant_id"), autoincrement=False)
    created = Column("created", DateTime, nullable=True)
    modified = Column("modified", DateTime, nullable=True)
    codeId = Column("code_id", Integer, ForeignKey("code.code_id"), nullable=False)


event.listen(ParticipantRaceAnswers, "before_insert", model_insert_listener)
event.listen(ParticipantRaceAnswers, "before_update", model_update_listener)
