class LegacyRouter:
    """
    Router para direccionar modelos entre default y legacy
    """
    
    def db_for_read(self, model, **hints):
        """Modelos legacy van a BD legacy, los demás a default"""
        if hasattr(model, '_legacy_db'):
            return 'legacy'
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Modelos legacy van a BD legacy, los demás a default"""
        if hasattr(model, '_legacy_db'):
            return 'legacy'
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Permitir relaciones si están en la misma BD"""
        db1 = getattr(obj1, '_state', None)
        db2 = getattr(obj2, '_state', None)
        
        if db1 and db2:
            return db1.db == db2.db
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Solo migrar modelos de Django a 'default'
        Los modelos legacy NO se migran
        """
        if db == 'legacy':
            return False  # No migrar NADA a legacy
        return True  # default acepta todas las migraciones normales