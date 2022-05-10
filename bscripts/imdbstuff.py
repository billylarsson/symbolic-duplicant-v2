from PyQt5                     import QtCore, QtGui, QtWidgets
from PyQt5.QtGui               import QPixmap
from bscripts.database_stuff   import DB, Translate, sqlite
from bscripts.preset_colors    import *
from PyQt5.QtCore              import QEvent
from bscripts.settings_widgets import GLOBALHighLight, GODLabel, EventFilter
from bscripts.settings_widgets import MovableScrollWidget
from bscripts.sshstuff         import ssh_command
from bscripts.tricks           import tech as t
import os, random, webbrowser
import shutil
import time

pos = t.pos
style = t.style

class TitleGenre(GODLabel, GLOBALHighLight):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hold = False

    def mousePressEvent(self, ev):
        self.hold = True
        self.parent.title.mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if not self.hold:
            self._highlight_signal.highlight.emit(self.type)
            self._lights_out()
            return

        self.parent.drag_widget(ev)

    def mouseReleaseEvent(self, ev):
        self.hold = False

class Episode(TitleGenre):
    def mouseDoubleClickEvent(self, a0):
        if a0.button() == 1:
            self.show_episode(1)
        else:
            self.show_episode(-1)

    def show_episode(self, add=0):
        episode = self.parent.get_episode()
        if episode:
            ep = int(episode[0][4:6]) + add
            if len(str(ep)) != 2:
                ep = str(0) + str(ep)

            ep = f"{episode[0][0:4]}{ep}"
            self.setText(ep)
            self.parent.s01e01 = [ep]
            self.parent.set_proper_title()

