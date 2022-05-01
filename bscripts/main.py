from PyQt5                     import Qt, QtCore, QtWidgets
from bscripts.database_stuff   import DB, sqlite
from bscripts.imdbstuff        import imdb_things,CoverTurner
from bscripts.preset_colors    import *
from bscripts.settings_widgets import Canvas, GLOBALHighLight, GODLabel
from bscripts.settings_widgets import MovableScrollWidget, create_indikator
from bscripts.tricks           import tech as t
import os
import screeninfo
import sys, datetime

pos = t.pos
style = t.style

class SettingsButton(GODLabel, GLOBALHighLight):
    def mouseReleaseEvent(self, ev):
        self.activation_toggle()
        t.save_config(self.type, self.activated)
        t.signal_highlight()

class GOBack(GODLabel, GLOBALHighLight):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        t.highlight_style(self, 'folders')

    def mouseReleaseEvent(self, ev):
        self.main.browser.title.setText(self.path)

        if self.path != t.config('download_folder').rstrip(os.sep):
            self.main.browser.widgets = [x for x in self.main.browser.widgets if x != self]

        t.close_and_pop(self.main.browser.widgets)
        if self.path != t.config('download_folder').rstrip(os.sep):
            self.main.browser.widgets.append(self)

        self.main.draw_this_dir(self.path)
        self.path = self.path.split(os.sep)
        self.path = os.sep.join(self.path[0:-1])

class FilesFolder(GODLabel, GLOBALHighLight):
    def skip_this_path(self):
        skip = dbcache('skipped')
        skip = {x[DB.skipped.local_path] for x in skip}

        if self.data['path'] not in skip:
            query, values = sqlite.empty_insert_query('skipped')
            values[DB.skipped.local_path] = self.data['path']
            sqlite.execute(query, values)
            self.setText('ADDED TO FUCK OFF LIST')
            self.main.ff = [x for x in self.main.ff if x['path'] != self.data['path']]
        else:
            sqlite.execute('delete from skipped where local_path = (?)', self.data['path'])
            self.setText('NO LONGER MEMBER OF FUCK OFF LIST')

class Folder(FilesFolder):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        t.highlight_style(self, 'folders')

    def show_size(self):
        pass

    def mouseReleaseEvent(self, ev):
        if ev.button() == 1:
            t.close_and_pop(self.main.browser.widgets)
            thing = GOBack(place=self.main.browser.backplate, mouse=True, text='..', main=self.main, indent=10)
            thing.path = self.data['path'].split(os.sep)
            thing.path = os.sep.join(thing.path[0:-1])
            pos(thing, height=35, width=self.main.browser.backplate)
            self.main.browser.widgets.append(thing)
            self.main.draw_this_dir(self.data['path'])
            self.main.browser.title.setText(self.data['path'])
        else:
            self.skip_this_path()

