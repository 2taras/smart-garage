from datetime import datetime
import random
from .db import SystemConfig

class ConfigManager:
    @staticmethod
    def get_value(db, key: str):
        config = db.query(SystemConfig).filter_by(key=key).first()
        return config.value if config else None

    @staticmethod
    def set_value(db, key: str, value: str):
        config = db.query(SystemConfig).filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            db.add(config)
        db.commit()

    @staticmethod
    def get_temp_password(db):
        password = ConfigManager.get_value(db, 'temp_password')
        if not password:
            password = str(random.randint(1000, 9999))
            ConfigManager.set_value(db, 'temp_password', password)
        return password

    @staticmethod
    def reset_temp_password(db):
        new_password = str(random.randint(1000, 9999))
        ConfigManager.set_value(db, 'temp_password', new_password)
        return new_password