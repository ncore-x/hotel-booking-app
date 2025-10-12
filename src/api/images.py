from fastapi import APIRouter, UploadFile, HTTPException, status

from src.services.images import ImagesService

router = APIRouter(prefix="/images", tags=["Изображения отелей"])


@router.post("", summary="Загрузка изображения отеля", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile):
    """
    Загрузка изображения (PNG/JPEG). Возвращает метаданные сохранённого изображения.
    """
    try:
        result = await ImagesService().upload_image(file)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера")
    return result