class File(FilesFolder):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate = None
        self.data = data
        t.highlight_style(self, 'files')

    def mouseReleaseEvent(self, ev):
        if ev.button() == 1:
            if not self.candidate:
                self.open_file(ev)
                self.candidate.signal.killswitch.connect(lambda: setattr(self, 'candidate', None))
                t.signal_highlight()
            else:
                self.candidate.signal.killswitch.emit()
        else:
            self.skip_this_path()

    def show_size(self):
        size = os.path.getsize(self.data['path'])

        if size > 1000000000:
            text = f"{round(size / 1000000000, 2)} GB"
        else:
            text = f"{round(size / 1000000)} MB"

        self.size = GODLabel(place=self, text=text, center=True, monospace=True)
        style(self.size, background='transparent', color='WHITE')
        t.shrink_label_to_text(self.size)
        pos(self.size, height=self, right=self.width() - 10)

    def get_years(self, path):
        years = []
        tmp = path.split(os.sep)[-1]
        for year in range(datetime.datetime.now().year - 100, datetime.datetime.now().year + 2):
            if str(year) in tmp and str(year) not in years:
                years.append(str(year))

        return years

    def get_episode(self, path):
        episode = []

        if len(path) > len('S01E01'):
            for c in range(0, len(path) + 1 - len('S01E01')):
                tmp = path[c:c+6].upper()
                if tmp[0] == 'S' and tmp[3] == 'E':
                    if len([x for x in tmp if x.isdigit()]) == 4:
                        episode.append(tmp)

        return episode

    def get_name(self, path, years=[], episode=[]):
        name = path.split(os.sep)[-1]

        if '(' in name:
            name = name[0:name.find('(')]

        for i in years + episode:
            if str(i).lower() in name.lower():
                name = name[0:name.lower().find(str(i).lower())]

        if name[0] == '[' and ']' in name:
            name = name[name.find(']')+1:]

        name = name.replace(' ', '.').split('.')
        name = [x for x in name if x] # kills empty
        name = ' '.join(name)
        return name

    def fetch_data(self, years, episode):
        if episode:
            query = 'select * from titles where start_year = null and type != "movie"'
        else:
            query = 'select * from titles where start_year = null and type = "movie"'

        data = dbcache(query=query)

        for year in years:
            if episode:
                query = 'select * from titles where start_year = (?) and type != "movie"'
            else:
                query = 'select * from titles where start_year = (?) and type = "movie"'

            data += dbcache(query=query, values=year)

        return data

    def search_this_string(self, searchstring):
        episode = self.get_episode(searchstring)
        years = self.get_years(searchstring)
        name = self.get_name(searchstring, episode=episode, years=years)
        return name, years, episode

    def gather_imdb_candidates(self, name, years, episode):

        def splitsearch(data):
            titles = {x[DB.titles.title].lower() for x in data}

            for i in [x.lower().strip() for x in name.split() if x.strip()]:
                titles = {x for x in titles if x.find(i) > -1}

            return [x for x in data if x[DB.titles.title].lower() in titles]

        if years:
            data = self.fetch_data(years, episode)
            data = splitsearch(data)

        if not years or not data:
            data = self.fetch_data([x for x in range(2000, datetime.datetime.now().year + 1)], episode)
            data = splitsearch(data)

        if years:  # sorts specified year on top (title must still match)
            tmp = [x for x in data if x[DB.titles.start_year] == years[0]]
            tmp += [x for x in data if x not in tmp]
            data = tmp

        tmp = [x for x in data if x[DB.titles.title].lower() == name.lower()]
        tmp += [x for x in data if x not in tmp and x[DB.titles.title].lower().startswith(name.lower())]
        tmp += [x for x in data if x not in tmp]

        return tmp

    def open_file(self, ev=None):
        name, years, episode = self.search_this_string(searchstring=self.data['path'])
        data = self.gather_imdb_candidates(name, years, episode)

        self.candidate = CoverTurner(place=self.main, candidates=data, main=self.main, signal=True, data=self.data, parent=self)
        if ev:
            pos(self.candidate, top=ev.y(), left=ev.x())


class DBFromCache:
    def __init__(self):
        self.cache = {}

    def __call__(self, table=None, reset=False, query=None, values=None, all=True):
        if reset:
            if not table:
                self.cache = {}
            elif table and table in self.cache:
                self.cache.pop(table)
            elif query and query in self.cache:
                self.cache.pop(query)

        if query and query+str(values) not in self.cache:
            data = sqlite.execute(query=query, values=values, all=all)
            self.cache[query+str(values)] = [x for x in data]

        if table and table not in self.cache:
            query = f'select * from {table}'
            data = sqlite.execute(query=query, all=all)
            self.cache[table] = [x for x in data]

        if table and table in self.cache:
            return self.cache[table]

        elif query+str(values) in self.cache:
            return self.cache[query+str(values)]

        return []

dbcache = DBFromCache()

