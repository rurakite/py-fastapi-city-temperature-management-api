# crud.py

from sqlalchemy.orm import Session
from . import models, schemas


def create_temperature(db: Session, temperature: schemas.TemperatureCreate):
    db_temperature = models.Temperature(**temperature.dict())
    db.add(db_temperature)
    db.commit()
    db.refresh(db_temperature)
    return db_temperature


def get_all_temperatures(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Temperature).offset(skip).limit(limit).all()


def get_temperatures_by_city(db: Session, city_id: int):
    return (
        db.query(models.Temperature)
        .filter(models.Temperature.city_id == city_id)
        .all()
    )
