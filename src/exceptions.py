from datetime import date
from fastapi import HTTPException


# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions (сервисный слой — никаких HTTP-импортов ниже этой черты)
# ──────────────────────────────────────────────────────────────────────────────


class NabronirovalException(Exception):
    detail = "Неожиданная ошибка!"

    def __init__(self, *args, **kwargs):
        super().__init__(self.detail, *args, **kwargs)


class ObjectNotFoundException(NabronirovalException):
    detail = "Объект не найден!"


class RoomNotFoundException(NabronirovalException):
    detail = "Номер не найден!"


class HotelNotFoundException(NabronirovalException):
    detail = "Отель не найден!"


class ObjectAlreadyExistsException(NabronirovalException):
    detail = "Похожий объект уже существует!"


class AllRoomsAreBookedException(NabronirovalException):
    detail = "Не осталось свободных номеров!"


class IncorrectTokenException(NabronirovalException):
    detail = "Некорректный токен!"


class EmailNotRegisteredException(NabronirovalException):
    detail = "Пользователь с таким email не зарегистрирован!"


class IncorrectPasswordException(NabronirovalException):
    detail = "Пароль неверный!"


class UserAlreadyExistsException(NabronirovalException):
    detail = "Пользователь уже существует!"


class SameEmailException(NabronirovalException):
    detail = "Новый email совпадает с текущим!"


class UserNotAuthenticatedException(NabronirovalException):
    detail = "Вы не в системе, выход невозможен!"


class FacilityTitleEmptyException(NabronirovalException):
    detail = "Название удобства не может быть пустым!"


class ExpiredTokenException(NabronirovalException):
    detail = "Токен доступа истёк!"


class InvalidRefreshTokenException(NabronirovalException):
    detail = "Недействительный refresh-токен!"


class CannotDeleteHotelWithRoomsException(NabronirovalException):
    detail = "Невозможно удалить отель, у которого есть номера!"


class CannotDeleteRoomWithBookingsException(NabronirovalException):
    detail = "Невозможно удалить номер, у которого есть бронирования!"


class PastDateException(NabronirovalException):
    detail = "Дата не может быть в прошлом!"


class InvalidBookingPeriodException(NabronirovalException):
    detail = "Некорректный период бронирования!"


class InvalidDateRangeException(NabronirovalException):
    detail = "Дата заезда не может быть позже даты выезда!"


class InsufficientPermissionsException(NabronirovalException):
    detail = "Недостаточно прав для выполнения этого действия!"


# Image domain exceptions
class ImageNotFoundException(NabronirovalException):
    detail = "Изображение не найдено!"


class FileTooLargeException(NabronirovalException):
    detail = "Файл слишком большой!"


class EmptyFileException(NabronirovalException):
    detail = "Файл пустой!"


class UnsupportedMediaTypeException(NabronirovalException):
    detail = "Неподдерживаемый тип файла!"


class CorruptedImageException(NabronirovalException):
    detail = "Повреждённый или неверный файл изображения!"


# ──────────────────────────────────────────────────────────────────────────────
# Domain helper (поднимает domain-исключение, не HTTP!)
# ──────────────────────────────────────────────────────────────────────────────


def check_date_to_after_date_from(date_from: date, date_to: date) -> None:
    if date_to <= date_from:
        raise InvalidDateRangeException()


# ──────────────────────────────────────────────────────────────────────────────
# HTTP exceptions (только API-слой)
# ──────────────────────────────────────────────────────────────────────────────


class NabronirovalHTTPException(HTTPException):
    status_code = 500
    detail = None

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class HotelNotFoundHTTPException(NabronirovalHTTPException):
    status_code = 404
    detail = "Отель не найден!"


class RoomNotFoundHTTPException(NabronirovalHTTPException):
    status_code = 404
    detail = "Номер не найден!"


class AllRoomsAreBookedHTTPException(NabronirovalHTTPException):
    status_code = 409
    detail = "Не осталось свободных номеров!"


class IncorrectTokenHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Некорректный токен!"


class EmailNotRegisteredHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Пользователь с таким email не зарегистрирован!"


class UserEmailAlreadyExistsHTTPException(NabronirovalHTTPException):
    status_code = 409
    detail = "Пользователь с такой почтой уже существует!"


class IncorrectPasswordHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Пароль неверный!"


class NoAccessTokenHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Вы не предоставили токен доступа!"


class UserNotAuthenticatedHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Вы не в системе, выход невозможен!"


class UserIsAlreadyAuthenticatedHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Вы уже вошли в систему!"


class ObjectAlreadyExistsHTTPException(NabronirovalHTTPException):
    status_code = 409
    detail = "Похожий объект уже существует!"


class FacilityTitleEmptyHTTPException(NabronirovalHTTPException):
    status_code = 422
    detail = "Название удобства не может быть пустым!"


class ExpiredTokenHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Токен доступа истёк!"


class InvalidRefreshTokenHTTPException(NabronirovalHTTPException):
    status_code = 401
    detail = "Недействительный refresh-токен!"


class SameEmailHTTPException(NabronirovalHTTPException):
    status_code = 409
    detail = "Новый email совпадает с текущим!"


class ObjectNotFoundHTTPException(NabronirovalHTTPException):
    status_code = 404
    detail = "Объект не найден!"


class InvalidDateRangeHTTPException(NabronirovalHTTPException):
    status_code = 422
    detail = "Дата заезда не может быть позже даты выезда!"


class CannotDeleteHotelWithRoomsHTTPException(NabronirovalHTTPException):
    status_code = 409
    detail = "Невозможно удалить отель, у которого есть номера!"


class CannotDeleteRoomWithBookingsHTTPException(NabronirovalHTTPException):
    status_code = 409
    detail = "Невозможно удалить номер, у которого есть бронирования!"


class PastDateHTTPException(NabronirovalHTTPException):
    status_code = 422
    detail = "Дата не может быть в прошлом!"


class InvalidBookingPeriodHTTPException(NabronirovalHTTPException):
    status_code = 422
    detail = "Некорректный период бронирования!"


class InsufficientPermissionsHTTPException(NabronirovalHTTPException):
    status_code = 403
    detail = "Недостаточно прав для выполнения этого действия!"


class FileTooLargeHTTPException(NabronirovalHTTPException):
    status_code = 413
    detail = "Файл слишком большой!"


class EmptyFileHTTPException(NabronirovalHTTPException):
    status_code = 400
    detail = "Файл пустой!"


class UnsupportedMediaTypeHTTPException(NabronirovalHTTPException):
    status_code = 415
    detail = "Неподдерживаемый тип файла!"


class CorruptedImageHTTPException(NabronirovalHTTPException):
    status_code = 400
    detail = "Повреждённый или неверный файл изображения!"


class ImageNotFoundHTTPException(NabronirovalHTTPException):
    status_code = 404
    detail = "Изображение не найдено!"