def easy_positions(self, note, notes, alpha=None, vertical=False, x_extra={}, y_extra={}, overlapping=3):

    def add_overlapping(top, bottom, left, right, overlapping):
        return (x for x in [top+overlapping, bottom-overlapping, left+overlapping, right-overlapping] if x > 0 or 1)

    def get_position(this):
        top, bottom = this.geometry().top(), this.geometry().bottom()
        left, right = this.geometry().left(), this.geometry().right()
        return top,bottom,left,right

    def get_new_top_bottom_left_right_below(i):
        i_top, i_bottom, i_left, _ = get_position(i)
        new_top = i_bottom + 1
        if y_extra and 'y_margin' in y_extra:
            new_top += y_extra['y_margin']
        return add_overlapping(new_top, new_top + note.height(), i_left, i_left + note.width(), overlapping)

    def get_new_top_bottom_left_right_after(i):
        i_top, i_bottom, _, i_right = get_position(i)
        new_left = i_right + 1
        if x_extra and 'x_margin' in x_extra:
            new_left += x_extra['x_margin']
        return add_overlapping(i_top, i_top + note.height(), new_left, new_left + note.width(), overlapping)

    def used_this_position(new_top, new_bottom, new_left, new_right):
        for i in [x for x in notes if x != note]:
            i_top, i_bottom, i_left, i_right = get_position(this=i)

            if new_top >= i_top and new_top <= i_bottom or new_bottom >= i_top and new_bottom <= i_bottom:

                if new_left >= i_left and new_left <= i_right:
                    return True

                elif new_right >= i_left and new_right <= i_right:
                    return True

    def vertical_trial(highjack=None):
        notes.sort(key=lambda x:x.geometry().left())
        notes.sort(key=lambda x:x.geometry().bottom())

        for i in [x for x in notes if not highjack or x == highjack]:
            new_top, new_bottom, new_left, new_right = get_new_top_bottom_left_right_below(i)

            if new_bottom + 25 > self.height():
                continue

            if used_this_position(new_top, new_bottom, new_left, new_right):
                continue

            if not highjack:
                pos(note, below=i, **y_extra)

            return True

    def vertical_highjack(new_bottom):
        for ii in notes:
            _, ii_bottom, _, _ = get_new_top_bottom_left_right_below(ii)
            if ii_bottom < new_bottom and vertical_trial(highjack=ii):
                pos(note, below=ii, **y_extra)
                return True

    def horizontal_trial():
        notes.sort(key=lambda x:x.geometry().top())

        for i in [x for x in notes]:
            new_top, new_bottom, new_left, new_right = get_new_top_bottom_left_right_after(i)

            if new_right > self.width():
                continue

            if used_this_position(new_top, new_bottom, new_left, new_right):
                continue

            if not vertical_highjack(new_bottom):  # tries better vertical before final approval
                pos(note, after=i, **x_extra)

            return True

    if vertical and vertical_trial():
        return True
    elif horizontal_trial():
        return True
    else:
        vertical_trial()


class SETTINGSTHINGEY(Canvas):
    class LineEdit(Canvas.LineEdit):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.returnPressed.connect(self.save_settings)
            self.setText(t.config(self.parent.type) or "change me and press enter")

        def save_settings(self):
            if self.text().strip():
                t.save_config(self.parent.type, self.text().strip())
                self.text_changed()

        def text_changed(self):
            text = self.text().strip()
            if text != t.config(self.parent.type):
                style(self, color=ORANGE3)
            else:
                style(self, color=WHITE)

class PASSTHINGEY(SETTINGSTHINGEY):
    class LineEdit(SETTINGSTHINGEY.LineEdit):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.text() == t.config('nas_pwd'):
                self.setText('xôÌÙ<ẑ>ÙÌôx')
                style(self, color=LIGHTBLUE3)

