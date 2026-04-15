from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from high_load_ai.domain.models import AgentRun, RunId, RunStatus
from high_load_ai.domain.ports import AgentRunRepository
from high_load_ai.infrastructure.db.models import AgentRunModel


class SqlAlchemyAgentRunRepository(AgentRunRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, run: AgentRun) -> AgentRun:
        async with self._session_factory() as session:
            session.add(_to_model(run))
            await session.commit()
        return run

    async def update(self, run: AgentRun) -> AgentRun:
        async with self._session_factory() as session:
            model = await session.get(AgentRunModel, str(run.id))
            if model is None:
                model = _to_model(run)
                session.add(model)
            else:
                model.prompt = run.prompt
                model.status = run.status.value
                model.output_text = run.output_text
                model.error_message = run.error_message
                model.updated_at = run.updated_at
            await session.commit()
        return run

    async def get(self, run_id: UUID) -> AgentRun | None:
        async with self._session_factory() as session:
            query = select(AgentRunModel).where(AgentRunModel.id == str(run_id))
            model = await session.scalar(query)
            if model is None:
                return None
            return _to_entity(model)


def _to_model(run: AgentRun) -> AgentRunModel:
    return AgentRunModel(
        id=str(run.id),
        prompt=run.prompt,
        status=run.status.value,
        output_text=run.output_text,
        error_message=run.error_message,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


def _to_entity(model: AgentRunModel) -> AgentRun:
    return AgentRun(
        id=RunId(UUID(model.id)),
        prompt=model.prompt,
        status=RunStatus(model.status),
        output_text=model.output_text,
        error_message=model.error_message,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
