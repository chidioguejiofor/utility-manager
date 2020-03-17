import flask_migrate


class TestMigrations:
    def test_migrations(self, app):
        flask_migrate.upgrade()
        flask_migrate.downgrade(revision='41efd0e44e75')
        flask_migrate.downgrade()
        flask_migrate.upgrade()
        flask_migrate.downgrade(revision='41efd0e44e75')
        flask_migrate.downgrade()
