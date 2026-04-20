import asyncio
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.apps.models import (
    CompanyMemberModel,
    CompanyModel,
    ResumeModel,
    ResumeSkillLink,
    SkillModel,
    UserModel,
    UserSkillLink,
    VacancyModel,
    VacancySkillLink,
    WorkExperienceModel,
)
from src.apps.shared.enums import (
    CompanyMemberRole,
    CompanyStatus,
    CompanyType,
    EmploymentType,
    FollowPolicy,
    JobSearchStatus,
    PaymentFrequency,
    ProficiencyLevel,
    SalaryCurrency,
    Specialization,
    SubmissionType,
    UserRole,
    UserStatus,
    VacancyStatus,
    WorkFormat,
)
from src.core.settings import get_settings

# ─────────────────────────────────────────────────────────────────────────────
# Raw data tables
# ─────────────────────────────────────────────────────────────────────────────

ALL_SKILLS = [
    # Languages
    "Python",
    "JavaScript",
    "TypeScript",
    "Go",
    "Rust",
    "Java",
    "Kotlin",
    "Swift",
    "Dart",
    "C++",
    "PHP",
    # Web frameworks / libraries
    "FastAPI",
    "Django",
    "Flask",
    "Node.js",
    "Express.js",
    "React",
    "Vue.js",
    "Next.js",
    "Nuxt.js",
    "Angular",
    "Svelte",
    # Mobile
    "React Native",
    "Flutter",
    # Databases
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",
    "SQLite",
    "ClickHouse",
    # Cloud & DevOps
    "Docker",
    "Kubernetes",
    "Terraform",
    "AWS",
    "GCP",
    "Azure",
    "CI/CD",
    "GitHub Actions",
    "Linux",
    "Nginx",
    # Data & ML
    "Machine Learning",
    "PyTorch",
    "TensorFlow",
    "Pandas",
    "NumPy",
    "Apache Spark",
    "Apache Kafka",
    "Airflow",
    # APIs & architecture
    "GraphQL",
    "REST API",
    "gRPC",
    "WebSocket",
    "Microservices",
    # Other
    "Git",
    "RabbitMQ",
    "Celery",
    "Selenium",
    "Playwright",
    # Extra (referenced in link tables)
    "Dart",
    "Firebase",
    "Android",
    "Spring Boot",
]

# ── Users ─────────────────────────────────────────────────────────────────────
# (first, last, email, country, city, specialization, headline, job_search_status, github_url, linkedin_url)
USERS = [
    (
        "Alex",
        "Carter",
        "alex.carter@example.com",
        "USA",
        "San Francisco",
        Specialization.backend,
        "Senior Python Engineer · FastAPI & PostgreSQL",
        JobSearchStatus.open_to_offers,
        "https://github.com/alexcarter",
        "https://linkedin.com/in/alexcarter",
    ),
    (
        "Maria",
        "Santos",
        "maria.santos@example.com",
        "Brazil",
        "São Paulo",
        Specialization.fullstack,
        "Full-Stack Dev · React + FastAPI",
        JobSearchStatus.actively_looking,
        "https://github.com/mariasantos",
        "https://linkedin.com/in/mariasantos",
    ),
    (
        "James",
        "Chen",
        "james.chen@example.com",
        "UK",
        "London",
        Specialization.backend,
        "Go & gRPC Backend Engineer · 6 YoE",
        JobSearchStatus.not_looking,
        "https://github.com/jameschen",
        None,
    ),
    (
        "Priya",
        "Nair",
        "priya.nair@example.com",
        "India",
        "Bangalore",
        Specialization.frontend,
        "React / Next.js · UI Performance & Accessibility",
        JobSearchStatus.open_to_offers,
        "https://github.com/priyanair",
        "https://linkedin.com/in/priyanair",
    ),
    (
        "Lucas",
        "Müller",
        "lucas.muller@example.com",
        "Germany",
        "Berlin",
        Specialization.devops,
        "Platform Engineer · K8s · Terraform · AWS",
        JobSearchStatus.not_looking,
        "https://github.com/lucasmuller",
        "https://linkedin.com/in/lucasmuller",
    ),
    (
        "Sofia",
        "Rossi",
        "sofia.rossi@example.com",
        "Italy",
        "Milan",
        Specialization.frontend,
        "Vue.js & TypeScript Specialist",
        JobSearchStatus.actively_looking,
        None,
        "https://linkedin.com/in/sofiarossi",
    ),
    (
        "David",
        "Kim",
        "david.kim@example.com",
        "South Korea",
        "Seoul",
        Specialization.cross_platform_mobile,
        "React Native & iOS Developer",
        JobSearchStatus.open_to_offers,
        "https://github.com/davidkim",
        "https://linkedin.com/in/davidkim",
    ),
    (
        "Aisha",
        "Okonkwo",
        "aisha.okonkwo@example.com",
        "Nigeria",
        "Lagos",
        Specialization.backend,
        "Node.js Microservices Engineer",
        JobSearchStatus.actively_looking,
        "https://github.com/aishaokonkwo",
        None,
    ),
    (
        "Nicolás",
        "Vargas",
        "nicolas.vargas@example.com",
        "Colombia",
        "Bogotá",
        Specialization.fullstack,
        "Django · React · PostgreSQL",
        JobSearchStatus.open_to_offers,
        "https://github.com/nicolasvargas",
        "https://linkedin.com/in/nicolasvargas",
    ),
    (
        "Emma",
        "Larsson",
        "emma.larsson@example.com",
        "Sweden",
        "Stockholm",
        Specialization.machine_learning,
        "ML Engineer · NLP · PyTorch · Spotify alumni",
        JobSearchStatus.not_looking,
        "https://github.com/emmalarsson",
        "https://linkedin.com/in/emmalarsson",
    ),
    (
        "Omar",
        "Hassan",
        "omar.hassan@example.com",
        "UAE",
        "Dubai",
        Specialization.backend,
        "Python / FastAPI API Architect · 8 YoE",
        JobSearchStatus.open_to_offers,
        "https://github.com/omarhassan",
        "https://linkedin.com/in/omarhassan",
    ),
    (
        "Yuki",
        "Tanaka",
        "yuki.tanaka@example.com",
        "Japan",
        "Tokyo",
        Specialization.frontend,
        "React · Accessibility-first Development",
        JobSearchStatus.actively_looking,
        "https://github.com/yukitanaka",
        "https://linkedin.com/in/yukitanaka",
    ),
    (
        "Tomáš",
        "Novák",
        "tomas.novak@example.com",
        "Czech Republic",
        "Prague",
        Specialization.systems,
        "Rust & Python Systems Engineer · JetBrains alumni",
        JobSearchStatus.not_looking,
        "https://github.com/tomasnovak",
        None,
    ),
    (
        "Lena",
        "Petrova",
        "lena.petrova@example.com",
        "Russia",
        "Moscow",
        Specialization.fullstack,
        "Fullstack · Next.js · Nest.js · TypeScript",
        JobSearchStatus.actively_looking,
        "https://github.com/lenapetrova",
        "https://linkedin.com/in/lenapetrova",
    ),
    (
        "Kwame",
        "Asante",
        "kwame.asante@example.com",
        "Ghana",
        "Accra",
        Specialization.cross_platform_mobile,
        "Flutter Developer · 4 YoE",
        JobSearchStatus.open_to_offers,
        "https://github.com/kwameasante",
        "https://linkedin.com/in/kwameasante",
    ),
    (
        "Ana",
        "López",
        "ana.lopez@example.com",
        "Spain",
        "Madrid",
        Specialization.cloud,
        "Cloud Platform Engineer · GCP & Terraform",
        JobSearchStatus.not_looking,
        None,
        "https://linkedin.com/in/analopez",
    ),
    (
        "Ben",
        "Thompson",
        "ben.thompson@example.com",
        "Australia",
        "Sydney",
        Specialization.backend,
        "Java / Kotlin Microservices · Atlassian alumni",
        JobSearchStatus.actively_looking,
        "https://github.com/benthompson",
        "https://linkedin.com/in/benthompson",
    ),
    (
        "Fatima",
        "Al-Rashid",
        "fatima.alrashid@example.com",
        "Saudi Arabia",
        "Riyadh",
        Specialization.data_engineering,
        "Data Engineer · Kafka · Spark · Elasticsearch",
        JobSearchStatus.open_to_offers,
        None,
        "https://linkedin.com/in/fatimaalrashid",
    ),
    (
        "Sven",
        "Berg",
        "sven.berg@example.com",
        "Norway",
        "Oslo",
        Specialization.backend,
        "GraphQL API Specialist · Node.js",
        JobSearchStatus.not_looking,
        "https://github.com/svenberg",
        None,
    ),
    (
        "Mei",
        "Zhang",
        "mei.zhang@example.com",
        "China",
        "Shanghai",
        Specialization.frontend,
        "Senior React Developer · Design Systems",
        JobSearchStatus.actively_looking,
        "https://github.com/meizhang",
        "https://linkedin.com/in/meizhang",
    ),
    (
        "Carlos",
        "Mendez",
        "carlos.mendez@example.com",
        "Mexico",
        "Mexico City",
        Specialization.fullstack,
        "FastAPI · React · Docker",
        JobSearchStatus.open_to_offers,
        "https://github.com/carlosmendez",
        "https://linkedin.com/in/carlosmendez",
    ),
    (
        "Ingrid",
        "Hansen",
        "ingrid.hansen@example.com",
        "Denmark",
        "Copenhagen",
        Specialization.sre,
        "SRE · Observability · Prometheus · Grafana",
        JobSearchStatus.actively_looking,
        "https://github.com/ingridhansen",
        "https://linkedin.com/in/ingridhansen",
    ),
    (
        "Raj",
        "Patel",
        "raj.patel@example.com",
        "India",
        "Mumbai",
        Specialization.backend,
        "Python · AWS · Serverless",
        JobSearchStatus.not_looking,
        "https://github.com/rajpatel",
        "https://linkedin.com/in/rajpatel",
    ),
    (
        "Chiara",
        "Ferrari",
        "chiara.ferrari@example.com",
        "Italy",
        "Rome",
        Specialization.android,
        "Android & Kotlin Developer",
        JobSearchStatus.open_to_offers,
        "https://github.com/chiaraferrari",
        "https://linkedin.com/in/chiaraferrari",
    ),
    (
        "Aaron",
        "Mitchell",
        "aaron.mitchell@example.com",
        "USA",
        "Austin",
        Specialization.machine_learning,
        "Senior ML Engineer · Recommendation Systems",
        JobSearchStatus.actively_looking,
        "https://github.com/aaronmitchell",
        "https://linkedin.com/in/aaronmitchell",
    ),
]

