from fastapi import Query, Body, APIRouter


router = APIRouter(prefix="/hotels", tags=["Отели"])


hotels = [
    {"id": 1, "title": "Sochi", "name": "sochi"},
    {"id": 2, "title": "Dubai", "name": "dubai"}
]


@router.get("", summary="Получение отеля(ей)", description="Можно фильтровать по id или title")
def get_hotels(
    id: int | None = Query(None, description="Айдишник"),
    title: str | None = Query(None, description="Название отеля"),
):
    hotels_ = []
    for hotel in hotels:
        if id and hotel["id"] != id:
            continue
        if title and hotel["title"] != title:
            continue
        hotels_.append(hotel)
    return hotels_


@router.post("", summary="Создание нового отеля")
def create_hotel(
    title: str = Body(embed=True),
):
    global hotels
    hotels.append({
        "id": hotels[-1]["id"] + 1,
        "title": title
    })
    return {"status": "Ok"}


@router.put("/{hotel_id}", summary="Обновление отеля", description="Полное обноелвение данных по отелю")
def hotel_put_update(
    hotel_id: int,
    title: str = Body(),
    name: str = Body(),
):
    global hotels
    hotel = [hotel for hotel in hotels if hotel["id"] == hotel_id][0]
    hotel["title"] = title
    hotel["name"] = name
    return {"status": "Ok"}


@router.patch("/{hotel_id}", summary="Частичное обновление отеля", description="Обновление отеля по 'name' или 'title'")
def hotel_patch_update(
    hotel_id: int,
    title: str | None = Body(None),
    name: str | None = Body(None),
):
    global hotels
    hotel = [hotel for hotel in hotels if hotel["id"] == hotel_id][0]
    if hotel["id"] == hotel_id:
        if title:
            hotel["title"] = title
        if name:
            hotel["name"] = name
        return {"status": "Ok"}


@router.delete("/{hotel_id}", summary="Удаление отеля")
def delete_hotels(hotel_id: int):
    global hotels
    hotels = [hotel for hotel in hotels if hotel["id"] != hotel_id]
    return {"status": "Ok"}
