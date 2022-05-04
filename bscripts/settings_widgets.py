from PyQt5                  import QtCore, QtGui, QtWidgets
from PyQt5.QtCore           import QEvent, QObject, pyqtSignal
from bscripts.preset_colors import *
from bscripts.tricks        import tech as t
import os, time

pos = t.pos
style = t.style

class EventFilter(QObject):
    event_highjack = pyqtSignal()

    def __init__(self, eventparent, eventtype=QEvent.Resize, master_fn=None):
        super().__init__(eventparent)
        self.eventtype = eventtype
        self._widget = eventparent
        self.widget.installEventFilter(self)
        if master_fn:
            self.event_highjack.connect(master_fn)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, widget, event) -> bool:
        if widget == self._widget and event.type() == self.eventtype:
            self.event_highjack.emit()
        return super().eventFilter(widget, event)

class GOD:
    def __init__(self,
                 place=None,
                 main=None,
                 type=None,
                 signal=None,
                 reset=True,
                 parent=None,
                 load=False,
                 inherit_type=False,
                 *args, **kwargs
                 ):

        self.activated = False
        self.main = main or False
        self.parent = parent or place or main or False
        self.determine_type(inherit_type, place, type)
        self.setup_signal(signal, reset)
        self.load_settings(load)

    def load_settings(self, load):
        if not load or not self.type:
            return

        rv = t.config(self.type)
        if rv == True:
            self.activation_toggle(force=True, save=False)

    def setup_signal(self, signal, reset):
        if type(signal) == str:
            self.signal = t.signals(signal, reset=reset)
        else:
            self.signal = t.signals(self.type, reset=reset)

    def determine_type(self, inherit_type, place, type):
        if type:
            self.type = type
        elif inherit_type and place and 'type' in dir(place) and place.type not in ['main']: # blacklist
            self.type = place.type
        else:
            self.type = t.md5_hash_string(under=True)

    def save(self, type=None, data=None):
        if data:
            if type:
                t.save_config(type, data)
            elif self.type:
                t.save_config(self.type, data)

    def activation_toggle(self, force=None, save=True):
        if force == False:
            self.activated = False
        elif force == True:
            self.activated = True
        else:
            if self.activated:
                self.activated = False
            else:
                self.activated = True

        if save:
            t.save_config(self.type, self.activated)

class DragDroper(GOD):
    def __init__(self, drops=False, mouse=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(drops)
        self.setMouseTracking(mouse)

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:
        data = a0.mimeData().urls()
        if data:
            self.setAcceptDrops(True)
            a0.acceptProposedAction()
            return

        self.setAcceptDrops(False)

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        files = [x for x in a0.mimeData().urls()]
        if files and files[0].isLocalFile():
            a0.accept()
            files = [x.path() for x in a0.mimeData().urls()]
            self.filesdropped(files, a0)

        files = [x.path() for x in a0.mimeData().urls()]
        if files:
            files = [x for x in files if os.path.exists(x)]
            if files:
                self.filesdropped(files, a0)

class GODLabel(QtWidgets.QLabel, GOD):

    def __init__(self, center=False, qframebox=False, monospace=False, linewidth=1, bold=False, direct_hide=False, *args, **kwargs):

        self.old_position = False
        self.steady = False

        super().__init__(kwargs['place'], *args, **kwargs)

        self.setAttribute(55)  # delete on close

        if bold:
            my_font = QtGui.QFont()
            my_font.setBold(True)
            self.setFont(my_font)

        if qframebox:
            self.setFrameShape(QtWidgets.QFrame.Box)
            self.setLineWidth(linewidth)

        if monospace:
            self.setFont(QtGui.QFont('Monospace', 9, QtGui.QFont.Monospace))

        if center:
            self.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)

        if not direct_hide:
            self.show()

    def filesdropped(self, files, *args, **kwargs):
        pass

class GODLE(QtWidgets.QLineEdit, GOD):
    def __init__(self, *args, **kwargs):
        super().__init__(kwargs['place'], *args, **kwargs)
        self.textChanged.connect(self.text_changed)
        self.show()

    def text_changed(self):
        text = self.text().strip()
        if not text:
            return

