import os
from sqlalchemy import create_engine

import urllib


        
                
class Config(object):
    SECRET_KEY = 'Clave nueva'
    SESSION_COOKIE_SECRET = False 
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost:3306/pizzas'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        