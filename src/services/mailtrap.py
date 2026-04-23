from aiohttp import ClientSession
from pydantic import BaseModel, ConfigDict, Field

from src.core.logger import logger
from src.core.settings import MailtrapConfig


class Mailbox(BaseModel):
    name: str
    email: str


class Payload(BaseModel):
    from_: Mailbox = Field(serialization_alias="from")
    to: list[Mailbox]
    template_uuid: str
    template_variables: dict

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)


class SuccessResponse(BaseModel):
    success: bool
    message_ids: list[str]


class ErrorResponse(BaseModel):
    success: bool
    errors: list[str]


class MailtrapError(Exception):
    """Custom exception raised when the Mailtrap API returns an error."""

    def __init__(self, error: ErrorResponse):
        self.error = error
        super().__init__(f"success: {error.success}, errors: {error.errors}")


class Mailtrap:
    URL = "https://send.api.mailtrap.io/api/send"

    @staticmethod
    async def send(api_key: str, payload: Payload) -> None:
        """Helper method to handle the shared HTTP request logic."""

        json = payload.model_dump(by_alias=True)
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": api_key,
        }

        async with ClientSession() as session:
            async with session.post(Mailtrap.URL, json=json, headers=headers) as res:
                status = res.status
                data = await res.json()

                if status == 200:
                    response = SuccessResponse(**data)
                    logger.debug(f"Mailtrap success: {response}")
                    return

                response = ErrorResponse(**data)
                logger.error(f"Mailtrap error: {response}")
                raise MailtrapError(response)

    @classmethod
    async def send_email_verification_link(cls, to_name: str, to_email: str, link: str, cfg: MailtrapConfig) -> None:
        template = cfg.verification

        payload = Payload(
            from_=Mailbox(name=template.from_name, email=template.from_email),
            to=[Mailbox(name=to_name, email=to_email)],
            template_uuid=template.template_uuid,
            template_variables={"link": link},
        )

        await cls.send(cfg.api_key, payload)

    @classmethod
    async def send_password_setup_link(
        cls,
        to_name: str,
        to_email: str,
        link: str,
        cfg: MailtrapConfig,
    ) -> None:
        template = cfg.password_setup

        payload = Payload(
            from_=Mailbox(
                name=template.from_name,
                email=template.from_email,
            ),
            to=[
                Mailbox(
                    name=to_name,
                    email=to_email,
                )
            ],
            template_uuid=template.template_uuid,
            template_variables={
                "link": link,
            },
        )

        await cls.send(cfg.api_key, payload)

    @classmethod
    async def send_feedback_confirmation(
        cls,
        to_name: str,
        to_email: str,
        message: str,
        cfg: MailtrapConfig,
    ) -> None:
        template = cfg.feedback_confirmation

        payload = Payload(
            from_=Mailbox(
                name=template.from_name,
                email=template.from_email,
            ),
            to=[
                Mailbox(
                    name=to_name,
                    email=to_email,
                )
            ],
            template_uuid=template.template_uuid,
            template_variables={
                "name": to_name,
                "message": message,
            },
        )

        await cls.send(cfg.api_key, payload)
