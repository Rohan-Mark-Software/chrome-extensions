import os


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Cache
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    CACHE_REDIS_DB = int(os.getenv('REDIS_DB', 0))
    CACHE_REDIS_URL = f"redis://{CACHE_REDIS_HOST}:{CACHE_REDIS_PORT}/{CACHE_REDIS_DB}"
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))
    
    # Search
    MAX_RESULTS_LIMIT = 50
    DEFAULT_MAX_RESULTS = 10
    THREAD_POOL_SIZE = 2
    REQUEST_TIMEOUT = 10
    
    # User Agent
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    CACHE_TYPE = 'SimpleCache'


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}