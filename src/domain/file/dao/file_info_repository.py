from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.exception import NotFoundException
from src.domain.file.dto.file_info_dto import FileInfoServiceDTO
from src.infra.db.orm.init.file_info import FileInfo
from src.infra.util.convert_util import get_first_template


class FileInfoRepository:
    async def upsert_file_info(self, db: AsyncSession, dto: FileInfoServiceDTO) -> FileInfoServiceDTO:
        model = FileInfo.from_dto(dto)
        if model.info_id is None or model.user_id == '':
            # New entity, do auto increment
            # Refresh the model when it an insert
            db.add(model)
            await db.commit()
            # Refresh the model when it an insert
            await db.refresh(model)
        else:
            # Check if the record exists
            query = select(FileInfo).filter_by(info_id=model.info_id)
            result = await db.execute(query)

            existing_model = result.scalars().first()

            if existing_model is not None:
                # Update the existing model
                for key, value in model.__dict__.items():
                    if key != "_sa_instance_state":
                        setattr(existing_model, key, value)
                await db.merge(existing_model)
                await db.commit()
            else:
                raise NotFoundException("Record not found")
        res: FileInfoServiceDTO = FileInfoServiceDTO.of(model)
        return res


    async def get_file_info_by_id(self, db: AsyncSession, info_id: str) -> FileInfoServiceDTO:
        stmt = select(FileInfo).filter_by(info_id=info_id)
        res: FileInfo = await get_first_template(db, stmt)

        return FileInfoServiceDTO.of(res)

    async def delete_by_id(self, db: AsyncSession, info_id: str) -> None:
        stmt = select(FileInfo).filter_by(info_id=info_id)
        model: FileInfo = await get_first_template(db, stmt)
        if model is not None:
            model.is_deleted = True
            await db.merge(model)
            await db.commit()

        else:
            raise NotFoundException("Record not found")