class IMDBPlate(GODLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self, background='transparent', color='transparent')
        self.parent.raise_group.append(self)
        self.positioned = []

    def __call__(self):
        t.close_and_pop(self.positioned)
        pos(self, width=self.parent.width() * 0.5, height=self.parent.height() * 0.5)

        self.make_year()
        self.make_title()
        self.make_episode()
        self.make_categories()

        xy = [(x.geometry().right(), x.geometry().bottom()) for x in self.positioned]
        xy.sort(key=lambda x:x[0])
        pos(self, width=xy[-1][0] + 2)
        xy.sort(key=lambda x:x[1])
        pos(self, height=xy[-1][1] + 2)

        self.make_imdb_link()
        self.follow_parent()

    def make_episode(self):
        episode = self.parent.get_episode()
        if episode:
            label = Episode(place=self, qframebox=True, text=episode[0].upper(), center=True, mouse=True, parent=self.parent, monospace=True, bold=True)
            style(label, font=10)
            label.deactivated_on = dict(background=GRAY53, color=GRAY15)
            label.deactivated_off = dict(background=GRAY45, color=GRAY12)
            t.shrink_label_to_text(label, x_margin=20, y_margin=2, height=True)
            label.show_episode()
            self.position_this(label, y_extra=-1)

    def make_title(self):
        label = TitleGenre(place=self, qframebox=True, text=self.parent.candidates[0][DB.titles.type].upper(), center=True, mouse=True, parent=self.parent)
        style(label, font=14)
        label.deactivated_on = dict(background=GRAY60, color=GRAY10)
        label.deactivated_off = dict(background=GRAY50, color=GRAY8)
        t.shrink_label_to_text(label, x_margin=20, y_margin=2, height=True)
        self.position_this(label, y_extra=-1)

    def make_year(self):
        year = f"{self.parent.candidates[0][DB.titles.start_year] or ''}"
        if self.parent.candidates[0][DB.titles.end_year]:
            year += f" - {self.parent.candidates[0][DB.titles.end_year]}"

        if year:
            label = TitleGenre(place=self, qframebox=True, text=year, center=True, mouse=True, parent=self.parent)
            style(label, font=10)
            label.deactivated_on = dict(background=GRAY65, color=GRAY10)
            label.deactivated_off = dict(background=GRAY55, color=GRAY10)
            t.shrink_label_to_text(label, x_margin=20, y_margin=2, height=True)
            self.position_this(label)

    def make_categories(self):

        for count, i in enumerate(self.parent.candidates[0]):
            if i == '1':
                cols = [x for x in dir(DB.titles) if '__' not in x]
                if not [getattr(DB.titles, x) for x in cols if getattr(DB.titles, x) == count]:
                    rvdict = sqlite.get_all_tables_and_columns()
                    setattr(DB.titles, rvdict['titles'][count], count)

                for ii in [x for x in dir(DB.titles) if '__' not in x]:
                    if getattr(DB.titles, ii) == count:

                        rgb, top = (255,255,255,), 150

                        while sum(rgb) > 400:
                            random.seed('red' + ii)
                            red = top * random.random()
                            random.seed('green' + ii)
                            green = top * random.random()
                            random.seed('blue' + ii)
                            blue = top * random.random()
                            rgb, top = (red if red < 235 else 235, green if green < 235 else 235, blue if blue < 235 else 235,), top-1
                            rgb = (rgb[0] if rgb[0] > 30 else 30, rgb[1] if rgb[1] > 30 else 30, rgb[2] if rgb[2] > 30 else 30,)

                        red, green, blue = int(rgb[0]), int(rgb[1]), int(rgb[2])
                        rgb1 = f'rgb({red if red > 30 else 30},{green if green > 30 else 30},{blue if blue > 30 else 30})'
                        rgb2 = f'rgb({red+15 if red > 45 else 45},{green+15 if green > 45 else 45},{blue if blue+15 > 45 else 45})'

                        back = GODLabel(place=self, styleSheet='background:rgb(10,10,10)', type='_move')
                        label = TitleGenre(place=back, text=ii, center=True, mouse=True, parent=self.parent)

                        if sum([red, green, blue]) < 150:
                            label.deactivated_on = dict(background=rgb2, color=GRAY)
                            label.deactivated_off = dict(background=rgb1, color=GRAY, font=11)
                        else:
                            label.deactivated_on = dict(background=rgb2, color=BLACK)
                            label.deactivated_off = dict(background=rgb1, color=BLACK, font=11)

                        t.shrink_label_to_text(label, x_margin=20, y_margin=2, height=True)
                        pos(back, height=label, width=label, add=2)
                        pos(label, top=1, left=1)

                        self.position_this(back, y_extra=3)

        {pos(x, move=[0,15]) for x in self.positioned if x.type == '_move'}

    def make_imdb_link(self):
        if 'imdblink' in dir(self):
            self.imdblink.close()

        class IMDBLink(TitleGenre):
            def follow_parent(self):
                if 'ratings_label' in dir(self.parent):
                    pos(self.backplate, below=self.parent.ratings_label, move=[10,1])
                else:
                    pos(self.backplate, bottom=self.parent, left=self.parent, move=[-10,-3])
                self.backplate.raise_()

            def mouseReleaseEvent(self, ev):
                self.hold = False

                if ev.button() == 1:
                    webbrowser.open(self.link)
                else:
                    sqlite.execute('delete from imgcache where tconst is (?)', self.parent.candidates[0][DB.titles.tconst])
                    self.parent.title.setText('COVER DELETED FROM IMG CACHE')

        link = f"http://imdb.com/title/{self.parent.candidates[0][DB.titles.tconst]}"
        back = GODLabel(place=self.main, styleSheet='background:rgb(10,10,10)', parent=self.parent)
        label = IMDBLink(place=back, center=True, mouse=True, parent=self.parent, text=link)
        label.deactivated_on = dict(background='rgb(100,100,200)', color=BLACK)
        label.deactivated_off = dict(background='rgb(100,100,150)', color=BLACK)
        t.signal_highlight()
        t.shrink_label_to_text(label, x_margin=20, y_margin=2, height=True)

        pos(back, height=label, width=label, add=2, move=[0,40])
        pos(label, top=1, left=1)

        self.imdblink, label.backplate, label.link = back, back, link

        EventFilter(eventparent=self.parent, eventtype=QEvent.Move, master_fn=label.follow_parent)
        EventFilter(eventparent=self.parent, eventtype=QEvent.Resize, master_fn=label.follow_parent)
        EventFilter(eventparent=self.parent.title, eventtype=QEvent.MouseButtonPress, master_fn=label.follow_parent)
        EventFilter(eventparent=self.parent.cover, eventtype=QEvent.MouseButtonPress, master_fn=label.follow_parent)
        EventFilter(eventparent=self.parent, eventtype=QEvent.Close, master_fn=lambda: self.imdblink.close())

    def position_this(self, widget, vertical=True, x_extra=0, y_extra=0, **kwargs):
        x_extra, y_extra = dict(x_margin=x_extra), dict(y_margin=y_extra)
        self.positioned = [x for x in self.positioned if x != widget]
        self.main.easy_positions(self, widget, notes=self.positioned, vertical=vertical, y_extra=y_extra, x_extra=x_extra, **kwargs)
        self.positioned.append(widget)

    def follow_parent(self):
        pos(self, after=self.parent, x_margin=-10, bottom=self.parent, y_margin=200)
        self.raise_()

