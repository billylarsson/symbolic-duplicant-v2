from PyQt5                     import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap
from bscripts.database_stuff   import DB, Translate, sqlite
from bscripts.preset_colors    import *
from bscripts.settings_widgets import GLOBALHighLight, GODLabel, MovableScrollWidget
from bscripts.tricks           import tech as t
import gzip
import os, paramiko
import shutil
import time

pos = t.pos
style = t.style

def ssh_command(command, sleep=1):
    s = paramiko.SSHClient()
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    s.load_system_host_keys()
    s.connect(
        t.config('nas_ssh', curious=True),
        '22',
        t.config('nas_login', curious=True),
        t.config('nas_pwd', curious=True)
    )
    s.exec_command(command)
    time.sleep(sleep)
    s.close()

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
                tmpfile = t.tmp_file(url, hash=True, days=1, extension='gz')
                file = t.download_file(url, tmpfile, days=1)
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

    makeimdb = RefreshImdb(
        place=self,
        mouse=True,
        main=self,
    )
    t.pos(makeimdb, size=[200,50], bottom=self.height()-1)
    makeimdb.setText('UPDATE IMdb')
    t.signal_highlight()

class CoverTurner(MovableScrollWidget):
    def __init__(self, candidates, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pos(self, width=480)
        self.overwrite = False
        self.data = data
        self.candidates = candidates
        self.make_title()

        self.signal.stringdelivery.connect(self.set_this_cover)
        self.signal.error.connect(lambda: self.title.setText('ERROR!'))
        self.signal.killswitch.connect(self.killme)

        self.cover = GODLabel(place=self.backplate)
        self.widgets.append(self.cover)
        pos(self.cover, width=self.title, height=self.title.width() * 1.5)
        style(self.cover, background=BLACK, color=WHITESMOKE)
        style(self.title, background='rgb(20,20,40)', color=WHITE)
        style(self.backplate, background=BLACK)
        style(self.toolplate, background=GRAY11)

        self.expand_me()
        self.make_next_prev_buttons()
        self.make_implement_button()
        self.make_search_bar()
        self.change_candidate()

    def manual_search(self):
        if not self.lineedit.text().strip():
            self.title.setText('oooh, please...!')
            return

        name, years, episode = self.parent.search_this_string(searchstring=self.lineedit.text().strip())
        data = self.parent.gather_imdb_candidates(name, years, episode)

        if data:
            self.candidates = data
            self.change_candidate()
        else:
            self.title.setText('FOUND NOTHING!')

        self.make_next_prev_buttons()

    def mouseReleaseEvent(self, ev):
        if ev.button() == 2:
            self.signal.killswitch.emit()

    def make_search_bar(self):
        self.lineedit = QtWidgets.QLineEdit(self.toolplate)
        self.lineedit.setTextMargins(10,0,10,0)
        self.lineedit.returnPressed.connect(self.manual_search)
        self.lineedit.show()
        self.toolplate.widgets.append(self.lineedit)
        pos(self.lineedit, coat=self.implement_btn, below=self.implement_btn)
        style(self.lineedit, background=GRAY11, color=WHITESMOKE)
        t.tooltip(self.lineedit, 'SMART: Battlestar Galactica S01E09 2012')
        self.expand_me()

    def killme(self):
        self.close()


    def implement_file(self):
        loc = self.get_distant_path_object()

        if not os.path.exists(loc.folder):
            ssh_command(f'mkdir -m 777 "{loc.folder}"')
            if os.path.exists(loc.full_path):
                self.title.setText(f'MADE FOLDER: {loc.folder.split(os.sep)[-1]}')
            else:
                self.title.setText('CREATING FOLDER FAILED')

        if os.path.exists(loc.full_path) and self.overwrite:
            os.remove(loc.full_path)
            os.sync()
            time.sleep(0.1)

        if not os.path.exists(loc.full_path):
            try: os.symlink(self.data['path'], loc.full_path)
            except PermissionError: self.title.setText(f'PERMISSION ERROR')
        else:
            self.title.setText('SYMBOLIC LINK ALREADY EXISTS?')
            t.highlight_style(self.implement_btn, name='overwrite')
            self.implement_btn.setText('OVERWRITE')
            self.overwrite = True
            t.signal_highlight()
            return

        os.sync()
        time.sleep(0.1)

        if os.path.islink(loc.full_path):
            self.title.setText('LINK SUCCESSFULLY CREATED')
            self.data['category'] = 'linked'
            self.change_to_unimplement_button()

    def unimplement_file(self):
        loc = self.get_distant_path_object()
        if os.path.islink(loc.full_path):

            os.remove(loc.full_path)

            self.title.setText('LINK SUCCESSFULLY REMOVED')
            self.data['category'] = 'unlinked'
            self.change_to_implementing_button()

            for walk in os.walk(loc.folder):
                if not walk[1] and not walk[2]:
                    shutil.rmtree(walk[0])
                    self.title.setText('LINK REMOVED and FOLDER DELETED')
                break

    def get_distant_path_object(self):
        if self.candidates[0][DB.titles.type] == 'movie':
            path = t.config('movie_folder')
            if not path:
                self.title.setText('MISSING MOVIE FOLDER')
                return

            loc = t.separate_file_from_folder(path + os.sep + self.candidates[0][DB.titles.title])
            path = self.data['path'].split(os.sep)[-1]
            loc = t.separate_file_from_folder(loc.path + os.sep + path)
        else:
            path = t.config('tv_folder')
            if not path:
                self.title.setText('MISSING TV-SHOWS FOLDER')
                return

            loc = t.separate_file_from_folder(path + os.sep + self.candidates[0][DB.titles.title])
            ext = self.data['path'].lower().split('.')[-1]
            episode = self.parent.get_episode(self.data['path'])
            if episode: episode = episode[0]
            else: episode = ""
            fname = f"{self.candidates[0][DB.titles.title]} {episode}.{ext}"
            loc = t.separate_file_from_folder(loc.path + os.sep + fname)

        return loc

    def make_implement_button(self):
        class BTN(GODLabel, GLOBALHighLight):
            def mouseReleaseEvent(self, ev):

                if self.parent.data['category'] == 'unlinked':
                    self.parent.implement_file()

                elif self.parent.data['category'] == 'linked':
                    self.parent.unimplement_file()

                t.signal_highlight()

        self.implement_btn = BTN(place=self.toolplate, mouse=True, center=True, qframebox=True, parent=self)
        self.toolplate.widgets.append(self.implement_btn)
        pos(self.implement_btn, width=self.title, below=self.title, height=self.title.height() * 0.8)
        self.expand_me()

    def change_to_implementing_button(self):
        if self.data['category'] == 'unlinked':
            t.highlight_style(self.implement_btn, name='implement')
            self.implement_btn.setText('IMPLEMENT')

    def change_to_unimplement_button(self):
        if self.data['category'] == 'linked':
            t.highlight_style(self.implement_btn, name='unimplement')
            self.implement_btn.setText('UN-IMPLEMENT')

    def make_next_prev_buttons(self):
        if self.candidates and len(self.candidates) > 1:

            class BTN(GODLabel, GLOBALHighLight):
                def mouseReleaseEvent(self, ev):
                    self.parent.change_candidate(**self.kwargs)

            if 'next_button' not in dir(self):
                self.next_button = BTN(place=self.title, qframebox=True, parent=self, mouse=True)
                self.next_button.kwargs = dict(next=True)
                pos(self.next_button, height=self.title, width=20, right=self.title)
                t.tooltip(self.next_button, 'SCROLL FORWARD')
                t.highlight_style(self.next_button, name='next_back')

            if 'prev_button' not in dir(self):
                self.prev_button = BTN(place=self.title, qframebox=True, parent=self, mouse=True)
                self.prev_button.kwargs = dict(previous=True)
                pos(self.prev_button, height=self.title, width=20)
                t.tooltip(self.prev_button, 'SCROLL BACK')
                t.highlight_style(self.prev_button, name='next_back')
        else:
            if 'next_button' in dir(self):
                self.next_button.close()
                del self.next_button
            if 'prev_button' in dir(self):
                self.prev_button.close()
                del self.prev_button

    def set_this_cover(self, path, store=True):
        self.cover.clear()
        pixmap = QPixmap(path).scaledToWidth(self.cover.width(), QtCore.Qt.SmoothTransformation)
        self.cover.setPixmap(pixmap)
        pos(self.cover, height=pixmap)
        self.set_proper_title()
        self.expand_me()
        t.signal_highlight()

        if store:
            self.store_cover_to_cache(path)

    def set_proper_title(self):
        text = self.candidates[0][DB.titles.title]

        if self.lineedit.text():
            searchstring = self.lineedit.text().strip()
        else:
            searchstring = self.data['path']

        _, _, episode = self.parent.search_this_string(searchstring=searchstring)
        if episode:
            text += f" {episode[0].upper()}"

        self.title.setText(text)

    def store_cover_to_cache(self, path):
        blob = t.make_image_into_blob(path)
        data = sqlite.execute('select * from imgcache where tconst = (?)', self.candidates[0][DB.titles.tconst])
        if not data:
            query, values = sqlite.empty_insert_query('imgcache')
            values[DB.imgcache.tconst] = self.candidates[0][DB.titles.tconst]
            values[DB.imgcache.image] = blob
            sqlite.execute(query, values)
        else:
            sqlite.execute('update imgcache set image = (?) where tconst = (?)', blob, self.candidates[0][DB.titles.tconst],)

    def change_candidate(self, next=False, previous=False):
        if not self.candidates:
            return

        if next:
            self.candidates.insert(-1, self.candidates[0])
            self.candidates.pop(0)

        elif previous:
            self.candidates.insert(0, self.candidates[-1])
            self.candidates.pop(-1)

        data = sqlite.execute('select * from imgcache where tconst = (?)', self.candidates[0][DB.titles.tconst])
        if data:
            path = t.blob_path_from_blob_object(data[DB.imgcache.image])
            self.set_this_cover(path, store=False)
        else:
            self.title.setText('DOWNLOADING COVER')
            t.thread(self.download_imdb_cover, slave_args=(self.candidates[0],))

        self.change_to_implementing_button()
        self.change_to_unimplement_button()
        self.show_year_genre_runtime_type()
        self.overwrite = False

    def show_year_genre_runtime_type(self):
        pass

    def download_imdb_cover(self, db_input):
        left = '<meta property="og:image" content="'
        right = '"/>'

        url = 'https://www.imdb.com/title/' + db_input[DB.titles.tconst] + '/'

        file = t.download_file(url, reuse=True)

        with open(file) as f:
            content = f.read()
            content = content.split('\n')
            for i in content:
                if left in i:
                    cut1 = i.find(left)
                    cut2 = i[cut1:].find(right) + cut1
                    if cut1 < cut2:
                        image_url = i[cut1 + len(left):cut2]
                        rv = t.download_file(image_url, reuse=True)
                        if rv:
                            self.signal.stringdelivery.emit(rv)
                            return

        self.signal.error.emit(dict(message='DOWNLOAD ERROR'))