# ── User skills ───────────────────────────────────────────────────────────────
# (skill_name, proficiency, days_since_last_used)
USER_SKILLS: dict[str, list[tuple[str, ProficiencyLevel, int]]] = {
    "alex.carter@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("FastAPI", ProficiencyLevel.expert, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.advanced, 0),
        ("Redis", ProficiencyLevel.intermediate, 30),
        ("Celery", ProficiencyLevel.intermediate, 60),
    ],
    "maria.santos@example.com": [
        ("React", ProficiencyLevel.advanced, 0),
        ("FastAPI", ProficiencyLevel.intermediate, 0),
        ("TypeScript", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.intermediate, 30),
        ("Docker", ProficiencyLevel.beginner, 90),
    ],
    "james.chen@example.com": [
        ("Go", ProficiencyLevel.expert, 0),
        ("gRPC", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Kubernetes", ProficiencyLevel.intermediate, 60),
        ("Python", ProficiencyLevel.intermediate, 180),
    ],
    "priya.nair@example.com": [
        ("React", ProficiencyLevel.expert, 0),
        ("TypeScript", ProficiencyLevel.expert, 0),
        ("Next.js", ProficiencyLevel.advanced, 0),
        ("GraphQL", ProficiencyLevel.intermediate, 60),
        ("REST API", ProficiencyLevel.advanced, 0),
    ],
    "lucas.muller@example.com": [
        ("Kubernetes", ProficiencyLevel.expert, 0),
        ("Terraform", ProficiencyLevel.expert, 0),
        ("AWS", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.expert, 0),
        ("CI/CD", ProficiencyLevel.advanced, 0),
        ("Linux", ProficiencyLevel.expert, 0),
    ],
    "sofia.rossi@example.com": [
        ("Vue.js", ProficiencyLevel.expert, 0),
        ("TypeScript", ProficiencyLevel.advanced, 0),
        ("JavaScript", ProficiencyLevel.expert, 0),
        ("Nuxt.js", ProficiencyLevel.advanced, 0),
        ("REST API", ProficiencyLevel.intermediate, 30),
    ],
    "david.kim@example.com": [
        ("React Native", ProficiencyLevel.expert, 0),
        ("Swift", ProficiencyLevel.advanced, 0),
        ("JavaScript", ProficiencyLevel.advanced, 0),
        ("TypeScript", ProficiencyLevel.intermediate, 30),
        ("REST API", ProficiencyLevel.intermediate, 0),
    ],
    "aisha.okonkwo@example.com": [
        ("Node.js", ProficiencyLevel.expert, 0),
        ("Express.js", ProficiencyLevel.advanced, 0),
        ("MongoDB", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.intermediate, 0),
        ("JavaScript", ProficiencyLevel.expert, 0),
    ],
    "nicolas.vargas@example.com": [
        ("Python", ProficiencyLevel.advanced, 0),
        ("Django", ProficiencyLevel.advanced, 0),
        ("React", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("REST API", ProficiencyLevel.advanced, 0),
    ],
    "emma.larsson@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("PyTorch", ProficiencyLevel.expert, 0),
        ("Machine Learning", ProficiencyLevel.expert, 0),
        ("Pandas", ProficiencyLevel.advanced, 0),
        ("NumPy", ProficiencyLevel.advanced, 0),
        ("Apache Spark", ProficiencyLevel.intermediate, 90),
    ],
    "omar.hassan@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("FastAPI", ProficiencyLevel.expert, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Redis", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.advanced, 0),
    ],
    "yuki.tanaka@example.com": [
        ("React", ProficiencyLevel.expert, 0),
        ("TypeScript", ProficiencyLevel.advanced, 0),
        ("Next.js", ProficiencyLevel.advanced, 0),
        ("GraphQL", ProficiencyLevel.intermediate, 60),
        ("JavaScript", ProficiencyLevel.expert, 0),
    ],
    "tomas.novak@example.com": [
        ("Rust", ProficiencyLevel.expert, 0),
        ("Python", ProficiencyLevel.advanced, 60),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("gRPC", ProficiencyLevel.intermediate, 120),
        ("C++", ProficiencyLevel.intermediate, 365),
    ],
    "lena.petrova@example.com": [
        ("TypeScript", ProficiencyLevel.expert, 0),
        ("Next.js", ProficiencyLevel.advanced, 0),
        ("Node.js", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.intermediate, 30),
        ("React", ProficiencyLevel.advanced, 0),
    ],
    "kwame.asante@example.com": [
        ("Flutter", ProficiencyLevel.expert, 0),
        ("Dart", ProficiencyLevel.expert, 0),
        ("Firebase", ProficiencyLevel.advanced, 0),
        ("REST API", ProficiencyLevel.intermediate, 0),
    ],
    "ana.lopez@example.com": [
        ("GCP", ProficiencyLevel.expert, 0),
        ("Terraform", ProficiencyLevel.expert, 0),
        ("Kubernetes", ProficiencyLevel.advanced, 0),
        ("CI/CD", ProficiencyLevel.expert, 0),
        ("Docker", ProficiencyLevel.advanced, 0),
        ("Linux", ProficiencyLevel.expert, 0),
    ],
    "ben.thompson@example.com": [
        ("Java", ProficiencyLevel.expert, 0),
        ("Kotlin", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Apache Kafka", ProficiencyLevel.intermediate, 60),
        ("Docker", ProficiencyLevel.intermediate, 0),
    ],
    "fatima.alrashid@example.com": [
        ("Python", ProficiencyLevel.advanced, 0),
        ("Apache Kafka", ProficiencyLevel.expert, 0),
        ("Elasticsearch", ProficiencyLevel.advanced, 0),
        ("Apache Spark", ProficiencyLevel.advanced, 0),
        ("Airflow", ProficiencyLevel.intermediate, 30),
    ],
    "sven.berg@example.com": [
        ("Node.js", ProficiencyLevel.expert, 0),
        ("GraphQL", ProficiencyLevel.expert, 0),
        ("TypeScript", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.intermediate, 30),
        ("Redis", ProficiencyLevel.intermediate, 60),
    ],
    "mei.zhang@example.com": [
        ("React", ProficiencyLevel.expert, 0),
        ("TypeScript", ProficiencyLevel.expert, 0),
        ("Next.js", ProficiencyLevel.advanced, 0),
        ("JavaScript", ProficiencyLevel.expert, 0),
        ("GraphQL", ProficiencyLevel.intermediate, 90),
    ],
    "carlos.mendez@example.com": [
        ("Python", ProficiencyLevel.advanced, 0),
        ("FastAPI", ProficiencyLevel.advanced, 0),
        ("React", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.intermediate, 0),
    ],
    "ingrid.hansen@example.com": [
        ("Kubernetes", ProficiencyLevel.advanced, 0),
        ("AWS", ProficiencyLevel.expert, 0),
        ("Linux", ProficiencyLevel.expert, 0),
        ("CI/CD", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.advanced, 0),
    ],
    "raj.patel@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("AWS", ProficiencyLevel.expert, 0),
        ("FastAPI", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.intermediate, 0),
    ],
    "chiara.ferrari@example.com": [
        ("Kotlin", ProficiencyLevel.expert, 0),
        ("Java", ProficiencyLevel.advanced, 60),
        ("Android", ProficiencyLevel.expert, 0),
        ("REST API", ProficiencyLevel.advanced, 0),
    ],
    "aaron.mitchell@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("Machine Learning", ProficiencyLevel.expert, 0),
        ("PyTorch", ProficiencyLevel.expert, 0),
        ("TensorFlow", ProficiencyLevel.advanced, 0),
        ("Pandas", ProficiencyLevel.advanced, 0),
        ("NumPy", ProficiencyLevel.advanced, 0),
    ],
}

