from src.apps.shared.enums import CompanyType, JobSearchStatus, Specialization, VacancyStatus
from src.apps.shared.schemas import CamelCaseOut


class BucketBase(CamelCaseOut):
    count: int
    percentage: float


class JobSearchStatusBucket(BucketBase):
    key: JobSearchStatus


class SpecializationBucket(BucketBase):
    key: Specialization


class VacancyStatusBucket(BucketBase):
    key: VacancyStatus


class CompanyTypeBucket(BucketBase):
    key: CompanyType


class UsersStats(CamelCaseOut):
    total: int
    looking_for_job_count: int
    looking_for_job_percentage: float

    by_job_search_status: list[JobSearchStatusBucket]
    by_specialization: list[SpecializationBucket]


class VacanciesStats(CamelCaseOut):
    total: int
    open: int
    by_status: list[VacancyStatusBucket]
    by_specialization: list[SpecializationBucket]


class CompaniesStats(CamelCaseOut):
    total: int
    by_type: list[CompanyTypeBucket]


class Stats(CamelCaseOut):
    users: UsersStats
    vacancies: VacanciesStats
    companies: CompaniesStats
