from fastapi import APIRouter, BackgroundTasks, UploadFile

from src.services.images import ImagesService

router = APIRouter(prefix="/images", tags=["Изображения отелей"])


@router.post("", summary="Загрузка изображения отеля")
def upload_image(file: UploadFile, background_tasks: BackgroundTasks):
    ImagesService().upload_image(file, background_tasks)
