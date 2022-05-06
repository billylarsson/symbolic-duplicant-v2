from bscripts.sqlite_handler import SQLite
import os

sqlite = SQLite(
    DATABASE_FILENAME=os.environ['DATABASE_FILENAME'],
    DATABASE_FOLDER=os.environ['DATABASE_FOLDER'],
    DATABASE_SUBFOLDER=os.environ['DATABASE_SUBFOLDER'],
    INI_FILENAME=os.environ['INI_FILENAME'],
    INI_FILE_DIR=os.environ['INI_FILE_DIR'],
    ini_variable='local_database',
)

class DB:
    class skipped:
        local_path = sqlite.db_sqlite('skipped', 'local_path')
        
    class titles:
        tconst = sqlite.db_sqlite('titles', 'tconst')
        type = sqlite.db_sqlite('titles', 'type')
        title = sqlite.db_sqlite('titles', 'title')
        start_year = sqlite.db_sqlite('titles', 'start_year', 'integer')
        end_year = sqlite.db_sqlite('titles', 'end_year', 'integer')
        runtime = sqlite.db_sqlite('titles', 'runtime', 'integer')

    class ratings:
        tconst = sqlite.db_sqlite('ratings', 'tconst', auto=False)
        average = sqlite.db_sqlite('ratings', 'average', 'float')
        votes = sqlite.db_sqlite('ratings', 'votes', 'integer')

    class settings:
        config = sqlite.db_sqlite('settings', 'config', 'blob')

    class imgcache:
        tconst = sqlite.db_sqlite('imgcache', 'tconst', 'config')
        image = sqlite.db_sqlite('imgcache', 'image', 'config', 'blob')

class Translate:
    class titles:
        tconst = DB.titles.tconst
        titleType = DB.titles.type
        primaryTitle = DB.titles.title
        startYear = DB.titles.start_year
        endYear = DB.titles.end_year
        runtimeMinutes = DB.titles.runtime

    class ratings:
        tconst = DB.ratings.tconst
        averageRating = DB.ratings.average
        numVotes = DB.ratings.votes