class MainDuplicant(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        style(self, background='rgb(30,30,55)', color=WHITE)

        self.positioned = []
        self.position_mainwindow()

        self.show()

        self.create_settings_stuff()
        self.create_browsingwidget()
        self.create_settings_buttons()
        self.create_browse_button()
        imdb_things(self)
        self.create_kill_all_dead()

        self.signal = t.signals('main')
        self.signal.listdelivery.connect(self.draw_files_and_folders)

        dbcache('skipped')
        t.thread(self.browse_files_and_folders)

    def create_kill_all_dead(self):
        class KillBTN(GODLabel, GLOBALHighLight):
            def __init__(self, *args, **kwargs):
                super().__init__(
                    deactivated_on=dict(background=BLACK, color=WHITE),
                    deactivated_off=dict(background=GRAY, color=BLACK),
                    *args, **kwargs
                )

            def mouseReleaseEvent(self, ev):
                auto = False
                for i in [x for x in self.main.ff if x['category'] == 'dead']:
                    if os.path.islink(i['path']):

                        if not auto:
                            userinput = input(f"DELETE: {i['path']} (Yes, No, All, Quit)")

                        if userinput[0].lower() == 'q':
                            break

                        if userinput[0].lower() == 'a':
                            auto = True

                        if userinput[0].lower() == 'y' or auto == True:
                            os.remove(i['path'])

                            folder = i['path'].split(os.sep)[1:-1]

                            for walk in os.walk(os.sep.join(folder)):
                                if not walk[1] and not walk[2]:
                                    shutil.rmtree(walk[0])
                                    break

                        self.main.ff = [x for x in self.main.ff if x != i]


        kill = KillBTN(place=self, mouse=True, qframebox=True, center=True, text='KILL ALL DEAD', main=self)
        pos(kill, coat=self.refresh_imdb_button, after=self.refresh_imdb_button, x_margin=3)

    def browse_files_and_folders(self):
        folder = t.config('download_folder')
        files = dict(files=[], folders=[], linked=[], unlinked=[], dead=[])
        whitelist = {'mkv', 'mpeg', 'mp4', 'mov', 'avi'}

        if folder and os.path.exists(folder):
            skip = dbcache('skipped', reset=True)
            skip = {x[DB.skipped.local_path] for x in skip}

            for walk in os.walk(folder):

                if walk[0].split(os.sep)[-1].lower() == 'sample':
                    continue

                elif walk[0] in skip and t.config('HIDE SKIPPED'):
                    continue

                files['folders'].append(walk[0])

                for i in walk[2]:

                    if 'sample' in i.lower():
                        continue

                    ext = i.split('.')

                    if not ext[-1].lower() in whitelist:
                        continue

                    f = t.separate_file_from_folder(walk[0] + '/' + i)

                    if f.path in skip and t.config('HIDE SKIPPED'):
                        continue

                    files['files'].append(f.path)


        for folder in [x for x in {t.config('movie_folder'), t.config('tv_folder')} if x and os.path.exists(x)]:
            for walk in os.walk(folder):

                for i in walk[2]:

                    ext = i.split('.')

                    if not ext[-1].lower() in whitelist:
                        continue

                    f = t.separate_file_from_folder(walk[0] + '/' + i)

                    if os.path.islink(f.path):
                        link = os.readlink(f.path)
                        if link in files['files']:
                            files['linked'].append(link)
                        else:
                            files['dead'].append(f.path)


        files['unlinked'] = [x for x in files['files'] if x not in files['linked']]

        completelist  = [{'used':False, 'path':x.rstrip(os.sep), 'category': 'folder'} for x in files['folders']]
        completelist += [{'used':False, 'path':x.rstrip(os.sep), 'category': 'linked'} for x in files['linked']]
        completelist += [{'used':False, 'path':x.rstrip(os.sep), 'category': 'unlinked'} for x in files['unlinked']]
        completelist += [{'used':False, 'path':x.rstrip(os.sep), 'category': 'dead'} for x in files['dead']]

        completelist.sort(key=lambda x:x['path'])
        self.signal.listdelivery.emit(completelist)

    def draw_files_and_folders(self, ff):
        self.ff = ff
        t.close_and_pop(self.browser.widgets)
        self.draw_this_dir(t.config('download_folder').rstrip(os.sep), smooth=True)

    def draw_this_dir(self, folder, smooth=False):
        for ff in [('folder', Folder,), ({'linked','unlinked'}, File,)]:

            for i in self.ff:

                if i['used']:
                    continue

                elif i['category'] not in ff[0]:
                    continue

                elif t.config('HIDE LINKED') and i['category'] == 'linked':
                    continue

                elif t.config('HIDE UNLINKED') and i['category'] == 'unlinked':
                    continue


                if i['category'] == 'folder':
                    linked = [x for x in self.ff if x['category'] == 'linked' and x['path'].startswith(i['path'])]
                    unlinked = [x for x in self.ff if x['category'] == 'unlinked' and x['path'].startswith(i['path'])]

                    if not linked and not unlinked:
                        continue

                    if t.config('HIDE LINKED') and not unlinked:
                        continue

                    if t.config('HIDE UNLINKED') and not linked:
                        continue


                tmp = i['path'].split(os.sep)
                tmp = os.sep.join(tmp[0:-1])

                if tmp != folder:
                    continue

                i['used'] = True

                text = i['path'].split(os.sep)[-1]
                thing = ff[1](place=self.browser.backplate, mouse=True, text=text, main=self, data=i, indent=10)
                pos(thing, height=35, width=self.browser.backplate, top=len(self.browser.widgets) * 36, move=[0,1])
                thing.show_size()

                self.browser.widgets.append(thing)
                self.browser.expand_me()

                if smooth:
                    t.signal_highlight()
                    t.thread(dummy=True, master_fn=self.draw_this_dir, master_args=(folder,))
                    return

        t.signal_highlight()
        [x.update({'used':False}) for x in self.ff]

    def create_browse_button(self):
        class Browse(GODLabel, GLOBALHighLight):
            def mouseReleaseEvent(self, ev):
                self.main.browse_files_and_folders()

        back = GODLabel(place=self.browser.title)
        style(back, background=GRAY50)
        pos(back, height=self.browser.title, width=150)
        button = Browse(place=back, mouse=True, text='RE-BROWSE', center=True, bold=True, main=self)
        pos(button, inside=back, margin=1)
        t.highlight_style(button, name='folders')

    def create_settings_buttons(self):
        for i in [('HIDE LINKED',False,), ('HIDE UNLINKED',True,), ('HIDE SKIPPED',True,)]:
            back = GODLabel(place=self)
            style(back, background=GRAY50)
            pos(back, size=[170,30])
            button = SettingsButton(place=back, mouse=True, type=i[0], text=i[0], center=True, bold=True)
            pos(button, inside=back, margin=1)
            button.activation_toggle(force=t.config(i[0]) or False)
            t.highlight_style(button, name='settingsbutton')
            self.position_this(back, vertical=i[1], x_extra=3, y_extra=3)

        t.signal_highlight()

    def create_browsingwidget(self):
        self.browser = MovableScrollWidget(place=self, scroller=True, main=self)
        self.browser.make_title('BROWSING WIDGET')
        self.browser.expand_me()
        self.position_this(self.browser, vertical=True)
        pos(self.browser, width=self.width() * 0.5, move=[0,5])

        style(self.browser.title, background=GRAY1, color=WHITE)
        style(self.browser.backplate, background=GRAY16, color=WHITE)

    def create_settings_stuff(self):
        thing = QtWidgets.QLineEdit(self);pos(thing, right=-10);thing.show()  # you can remove this nothing bad happens (lazy fix small bug when closing imdb-widget)

        for count, i in enumerate([
            dict(type='download_folder', tiplabel='PIRATE FOLDER', vertical=True),
            dict(type='movie_folder', tiplabel='MOVIES FOLDER', vertical=True),
            dict(type='tv_folder', tiplabel='TVSHOW FOLDER', vertical=True),

            dict(type='nas_ssh', tiplabel='NAS NWADDRESS', vertical=False),
            dict(type='nas_login', tiplabel='NAS ROOTLOGIN', vertical=True),
            dict(type='nas_pwd', tiplabel='NAS PASSWORDS', vertical=True),

            ]):

            thing = create_indikator(
                place=self,
                tiplabel=i['tiplabel'],
                lineedit=True,
                tipfont=10,
                autohide_tiplabel=True,
                Special=SETTINGSTHINGEY if i['type'] != 'nas_pwd' else PASSTHINGEY,
                type=i['type'],
                )

            pos(thing, size=[600,30], move=[3,3])
            style(thing, background=BLACK)
            self.position_this(thing, i['vertical'], x_extra=3, y_extra=3)

            if count > 2:
                pos(thing, width=250)

    def position_mainwindow(self, primary=True, width_factor=0.8, height_factor=0.8, x_margin=0.1, y_margin=0.1):
        if primary:
            monitors = [x for x in screeninfo.get_monitors() if x.is_primary]
        else:
            monitors = [x for x in screeninfo.get_monitors() if not x.is_primary]

        if monitors:
            monitor = monitors[0]

            x = int(monitor.x)
            y = int(monitor.y)
            w = int(monitor.width * width_factor)
            h = int(monitor.height * height_factor)

            self.move(x + int(monitor.width * x_margin), y + (int(monitor.height * y_margin)))
            self.resize(w, h)
        else:
            self.resize(1000, 700)
            self.move(100,100)



    def position_this(self, widget, vertical=True, x_extra=0, y_extra=0):
        if type(widget) == list:
            widget = widget[-1]

        x_extra, y_extra = dict(x_margin=x_extra), dict(y_margin=y_extra)
        self.positioned = [x for x in self.positioned if x != widget]
        easy_positions(self, widget, notes=self.positioned, vertical=vertical, y_extra=y_extra, x_extra=x_extra)
        self.positioned.append(widget)