# ── Work experiences ──────────────────────────────────────────────────────────
# (email, company_name, location, position, description, started_at, ended_at)
WORK_EXPERIENCES = [
    (
        "alex.carter@example.com",
        "Stripe",
        "San Francisco, USA",
        "Senior Backend Engineer",
        "Led the Python platform team building payment APIs serving 10M+ daily transactions.",
        date(2021, 3, 1),
        None,
    ),
    (
        "alex.carter@example.com",
        "Twilio",
        "San Francisco, USA",
        "Software Engineer",
        "Built developer-facing REST and WebSocket APIs in Python/Flask.",
        date(2018, 6, 1),
        date(2021, 2, 28),
    ),
    (
        "maria.santos@example.com",
        "Nubank",
        "São Paulo, Brazil",
        "Full-Stack Engineer",
        "Developed customer-facing features for digital banking app with React and FastAPI.",
        date(2020, 1, 1),
        None,
    ),
    ("james.chen@example.com", "Cloudflare", "London, UK", "Software Engineer (Go)", "Worked on CDN edge nodes and routing infrastructure in Go.", date(2019, 7, 1), None),
    ("priya.nair@example.com", "Flipkart", "Bangalore, India", "Frontend Engineer", "Owned product listing and checkout pages serving 50M+ monthly users.", date(2020, 4, 1), None),
    (
        "priya.nair@example.com",
        "Infosys",
        "Bangalore, India",
        "Junior Frontend Developer",
        "Delivered React UI components for enterprise clients.",
        date(2018, 7, 1),
        date(2020, 3, 31),
    ),
    (
        "lucas.muller@example.com",
        "Zalando",
        "Berlin, Germany",
        "DevOps Engineer",
        "Managed 200-node Kubernetes clusters across EU data centres with Terraform.",
        date(2018, 9, 1),
        None,
    ),
    (
        "sofia.rossi@example.com",
        "Lastminute.com",
        "Milan, Italy",
        "Frontend Developer",
        "Built Vue.js booking flows for flights and hotels used by 5M+ monthly visitors.",
        date(2021, 1, 1),
        None,
    ),
    ("david.kim@example.com", "Kakao", "Seoul, South Korea", "Mobile Developer", "Developed and shipped React Native features for KakaoTalk mobile app.", date(2020, 5, 1), None),
    (
        "aisha.okonkwo@example.com",
        "Paystack",
        "Lagos, Nigeria",
        "Backend Developer",
        "Developed Node.js payment processing services handling high-volume transactions.",
        date(2021, 5, 1),
        None,
    ),
    (
        "nicolas.vargas@example.com",
        "Rappi",
        "Bogotá, Colombia",
        "Full-Stack Developer",
        "Maintained Django REST APIs and React dashboards for the operations team.",
        date(2020, 2, 1),
        None,
    ),
    ("emma.larsson@example.com", "Spotify", "Stockholm, Sweden", "ML Engineer", "Worked on podcast and music recommendation models serving 500M+ users.", date(2020, 6, 1), None),
    (
        "emma.larsson@example.com",
        "KTH Royal Institute",
        "Stockholm, Sweden",
        "Research Assistant",
        "NLP research on Swedish-language models and text classification.",
        date(2018, 9, 1),
        date(2020, 5, 31),
    ),
    (
        "omar.hassan@example.com",
        "Careem",
        "Dubai, UAE",
        "Senior Backend Engineer",
        "Built ride-hailing APIs handling millions of daily requests with FastAPI and PostgreSQL.",
        date(2019, 3, 1),
        None,
    ),
    (
        "yuki.tanaka@example.com",
        "Mercari",
        "Tokyo, Japan",
        "Frontend Engineer",
        "Led accessibility overhaul of the main marketplace, achieving WCAG 2.1 AA compliance.",
        date(2021, 7, 1),
        None,
    ),
    ("tomas.novak@example.com", "JetBrains", "Prague, Czech Rep.", "Systems Engineer", "Developed Rust-based language server components and IDE plugins.", date(2019, 1, 1), None),
    ("lena.petrova@example.com", "VK", "Moscow, Russia", "Full-Stack Developer", "Built Next.js SSR apps and Nest.js APIs for social media platform.", date(2020, 9, 1), None),
    (
        "kwame.asante@example.com",
        "mPharma",
        "Accra, Ghana",
        "Mobile Developer (Flutter)",
        "Developed Flutter app for pharmacy inventory management across 6 African countries.",
        date(2021, 3, 1),
        None,
    ),
    (
        "ana.lopez@example.com",
        "Telefónica",
        "Madrid, Spain",
        "Cloud Engineer",
        "Led GCP migration of legacy telecom systems, reducing infrastructure costs by 40%.",
        date(2019, 5, 1),
        None,
    ),
    (
        "ben.thompson@example.com",
        "Atlassian",
        "Sydney, Australia",
        "Backend Engineer",
        "Worked on Jira Service Management microservices in Kotlin and Java.",
        date(2019, 5, 1),
        None,
    ),
    (
        "fatima.alrashid@example.com",
        "SABIC",
        "Riyadh, Saudi Arabia",
        "Data Engineer",
        "Designed Kafka + Spark pipelines processing 500GB/day of industrial IoT sensor data.",
        date(2020, 1, 1),
        None,
    ),
    ("sven.berg@example.com", "Equinor", "Oslo, Norway", "Backend Engineer", "Built GraphQL APIs for maritime and energy data platforms.", date(2019, 4, 1), None),
    (
        "mei.zhang@example.com",
        "ByteDance",
        "Shanghai, China",
        "Senior Frontend Engineer",
        "Built internal design system used across 30+ internal products.",
        date(2020, 8, 1),
        None,
    ),
    (
        "carlos.mendez@example.com",
        "Kavak",
        "Mexico City, Mexico",
        "Full-Stack Engineer",
        "Built FastAPI services and React dashboards for used-car marketplace operations.",
        date(2021, 2, 1),
        None,
    ),
    (
        "ingrid.hansen@example.com",
        "Maersk",
        "Copenhagen, Denmark",
        "SRE",
        "Maintained 99.99% uptime for logistics APIs; implemented Prometheus/Grafana observability.",
        date(2020, 3, 1),
        None,
    ),
    (
        "raj.patel@example.com",
        "Tata Consultancy",
        "Mumbai, India",
        "Cloud Engineer",
        "Architected AWS Lambda-based event-driven solutions for banking clients.",
        date(2019, 6, 1),
        None,
    ),
    ("chiara.ferrari@example.com", "Mediaset", "Milan, Italy", "Android Developer", "Built and maintained Android streaming app with 2M+ downloads.", date(2021, 1, 1), None),
    (
        "aaron.mitchell@example.com",
        "Indeed",
        "Austin, USA",
        "Senior ML Engineer",
        "Developed recommendation models for job matching; shipped improvements increasing CTR by 18%.",
        date(2020, 2, 1),
        None,
    ),
    (
        "aaron.mitchell@example.com",
        "Dell Technologies",
        "Austin, USA",
        "Data Scientist",
        "Built predictive churn models and A/B testing infrastructure for enterprise SaaS products.",
        date(2017, 6, 1),
        date(2020, 1, 31),
    ),
]