class CoverTurner(MovableScrollWidget):
    def __init__(self, candidates, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pos(self, width=480)
        self.overwrite = False
        self.s01e01 = False
        self.data = data
        self.candidates = candidates
        self.make_title()

        self.signal.stringdelivery.connect(self.set_this_cover)
        self.signal.error.connect(lambda: self.title.setText('ERROR!'))
        self.signal.killswitch.connect(self.killme)

        self.cover = GODLabel(place=self.backplate, parent=self)
        self.cover.mousePressEvent = self.title.mousePressEvent
        self.cover.mouseMoveEvent = self.title.mouseMoveEvent

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

        self.s01e01 = False  # resets this, lazy fix

        name, years, episode = self.parent.search_this_string(searchstring=self.lineedit.text().strip())
        data = self.parent.gather_imdb_candidates(name, years, episode)

        if data:
            self.candidates = data
            self.change_candidate()
        else:
            self.title.setText('FOUND NOTHING!')

        self.make_next_prev_buttons()

    def text_changed(self, text):
        if 'tiplabel' not in dir(self.lineedit):
            self.lineedit.tiplabel = GODLabel(place=self.lineedit, text='YEAR MISSING FROM QUERY', center=True, direct_hide=True)
            style(self.lineedit.tiplabel, background=TRANSPARENT, color=GRAY, font=8)
            t.shrink_label_to_text(self.lineedit.tiplabel, x_margin=8)
            pos(self.lineedit.tiplabel, height=self.lineedit, right=self.lineedit)

        if len(text) > 3:
            if not self.parent.get_years(text):
                self.lineedit.tiplabel.show()
                return

        self.lineedit.tiplabel.hide()

    def mouseReleaseEvent(self, ev):
        if ev.button() == 2:
            self.signal.killswitch.emit()

    def make_search_bar(self):
        self.lineedit = QtWidgets.QLineEdit(self.toolplate)
        self.lineedit.setTextMargins(10,0,10,0)
        self.lineedit.returnPressed.connect(self.manual_search)
        self.lineedit.textChanged.connect(self.text_changed)
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
            if t.config('nas_ssh') and t.config('nas_login') and t.config('nas_pwd'):
                ssh_command(f'mkdir -m 777 "{loc.folder}"')
            else:
                os.umask(0)
                os.mkdirs(loc.folder, 0o777)

            if os.path.exists(loc.full_path):
                self.title.setText(f'MADE FOLDER: {loc.folder.split(os.sep)[-1]}')
            else:
                self.title.setText('CREATING FOLDER FAILED')

        if os.path.exists(loc.full_path) and self.overwrite:
            os.remove(loc.full_path)
            if os.sep == '/': os.sync()
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

        if os.sep == '/': os.sync()
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

            episode = self.get_episode() or ""
            if episode:
                episode = " " + episode[0]

            fname = f"{self.candidates[0][DB.titles.title]}{episode}.{ext}"
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

    def get_episode(self):
        if self.lineedit.text():
            searchstring = self.lineedit.text().strip()
        else:
            searchstring = self.data['path']

        _, _, episode = self.parent.search_this_string(searchstring=searchstring)
        return self.s01e01 or episode

    def set_proper_title(self):
        text = self.candidates[0][DB.titles.title]
        episode = self.get_episode()
        if episode:
            text += f" {episode[0].upper()}"

        self.title.setText(text)

    def store_cover_to_cache(self, path):
        blob = t.make_image_into_blob(path, quality=80, method=1)  # prefer speed over storage
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
            self.candidates.append(self.candidates[0])
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
        self.show_rating()

        self.overwrite = False

        pos(self, move=[1,1])
        pos(self, move=[-1,-1])  # lazy hack, this emits a move/resize signal

    def show_rating(self):
        if 'ratings_label' in dir(self):
            self.ratings_label.close()
            del self.ratings_label

        if not self.main.dbcache(table='ratings', curious=True):
            data = sqlite.execute('select * from ratings', all=True)
            tmp = {x[DB.ratings.tconst]: x[DB.ratings.average] for x in data}
            self.main.dbcache(table='ratings', store_this=tmp)

        ratings = self.main.dbcache('ratings', as_is=True)
        tconst = self.candidates[0][DB.titles.tconst]

        if tconst in ratings:
            try: rating = float(ratings[tconst])
            except ValueError: return

            if rating > 10 or rating <= 0:
                return

            class RatingssLabel(GODLabel):
                def follow_parent(self):
                    pos(self, below=self.parent)
                    self.raise_()

            self.ratings_label = RatingssLabel(place=self.main, parent=self)
            pos(self.ratings_label, width=self, below=self, height=12)

            EventFilter(eventparent=self, eventtype=QEvent.Move, master_fn=self.ratings_label.follow_parent)
            EventFilter(eventparent=self, eventtype=QEvent.Resize, master_fn=self.ratings_label.follow_parent)
            EventFilter(eventparent=self.title, eventtype=QEvent.MouseButtonPress, master_fn=self.ratings_label.follow_parent)
            EventFilter(eventparent=self.cover, eventtype=QEvent.MouseButtonPress, master_fn=self.ratings_label.follow_parent)
            EventFilter(eventparent=self, eventtype=QEvent.Close, master_fn=lambda: self.ratings_label.close() if 'ratings_label' in dir(self) else None)

            for i in range(1, 11):
                label = GODLabel(place=self.ratings_label, qframebox=True, edges=4)
                pos(label, height=self.ratings_label, width=self.ratings_label.width() / 10)
                pos(label, left=(i-1) * label.width())
                style(label, color=BLACK)

                if rating > i:
                    style(label, background=WHITE)
                else:
                    style(label, background=GRAY)
                    part = GODLabel(place=self.ratings_label, styleSheet='background:white')
                    pos(part, height=label.height()-2, width=label.width() * (rating - i) - 4, left=(i-1) * label.width(), move=[1,1])

                if i == 10:
                    pos(label, reach=dict(right=self.ratings_label.width()-1))

    def show_year_genre_runtime_type(self):
        if not 'imdbplate' in dir(self):
            self.imdbplate = IMDBPlate(place=self.main, main=self.main, parent=self)
            EventFilter(eventparent=self, master_fn=self.imdbplate.follow_parent, eventtype=QEvent.Move)
            self.signal.killswitch.connect(lambda: self.imdbplate.close())

        self.imdbplate()
        self.imdbplate.follow_parent()

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
