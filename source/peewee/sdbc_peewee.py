import re
import warnings
from librepy.pybrex.values import pybrex_logger

try:
    from librepy.peewee import sdbc_dbapi
except ImportError:
    sdbc_dbapi = None

from librepy.peewee.peewee import (
    Database,
    PostgresqlDatabase,
    ImproperlyConfigured,
    OperationalError,
    InterfaceError,
)

logger = pybrex_logger(__name__)

class SDBCPostgresqlDatabase(PostgresqlDatabase):
    """
    Peewee Database subclass using the sdbc_dbapi DB-API 2.0 wrapper
    for PostgreSQL connections within LibreOffice.
    """

    param = '?'  # Explicitly use qmark style for SDBC

    def __init__(self, database, **kwargs):
        """
        Initializes the SDBCPostgresqlDatabase.

        :param str database: The name of the database to connect to.
        :param kwargs: Connection parameters for sdbc_dbapi.connect
        """
        if sdbc_dbapi is None:
            logger.error("sdbc_dbapi module not found")
            raise ImproperlyConfigured(
                'sdbc_dbapi module not found. '
                'Please ensure sdbc_dbapi.py is accessible.'
            )

        self._sdbc_connect_kwargs = kwargs.copy()

        sdbc_params = ['user', 'password', 'host', 'port', 'dsn', 'connect_timeout']
        peewee_params = ['thread_safe', 'autorollback', 'field_types',
                         'operations', 'autocommit', 'autoconnect', 'sequences']
        parent_kwargs = {}
        for key in list(self._sdbc_connect_kwargs.keys()):
            if key in sdbc_params:
                pass
            elif key in peewee_params:
                parent_kwargs[key] = self._sdbc_connect_kwargs.pop(key)

        parent_kwargs['thread_safe'] = False
        Database.__init__(self, database, **parent_kwargs)
        self.init(database, **self._sdbc_connect_kwargs)

    def connect(self, reuse_if_open=True):
        """
        Establish a connection and initialize transaction status.
        `reuse_if_open=True` is critical for connection reuse.
        """
        if not self.is_closed() and reuse_if_open:
            return True

        super(SDBCPostgresqlDatabase, self).connect(reuse_if_open=reuse_if_open)

        if not self.is_closed():
            self.transaction_status = self._state.conn.get_transaction_status
        else:
            logger.warning("Connection appears to be closed after connect attempt")

        return not self.is_closed()

    def init(self, database, **kwargs):
        """Stores connection parameters for later use in _connect."""
        self.database = database
        self.connect_params = kwargs
        self.deferred = not bool(database)

        self.connect_params.setdefault('database', self.database)
        self.connect_params.setdefault('user', kwargs.get('user'))
        self.connect_params.setdefault('password', kwargs.get('password'))
        self.connect_params.setdefault('host', kwargs.get('host'))
        self.connect_params.setdefault('port', kwargs.get('port', 5432))
        self.connect_params.setdefault('dsn', kwargs.get('dsn'))
        self.connect_params.setdefault('connect_timeout', kwargs.get('connect_timeout', 5))

        self.returning_clause = getattr(self, 'returning_clause', True)
        self.for_update = getattr(self, 'for_update', True)

        self.returning_clause = False

    def _connect(self):
        """Establish the database connection using sdbc_dbapi.connect."""
        if sdbc_dbapi is None:
            logger.error("sdbc_dbapi module not found in _connect()")
            raise ImproperlyConfigured('sdbc_dbapi module not found.')

        if self.deferred:
            logger.error("Database must be initialized before connecting")
            raise InterfaceError('Error, database must be initialized before connecting.')

        try:
            conn = sdbc_dbapi.connect(**self.connect_params)
            logger.info(f"Successfully connected via sdbc_dbapi")
            
            self.transaction_status = conn.get_transaction_status
            
            return conn
        except sdbc_dbapi.Error as e:
            logger.error(f"SDBC database error during connection: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting via SDBC: {e}")
            raise OperationalError(f"Unexpected error connecting via SDBC: {e}")

    def _initialize_connection(self, conn):
        """Initialize the connection after it's established."""
        try:
            conn.set_autocommit(True)
        except sdbc_dbapi.Error as e:
            logger.warning(f"Could not set autocommit=True on SDBC connection: {e}")
            warnings.warn(f"Could not set autocommit=True on SDBC connection: {e}")

    def _set_server_version(self, conn):
        """
        Hardcoded PostgreSQL server version to 9.3 to avoid connection issues
        during version detection.
        """
        self.server_version = (9, 3, 0)
        
        # This logic is kept to ensure peewee features are set correctly based on the hardcoded version.
        if self.server_version >= (9, 6, 0):
             self.safe_create_index = True
        else:
             self.safe_create_index = False

    def is_connection_usable(self):
        """
        Check if the SDBC connection is usable.
        This mimics peewee's psycopg2 implementation by checking transaction
        status, which is more efficient than a "ping" query.
        """
        if self.is_closed():
            return False

        conn = self._state.conn
        if conn is None:
            return False

        try:
            status = conn.get_transaction_status()
        except sdbc_dbapi.Error as e:
            logger.warning(f"Error getting transaction status: {e}")
            self.close()
            return False
        else:
            return status == sdbc_dbapi.TRANSACTION_STATUS_IDLE

    def get_binary_type(self):
        """
        Return the appropriate binary type constructor for SDBC.
        Overrides the parent method which depends on psycopg2.
        """
        # sdbc_dbapi defines Binary = bytes
        return sdbc_dbapi.Binary

    def last_insert_id(self, cursor, model):
        """
        Retrieve the last inserted ID using SELECT lastval()
        since RETURNING is disabled for SDBC.
        """
        try:
            cursor.execute("SELECT lastval()")
            result = cursor.fetchone()
            return result[0] if result else None
        except (sdbc_dbapi.Error, IndexError, TypeError) as e:
            logger.error(f"Could not retrieve lastval(): {e}")
            warnings.warn(f"Could not retrieve lastval(): {e}")
            return None

    # Override metadata methods to use '?' placeholders for SDBC
    def get_tables(self, schema=None):
        query = ('SELECT tablename FROM pg_catalog.pg_tables '
                 'WHERE schemaname = ? ORDER BY tablename')
        cursor = self.execute_sql(query, (schema or 'public',))
        return [table for table, in cursor.fetchall()]

    def get_views(self, schema=None):
        query = ('SELECT viewname, definition FROM pg_catalog.pg_views '
                 'WHERE schemaname = ? ORDER BY viewname')
        cursor = self.execute_sql(query, (schema or 'public',))
        from librepy.peewee.peewee import ViewMetadata
        return [ViewMetadata(view_name, sql.strip(' \\t;'))
                for (view_name, sql) in cursor.fetchall()]

    def get_indexes(self, table, schema=None):
        query = """
            SELECT
                i.relname, idxs.indexdef, idx.indisunique,
                array_to_string(ARRAY(
                    SELECT pg_get_indexdef(idx.indexrelid, k + 1, TRUE)
                    FROM generate_subscripts(idx.indkey, 1) AS k
                    ORDER BY k), ',')
            FROM pg_catalog.pg_class AS t
            INNER JOIN pg_catalog.pg_index AS idx ON t.oid = idx.indrelid
            INNER JOIN pg_catalog.pg_class AS i ON idx.indexrelid = i.oid
            INNER JOIN pg_catalog.pg_indexes AS idxs ON
                (idxs.tablename = t.relname AND idxs.indexname = i.relname)
            WHERE t.relname = ? AND t.relkind = ? AND idxs.schemaname = ?
            ORDER BY idx.indisunique DESC, i.relname;"""
        cursor = self.execute_sql(query, (table, 'r', schema or 'public'))
        from librepy.peewee.peewee import IndexMetadata
        return [IndexMetadata(name, sql.rstrip(' ;'), columns.split(','),
                              is_unique, table)
                for name, sql, is_unique, columns in cursor.fetchall()]

    def get_columns(self, table, schema=None):
        query = """
            SELECT column_name, is_nullable, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = ? AND table_schema = ?
            ORDER BY ordinal_position"""
        cursor = self.execute_sql(query, (table, schema or 'public'))
        pks = set(self.get_primary_keys(table, schema))
        from librepy.peewee.peewee import ColumnMetadata
        return [ColumnMetadata(name, dt, null == 'YES', name in pks, table, df)
                for name, null, dt, df in cursor.fetchall()]

    def get_primary_keys(self, table, schema=None):
        query = """
            SELECT kc.column_name
            FROM information_schema.table_constraints AS tc
            INNER JOIN information_schema.key_column_usage AS kc ON (
                tc.table_name = kc.table_name AND
                tc.table_schema = kc.table_schema AND
                tc.constraint_name = kc.constraint_name)
            WHERE
                tc.constraint_type = ? AND
                tc.table_name = ? AND
                tc.table_schema = ?"""
        ctype = 'PRIMARY KEY'
        cursor = self.execute_sql(query, (ctype, table, schema or 'public'))
        return [pk for pk, in cursor.fetchall()]

    def get_foreign_keys(self, table, schema=None):
        sql = """
            SELECT DISTINCT
                kcu.column_name, ccu.table_name, ccu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON (tc.constraint_name = kcu.constraint_name AND
                    tc.constraint_schema = kcu.constraint_schema AND
                    tc.table_name = kcu.table_name AND
                    tc.table_schema = kcu.table_schema)
            JOIN information_schema.constraint_column_usage AS ccu
                ON (ccu.constraint_name = tc.constraint_name AND
                    ccu.constraint_schema = tc.constraint_schema)
            WHERE
                tc.constraint_type = 'FOREIGN KEY' AND
                tc.table_name = ? AND
                tc.table_schema = ?"""
        cursor = self.execute_sql(sql, (table, schema or 'public'))
        from librepy.peewee.peewee import ForeignKeyMetadata
        return [ForeignKeyMetadata(row[0], row[1], row[2], table)
                for row in cursor.fetchall()]

    def sequence_exists(self, sequence):
        res = self.execute_sql("""
            SELECT COUNT(*) FROM pg_class, pg_namespace
            WHERE relkind='S'
                AND pg_class.relnamespace = pg_namespace.oid
                AND relname=?""", (sequence,))
        fetched = res.fetchone()
        return bool(fetched[0]) if fetched else False

    # Override table_exists to ensure it uses the overridden get_tables
    def table_exists(self, table_name, schema=None):
        from librepy.peewee.peewee import is_model
        if is_model(table_name):
            model = table_name
            table_name = model._meta.table_name
            schema = model._meta.schema
        
        return table_name in self.get_tables(schema=schema)

    def close(self):
        """Close the database connection."""
        logger.info("Closing SDBCPostgresqlDatabase connection")
        super(SDBCPostgresqlDatabase, self).close()

    def is_closed(self):
        """Check if the database connection is closed."""
        return super(SDBCPostgresqlDatabase, self).is_closed()