
from pickle import load
import pytest
import time
import os
import nest_asyncio
import json
import asyncio
import sqlalchemy
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from pydbantic import DataBaseModel, Database
from pydbantic.cache import Redis
from tests.models import Department, Employee, EmployeeInfo, Positions




DB_PATH = {
    'sqlite': 'sqlite:///test.db',
    'mysql': 'mysql://josh:abcd1234@127.0.0.1/database',
    'postgres': 'postgresql://postgres:abcd1234@localhost/database'
}

DB_URL = DB_PATH[os.environ['ENV']]

@pytest.fixture(scope="session")
def event_loop():
    nest_asyncio.apply()
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture()
def db_url():
    return DB_PATH[os.environ['ENV']]

@pytest.mark.asyncio
@pytest.fixture(params=[DB_URL])
async def empty_database_and_model_no_cache(request):
    db = await Database.create(
        request.param,
        tables=[Employee, 
                EmployeeInfo, 
                Positions,
                Department],
        cache_enabled=False,
        testing=True
    )
    yield db, Employee

@pytest.mark.asyncio
@pytest.fixture(params=[DB_URL])
async def database_with_cache(request):

    db = await Database.create(
            request.param,  
            tables=[
                Employee, 
                EmployeeInfo, 
                Positions,
                Department
            ],
            cache_enabled=True,
            testing=True
        )

    yield db, Employee
    db.metadata.drop_all()

    await db.cache.redis.flushall()
    await db.cache.redis.close()

@pytest.fixture()
async def empty_database_and_model_with_cache(database_with_cache):

    db = database_with_cache

    yield db, Employee

async def load_db(db):
    async with db:
        for i in range(200):
            employee = Employee(**json.loads(
        f"""
  {{
    "employee_id": "abcd{i}",
    "employee_info": {{
      "ssn": "{i}",
      "first_name": "joe",
      "last_name": "last",
      "address": "{i} lane",
      "address2": null,
      "city": null,
      "zip": null
    }},
    "position": [{{
      "position_id": "1234",
      "name": "manager",
      "department": {{
        "department_id": "5678",
        "name": "hr",
        "company": "abc company",
        "is_sensitive": false
      }}
    }}],
    "salary": 0,
    "is_employed": true,
    "date_employed": null
  }}""")
    )
            await employee.insert()

@pytest.mark.asyncio
@pytest.fixture()
async def loaded_database_and_model(database_with_cache):
    db, Employee = database_with_cache
    await load_db(db)
    yield db, Employee

@pytest.mark.asyncio
@pytest.fixture()
async def loaded_database_and_model_no_cache(empty_database_and_model_no_cache):
    db = empty_database_and_model_no_cache
    for i in range(200):
        employee = Employee(**json.loads(
        f"""
  {{
    "employee_id": "abcd{i}",
    "employee_info": {{
      "ssn": "1234",
      "first_name": "joe",
      "last_name": "last",
      "address": "123 lane",
      "address2": null,
      "city": null,
      "zip": null
    }},
    "position": [{{
      "position_id": "1234",
      "name": "manager",
      "department": {{
        "department_id": "5678",
        "name": "hr",
        "company": "abc company",
        "is_sensitive": false
      }}
    }}],
    "salary": 0,
    "is_employed": true,
    "date_employed": null
  }}""")
    )

        await employee.insert()

    yield db, Employee

@pytest.mark.asyncio
@pytest.fixture()
async def loaded_database_and_model_with_cache(database_with_cache):
    db = database_with_cache
    for i in range(20):
        employee = Employee(**json.loads(
        f"""
  {{
    "employee_id": "abcd{time.time()}",
    "employee_info": {{
      "ssn": "{i}1234",
      "first_name": "joe",
      "last_name": "last",
      "address": "123 lane",
      "address2": null,
      "city": null,
      "zip": null
    }},
    "position": [{{
      "position_id": "1234",
      "name": "manager",
      "department": {{
        "department_id": "5678",
        "name": "hr",
        "company": "abc company",
        "is_sensitive": false
      }}
    }}],
    "salary": 0,
    "is_employed": true,
    "date_employed": null
  }}""")
    )

        await employee.insert()

    yield db, Employee

@pytest.mark.asyncio
@pytest.fixture()
def init_model():
    with open('example.py', 'w') as e:
        e.write(
            """
from pydbantic import DataBaseModel
class Data(DataBaseModel):
    a: int
    b: float
    c: str = 'test'
    i: str
"""
        )

    from example import Data
    yield Data
    with open('example.py', 'w') as e:
        e.write(
            """
from pydbantic import DataBaseModel
class Data(DataBaseModel):
    a: int
    b: float
    c: str = 'test'
    d: tuple = (1,2)
    i: str
"""
        )