# ── Resumes ───────────────────────────────────────────────────────────────────
# (email, title, summary, spec, sal_min, sal_max, currency, work_format, employment_type, country, city)
RESUMES = [
    (
        "alex.carter@example.com",
        "Senior Backend Engineer",
        "8 years of Python expertise. Proven track record at Stripe and Twilio. Deep knowledge of FastAPI, PostgreSQL, and distributed systems. Seeking Staff/Principal roles.",
        Specialization.backend,
        120000,
        160000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "USA",
        "San Francisco",
    ),
    (
        "maria.santos@example.com",
        "Full-Stack Engineer (React+Python)",
        "Versatile full-stack developer with strong product sense. Comfortable owning both the React frontend and FastAPI backend. Open to seed-stage startups and scale-ups.",
        Specialization.fullstack,
        60000,
        90000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "Brazil",
        "São Paulo",
    ),
    (
        "james.chen@example.com",
        "Backend Engineer (Go)",
        "Go developer focused on distributed systems, microservices, and gRPC. Former Cloudflare engineer. Writes clean, well-tested code.",
        Specialization.backend,
        100000,
        140000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "UK",
        "London",
    ),
    (
        "priya.nair@example.com",
        "Senior Frontend Engineer",
        "React/Next.js specialist with a passion for web performance and accessibility. Have led frontend architecture for products serving tens of millions of users.",
        Specialization.frontend,
        90000,
        120000,
        SalaryCurrency.USD,
        WorkFormat.hybrid,
        EmploymentType.full_time,
        "India",
        "Bangalore",
    ),
    (
        "emma.larsson@example.com",
        "ML Engineer",
        "NLP & recommendation systems specialist. Shipped production ML models at Spotify. Strong Python, PyTorch, and MLOps background.",
        Specialization.machine_learning,
        130000,
        170000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "Sweden",
        "Stockholm",
    ),
    (
        "omar.hassan@example.com",
        "Senior Python/FastAPI Engineer",
        "8+ years building scalable Python APIs. Led backend teams at Careem. Expertise in async Python, PostgreSQL query optimisation, and API design.",
        Specialization.backend,
        100000,
        135000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "UAE",
        "Dubai",
    ),
    (
        "lucas.muller@example.com",
        "Senior DevOps / Platform Engineer",
        "Kubernetes and Terraform expert. Built and scaled the DevOps practice at Zalando. Deep AWS experience and IaC advocacy.",
        Specialization.devops,
        110000,
        145000,
        SalaryCurrency.EUR,
        WorkFormat.hybrid,
        EmploymentType.full_time,
        "Germany",
        "Berlin",
    ),
    (
        "kwame.asante@example.com",
        "Flutter Developer",
        "Flutter specialist with 4 years of experience. Shipped 5 cross-platform apps. Strong Dart skills and eye for pixel-perfect UI.",
        Specialization.cross_platform_mobile,
        50000,
        70000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "Ghana",
        "Accra",
    ),
    (
        "carlos.mendez@example.com",
        "Full-Stack Engineer (FastAPI+React)",
        "Hands-on full-stack engineer comfortable from DB schema to React component. Enjoys product-focused engineering at LatAm startups.",
        Specialization.fullstack,
        55000,
        75000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "Mexico",
        "Mexico City",
    ),
    (
        "aaron.mitchell@example.com",
        "Senior ML Engineer",
        "Recommendation systems and ranking model specialist. Former Indeed. Expert in PyTorch, offline/online experimentation, and production ML.",
        Specialization.machine_learning,
        140000,
        180000,
        SalaryCurrency.USD,
        WorkFormat.remote,
        EmploymentType.full_time,
        "USA",
        "Austin",
    ),
]

RESUME_SKILLS: dict[str, list[tuple[str, ProficiencyLevel, int]]] = {
    "alex.carter@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("FastAPI", ProficiencyLevel.expert, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.advanced, 0),
        ("Redis", ProficiencyLevel.intermediate, 30),
    ],
    "maria.santos@example.com": [
        ("React", ProficiencyLevel.advanced, 0),
        ("FastAPI", ProficiencyLevel.intermediate, 0),
        ("TypeScript", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.intermediate, 30),
    ],
    "james.chen@example.com": [
        ("Go", ProficiencyLevel.expert, 0),
        ("gRPC", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Kubernetes", ProficiencyLevel.intermediate, 60),
    ],
    "priya.nair@example.com": [
        ("React", ProficiencyLevel.expert, 0),
        ("TypeScript", ProficiencyLevel.expert, 0),
        ("Next.js", ProficiencyLevel.advanced, 0),
        ("GraphQL", ProficiencyLevel.intermediate, 60),
    ],
    "emma.larsson@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("PyTorch", ProficiencyLevel.expert, 0),
        ("Machine Learning", ProficiencyLevel.expert, 0),
        ("Pandas", ProficiencyLevel.advanced, 0),
    ],
    "omar.hassan@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("FastAPI", ProficiencyLevel.expert, 0),
        ("PostgreSQL", ProficiencyLevel.advanced, 0),
        ("Redis", ProficiencyLevel.advanced, 0),
    ],
    "lucas.muller@example.com": [
        ("Kubernetes", ProficiencyLevel.expert, 0),
        ("Terraform", ProficiencyLevel.expert, 0),
        ("AWS", ProficiencyLevel.advanced, 0),
        ("Docker", ProficiencyLevel.expert, 0),
    ],
    "kwame.asante@example.com": [("Flutter", ProficiencyLevel.expert, 0), ("Dart", ProficiencyLevel.expert, 0), ("Firebase", ProficiencyLevel.advanced, 0)],
    "carlos.mendez@example.com": [
        ("Python", ProficiencyLevel.advanced, 0),
        ("FastAPI", ProficiencyLevel.advanced, 0),
        ("React", ProficiencyLevel.advanced, 0),
        ("PostgreSQL", ProficiencyLevel.intermediate, 0),
    ],
    "aaron.mitchell@example.com": [
        ("Python", ProficiencyLevel.expert, 0),
        ("Machine Learning", ProficiencyLevel.expert, 0),
        ("PyTorch", ProficiencyLevel.expert, 0),
        ("TensorFlow", ProficiencyLevel.advanced, 0),
    ],
}

