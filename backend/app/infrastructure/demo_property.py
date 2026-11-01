"""The single fictional property this proof of concept sells for."""
from app.domain.hotel import Contact, Property

DEMO_PROPERTY = Property(
    name="Hotel A",
    city="Lisbon",
    address="Street A 1, Lisbon, Portugal",
    currency="EUR",
    room_types=("Standard King", "Standard Double", "Deluxe King", "Junior Suite"),
    dorm=Contact("DORM A", "Director of Revenue Management", "dorm.a@hotela.example"),
    salesperson=Contact("Umar Azhar", "Senior Group Sales Manager", "umar.azhar@hotela.example"),
)
