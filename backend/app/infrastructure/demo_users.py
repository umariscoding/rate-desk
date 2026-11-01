"""The two demo accounts: the salesperson and the DORM of the demo property."""
from app.domain.user import Role, User
from app.infrastructure.demo_property import DEMO_PROPERTY

SALESPERSON_LOGIN = User("umar", DEMO_PROPERTY.salesperson.name, Role.SALESPERSON)
DORM_LOGIN = User("dorm", DEMO_PROPERTY.dorm.name, Role.DORM)
DEMO_USERS = (SALESPERSON_LOGIN, DORM_LOGIN)