# ── Companies ─────────────────────────────────────────────────────────────────
# (name, country, city, type, status, tagline, description, website, contact_email, owner_email)
COMPANIES = [
    (
        "Axiom Labs",
        "USA",
        "San Francisco",
        CompanyType.startup,
        CompanyStatus.approved,
        "Build the future, ship today",
        "Early-stage startup building AI-powered developer tooling. Remote-first, competitive equity.",
        "https://axiomlabs.io",
        "jobs@axiomlabs.io",
        "alex.carter@example.com",
    ),
    (
        "NovaTech GmbH",
        "Germany",
        "Berlin",
        CompanyType.enterprise,
        CompanyStatus.approved,
        "Engineering at scale",
        "Berlin-based engineering consultancy delivering mission-critical systems for fintech and logistics.",
        "https://novatech.de",
        "talent@novatech.de",
        "lucas.muller@example.com",
    ),
    (
        "Pixel & Code",
        "UK",
        "London",
        CompanyType.agency,
        CompanyStatus.approved,
        "Digital products with purpose",
        "Award-winning product studio crafting web and mobile experiences for global brands.",
        "https://pixelandcode.co.uk",
        "hello@pixelandcode.co.uk",
        "james.chen@example.com",
    ),
    (
        "Orbis Systems",
        "Netherlands",
        "Amsterdam",
        CompanyType.startup,
        CompanyStatus.approved,
        "Real-time data infrastructure for everyone",
        "Series A startup solving real-time data streaming for mid-market businesses.",
        "https://orbis.systems",
        "careers@orbis.systems",
        "fatima.alrashid@example.com",
    ),
    (
        "Deeproute AI",
        "USA",
        "Austin",
        CompanyType.product_company,
        CompanyStatus.approved,
        "Intelligence embedded everywhere",
        "AI/ML product company specialising in recommendation engines and NLP pipelines.",
        "https://deeproute.ai",
        "hiring@deeproute.ai",
        "aaron.mitchell@example.com",
    ),
    (
        "Helix Health",
        "USA",
        "Boston",
        CompanyType.startup,
        CompanyStatus.approved,
        "Technology that saves lives",
        "HealthTech startup building HIPAA-compliant patient-data platforms.",
        "https://helixhealth.com",
        "talent@helixhealth.com",
        "raj.patel@example.com",
    ),
    (
        "Stormfront AS",
        "Norway",
        "Oslo",
        CompanyType.enterprise,
        CompanyStatus.approved,
        "Maritime meets modern technology",
        "Software house serving Nordic maritime and energy sectors with bespoke enterprise solutions.",
        "https://stormfront.no",
        "rekruttering@stormfront.no",
        "sven.berg@example.com",
    ),
    (
        "Tangent Mobile",
        "UK",
        "Manchester",
        CompanyType.agency,
        CompanyStatus.approved,
        "Mobile-first, always",
        "Cross-platform mobile agency with 50+ shipped apps across retail, fintech, and healthcare.",
        "https://tangentmobile.co.uk",
        "work@tangentmobile.co.uk",
        "david.kim@example.com",
    ),
    (
        "Cobalt Platform",
        "Brazil",
        "São Paulo",
        CompanyType.startup,
        CompanyStatus.approved,
        "Payments infrastructure for Latin America",
        "Fintech startup building next-generation payment rails across LatAm. YC W23.",
        "https://cobaltplatform.com",
        "jobs@cobaltplatform.com",
        "maria.santos@example.com",
    ),
    (
        "ArcticByte Oy",
        "Finland",
        "Helsinki",
        CompanyType.startup,
        CompanyStatus.approved,
        "Edge computing, redefined",
        "Deep-tech startup building WebAssembly-based edge runtimes in Rust.",
        "https://arcticbyte.fi",
        "careers@arcticbyte.fi",
        "tomas.novak@example.com",
    ),
    (
        "Mosaic Digital",
        "Australia",
        "Sydney",
        CompanyType.agency,
        CompanyStatus.approved,
        "Full-spectrum digital agency",
        "Sydney-based digital agency covering strategy, design, and engineering for enterprise clients.",
        "https://mosaicdigital.com.au",
        "studio@mosaicdigital.com.au",
        "ben.thompson@example.com",
    ),
    (
        "Vela Data",
        "Spain",
        "Madrid",
        CompanyType.product_company,
        CompanyStatus.approved,
        "Unlock your data's potential",
        "Madrid-based data platform startup helping companies build internal data products.",
        "https://veladata.io",
        "careers@veladata.io",
        "ana.lopez@example.com",
    ),
    (
        "Ironclad Security",
        "Canada",
        "Toronto",
        CompanyType.product_company,
        CompanyStatus.approved,
        "Zero-trust security for the cloud era",
        "Cloud-native SIEM and threat-detection SaaS provider.",
        "https://ironcladsec.com",
        "talent@ironcladsec.com",
        "ingrid.hansen@example.com",
    ),
    (
        "Zephyr Cloud",
        "India",
        "Bangalore",
        CompanyType.enterprise,
        CompanyStatus.approved,
        "Cloud-native from day one",
        "Cloud solutions company with 300+ engineers across AWS, GCP, and Azure practices.",
        "https://zephyrcloud.in",
        "hr@zephyrcloud.in",
        "omar.hassan@example.com",
    ),
]

