from collections.abc import AsyncIterator
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.document_click_log import DocumentClickLog
from repository.document_click_log import DocumentClickLogRepository
from schema.document_click_log import (
    CreateDocumentClickLogRequest,
    DocumentClickLogStatsResponse,
)
from schema.user import User
from service.knowledge_base import KnowledgeBaseService


class DocumentClickLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.document_click_log_repository = DocumentClickLogRepository(session)

    async def create_click_log(
        self,
        user: User,
        thread_id: int,
        message_id: int,
        request: CreateDocumentClickLogRequest,
    ):
        try:
            await self.document_click_log_repository.create(
                user_id=user.id,
                name=user.name,
                thread_id=thread_id,
                message_id=message_id,
                document_id=request.document_id,
                document_name=request.document_name,
            )
        except Exception as e:
            logger.error(f"ドキュメントクリックログ作成失敗: {e}")
            raise

    async def get_click_stats(self) -> list[DocumentClickLogStatsResponse]:
        try:
            stats = await self.document_click_log_repository.get_click_stats()
            return [
                DocumentClickLogStatsResponse(
                    document_id=stat["document_id"],
                    document_name=KnowledgeBaseService.resolve_filename(
                        stat["s3_bucket_name"], 
                        stat["s3_object_key"]
                    ),
                    last_access=stat["last_access"],
                    num_clicked=stat["num_clicked"],
                )
                for stat in stats
            ]
        except Exception as e:
            logger.error(f"ドキュメントクリック統計取得失敗: {e}")
            raise

    async def get_click_stats_by_year_month(
        self,
        year_month: str,
        limit: int = 10,
        page: int = 1,
        sort_by: str = "num_clicked",
        order: str = "desc",
    ) -> tuple[list[DocumentClickLogStatsResponse], int]:
        try:
            stats, total = await self.document_click_log_repository.get_click_stats_by_year_month(
                year_month, limit, page, sort_by, order
            )
            return [
                DocumentClickLogStatsResponse(
                    document_id=stat["document_id"],
                    document_name=KnowledgeBaseService.resolve_filename(
                        stat["s3_bucket_name"], 
                        stat["s3_object_key"]
                    ),
                    last_access=stat["last_access"],
                    num_clicked=stat["num_clicked"],
                )
                for stat in stats
            ], total
        except Exception as e:
            logger.error(f"資料クリックログ取得失敗: {e}")
            raise

    async def get_available_months(self) -> list[str]:
        try:
            return await self.document_click_log_repository.get_available_months()
        except Exception as e:
            logger.error(f"利用可能月取得失敗: {e}")
            raise

    async def get_logs_for_export(
        self,
        year_month: str | None = None,
    ) -> AsyncIterator[DocumentClickLog]:
        try:
            if year_month:
                async for log in self.document_click_log_repository.stream_logs_by_year_month(year_month):
                    yield log
                return

            async for log in self.document_click_log_repository.stream_all():
                yield log
        except Exception as e:
            logger.error(f"エクスポート失敗: {e}")
            raise

if __name__ == "__main__":
    pass