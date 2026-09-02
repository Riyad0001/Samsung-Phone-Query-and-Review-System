from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base()


class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), default="Samsung")
    display_size = Column(String(100))
    display_type = Column(String(100))
    resolution = Column(String(100))
    processor = Column(String(200))
    ram = Column(String(100))
    storage = Column(String(100))
    main_camera = Column(Text)
    selfie_camera = Column(Text)
    battery = Column(String(100))
    os_version = Column(String(100))
    weight = Column(String(100))
    dimensions = Column(String(200))
    price = Column(String(100))
    gsmarena_url = Column(String(500), unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "display_size": self.display_size,
            "display_type": self.display_type,
            "resolution": self.resolution,
            "processor": self.processor,
            "ram": self.ram,
            "storage": self.storage,
            "main_camera": self.main_camera,
            "selfie_camera": self.selfie_camera,
            "battery": self.battery,
            "os_version": self.os_version,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "price": self.price,
        }

    def __repr__(self):
        return f"<Phone(name='{self.name}')>"


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()