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
    ImageNotFoundException,
    ImageNotFoundHTTPException,
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


@router.delete(
    "/{hotel_id}/images/{image_id}",
    summary="Удаление изображения отеля",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_image(_: AdminDep, hotel_id: int, image_id: int, db: DBDep):
    """Удаление изображения отеля. Только для администраторов."""
    try:
        await ImagesService(db).delete_image(hotel_id, image_id)
    except HotelNotFoundException:
        raise HotelNotFoundHTTPException()
    except ImageNotFoundException:
        raise ImageNotFoundHTTPException()
