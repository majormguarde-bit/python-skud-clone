import fdb
import os
import logging

logger = logging.getLogger(__name__)

class FirebirdClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebirdClient, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        """Establish connection to Firebird database"""
        try:
            # Import here to avoid circular dependency
            from app.models import Settings
            
            # Helper to get setting with fallback
            def get_setting(key, default):
                try:
                    s = Settings.query.filter_by(key=key).first()
                    return s.value if s else default
                except:
                    return default

            host = get_setting('FIREBIRD_HOST', os.environ.get('FIREBIRD_HOST', 'localhost'))
            try:
                port = int(get_setting('FIREBIRD_PORT', os.environ.get('FIREBIRD_PORT', '3050')))
            except ValueError:
                port = 3050
                
            database = get_setting('FIREBIRD_DATABASE', os.environ.get('FIREBIRD_DATABASE', 'database.fdb'))
            user = get_setting('FIREBIRD_USER', os.environ.get('FIREBIRD_USER', 'sysdba'))
            password = get_setting('FIREBIRD_PASSWORD', os.environ.get('FIREBIRD_PASSWORD', 'masterkey'))
            charset = get_setting('FIREBIRD_CHARSET', os.environ.get('FIREBIRD_CHARSET', 'WIN1251'))
            
            dsn = f"{host}/{port}:{database}"
            
            logger.info(f"Connecting to Firebird: {dsn} as {user}")
            
            self.connection = fdb.connect(
                dsn=dsn,
                user=user,
                password=password,
                charset=charset
            )
            logger.info("Successfully connected to Firebird database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Firebird: {e}")
            self.connection = None
            return False

    def disconnect(self):
        """Close connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Firebird connection closed")
            except Exception as e:
                logger.error(f"Error closing Firebird connection: {e}")
            finally:
                self.connection = None

    def reconnect(self):
        """Reconnect to database"""
        logger.info("Reconnecting to Firebird database...")
        self.disconnect()
        return self.connect()

    def get_connection(self):
        """Get current connection, reconnect if necessary"""
        if self.connection is None:
            self.connect()
        return self.connection
    
    def is_connected(self):
        return self.connection is not None

# Global instance
fb_client = FirebirdClient()
