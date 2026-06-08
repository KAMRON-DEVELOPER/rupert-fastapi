from datetime import date

from src.apps.shared.schemas import ResponseSchema
from src.apps.shared.schemas.enums import (
    CompanyType,
    JobSearchStatus,
    Specialization,
    VacancyStatus,
)


class BucketBase(ResponseSchema):
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


class DailyActiveUsersBucket(ResponseSchema):
    count: int
    anonymous_count: int
    date: date


class UsersStats(ResponseSchema):
    total: int
    looking_for_job_count: int
    looking_for_job_percentage: float
    dau_chart: list[DailyActiveUsersBucket]
    by_job_search_status: list[JobSearchStatusBucket]
    by_specialization: list[SpecializationBucket]


class VacanciesStats(ResponseSchema):
    total: int
    open: int
    by_status: list[VacancyStatusBucket]
    by_specialization: list[SpecializationBucket]


class CompaniesStats(ResponseSchema):
    total: int
    by_type: list[CompanyTypeBucket]


class Stats(ResponseSchema):
    users: UsersStats
    vacancies: VacanciesStats
    companies: CompaniesStats
