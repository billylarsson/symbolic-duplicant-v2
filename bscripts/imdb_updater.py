from PyQt5                     import QtCore, QtGui, QtWidgets
from bscripts.preset_colors    import *
from bscripts.settings_widgets import GLOBALHighLight, GODLabel
from bscripts.tricks           import tech as t
from bscripts.database_stuff   import sqlite, DB, Translate
import gzip
import os
import shutil
import time

def imdb_things(self):
    class RefreshButton(GODLabel, GLOBALHighLight):
        def __init__(self, *args, **kwargs):
            super().__init__(
                deactivated_on=dict(background=BLACK, color=WHITE),
                deactivated_off=dict(background=GRAY, color=BLACK),
                *args, **kwargs
            )
            self.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
            self.setFrameShape(QtWidgets.QFrame.Box)
            self.setLineWidth(1)


    class RefreshImdb(RefreshButton):
        def download_and_update(self, signal):
            manylist = []

            def download(url):
                file = t.download_file(url, days=1)
                if not os.path.exists(file):
                    return False
                else:
                    return file

            def unpack(file, url):
                tmpfile = t.tmp_file(file_of_interest=url, hash=True, delete=True, extension='tsv')
                try:
                    with gzip.open(file, 'rb') as f_in:
                        with open(tmpfile, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                except:
                    return False

                if not os.path.exists(tmpfile):
                    return False

                return tmpfile

            def get_cycle_stuff(f):
                content = f.read().split('\n')
                headers = content[0].split('\t')
                for count, i in enumerate(headers):
                    if i == 'titleType':
                        typeindex = count

                return content, headers, typeindex

            signal.progress.emit(dict(text='DOWNLOADING...'))
            url = 'https://datasets.imdbws.com/title.basics.tsv.gz'
            file = download(url)
            if not file:
                signal.error.emit(dict(text='DOWNLOAD FAILED'))
                return False

            signal.progress.emit(dict(text='UNPACKING...'))
            tsvfile = unpack(file, url)
            if not tsvfile:
                signal.error.emit(dict(text='UNPACKING FAILED'))
                return False

            includetypes = {'movie', 'tvSeries', 'tvMiniSeries'}

            checkpoint = 10000
            timer = time.time()
            with open(tsvfile) as f:
                signal.progress.emit(dict(text='UPDATING...'))
                content, headers, typeindex = get_cycle_stuff(f)
                query, values_org = sqlite.empty_insert_query('titles')
                sqlite.execute('delete from titles;') # deletes everything before starting

                for checkcount, i in enumerate(content[1:]):
                    data = i.split('\t')

                    if len(data) != len(headers):  # discards random errors (last row)
                        continue

                    if data[typeindex] not in includetypes:
                        continue

                    values = [None] * len(values_org)  # fresh values

                    for count in range(len(headers)):
                        if data[count] == '\\N':  # None
                            continue

                        elif headers[count] == 'originalTitle':  # that data seems unnessesary atm
                            continue

                        elif headers[count] == 'isAdult':  # genre/Adult ALMOST provides same knowledge
                            continue

                        elif headers[count] == 'genres':
                            genres = data[count].split(',')
                            for genre in genres:

                                if genre == '\\N':  # None
                                    continue

                                if not getattr(DB.titles, genre, None):
                                    if manylist:
                                        sqlite.execute(query, values=manylist)  # empties stack
                                        manylist = []

                                    column = sqlite.db_sqlite('titles', genre)
                                    setattr(DB.titles, genre, column)
                                    query, values_org = sqlite.empty_insert_query('titles')

                                    for prolong in range(len(values_org) - len(values)):  # prolong values
                                        values.append(None)

                                values[getattr(DB.titles, genre)] = True

                        else:
                            index = getattr(Translate.titles, headers[count])

                            for cc in range(len(data[count])):  # forces string-int into int

                                if not data[count][cc].isdigit():
                                    values[index] = data[count]
                                    break

                                elif cc + 1 == len(data[count]):
                                    values[index] = int(data[count])

                    manylist.append(tuple(values))
                    if checkcount > checkpoint and time.time() - timer > 0.25:
                        timer = time.time()
                        checkpoint += 10000
                        signal.progress.emit(dict(
                            progress=checkcount / len(content),
                        ))

            if manylist:
                signal.progress.emit(dict(progress=1, text='INJECTING'))
                sqlite.execute(query, values=manylist)
                signal.finished.emit()
            else:
                signal.error.emit(dict(text='NOTHING?'))

        def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.start_update_process()

        def start_update_process(self):
            def show_progress(progressdict, *args, **kwargs):

                if 'text' in progressdict:
                    if 'transparent_label' in dir(self):
                        self.transparent_label.setText(progressdict['text'])
                    else:
                        self.setText(progressdict['text'])

                if 'progress' in progressdict:
                    if 'progresslabel' not in dir(self):
                        self.progresslabel = GODLabel(place=self)
                        self.progresslabel.setFrameShape(QtWidgets.QFrame.Box)
                        self.progresslabel.setLineWidth(1)
                        t.style(self.progresslabel, background=GREEN, color=BLACK)
                        t.pos(self.progresslabel, height=self, width=0)
                        self.transparent_label = GODLabel(place=self)
                        t.pos(self.transparent_label, inside=self)
                        t.style(self.transparent_label, background='rgba(0,0,0,0)', color=BLACK, font=16)
                        self.transparent_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

                    width = self.width() * progressdict['progress']
                    if width > self.progresslabel.width() + 1:
                        t.pos(self.progresslabel, width=width)
                        if 'text' not in progressdict:
                            percent = str(round(progressdict['progress'] * 100,2)) + '%'
                            self.transparent_label.setText(percent)
                            self.setText("")

            def show_error(errordict, *args, **kwargs):
                if 'progresslabel' in dir(self):
                    self.progresslabel.close()
                    del self.progresslabel
                if 'transparent_label' in dir(self):
                    self.transparent_label.close()
                    del self.transparent_label

                self.setText(errordict['text'])

            def show_finished(*args, **kwargs):
                if 'progresslabel' in dir(self):
                    self.progresslabel.close()
                    del self.progresslabel
                if 'transparent_label' in dir(self):
                    self.transparent_label.close()
                    del self.transparent_label

                self.setText('JOBS DONE!')

            signal = t.signals()
            signal.progress.connect(show_progress)
            signal.error.connect(show_error)
            signal.finished.connect(show_finished)
            t.start_thread(self.download_and_update, slave_args=signal)

    self.refresh_imdb_button = RefreshImdb(
        place=self,
        mouse=True,
        main=self,
    )
    t.pos(self.refresh_imdb_button, size=[200,50], bottom=self.height()-1)
    self.refresh_imdb_button.setText('UPDATE IMdb')
    t.signal_highlight()