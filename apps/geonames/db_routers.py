class GeoNamesRouter(object):
    """
    A router to control all database operations on models in the
    geonames application.
    """
    APP = 'geonames'
    DB = 'geonames'

    def db_for_read(self, model, **hints):
        """
        Attempts to read geonames models go to geonames db.
        """
        if model._meta.app_label == self.APP:
            return self.DB
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write geonames models go to geonames db.
        """
        if model._meta.app_label == self.APP:
            return self.DB
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the geonames app is involved.
        """
        if obj1._meta.app_label == self.APP or obj2._meta.app_label == self.APP:
            return True
        return None

    def allow_migrate(self, db, model):
        """
        Make sure the geonames app only appears in the geonames db.
        """
        if db == self.DB:
            return model._meta.app_label == self.APP
        elif model._meta.app_label == self.APP:
            return False
        return None
