from enum import Enum, StrEnum, auto


class AutoName(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


# --- Auth ---
class AuthResultType(StrEnum):
    success = auto()
    new_user = auto()
    setup_password = auto()


# --- OAuthUsers ---
class Provider(AutoName):
    google = auto()
    github = auto()


# --- Users ---
class FollowStatus(AutoName):
    pending = auto()
    accepted = auto()
    declined = auto()


class FollowPolicy(AutoName):
    auto_accept = auto()
    require_approval = auto()


class UserRole(AutoName):
    user = auto()
    admin = auto()


class UserStatus(AutoName):
    active = auto()
    suspended = auto()
    pending_verification = auto()
    deleted = auto()


class JobSearchStatus(AutoName):
    actively_looking = auto()
    open_to_offers = auto()
    interviewing = auto()
    not_looking = auto()


class Specialization(AutoName):
    frontend = auto()
    backend = auto()
    fullstack = auto()

    ios = auto()
    android = auto()
    cross_platform_mobile = auto()
    desktop = auto()

    embedded = auto()
    systems = auto()
    firmware = auto()

    devops = auto()
    platform = auto()
    sre = auto()
    cloud = auto()

    data_engineering = auto()
    data_science = auto()
    machine_learning = auto()
    ai_engineering = auto()
    data_analytics = auto()

    security = auto()
    application_security = auto()

    blockchain = auto()
    game = auto()
    qa = auto()
    ui_ux = auto()
    developer_relations = auto()
    technical_writing = auto()


class ProficiencyLevel(AutoName):
    beginner = auto()
    intermediate = auto()
    advanced = auto()
    expert = auto()


# --- Companies ---
class CompanyType(AutoName):
    startup = auto()
    product_company = auto()
    agency = auto()
    outsourcing = auto()
    outstaffing = auto()
    enterprise = auto()
    government = auto()


class CompanyStatus(AutoName):
    pending = auto()
    approved = auto()
    rejected = auto()
    suspended = auto()


class CompanyMemberRole(AutoName):
    member = auto()
    recruiter = auto()
    owner = auto()


# --- Vacancy ---
class PaymentFrequency(AutoName):
    hourly = auto()
    daily = auto()
    once_a_week = auto()
    twice_a_month = auto()
    once_a_month = auto()
    per_project = auto()


class WorkFormat(AutoName):
    onsite = auto()
    remote = auto()
    hybrid = auto()


class EmploymentType(AutoName):
    full_time = auto()
    part_time = auto()
    contract = auto()
    internship = auto()


class SubmissionType(AutoName):
    profile = auto()
    resume = auto()


class VacancyStatus(AutoName):
    draft = auto()
    open = auto()
    archived = auto()
    closed = auto()


class ApplicationStatus(AutoName):
    pending = auto()
    viewed = auto()
    shortlisted = auto()
    interview = auto()
    offer = auto()
    rejected = auto()
    hired = auto()


# --- Feeds ---
class FeedEngagementType(AutoName):
    quote = auto()
    repost = auto()
    like = auto()
    view = auto()
    bookmark = auto()


class FeedVisibility(AutoName):
    public = auto()
    followers = auto()
    private = auto()


class ProcessStatus(AutoName):
    pending = auto()
    processed = auto()
    failed = auto()


class CommentPolicy(AutoName):
    everyone = auto()
    followers = auto()
    nobody = auto()


# --- Posts ---
class PostStatus(AutoName):
    draft = auto()
    published = auto()
    archived = auto()


class PostEngagementType(AutoName):
    like = auto()
    view = auto()
    bookmark = auto()


# --- Groups ---
class GroupType(AutoName):
    public = auto()
    private = auto()


class GroupMemberRole(AutoName):
    regular = auto()
    administrator = auto()
    owner = auto()


# --- Chats ---
class IncomingEvent(AutoName):
    # client → server

    # chats domain
    ping = auto()

    join_chat = auto()
    leave_chat = auto()

    typing_start = auto()
    typing_stop = auto()

    read_chat = auto()
    create_chat = auto()
    delete_chat = auto()
    clear_chat = auto()

    update_chat_settings = auto()

    send_message = auto()
    update_message = auto()
    delete_message = auto()

    # groups domain
    # ...
    # feeds domain
    # ...


class OutgoingEvent(AutoName):
    # server → client
    pong = auto()
    error = auto()

    chat_joined = auto()
    chat_left = auto()

    typing_start = auto()
    typing_stop = auto()

    chat_read = auto()
    chat_created = auto()
    chat_cleared = auto()
    chat_deleted = auto()

    user_online = auto()
    user_offline = auto()

    message_created = auto()
    message_updated = auto()
    message_deleted = auto()

    chat_settings_updated = auto()


# --- Shared ---
class SalaryCurrency(AutoName):
    UZS = auto()
    KZT = auto()
    KGS = auto()
    TJS = auto()
    TMT = auto()
    USD = auto()
    EUR = auto()
    TRY = auto()


class AttachmentStatus(AutoName):
    pending = auto()
    ready = auto()