# ── Vacancies ─────────────────────────────────────────────────────────────────
# required_skills / optional_skills: list of (skill_name, proficiency, years_of_exp_min or None)
VACANCIES = [
    (
        "Axiom Labs",
        "Senior Backend Engineer (Python/FastAPI)",
        Specialization.backend,
        "USA",
        "San Francisco",
        WorkFormat.remote,
        EmploymentType.full_time,
        140000,
        175000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        4,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "We're looking for a Senior Backend Engineer to lead the design of our core API platform. "
        "You'll architect high-throughput async services in Python/FastAPI, define database schemas, "
        "mentor junior engineers, and collaborate closely with the product team. We move fast and ship often.",
        [("Python", ProficiencyLevel.expert, 4), ("FastAPI", ProficiencyLevel.advanced, 3), ("PostgreSQL", ProficiencyLevel.advanced, 3)],
        [("Docker", ProficiencyLevel.intermediate, None), ("Redis", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Axiom Labs",
        "Frontend Engineer (React/TypeScript)",
        Specialization.frontend,
        "USA",
        "San Francisco",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        110000,
        145000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "Join our product team to build the next generation of our developer dashboard. "
        "You'll work in React + TypeScript with a focus on component architecture, performance, "
        "and accessibility. Experience with design systems is a strong plus.",
        [("React", ProficiencyLevel.advanced, 3), ("TypeScript", ProficiencyLevel.advanced, 2)],
        [("Next.js", ProficiencyLevel.intermediate, None), ("GraphQL", ProficiencyLevel.beginner, None)],
    ),
    (
        "NovaTech GmbH",
        "DevOps Engineer (Kubernetes/Terraform)",
        Specialization.devops,
        "Germany",
        "Berlin",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        75000,
        95000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "NovaTech is growing its platform team. You'll own CI/CD pipelines, manage Kubernetes "
        "clusters on AWS, and drive IaC adoption with Terraform. Strong Linux background essential.",
        [("Kubernetes", ProficiencyLevel.advanced, 3), ("Terraform", ProficiencyLevel.advanced, 2), ("AWS", ProficiencyLevel.intermediate, 2)],
        [("CI/CD", ProficiencyLevel.intermediate, None), ("Linux", ProficiencyLevel.intermediate, None)],
    ),
    (
        "NovaTech GmbH",
        "Backend Engineer (Go/Microservices)",
        Specialization.backend,
        "Germany",
        "Berlin",
        WorkFormat.onsite,
        EmploymentType.full_time,
        70000,
        90000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Build scalable microservices in Go for our logistics and fintech clients. "
        "You'll work with gRPC, Kafka, and PostgreSQL in a distributed-systems environment. "
        "We value clean code, solid test coverage, and proactive communication.",
        [("Go", ProficiencyLevel.advanced, 2), ("PostgreSQL", ProficiencyLevel.intermediate, 2), ("gRPC", ProficiencyLevel.intermediate, 1)],
        [("Apache Kafka", ProficiencyLevel.beginner, None), ("Docker", ProficiencyLevel.intermediate, None)],
    ),
    (
        "NovaTech GmbH",
        "iOS Developer (Swift)",
        Specialization.ios,
        "Germany",
        "Berlin",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        65000,
        85000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Build a new iOS client for one of our largest logistics customers from the ground up. "
        "Own the full mobile development lifecycle from architecture to App Store release. "
        "Familiarity with BLE and CoreLocation is a bonus.",
        [("Swift", ProficiencyLevel.advanced, 3)],
        [("React Native", ProficiencyLevel.beginner, None), ("REST API", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Pixel & Code",
        "Full-Stack Engineer (React + Node.js)",
        Specialization.fullstack,
        "UK",
        "London",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        65000,
        85000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "Pixel & Code is hiring a versatile full-stack engineer to work across client projects. "
        "You'll build everything from marketing sites to complex web apps using React on the frontend "
        "and Node.js or Python on the backend. Excellent communication is a must.",
        [("React", ProficiencyLevel.advanced, 3), ("Node.js", ProficiencyLevel.intermediate, 2), ("TypeScript", ProficiencyLevel.intermediate, 2)],
        [("Python", ProficiencyLevel.beginner, None), ("PostgreSQL", ProficiencyLevel.beginner, None)],
    ),
    (
        "Pixel & Code",
        "Vue.js Frontend Developer",
        Specialization.frontend,
        "UK",
        "London",
        WorkFormat.remote,
        EmploymentType.contract,
        400,
        550,
        SalaryCurrency.EUR,
        PaymentFrequency.daily,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "6-month contract to deliver a large-scale Vue.js migration for a media client. "
        "Ideal for someone who enjoys greenfield work and can hit the ground running. "
        "Nuxt.js experience is a big advantage.",
        [("Vue.js", ProficiencyLevel.advanced, 2), ("TypeScript", ProficiencyLevel.intermediate, 1), ("JavaScript", ProficiencyLevel.advanced, 3)],
        [("Nuxt.js", ProficiencyLevel.intermediate, None), ("REST API", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Orbis Systems",
        "Data Engineer (Kafka/Python)",
        Specialization.data_engineering,
        "Netherlands",
        "Amsterdam",
        WorkFormat.remote,
        EmploymentType.full_time,
        70000,
        95000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Orbis is building a real-time data streaming platform. We need a data engineer comfortable " "with Kafka, Spark, and building reliable pipelines at scale.",
        [("Apache Kafka", ProficiencyLevel.advanced, 3), ("Python", ProficiencyLevel.advanced, 3), ("PostgreSQL", ProficiencyLevel.intermediate, 2)],
        [("Elasticsearch", ProficiencyLevel.beginner, None), ("Docker", ProficiencyLevel.intermediate, None), ("Airflow", ProficiencyLevel.beginner, None)],
    ),
    (
        "Deeproute AI",
        "ML Engineer (Recommendation Systems)",
        Specialization.machine_learning,
        "USA",
        "Austin",
        WorkFormat.remote,
        EmploymentType.full_time,
        130000,
        165000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        4,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Deeproute AI is looking for an ML Engineer to develop and ship recommendation and ranking "
        "models used by millions. Own the full ML lifecycle: data, training, evaluation, deployment. "
        "Production ML experience is essential.",
        [("Python", ProficiencyLevel.expert, 4), ("PyTorch", ProficiencyLevel.advanced, 3), ("Machine Learning", ProficiencyLevel.advanced, 4)],
        [("TensorFlow", ProficiencyLevel.intermediate, None), ("Pandas", ProficiencyLevel.advanced, None)],
    ),
    (
        "Deeproute AI",
        "Senior Python Engineer (ML Platform)",
        Specialization.backend,
        "USA",
        "Austin",
        WorkFormat.remote,
        EmploymentType.full_time,
        125000,
        160000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        5,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Own the ML training and serving infrastructure. Build APIs and tooling that data scientists "
        "rely on daily. Strong async Python and FastAPI background needed. MLflow or W&B experience is a bonus.",
        [("Python", ProficiencyLevel.expert, 5), ("FastAPI", ProficiencyLevel.advanced, 3), ("Docker", ProficiencyLevel.advanced, 3)],
        [("Kubernetes", ProficiencyLevel.intermediate, None), ("Redis", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Helix Health",
        "Backend Engineer (Python/FastAPI)",
        Specialization.backend,
        "USA",
        "Boston",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        115000,
        145000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Build the API layer powering our patient-data platform. Security, HIPAA compliance, and test "
        "coverage are first-class concerns. FastAPI, PostgreSQL, and our FHIR data layer. "
        "Healthcare data experience is a bonus.",
        [("Python", ProficiencyLevel.advanced, 3), ("FastAPI", ProficiencyLevel.advanced, 2), ("PostgreSQL", ProficiencyLevel.advanced, 3)],
        [("Redis", ProficiencyLevel.beginner, None), ("Docker", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Stormfront AS",
        "Backend Engineer (Node.js/GraphQL)",
        Specialization.backend,
        "Norway",
        "Oslo",
        WorkFormat.onsite,
        EmploymentType.full_time,
        85000,
        110000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        4,
        37,
        VacancyStatus.open,
        SubmissionType.profile,
        "Work on vessel-tracking and maritime logistics software used across Scandinavia. "
        "Build and maintain GraphQL APIs consumed by web and mobile clients. "
        "Domain-driven design interest is valued.",
        [("Node.js", ProficiencyLevel.advanced, 4), ("GraphQL", ProficiencyLevel.advanced, 3), ("TypeScript", ProficiencyLevel.intermediate, 2)],
        [("PostgreSQL", ProficiencyLevel.intermediate, None), ("Docker", ProficiencyLevel.beginner, None)],
    ),
    (
        "Tangent Mobile",
        "React Native Developer",
        Specialization.cross_platform_mobile,
        "UK",
        "Manchester",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        50000,
        70000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "Tangent Mobile is growing its cross-platform team. Build polished mobile apps using React Native "
        "for clients in retail and healthcare. Strong JS/TS fundamentals and App Store / Play Store "
        "publishing experience required.",
        [("React Native", ProficiencyLevel.advanced, 2), ("JavaScript", ProficiencyLevel.advanced, 3), ("TypeScript", ProficiencyLevel.intermediate, 1)],
        [("REST API", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Tangent Mobile",
        "Flutter Developer",
        Specialization.cross_platform_mobile,
        "UK",
        "Manchester",
        WorkFormat.remote,
        EmploymentType.full_time,
        50000,
        68000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "We're expanding our Flutter offering for clients who want a single codebase across iOS, "
        "Android, and Web. You'll be our Flutter lead, defining architecture and working directly "
        "with UX designers.",
        [("Flutter", ProficiencyLevel.advanced, 2), ("Dart", ProficiencyLevel.advanced, 2)],
        [("REST API", ProficiencyLevel.beginner, None), ("Firebase", ProficiencyLevel.beginner, None)],
    ),
    (
        "Cobalt Platform",
        "Senior Full-Stack Engineer (Django + React)",
        Specialization.fullstack,
        "Brazil",
        "São Paulo",
        WorkFormat.remote,
        EmploymentType.full_time,
        90000,
        120000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        4,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Cobalt is building payment infrastructure for LatAm. Own features across our Django/FastAPI "
        "backend and React frontend, processing millions of transactions daily. "
        "Reliability and security are our north stars.",
        [("Python", ProficiencyLevel.advanced, 4), ("React", ProficiencyLevel.advanced, 3), ("PostgreSQL", ProficiencyLevel.advanced, 3)],
        [("Docker", ProficiencyLevel.intermediate, None), ("Redis", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Cobalt Platform",
        "Backend Engineer (Python/Payments)",
        Specialization.backend,
        "Brazil",
        "São Paulo",
        WorkFormat.remote,
        EmploymentType.full_time,
        70000,
        95000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Join our payments core team building highly-available Python services. Implement new "
        "payment-provider integrations, write thorough tests, and participate in on-call rotations. "
        "Financial systems experience is a plus.",
        [("Python", ProficiencyLevel.advanced, 2), ("FastAPI", ProficiencyLevel.intermediate, 1), ("PostgreSQL", ProficiencyLevel.intermediate, 2)],
        [("Redis", ProficiencyLevel.beginner, None), ("Docker", ProficiencyLevel.intermediate, None)],
    ),
    (
        "ArcticByte Oy",
        "Systems Engineer (Rust/WebAssembly)",
        Specialization.systems,
        "Finland",
        "Helsinki",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        65000,
        85000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Build the core runtime for our edge computing platform in Rust. Deep knowledge of async Rust "
        "(Tokio), WebAssembly, and memory management is required. A highly technical role at the heart "
        "of the product.",
        [("Rust", ProficiencyLevel.expert, 3), ("Linux", ProficiencyLevel.advanced, 3)],
        [("Docker", ProficiencyLevel.beginner, None), ("C++", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Mosaic Digital",
        "Frontend Engineer (Next.js)",
        Specialization.frontend,
        "Australia",
        "Sydney",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        90000,
        120000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "Mosaic is looking for a frontend engineer with Next.js experience to lead enterprise web builds. "
        "Work with Australian retail and finance clients. Strong accessibility (WCAG 2.1 AA) and "
        "performance optimisation skills expected.",
        [("Next.js", ProficiencyLevel.advanced, 3), ("React", ProficiencyLevel.advanced, 3), ("TypeScript", ProficiencyLevel.advanced, 2)],
        [("GraphQL", ProficiencyLevel.intermediate, None), ("CI/CD", ProficiencyLevel.beginner, None)],
    ),
    (
        "Mosaic Digital",
        "Android Developer (Kotlin)",
        Specialization.android,
        "Australia",
        "Sydney",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        85000,
        115000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "Lead native Android builds for enterprise retail clients. Own architecture decisions, code "
        "review, and Play Store releases. Jetpack Compose experience is highly desirable.",
        [("Kotlin", ProficiencyLevel.advanced, 3), ("Java", ProficiencyLevel.intermediate, 2), ("Android", ProficiencyLevel.advanced, 3)],
        [("REST API", ProficiencyLevel.intermediate, None), ("CI/CD", ProficiencyLevel.beginner, None)],
    ),
    (
        "Vela Data",
        "Data Platform Engineer",
        Specialization.data_engineering,
        "Spain",
        "Madrid",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        45000,
        62000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Vela Data is building self-serve data products for companies without a dedicated data team. "
        "Work on ingestion, transformation, and serving layers, collaborating with customers directly.",
        [("Python", ProficiencyLevel.advanced, 2), ("PostgreSQL", ProficiencyLevel.intermediate, 2), ("Elasticsearch", ProficiencyLevel.intermediate, 1)],
        [("Apache Kafka", ProficiencyLevel.beginner, None), ("Docker", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Vela Data",
        "Backend Engineer (FastAPI)",
        Specialization.backend,
        "Spain",
        "Madrid",
        WorkFormat.remote,
        EmploymentType.full_time,
        40000,
        55000,
        SalaryCurrency.EUR,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Write clean, tested FastAPI services, design database schemas, and optimise slow queries. " "Good documentation habits are as important as code quality here.",
        [("Python", ProficiencyLevel.advanced, 2), ("FastAPI", ProficiencyLevel.intermediate, 1), ("PostgreSQL", ProficiencyLevel.advanced, 2)],
        [("Docker", ProficiencyLevel.beginner, None), ("Redis", ProficiencyLevel.beginner, None)],
    ),
    (
        "Ironclad Security",
        "Cloud Security Engineer",
        Specialization.cloud,
        "Canada",
        "Toronto",
        WorkFormat.remote,
        EmploymentType.full_time,
        110000,
        140000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        4,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Join our threat-detection engineering team. Deep AWS security services, IAM, and "
        "infrastructure hardening knowledge required. CISSP or AWS Security Specialty certification "
        "is a strong advantage.",
        [("AWS", ProficiencyLevel.expert, 4), ("Terraform", ProficiencyLevel.advanced, 3), ("Linux", ProficiencyLevel.advanced, 4)],
        [("Kubernetes", ProficiencyLevel.intermediate, None), ("CI/CD", ProficiencyLevel.intermediate, None)],
    ),
    (
        "Ironclad Security",
        "Backend Engineer (Python/Go)",
        Specialization.backend,
        "Canada",
        "Toronto",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        100000,
        130000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        3,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Build data-ingestion and alert-pipeline services at the core of our SIEM platform. "
        "High-throughput, low-latency systems experience essential. Work in both Python and Go.",
        [("Python", ProficiencyLevel.advanced, 3), ("Go", ProficiencyLevel.intermediate, 1), ("Apache Kafka", ProficiencyLevel.advanced, 2)],
        [("Elasticsearch", ProficiencyLevel.intermediate, None), ("Docker", ProficiencyLevel.advanced, None)],
    ),
    (
        "Zephyr Cloud",
        "Senior DevOps Engineer",
        Specialization.devops,
        "India",
        "Bangalore",
        WorkFormat.hybrid,
        EmploymentType.full_time,
        80000,
        110000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        5,
        40,
        VacancyStatus.open,
        SubmissionType.resume,
        "Lead DevOps practices across our AWS and GCP service lines. Define standards for container "
        "orchestration, GitOps workflows, and cost optimisation. Multi-cloud experience highly valued.",
        [("Kubernetes", ProficiencyLevel.expert, 5), ("AWS", ProficiencyLevel.advanced, 4), ("GCP", ProficiencyLevel.advanced, 3), ("Terraform", ProficiencyLevel.advanced, 4)],
        [("CI/CD", ProficiencyLevel.advanced, None), ("Linux", ProficiencyLevel.expert, None)],
    ),
    (
        "Zephyr Cloud",
        "React Frontend Developer",
        Specialization.frontend,
        "India",
        "Bangalore",
        WorkFormat.onsite,
        EmploymentType.full_time,
        50000,
        70000,
        SalaryCurrency.USD,
        PaymentFrequency.once_a_month,
        2,
        40,
        VacancyStatus.open,
        SubmissionType.profile,
        "Build internal tooling dashboards and client-facing portals with React and TypeScript. "
        "Consume REST and GraphQL APIs, work closely with backend teams. Strong component-testing "
        "habits expected.",
        [("React", ProficiencyLevel.advanced, 2), ("TypeScript", ProficiencyLevel.intermediate, 1), ("JavaScript", ProficiencyLevel.advanced, 3)],
        [("GraphQL", ProficiencyLevel.beginner, None), ("REST API", ProficiencyLevel.intermediate, None)],
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Engine + session factory
# ─────────────────────────────────────────────────────────────────────────────

settings = get_settings()
engine = create_async_engine(settings.database.url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# ─────────────────────────────────────────────────────────────────────────────
# Seed function
# ─────────────────────────────────────────────────────────────────────────────


async def seed(session: AsyncSession) -> None:
    today = date.today()

    # ── 1. Skills ──────────────────────────────────────────────────────────────
    print("  → Skills")
    referenced: set[str] = set(ALL_SKILLS)
    for skills in USER_SKILLS.values():
        for s, *_ in skills:
            referenced.add(s)
    for skills in RESUME_SKILLS.values():
        for s, *_ in skills:
            referenced.add(s)
    for row in VACANCIES:
        for s, *_ in row[16]:  # required_skills
            referenced.add(s)
        for s, *_ in row[17]:  # optional_skills
            referenced.add(s)

    skill_map: dict[str, SkillModel] = {}
    for name in sorted(referenced):
        skill = SkillModel(name=name)
        session.add(skill)
        skill_map[name] = skill
    await session.flush()
    print(f"     {len(skill_map)} skills")

    # ── 2. Users ───────────────────────────────────────────────────────────────
    print("  → Users")
    user_map: dict[str, UserModel] = {}
    for first, last, email, country, city, spec, headline, jss, github, linkedin in USERS:
        user = UserModel(
            email=email,
            email_verified=True,
            password_hash="$2b$12$seeddataplaceholderXXXXXXXXXXXXXXXXXXXXXXX",
            first_name=first,
            last_name=last,
            headline=headline,
            country=country,
            city=city,
            specialization=spec,
            role=UserRole.user,
            status=UserStatus.active,
            follow_policy=FollowPolicy.auto_accept,
            job_search_status=jss,
            github_url=github,
            linkedin_url=linkedin,
        )
        session.add(user)
        user_map[email] = user
    await session.flush()
    print(f"     {len(user_map)} users")

    # ── 3. User skill links ────────────────────────────────────────────────────
    print("  → User skills")
    count = 0
    for email, skills in USER_SKILLS.items():
        user = user_map[email]
        for skill_name, proficiency, offset_days in skills:
            if skill_name not in skill_map:
                continue
            session.add(
                UserSkillLink(
                    user_id=user.id,
                    skill_id=skill_map[skill_name].id,
                    proficiency=proficiency,
                    last_used_at=today - timedelta(days=offset_days),
                )
            )
            count += 1
    await session.flush()
    print(f"     {count} links")

    # ── 4. Work experiences ────────────────────────────────────────────────────
    print("  → Work experiences")
    count = 0
    for email, company_name, location, position, description, started_at, ended_at in WORK_EXPERIENCES:
        session.add(
            WorkExperienceModel(
                user_id=user_map[email].id,
                company_name=company_name,
                location=location,
                position=position,
                description=description,
                started_at=started_at,
                ended_at=ended_at,
            )
        )
        count += 1
    await session.flush()
    print(f"     {count} entries")

    # ── 5. Resumes + resume skill links ───────────────────────────────────────
    print("  → Resumes")
    resume_map: dict[str, ResumeModel] = {}
    for email, title, summary, spec, sal_min, sal_max, currency, work_fmt, emp_type, country, city in RESUMES:
        resume = ResumeModel(
            user_id=user_map[email].id,
            title=title,
            summary=summary,
            specialization=spec,
            salary_expectation_min=sal_min,
            salary_expectation_max=sal_max,
            salary_currency=currency,
            work_format=work_fmt,
            employment_type=emp_type,
            country=country,
            city=city,
        )
        session.add(resume)
        resume_map[email] = resume
    await session.flush()

    skill_count = 0
    for email, skills in RESUME_SKILLS.items():
        if email not in resume_map:
            continue
        for skill_name, proficiency, offset_days in skills:
            if skill_name not in skill_map:
                continue
            session.add(
                ResumeSkillLink(
                    resume_id=resume_map[email].id,
                    skill_id=skill_map[skill_name].id,
                    proficiency=proficiency,
                    last_used_at=today - timedelta(days=offset_days),
                )
            )
            skill_count += 1
    await session.flush()
    print(f"     {len(resume_map)} resumes · {skill_count} resume skill links")

    # ── 6. Companies + owners ──────────────────────────────────────────────────
    print("  → Companies")
    company_map: dict[str, CompanyModel] = {}
    for name, country, city, ctype, cstatus, tagline, description, website, contact_email, owner_email in COMPANIES:
        company = CompanyModel(
            name=name,
            country=country,
            city=city,
            type=ctype,
            status=cstatus,
            tagline=tagline,
            description=description,
            website_url=website,
            contact_email=contact_email,
        )
        session.add(company)
        company_map[name] = company
    await session.flush()

    member_count = 0
    for (name, *_, owner_email) in COMPANIES:
        if owner_email not in user_map:
            continue
        session.add(
            CompanyMemberModel(
                user_id=user_map[owner_email].id,
                company_id=company_map[name].id,
                role=CompanyMemberRole.owner,
            )
        )
        member_count += 1
    await session.flush()
    print(f"     {len(company_map)} companies · {member_count} members")

    # ── 7. Vacancies + skill links ─────────────────────────────────────────────
    print("  → Vacancies")
    vac_count = 0
    skill_link_count = 0
    for row in VACANCIES:
        (
            company_name,
            title,
            spec,
            country,
            city,
            work_fmt,
            emp_type,
            sal_min,
            sal_max,
            currency,
            pay_freq,
            years_exp,
            work_hours,
            status,
            sub_type,
            description,
            required_skills,
            optional_skills,
        ) = row

        vacancy = VacancyModel(
            company_id=company_map[company_name].id,
            title=title,
            description=description,
            specialization=spec,
            country=country,
            city=city,
            work_format=work_fmt,
            employment_type=emp_type,
            salary_min=sal_min,
            salary_max=sal_max,
            salary_currency=currency,
            payment_frequency=pay_freq,
            years_of_experience_min=years_exp,
            work_hours_per_week=work_hours,
            status=status,
            submission_type=sub_type,
        )
        session.add(vacancy)
        await session.flush()  # need vacancy.id before creating skill links

        for skill_name, proficiency, yoe in required_skills:
            if skill_name not in skill_map:
                continue
            session.add(
                VacancySkillLink(
                    vacancy_id=vacancy.id,
                    skill_id=skill_map[skill_name].id,
                    proficiency=proficiency,
                    years_of_experience_min=yoe,
                    is_required=True,
                )
            )
            skill_link_count += 1

        for skill_name, proficiency, yoe in optional_skills:
            if skill_name not in skill_map:
                continue
            session.add(
                VacancySkillLink(
                    vacancy_id=vacancy.id,
                    skill_id=skill_map[skill_name].id,
                    proficiency=proficiency,
                    years_of_experience_min=yoe,
                    is_required=False,
                )
            )
            skill_link_count += 1

        vac_count += 1

    await session.flush()
    print(f"     {vac_count} vacancies · {skill_link_count} vacancy skill links")


async def main() -> None:
    print("Starting seed...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed(session)
    print("\nDone ✓")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
