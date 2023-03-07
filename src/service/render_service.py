from datetime import datetime

from fastapi.templating import Jinja2Templates

from schemas import WeatherSchema


class RenderService:
    __templates = Jinja2Templates(directory="templates")

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
            wind_speed=weather.data.forecast[0].fl
        )

    @classmethod
    def two_fa_code(cls, two_fa_code: str) -> str:
        return cls.__templates.get_template(
            'two_fa_code.html'
        ).render(
            two_fa_code=two_fa_code,
            time=datetime.now().strftime('%c')
        )
