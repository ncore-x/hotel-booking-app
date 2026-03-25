from fastapi import APIRouter, UploadFile, status

from src.api.dependencies import AdminDep, DBDep
from src.exceptions import (
    CorruptedImageException,
    CorruptedImageHTTPException,
    EmptyFileException,
    EmptyFileHTTPException,
    FileTooLargeException,
    FileTooLargeHTTPException,
    HotelNotFoundException,
    HotelNotFoundHTTPException,
    UnsupportedMediaTypeException,
    UnsupportedMediaTypeHTTPException,
)
from src.schemas.images import HotelImage, ImageUploadResponse
from src.services.images import ImagesService

router = APIRouter(prefix="/hotels", tags=["Images"])


@router.post(
    "/{hotel_id}/images",
    summary="Загрузка изображения отеля",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(_: AdminDep, hotel_id: int, db: DBDep, file: UploadFile):
    """Загрузка изображения (PNG/JPEG/WebP, макс. 5 МБ). Только для администраторов."""
    try:
        return await ImagesService(db).upload_image(hotel_id, file)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except EmptyFileException:
        raise EmptyFileHTTPException()
    except FileTooLargeException:
        raise FileTooLargeHTTPException()
    except UnsupportedMediaTypeException:
        raise UnsupportedMediaTypeHTTPException()
    except CorruptedImageException:
        raise CorruptedImageHTTPException()


@router.get(
    "/{hotel_id}/images",
    summary="Изображения отеля",
    response_model=list[HotelImage],
)
async def get_hotel_images(hotel_id: int, db: DBDep):
    try:
        return await ImagesService(db).get_hotel_images(hotel_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
