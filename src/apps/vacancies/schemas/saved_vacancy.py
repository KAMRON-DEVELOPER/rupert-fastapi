from src.apps.shared.schemas import BaseOut
from src.apps.vacancies.schemas.vacancy import VacancyCardOut


# ---------------------------------------------------------------------------
# Saved Vacancy
# ---------------------------------------------------------------------------
class SavedVacancyOut(BaseOut):
    vacancy: VacancyCardOut
