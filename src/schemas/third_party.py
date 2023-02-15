from __future__ import annotations

from pydantic import BaseModel


class CityInfo(BaseModel):
    city: str = None
    citykey: str = None
    parent: str = None
    updateTime: str = None


class WeatherDayInfo(BaseModel):
    date: str = None
    high: str = None
    low: str = None
    ymd: str = None
    weak: str = None
    sunrise: str = None
    sunset: str = None
    aqi: str = None
    fx: str = None
    fl: str = None
    type: str = None
    notice: str = None


class WeatherData(BaseModel):
    # Attributes' Pinyin names from third party
    shidu: str = None
    pm25: int = None
    pm10: int = None
    quality: str = None
    wendu: str = None
    ganmao: str = None
    forecast: list[WeatherDayInfo] = [WeatherDayInfo()]
    yesterday: WeatherDayInfo = WeatherDayInfo()


class WeatherSchema(BaseModel):
    message: str = None
    status: int = None
    date: str = None
    time: str = None
    cityInfo: CityInfo = CityInfo()
    data: WeatherData = WeatherData()