class GODLEPath(GODLE):
    def __init__(self, autoinit=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if autoinit:
            self.set_saved_path()

    def filesdropped(self, files, *args, **kwargs):
        if not files:
            return

        self.setText(files[0])

    def text_changed(self):
        text = self.text().strip()

        if text and os.path.exists(text):
            self.save(data=text)
            if not self.activated:
                t.style(self, color='white')
                self.activation_toggle(force=True, save=False) # already saved
                if self.signal:
                    self.signal.activated.emit()
        else:
            if self.activated:
                t.style(self, color='gray')
                self.activation_toggle(force=False, save=False)
                if self.signal:
                    self.signal.deactivated.emit()

    def set_saved_path(self):
        rv = t.config(self.type)
        if rv and type(rv) in [str, int, float]:
            self.setText(str(rv))
            self.activation_toggle(force=True, save=False)
            if self.signal:
                self.signal.activated.emit()

class GLOBALHighLight(DragDroper, GOD):
    _decaylamp_timer = 0
    _decaylamp_runner = False
    def __init__(self,
                 signal=True,
                 highlight_signal='_global',
                 reset=False,
                 activated_on=None,
                 activated_off=None,
                 deactivated_on=None,
                 deactivated_off=None,
                 *args, **kwargs
                 ):

        super().__init__(signal=signal, reset=reset, *args, **kwargs)
        self._highlight_signal = t.signals(highlight_signal)
        self._highlight_signal.highlight.connect(self.highlight_toggle)

        self.activated_on = activated_on or dict(background=DARKOLIVEGREEN1, color=BLACK)
        self.activated_off = activated_off or dict(background=DARKOLIVEGREEN4, color=BLACK)
        self.deactivated_on = deactivated_on or dict(background=RED1, color=BLACK)
        self.deactivated_off = deactivated_off or dict(background=RED, color=BLACK)

    def highlight_toggle(self, string=None):
        if string == self.type:
            if self.activated:
                t.style(self, **self.activated_on)
            else:
                t.style(self, **self.deactivated_on)
        else:
            if self.activated:
                t.style(self, **self.activated_off)
            else:
                t.style(self, **self.deactivated_off)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.button() == 0:
            self._highlight_signal.highlight.emit(self.type)
            self._lights_out()

    def _lights_out(self, thread=False):
        if GLOBALHighLight._decaylamp_runner and time.time() > GLOBALHighLight._decaylamp_timer:
            GLOBALHighLight._decaylamp_runner = False
            self._highlight_signal.highlight.emit('_')
        else:
            if not thread:
                GLOBALHighLight._decaylamp_timer = time.time() + 2

            if not GLOBALHighLight._decaylamp_runner or thread:
                GLOBALHighLight._decaylamp_runner = True
                delay = GLOBALHighLight._decaylamp_timer - time.time()
                t.thread(pre_sleep=delay if delay > 0.3 else 0.3, master_fn=self._lights_out, name='climate_changer', master_kwargs={'thread':True})

class SliderWidget(GODLabel):
    def __init__(
            self,
            different_states,
            slider_width=False,
            slider_width_factor=False,
            slider_shrink_factor=1,
            snap=True,
            *args, **kwargs
        ):
        """
        :param different_states: list with states (uses len(list) to calculte steps)
        :param slider_width: int (pixels width)
        :param slider_width_factor: float 0.25 (25% of self.width)
        :param slider_shrink: float (0.85 for slightly smaller slider than steps)
        """
        super().__init__(*args, **kwargs)
        self.slider_width_factor = slider_width_factor
        self.slider_width = slider_width
        self.different_states = different_states
        self.slider_shrink_factor = slider_shrink_factor
        self.slider_rail = self.SliderRail(place=self)
        self.slider = self.Slider(
            place=self,
            type=self.type,
            qframebox=True,
            center=True,
            mouse=True,
            snap=snap,
        )
        self.slider.different_states = different_states
        self.slider.inrail = self.slider_rail.inrail
        self.steady = True

    class SliderRail(GODLabel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            t.style(self, background=DARK_BACK)
            self.inrail = GODLabel(place=self)
            t.style(self.inrail, background=GRAY)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if not self.steady:
            return

        elif self.slider_width_factor:
            width = self.width() / self.slider_width_factor
        elif self.slider_width:
            width = self.slider_width
        else:
            width = self.width() / len(self.different_states)

        t.pos(self.slider, height=self, width=width * self.slider_shrink_factor)
        w = self.width() - (self.slider.width() / 3)
        t.pos(self.slider_rail, height=3, top=self.height() / 2 - 1, width=w, left=self.slider.width()/6)
        self.slider.snap_widget(force=True)
        t.pos(self.slider_rail.inrail, left=1, top=1, width=self.slider.geometry().left(), height=1)

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        """
        clicking the sliderrail will snap both save that
        state and snap the slider to that position
        """
        for i in range(len(self.different_states)):
            x1 = (self.width() / len(self.different_states)) * i
            x2 = x1 + (self.width() / len(self.different_states))
            if ev.x() >= x1 and ev.x() <= x2:
                t.save_config(self.type, self.different_states[i])
                self.slider.state = self.different_states[i]
                self.slider.snap_widget(force=True)
                break

    class Slider(GODLabel, GLOBALHighLight):
        def __init__(self, snap=True, *args, **kwargs):
            self.hold = False
            self.snap = snap
            super().__init__(*args, **kwargs)

            rv = t.config(self.type, raw=True)
            if rv and rv['value'] != None:
                self.state = rv['value']
            else:
                self.state = self.parent.different_states[0]

        def change_text(self):
            pass

        def snap_widget(self, force=False):
            """
            will adjust the slider so it fits right over the right state
            :param force: overrides non-snapping slider (used for preset)
            """
            if not self.snap and not force:
                return

            if self.state == self.different_states[0]:
                t.pos(self, left=0)
            elif self.state == self.different_states[-1]:
                t.pos(self, right=self.parent.width() - self.lineWidth())
            else:
                for count, i in enumerate(self.different_states):
                    if self.state == i:
                        each = self.parent.width() / len(self.different_states)
                        x1 = each * count
                        x2 = x1 + each
                        if self.width() < each:
                            t.pos(self, center=[x1, x2])
                        else:
                            side = (self.width() - each) / 2
                            t.pos(self, left=x1 - side)
                            if self.geometry().left() < 0:
                                t.pos(self, left=0)
                            elif self.geometry().right() > self.parent.width():
                                t.pos(self, right=self.parent.width() - self.lineWidth())
                        break

            t.pos(self.inrail, width=self.geometry().left())

        def save_state(self):
            """
            if slider is smaller than each state, state is the one that its touches the most (bleed)
            if slider is larger than each state, state is based on what the left side touches
            (self.parent.width() - self.width() since the left side can only reach parent minus self)
            :return:
            """
            each = self.parent.width() / len(self.different_states)
            if self.width() < each:
                for i in range(len(self.different_states)):
                    x1 = each * i
                    x2 = x1 + each
                    bleed = (self.width() * 0.5) + 1
                    if self.geometry().left() >= x1 - bleed and self.geometry().right() <= x2 + bleed:
                        t.save_config(self.type, self.different_states[i])
                        self.state = self.different_states[i]
                        break
            else:
                each = (self.parent.width() - self.width()) / len(self.different_states)
                for i in range(len(self.different_states)):
                    x1 = each * i
                    x2 = x1 + each

                    if self.geometry().left() > x2:
                        continue

                    t.save_config(self.type, self.different_states[i])
                    self.state = self.different_states[i]
                    break

        def mouseReleaseEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.save_state()
            self.snap_widget()
            self.change_text()
            self.hold = False

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            if not self.hold:
                self._highlight_signal.highlight.emit(self.type)
                return

            delta = QtCore.QPoint(ev.globalPos() - self.old_position)

            if self.x() + delta.x() + self.width() > self.parent.width():
                self.move(self.parent.width() - self.width(), 0)

            elif self.x() + delta.x() < 0:
                self.move(self.x() + 0, 0)

            else:
                self.move(self.x() + delta.x(), 0)

            t.pos(self.inrail, width=self.geometry().left() - self.width() / 6)
            self.old_position = ev.globalPos()

            self.save_state()
            self.change_text()

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.hold = True
            self.old_position = ev.globalPos()

class Dummys:
    def __init__(self, *args, **kwargs):
        self.button = False
        self.lineedit = False
        self.canvas_border = False
        self.label = False
        self.tiplabel = False
        super().__init__(*args, **kwargs)

class Canvas(Dummys, GODLabel):
    def __init__(self,
                 edge,
                 width,
                 height,
                 button_width=0,
                 canvas_border=0,
                 canvas_background=TRANSPARENT,
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.edge = edge
        self.canvas_border = canvas_border
        self.button_width = button_width
        t.pos(self, size=[height, width])
        t.style(self, background=canvas_background)

    def tiplabel_autohide(self):
        if self.lineedit.text():
            self.tiplabel.hide()
        else:
            self.tiplabel.show()

    def build_lineedit(self, immutable=False, **kwargs):
        self.lineedit = self.LineEdit(place=self, main=self.main, parent=self, **kwargs)
        if immutable:
            self.lineedit.setReadOnly(True)

    def build_label(self, **kwargs):
        self.label = self.Label(place=self, main=self.main, parent=self, **kwargs)

    def build_button(self, **kwargs):
        self.button = self.Button(place=self, main=self.main, parent=self, **kwargs)

    def build_tiplabel(self, text, fontsize=None, width=None):
        if self.tiplabel or not self.lineedit:
            return

        self.tiplabel = GODLabel(place=self.lineedit, monospace=True)
        self.tiplabel = t.pos(self.tiplabel, inside=self.lineedit)

        self.tiplabel.setText(text)

        if fontsize:
            t.style(self.tiplabel, font=fontsize)
            self.tiplabel.font_size = fontsize

        if not width:
            t.shrink_label_to_text(self.tiplabel)

        if not fontsize:
            self.tiplabel.font_size = t.correct_broken_font_size(self.tiplabel)

        self.tiplabel.width_size = width
        t.style(self.tiplabel, color=GRAY, background=TRANSPARENT)

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if self.width() < 100:
            return

        self.set_positions()

    def set_positions(self):
        """
        self.button_width locks button at that width, else it will be symetric square from self.height()
        :return:
        """
        if self.canvas_border:
            cb = self.canvas_border
        else:
            cb = 0

        if self.button:
            hw = self.height() - (cb * 2)

            if self.button_width:
                bw = self.button_width
            else:
                bw = hw
            t.pos(self.button, height=hw, width=bw, left=cb, top=cb)

        if self.lineedit:
            if self.button:
                t.pos(self.lineedit, after=self.button, x_margin=self.edge, height=self.height() - (cb * 2), top=cb)
                t.pos(self.lineedit, left=self.lineedit, right=self.width() - cb - 1)
            else:
                t.pos(self.lineedit, inside=self, margin=cb)

            if self.tiplabel:
                if self.tiplabel.width_size:
                    t.pos(self.tiplabel, width=self.tiplabel.width_size)

                t.pos(self.tiplabel, height=self.lineedit.height() - (cb * 2), right=self.lineedit.width() - cb, x_margin=self.edge)

        if self.label:
            if self.button:
                t.pos(self.label, inside=self, left=dict(right=self.button), x_margin=self.edge, right=self.width() - cb)
                t.pos(self.label, height=self.label, sub=cb * 2, move=[0,cb])
            else:
                t.pos(self.label, inside=self, margin=cb)

    class LineEdit(Dummys, DragDroper, GODLEPath):
        def __init__(self,
                    activated_on=None,
                    activated_off=None,
                    deactivated_on=None,
                    deactivated_off=None,
                    lineedit_foreground = 'white',
                    lineedit_background = 'black',
                    *args, **kwargs
                    ):
            super().__init__(
                             activated_on=activated_on or dict(color=WHITE),
                             activated_off=activated_off or dict(color=WHITESMOKE),
                             deactivated_on=deactivated_on or dict(color=GRAY1),
                             deactivated_off=deactivated_off or dict(color=GRAY),
                             *args, **kwargs)

            t.style(self, background=lineedit_background, color=lineedit_foreground, font=14)

    class Label(Dummys, GODLabel, GLOBALHighLight):
        def __init__(self,
                        activated_on=None,
                        activated_off=None,
                        deactivated_on=None,
                        deactivated_off=None,
                        label_background='white',
                        label_foreground='black',
                        *args, **kwargs
                    ):
            super().__init__(
                             activated_on=activated_on or dict(color=WHITE),
                             activated_off=activated_off or dict(color=WHITESMOKE),
                             deactivated_on=deactivated_on or dict(color=GRAY1),
                             deactivated_off=deactivated_off or dict(color=GRAY),
                             *args, **kwargs)

            t.style(self, background=label_background, color=label_foreground, font=14)

    class Button(Dummys, GODLabel, GLOBALHighLight):
        def __init__(self, *args, **kwargs):
            super().__init__(
                deactivated_on=dict(background=RED1, color=BLACK),
                deactivated_off=dict(background=RED, color=BLACK),
                activated_on=dict(background=GREEN1, color=BLACK),
                activated_off=dict(background=GREEN, color=BLACK),
                *args, **kwargs)
            self.setFrameShape(QtWidgets.QFrame.Box)
            self.setLineWidth(self.parent.edge)

def create_indikator(
                        place,
                        edge=1,
                        button=False,
                        lineedit=False,
                        label=False,
                        tiplabel=None,
                        height=30,
                        width=300,
                        tipfont=None,
                        tipwidth=None,
                        tooltip=None,
                        type=None,
                        Special=None,
                        share_signal=True,
                        autohide_tiplabel=False,
                        *args, **kwargs
                    ):

    if Special:
        canvas = Special(place=place, edge=edge, width=width, height=height, type=type, *args, **kwargs)
    else:
        canvas = Canvas(place=place, edge=edge, width=width, height=height, type=type, *args, **kwargs)

    if share_signal:
        kwargs['signal'] = canvas.signal
        kwargs['reset'] = False

    if lineedit:
        canvas.build_lineedit(**kwargs)
    if label:
        canvas.build_label(**kwargs)
    if button:
        canvas.build_button(**kwargs)
    if tiplabel:
        canvas.build_tiplabel(text=tiplabel, fontsize=tipfont, width=tipwidth)
    if tooltip:
        t.tooltip(tooltip)
        t.style(canvas, tooltip=True, background='black', color='white', font=14)

    cycle = dict(lineedit='lineedit', label='label', button='button', tiplabel='tiplabel')
    cycle = {k:v for k,v in cycle.items() if k}
    for boolian, var in cycle.items():
        tmp = [getattr(canvas, v) for k,v in cycle.items() if var != v]
        [setattr(widget, var, getattr(canvas, var)) for widget in tmp if widget]

    if autohide_tiplabel and lineedit and tiplabel:
        canvas.lineedit.textChanged.connect(canvas.tiplabel_autohide)

    return canvas

class MovableScrollWidget(GODLabel):
    def __init__(self, toolplate={}, backplate={}, title={}, scrollarea={}, scroller={}, gap=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raise_group = [self]
        self.gap = gap or 0
        self.make_toolplate(**toolplate)
        self.make_backplate(**backplate)
        self.make_scrollarea(**scrollarea)
        self.make_scrollthing(scroller)
        self.widgets, self.toolplate.widgets = [], []
        if 'center' not in title: title.update({'center':True})
        self.title = self.TITLE(place=self.toolplate, parent=self, **title)
        self.toolplate.widgets.append(self.title)
        pos(pos(x, size=[0,0]) for x in [self.backplate, self.toolplate, self.title])
        self.steady = True
        self.show()

    def make_toolplate(self, qframebox=True, *args, **kwargs):
        self.toolplate = GODLabel(place=self, qframebox=qframebox, *args, **kwargs)
        self.toolplate.show()

    def make_backplate(self, qframebox=False, *args, **kwargs):
        self.backplate = GODLabel(place=self, qframebox=qframebox, *args, **kwargs)
        self.backplate.show()

    def make_scrollarea(self, *args, **kwargs):
        self.scrollarea = QtWidgets.QScrollArea(self)
        self.scrollarea.setWidget(self.backplate)
        self.scrollarea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollarea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollarea.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        self.scrollarea.setLineWidth(0)
        self.scrollarea.setStyleSheet('background-color:rgba(0,0,0,0);color:rgba(0,0,0,0)')
        self.scrollarea.show()

    def raise_us(self):
        [x.raise_() for x in self.raise_group]

    def drag_widget(self, ev):
        if not self.old_position:
            self.old_position = ev.globalPos()

        delta = QtCore.QPoint(ev.globalPos() - self.old_position)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_position = ev.globalPos()

    class TITLE(GODLabel, DragDroper):
        def set_title(self, text="", height=30, fontsize=12, *args, **kwargs):
            style(self, font=fontsize)
            pos(self, top=self.parent.toolplate.lineWidth(), height=height)
            self.setText(str(text))

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.parent.drag_widget(ev)

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.parent.old_position = ev.globalPos()
            self.parent.raise_us()

    def make_title(self, *args, **kwargs): # backwards compatible
        self.set_title(*args, **kwargs)

    def set_title(self, *args, **kwargs):
        self.title.set_title(*args, **kwargs)
        self.expand_me()


    class ScrollThiney(GODLabel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.eventfilter = EventFilter(eventparent=self.parent, eventtype=QEvent.Move, master_fn=self.follow_parent)
            style(self, background='green', color='black')

        def follow_parent(self, *args, **kwargs):
            if not self.old_position:
                pos(self, after=self.parent, move=[-1, self.parent.toolplate.height()])
            else:
                pos(self, after=self.parent, top=self.parent, move=[-1, self.old_position.scroller_offset])

            self.raise_()

        def drag_widget(self, ev):
            if not self.old_position:
                self.old_position = ev.globalPos()

            y = self.y() + (QtCore.QPoint(ev.globalPos() - self.old_position)).y()

            top = self.parent.geometry().top() + self.parent.toolplate.height()
            bottom = self.parent.geometry().bottom() - self.height() + self.lineWidth()

            maximum = self.parent.scrollarea.verticalScrollBar().maximum()
            maxpix = self.parent.height() - self.parent.toolplate.height()

            pixels_process = y - top

            if not pixels_process:
                value = 0
            else:
                value = pixels_process / maxpix
                value = int(maximum * value)
                if value > maximum:
                    value = maximum

            self.parent.scrollarea.verticalScrollBar().setValue(value)

            if y >= top and y <= bottom:

                self.move(self.x(), y)
                self.old_position = ev.globalPos()

            self.old_position.scroller_offset = self.geometry().top() - self.parent.geometry().top()

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.drag_widget(ev)

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.old_position = ev.globalPos()
            if ev.button() == 1:
                self.parent.raise_us()
                self.raise_()


    def make_scrollthing(self, kwgs):
        if not kwgs:
            return

        elif kwgs == True:
            kwgs = {}

        if 'qframebox' not in kwgs:
            kwgs['qframebox'] = True

        self.scroller = self.ScrollThiney(place=self.main, parent=self, **kwgs)
        pos(self.scroller, width=8, height=20)

    def resizeEvent(self, a0=None):
        if not self.steady:
            return

        tpw = [x.geometry().bottom() for x in self.toolplate.widgets] or [0] ; tpw.sort()

        lw = self.toolplate.lineWidth()

        pos(self.toolplate, top=0, width=self, height=tpw[-1] + (lw * 2))
        [pos(x, width=self.toolplate, sub=lw * 2, left=lw) for x in self.toolplate.widgets]

        lw = self.lineWidth()
        [pos(x, below=self.toolplate, width=self, sub=lw * 2, left=lw) for x in (self.backplate, self.scrollarea)]
        pos(self.backplate, top=0, left=0)  # maybe backplate resides inside the scrollarea, but i'm not sure

        if self.gap:
            [pos(x, move=[0,self.gap]) for x in (self.backplate, self.scrollarea)]

    def expand_me(self, customheight=False, porportion=0.8):
        bpw = [x.geometry().bottom() for x in self.widgets] or [0]
        bpw.sort()

        sflw, tplw, bplw = self.lineWidth(), self.toolplate.lineWidth(), self.backplate.lineWidth()
        pos(self.backplate, height=bpw[-1], add=sflw * 2)

        if not customheight:
            tpw = [x.geometry().bottom() for x in self.toolplate.widgets if self.toolplate.height() > tplw] or [0]
            tpw.sort()
            if self.main:
                maxheight = self.main.height() * porportion
                if bpw[-1] + self.toolplate.height() > maxheight:
                    pos(self, height=maxheight, add=sflw + self.gap)
                else:
                    pos(self, height=tpw[-1] + bpw[-1] + ((sflw + tplw) * 2), add=self.gap)
            else:
                pos(self, height=tpw[-1] + bpw[-1] + ((sflw + tplw) * 2), add=self.gap)

        pos(self.scrollarea, height=self, sub=self.toolplate.height())


