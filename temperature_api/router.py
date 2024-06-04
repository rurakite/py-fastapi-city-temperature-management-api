from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import httpx

from city_crud_api import crud as cities_crud
from . import crud as temperatures_crud
from . import schemas

import dependencies

router = APIRouter()

API_KEY = "2011750bdcb7475e85484928242402"


@router.post("/update", response_model=List[schemas.Temperature])
async def update_temperatures(db: Session = Depends(dependencies.get_db)):
    async with httpx.AsyncClient() as client:
        try:
            cities = cities_crud.get_all_cities(db)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching cities",
            )

        updated_temperatures = []
        for city in cities:
            try:
                response = await client.get(
                    f"http://api.weatherapi.com/v1/"
                    f"current.json?key={API_KEY}&q={city.name}&aqi=no"
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error fetching weather data for city {city.name}",
                )
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error requesting weather data: {str(exc)}",
                )

            temperature_data = schemas.TemperatureCreate(
                city_id=city.id,
                date_time=data["location"]["localtime"],
                temperature=data["current"]["temp_c"],
            )
            try:
                db_temperature = temperatures_crud.create_temperature(
                    db, temperature_data
                )
                updated_temperatures.append(db_temperature)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error creating temperature record",
                )

    return updated_temperatures


@router.get("/", response_model=List[schemas.Temperature])
def fetch_all_temperatures(
    commons: dependencies.CommonsDep,
    db: Session = Depends(dependencies.get_db),
):
    temperatures = temperatures_crud.get_all_temperatures(
        db, commons["skip"], commons["limit"]
    )

    return temperatures


@router.get("/{city_id}", response_model=List[schemas.Temperature])
def fetch_temperatures_by_city(
    city_id: int,
    db: Session = Depends(dependencies.get_db),
):
    temperature = temperatures_crud.get_temperatures_by_city(
        db, city_id=city_id
    )

    if temperature is None:
        raise HTTPException(
            status_code=404, detail=f"City with id {city_id} not found"
        )

    return temperature
