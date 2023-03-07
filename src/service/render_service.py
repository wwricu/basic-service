from fastapi.templating import Jinja2Templates

from schemas import WeatherSchema


class RenderService:
    __templates = Jinja2Templates(directory="templates")

    @classmethod
    def wind_to_mps(cls, level: int | str) -> int:
        if isinstance(level, str):
            level = int(level)
        match level:
            case 1 | 2:
                return level
            case 3:
                return 4
            case 4 | 5 | 6 | 7 | 8 | 9:
                return 3 * level - 6
            case 10 | 11 | 12:
                return 4 * level - 13
            case _:
                return 0

    @classmethod
    def daily_mail(cls, weather: WeatherSchema) -> str:
        return cls.__templates.get_template('daily_mail.html').render(
            city=weather.cityInfo.city,
            updated_time=weather.cityInfo.updateTime,
            type=weather.data.forecast[0].type,
            low=weather.data.forecast[0].low[2:],
            high=weather.data.forecast[0].high[2:],
            humidity=weather.data.shidu,
            quality=weather.data.quality,
            wind_speed=cls.wind_to_mps(
                weather.data.forecast[0].fl[:-1]
            ) * 3.6
        )