@pytest.fixture()
def new_model_1():
    from example import Data
    yield Data
    with open('example.py', 'w') as e:
        e.write(
            """
from pydbantic import DataBaseModel
class Data(DataBaseModel):
    a: int
    b: float
    c: str = 'test'
    d: list = [1,2]
    i: str
"""
        )

@pytest.fixture()
def new_model_2():
    with open('example.py', 'w') as e:
        e.write(f"""
from pydbantic import DataBaseModel
class Data(DataBaseModel):
    __renamed__ = [
        {{'old_name': 'b', 'new_name': 'b_new'}}
    ]
    a: int
    b_new: float
    c: str = 'test'
    d: list = [1,2]
    i: str
""")
    from example import Data
    yield Data
    with open('example.py', 'w') as e:
        e.write(
            """
import uuid
from pydbantic import DataBaseModel, PrimaryKey, Default

def get_uuid():
    return str(uuid.uuid4())

class Data(DataBaseModel):
    a: int
    b_new: float
    c: str
    d: list = PrimaryKey()
    e: str = Default(default=get_uuid)
    i: str
"""
        )

@pytest.fixture()
def new_model_3():
    from example import Data
    yield Data
    with open('example.py', 'w') as e:
        e.write(
            """
import uuid
from pydbantic import DataBaseModel, PrimaryKey, Default

def get_uuid():
    return str(uuid.uuid4())

class Data(DataBaseModel):
    a: int
    b_new: float
    c: str
    d: list
    e: str = PrimaryKey(default=get_uuid)
    i: str
"""
        )
@pytest.fixture()
def new_model_4():
    from example import Data
    yield Data
    with open('example_sub.py', 'w') as e:
        e.write(f"""
# {time.time()}
import uuid
from pydantic import BaseModel

def get_uuid():
    return str(uuid.uuid4())

class SubData(BaseModel):
    a: int = 1
    b: float = 1.0

""")
    with open('example.py', 'w') as e:
        e.write(
            """

from pydbantic import DataBaseModel, PrimaryKey, Default
from example_sub import get_uuid, SubData

class Data(DataBaseModel):
    a: int
    b_new: float
    c: str
    d: list
    e: str = PrimaryKey(default=get_uuid)
    i: str
    sub: SubData = None
"""
        )
@pytest.fixture()
def new_model_5():
    from example import Data, SubData
    yield Data, SubData
    os.remove('example_sub.py')
    os.remove('example.py')

@pytest.fixture()
def new_model_6():
    yield
    with open('example_sub.py', 'w') as e:
        e.write(f"""
# {time.time()}
import uuid
from pydantic import BaseModel

def get_uuid():
    return str(uuid.uuid4())

class SubData(BaseModel):
    a: int = 1
    b: float = 1.0

""")
    with open('example.py', 'w') as e:
        e.write(
            """
from typing import Optional
from pydbantic import DataBaseModel, PrimaryKey, Default
from example_sub import get_uuid, SubData

class Related(DataBaseModel):
    f: str = PrimaryKey(default=get_uuid)
    g: str = 'abcd1234'

class Data(DataBaseModel):
    a: int
    b_new: float
    c: str
    d: list
    e: str = PrimaryKey(default=get_uuid)
    i: str
    sub: SubData = None
    related: Optional[Related] = None
"""
        )

@pytest.fixture()
def new_model_7():
    from example import Data, SubData, Related
    yield Data, SubData, Related
    with open('example_sub.py', 'w') as e:
        e.write(f"""
# {time.time()}
import uuid
from pydantic import BaseModel

def get_uuid():
    return str(uuid.uuid4())

class SubData(BaseModel):
    a: int = 1
    b: float = 1.0

""")
    with open('example.py', 'w') as e:
        e.write(
            """

from pydbantic import DataBaseModel, PrimaryKey, Default
from example_sub import get_uuid, SubData

class Related(DataBaseModel):
    f: str = PrimaryKey(default=get_uuid)
    g: str = 'abcd1234'

class Data(DataBaseModel):
    a: int
    b_new: float
    c: str
    d: list
    e: str = PrimaryKey(default=get_uuid)
    i: str
    sub: SubData = None
    related: Optional[Related] = None
"""
        )


def endpoint_router():
    router = APIRouter()
    @router.post('/example/create')
    async def create_new_example(employee: Employee):
        return await employee.insert()
    
    return router

@pytest.mark.asyncio()
@pytest.fixture()
async def fastapi_app_with_loaded_database(loaded_database_and_model):
    app = FastAPI()

    app.include_router(endpoint_router())

    @app.post('/employee')
    async def new_example(employee: Employee):
        return await employee.insert()

    @app.get('/employees')
    async def view_employees():
        employees = await Employee.all()
        return employees

    return app