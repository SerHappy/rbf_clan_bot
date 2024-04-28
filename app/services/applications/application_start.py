import datetime as dt
from datetime import datetime, timedelta

from app.db.engine import UnitOfWork
from app.domain.application.entities import Application
from app.domain.application.exceptions import (
    ApplicationAlreadyAcceptedError,
    ApplicationAtWaitingStatusError,
    ApplicationCoolDownError,
    ApplicationDecisionDateNotFoundError,
    ApplicationDoesNotExistError,
    ApplicationWrongStatusError,
)
from app.domain.application.value_objects import ApplicationStatusEnum
from app.domain.user.exceptions import UserIsBannedError, UserNotFoundError


class ApplicationStartService:
    """Responsible for application start.

    It checks if the user is available to fill the application.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the application start service."""
        self._uow = uow

    # TODO: Refactor this into small private methods
    async def execute(self, user_id: int) -> Application:
        """Execute the application start service."""
        async with self._uow():
            user = await self._uow.user.get_by_id(user_id)
            if not user:
                raise UserNotFoundError
            if user.is_banned:
                raise UserIsBannedError
            try:
                user_application = await self._uow.application.retrieve_last(
                    user_id,
                )
            except ApplicationDoesNotExistError:
                user_application = await self._uow.application.create(user_id)
                await self._uow.commit()
                return user_application
            if user_application.status == ApplicationStatusEnum.IN_PROGRESS:
                user_application.clear()
                await self._uow.application_answer.delete_all_answers_by_application_id(
                    user_application.id,
                )
                await self._uow.commit()
                return user_application
            if user_application.status in (
                ApplicationStatusEnum.WAITING,
                ApplicationStatusEnum.PROCESSING,
            ):
                raise ApplicationAtWaitingStatusError
            if user_application.status == ApplicationStatusEnum.ACCEPTED:
                raise ApplicationAlreadyAcceptedError
            if user_application.status == ApplicationStatusEnum.REJECTED:
                now = datetime.now(tz=dt.UTC)
                if user_application.decision_date is None:
                    raise ApplicationDecisionDateNotFoundError
                if now - user_application.decision_date >= timedelta(days=30):
                    user_application = await self._uow.application.create(user_id)
                    await self._uow.commit()
                    return user_application
                raise ApplicationCoolDownError(
                    user_application.decision_date + timedelta(30),
                )
            raise ApplicationWrongStatusError