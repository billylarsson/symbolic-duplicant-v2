from PIL                     import Image
from PyQt5                   import QtCore, QtGui, QtWidgets
from PyQt5.Qt                import QObject, QRunnable, QThreadPool
from PyQt5.QtCore            import pyqtSignal, pyqtSlot
from PyQt5.QtGui             import QColor
from base64                  import b16encode
from bscripts.database_stuff import DB, sqlite
from bscripts.preset_colors  import *
from datetime                import datetime
from functools               import partial
from queue                   import Queue
from threading               import Lock
from urllib.request          import Request, urlopen
import copy
import hashlib
import os
import pathlib
import pickle
import platform
import random
import requests
import shutil
import ssl
import sys
import tempfile
import threading
import time
import traceback
import uuid

default_dict = dict(
    default=dict(
            ),
    highlight=dict(
        folders=[
            dict(deactivated_on=dict(background='rgb(55,50,50)', color=WHITE, font=14)),
            dict(deactivated_off=dict(background='rgb(25,20,20)', color='rgb(222,222,222)', font=14))
        ],
        files=[
            dict(deactivated_on=dict(background='rgb(30,40,30)', color=WHITE, font=13)),
            dict(deactivated_off=dict(background='rgb(15,25,15)', color='rgb(211,211,211)', font=13))
        ],
        goback=[
            dict(deactivated_on=dict(background='rgb(40,40,70)', color=GRAY)),
            dict(deactivated_off=dict(background='rgb(29,29,29)', color='rgb(201,201,201)', font=20))
        ],
        implement=[
            dict(deactivated_on=dict(background='rgb(190,190,255)', color=BLACK)),
            dict(deactivated_off=dict(background='rgb(150,150,230)', color=BLACK, font=10))
        ],
        unimplement=[
            dict(deactivated_on=dict(background='rgb(200,200,255)', color=BLACK)),
            dict(deactivated_off=dict(background='rgb(170,170,250)', color=BLACK, font=10))
        ],
        overwrite=[
            dict(deactivated_on=dict(background=RED1, color=BLACK)),
            dict(deactivated_off=dict(background=RED, color=BLACK, font=12))
        ],
        next_back=[
            dict(deactivated_on=dict(background=BLUE2, color=BLACK)),
            dict(deactivated_off=dict(background=BLUE4, color=BLACK, font=12))
        ],
        settingsbutton=[
            dict(activated_on=dict(background=GREEN2, color=GRAY10)),
            dict(activated_off=dict(background=GREEN4, color=GRAY10, font=12)),
            dict(deactivated_on=dict(background=GRAY22, color=BLACK)),
            dict(deactivated_off=dict(background=GRAY13, color=BLACK, font=12))
        ],
    ),
)

for i in default_dict['default']:
    if 'activated' not in default_dict['default'][i]:
        default_dict['default'][i].update({'activated': True})

qrcodedata = dict(width=145, height=145, work=[{14: [(145, 0)]}, {4: [(14, 0), (28, 1), (12, 0), (4, 1), (4, 0), (4, 1), (12, 0), (4, 1), (8, 0), (8, 1), (4, 0), (28, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (20, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (8, 0), (20, 1), (8, 0), (4, 1), (4, 0), (4, 1), (20, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (20, 0), (4, 1), (8, 0), (4, 1), (8, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (4, 0), (12, 1), (4, 0), (16, 1), (4, 0), (12, 1), (8, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (8, 0), (4, 1), (16, 0), (4, 1), (4, 0), (4, 1), (8, 0), (8, 1), (4, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (20, 0), (4, 1), (4, 0), (8, 1), (4, 0), (8, 1), (8, 0), (12, 1), (8, 0), (4, 1), (4, 0), (4, 1), (20, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (28, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (28, 1), (15, 0)]}, {4: [(50, 0), (12, 1), (8, 0), (12, 1), (4, 0), (12, 1), (47, 0)]}, {4: [(14, 0), (20, 1), (4, 0), (16, 1), (4, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (12, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (19, 0)]}, {4: [(30, 0), (4, 1), (12, 0), (4, 1), (4, 0), (4, 1), (4, 0), (8, 1), (8, 0), (4, 1), (8, 0), (24, 1), (12, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (8, 1), (8, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (8, 0), (4, 1), (4, 0), (4, 1), (8, 0), (4, 1), (4, 0), (8, 1), (12, 0), (4, 1), (27, 0)]}, {4: [(18, 0), (8, 1), (4, 0), (4, 1), (8, 0), (8, 1), (12, 0), (4, 1), (8, 0), (4, 1), (8, 0), (4, 1), (12, 0), (4, 1), (4, 0), (4, 1), (31, 0)]}, {4: [(14, 0), (12, 1), (4, 0), (4, 1), (4, 0), (20, 1), (4, 0), (12, 1), (8, 0), (4, 1), (20, 0), (4, 1), (4, 0), (12, 1), (19, 0)]}, {4: [(18, 0), (4, 1), (24, 0), (8, 1), (12, 0), (8, 1), (4, 0), (4, 1), (8, 0), (24, 1), (12, 0), (4, 1), (15, 0)]}, {4: [(14, 0), (8, 1), (12, 0), (8, 1), (4, 0), (8, 1), (4, 0), (12, 1), (4, 0), (4, 1), (4, 0), (4, 1), (8, 0), (8, 1), (4, 0), (8, 1), (8, 0), (4, 1), (19, 0)]}, {4: [(14, 0), (20, 1), (8, 0), (4, 1), (12, 0), (4, 1), (16, 0), (4, 1), (4, 0), (8, 1), (8, 0), (16, 1), (8, 0), (4, 1), (15, 0)]}, {4: [(22, 0), (4, 1), (8, 0), (8, 1), (4, 0), (8, 1), (4, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (16, 0), (8, 1), (19, 0)]}, {4: [(14, 0), (24, 1), (4, 0), (8, 1), (4, 0), (4, 1), (4, 0), (4, 1), (12, 0), (4, 1), (8, 0), (8, 1), (4, 0), (16, 1), (4, 0), (8, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (8, 0), (20, 1), (4, 0), (8, 1), (8, 0), (12, 1), (4, 0), (4, 1), (8, 0), (8, 1), (12, 0), (8, 1), (23, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (4, 1), (8, 0), (4, 1), (12, 0), (8, 1), (4, 0), (4, 1), (4, 0), (8, 1), (8, 0), (4, 1), (8, 0), (12, 1), (12, 0), (8, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (4, 1), (4, 0), (16, 1), (8, 0), (4, 1), (4, 0), (8, 1), (8, 0), (8, 1), (8, 0), (32, 1), (19, 0)]}, {4: [(46, 0), (8, 1), (12, 0), (8, 1), (16, 0), (8, 1), (12, 0), (4, 1), (8, 0), (8, 1), (15, 0)]}, {4: [(14, 0), (28, 1), (4, 0), (4, 1), (8, 0), (8, 1), (8, 0), (4, 1), (4, 0), (4, 1), (4, 0), (8, 1), (4, 0), (4, 1), (4, 0), (12, 1), (23, 0)]}, {4: [(14, 0), (4, 1), (20, 0), (4, 1), (8, 0), (4, 1), (4, 0), (4, 1), (8, 0), (4, 1), (4, 0), (4, 1), (4, 0), (12, 1), (12, 0), (8, 1), (4, 0), (8, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (4, 0), (16, 1), (12, 0), (12, 1), (8, 0), (36, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (8, 1), (28, 0), (4, 1), (20, 0), (8, 1), (15, 0)]}, {4: [(14, 0), (4, 1), (4, 0), (12, 1), (4, 0), (4, 1), (4, 0), (12, 1), (8, 0), (12, 1), (4, 0), (4, 1), (8, 0), (4, 1), (4, 0), (16, 1), (4, 0), (4, 1), (19, 0)]}, {4: [(14, 0), (4, 1), (20, 0), (4, 1), (4, 0), (4, 1), (12, 0), (8, 1), (4, 0), (4, 1), (12, 0), (8, 1), (8, 0), (12, 1), (4, 0), (4, 1), (19, 0)]}, {4: [(14, 0), (28, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (4, 1), (4, 0), (20, 1), (8, 0), (4, 1), (4, 0), (4, 1), (8, 0), (4, 1), (23, 0)]}, {15: [(145, 0)]}])

class DIRECTPOSITION:
    @staticmethod
    def digit(value):
        if type(value) == int or type(value) == float:
            return True

    @staticmethod
    def set_hw(widget, w, h):
        widget.resize(int(w), int(h))

    @staticmethod
    def set_geo(widget, x, y, w, h):
        widget.setGeometry(int(x), int(y), int(w), int(h))

    @staticmethod
    def extra(**kwargs):
        """
        ie: extra(dict(y_margin=kwgs))
        returns y_margin if such key are present
        :param kwargs: dictionary[key] = all_kwargs_from_parent
        :return: the value or 0
        """
        if not kwargs:
            return 0

        for master_key, slave_list in kwargs.items():

            for orders in slave_list:

                for k,v in orders.items():

                    if k == master_key:
                        return v

        return 0

    @staticmethod
    def width(widget, args, kwgs):

        if POS.digit(args):
            w = args
            h = widget.height()
        else:
            w = args.width()
            h = widget.height()

        POS.set_hw(widget, w + POS.extra(add=kwgs), h)

    @staticmethod
    def height(widget, args, kwgs):

        if POS.digit(args):
            w = widget.width()
            h = args
        else:
            w = widget.width()
            h = args.height()

        POS.set_hw(widget, w, h + POS.extra(add=kwgs))

    @staticmethod
    def size(widget, args, kwgs):
        """
        :param args: list/tuple with len(2) or widget
        """
        if type(args) == list or type(args) == tuple:
            w = args[0]
            h = args[1]

        else:
            w = args.width()
            h = args.height()

        POS.set_hw(widget, w + POS.extra(add=kwgs), h + POS.extra(add=kwgs))

    @staticmethod
    def inside(working_widget, parent, kwgs):
        """
        you can "coat" a widget that resides within its parent and
        using margins while doing so, but you cannot "coat" parent
        :param parent: must be a widget
        """
        margin = POS.extra(margin=kwgs)
        x, y = 0 + margin, 0 + margin
        w = parent.width() - margin * 2
        h = parent.height() - margin * 2
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def coat(working_widget, sister_widget, kwgs):
        """
        for two widgets that share the same parent you can coat one ontop
        the other to get their exact cordinates, this is very suitable.
        """
        margin = POS.extra(margin=kwgs)
        x = sister_widget.geometry().left() + margin
        y = sister_widget.geometry().top() + margin
        w = sister_widget.width() - margin * 2
        h = sister_widget.height() - margin * 2
        POS.set_geo(working_widget, x, y, w, h)

    @staticmethod
    def top(widget, args, kwgs):
        """
        read fn:left for same logic, basically if bottom is represented in kwgs its performed
        here as well meaning widget at will can stretch or shrink to reach bottom-destination
        """
        if not POS.digit(args):
            if type(args) == dict:
                if next(iter(args)) == 'top':
                    args = args['top'].geometry().top()
                else:
                    args = args['bottom'].geometry().bottom() + 1
            else:
                args = args.geometry().top()

        y_margin = POS.extra(y_margin=kwgs)

        x = widget.geometry().left()
        y = args + y_margin
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y ,w, h)

        bottom = POS.extra(bottom=kwgs)

        if bottom:

            if not POS.digit(bottom):

                if type(bottom) == dict:
                    if next(iter(bottom)) == 'bottom':
                        bottom = bottom['bottom'].geometry().bottom()
                    else:
                        bottom = bottom['top'].geometry().top() - 1
                else:
                    bottom = bottom.geometry().bottom()

            fill = bottom - widget.geometry().bottom() - y_margin
            POS.set_hw(widget, widget.width(), widget.height() + fill)

    @staticmethod
    def bottom(widget, args, kwgs):
        """ read fn:top """

        top = POS.extra(top=kwgs)

        if top: # rights task performed in fn:left
            return

        if not POS.digit(args):
            if type(args) == dict:
                if next(iter(args)) == 'bottom':
                    args = args['bottom'].geometry().bottom() + 1
                else:
                    args = args['top'].geometry().top()
            else:
                args = args.geometry().bottom() + 1

        y_margin = POS.extra(y_margin=kwgs)

        x = widget.geometry().left()
        y = args - widget.height() - y_margin
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y ,w, h)

    @staticmethod
    def left(widget, args, kwgs):
        """
        if argument is int moves widget to start from the argument pixel, if its an object
        then using that objects leftest pixel. if arguemnt is a dictionary(left=sister_widget)
        her's leftest pixel is used, however if dictionary(right=sister_widget) then it will
        be that rightest pixel plus one, assuming we want to start NEXT TO sisters widget.

        if right is somewhere within kwgs, right is dealt with within
        here and no changes will occur when it actually reaches fn:right

        x_margin simply moves the widget forward for that amount of pixels
        but if both left and right changes occurs simultaniously here, x_margin
        will actually shrink the finished position to honor both side margin-symetry

        :param args: int, dictionary or widget
        """
        if not POS.digit(args):

            if type(args) == dict:
                if next(iter(args)) == 'left':
                    args = args['left'].geometry().left() # assume left to left means sharing same pixel
                else:
                    args = args['right'].geometry().right() + 1 # assume left want to position NEXT to right position
            else:
                args = args.geometry().left()

        x_margin = POS.extra(x_margin=kwgs)

        x = args + x_margin
        y = widget.geometry().top()
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y, w, h)

        right = POS.extra(right=kwgs)

        if right:

            if not POS.digit(right):

                if type(right) == dict:
                    if next(iter(right)) == 'left':
                        right = right['left'].geometry().left() - 1 # assume right want to position BEFORE left position
                    else:
                        right = right['right'].geometry().right() # assume right to right means sharing same pixel
                else:
                    right = right.geometry().right()

            fill = right - widget.geometry().right() - x_margin
            POS.set_hw(widget, widget.width() + fill, widget.height())

    @staticmethod
    def right(widget, args, kwgs):
        """ read fn:left """
        left = POS.extra(left=kwgs)

        if left: # rights task performed in fn:left
            return

        if not POS.digit(args):

            if type(args) == dict:
                if next(iter(args)) == 'left':
                    args = args['left'].geometry().left() - 1  # assume right want to position BEFORE left position
                else:
                    args = args['right'].geometry().right()  # assume right to right means sharing same pixel
            else:
                args = args.geometry().right()

        x_margin = POS.extra(x_margin=kwgs)

        x = args - widget.width() + 1 - x_margin # because we count start (zero) as first pixel
        y = widget.geometry().top()
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x, y, w, h)

    @staticmethod
    def reach(widget, args, kwgs):
        """
        arguemnt must be wrapped inside a dictionary to work.

        same thing can be accomplished by using left & right, top & bottom together.
        the widgets position is fixed and the widgets side reaches for its desitnation digit or object

        ie: reach=dict(left=self.reachthiswidget) # reaches for the widget
        ie: reach=dict(left=120) # reaches for x,y position

        also, if you want to reach right to left you wrap that in a dictionary as below:
        ie: reach=dict(left=dict(right=self.reachthiswidget))
        NOTE: when doing so a pixel will be subtracted so edges touches instead of overlapping
        """
        def right(widget, args, kwgs):
            x_margin = 1 + POS.extra(x_margin=kwgs)
            if POS.digit(args):
                width = args - widget.pos().x()
            else:
                if type(args) == dict:
                    if 'left' in args:
                        width = args['left'].geometry().left() - widget.pos().x() - 1
                        x_margin -= (x_margin * 2) - 2
                    else:
                        width = args['right'].geometry().right() - widget.pos().x()
                else:
                    width = args.geometry().right() - widget.pos().x()
            POS.set_geo(widget, widget.pos().x(), widget.pos().y(), width + x_margin, widget.height())

        def left(widget, args, kwgs):
            x_margin = POS.extra(x_margin=kwgs)
            if POS.digit(args):
                extra = widget.pos().x() - args
                width = widget.width() + extra - x_margin
                POS.set_geo(widget, args + x_margin, widget.pos().y(), width, widget.height())
            else:
                if type(args) == dict:
                    if 'left' in args:
                        extra = widget.pos().x() - args['left'].geometry().left()
                    else:
                        extra = widget.pos().x() - args['right'].geometry().right() - 1
                        extra -= (x_margin * 2) - 2
                else:
                    extra = widget.pos().x() - args.geometry().left()
                x = widget.pos().x() - extra + x_margin
                POS.set_geo(widget, x, widget.pos().y(), widget.width() + extra - x_margin, widget.height())

        def bottom(widget, args, kwgs):
            y_margin = 1 + POS.extra(y_margin=kwgs)
            if POS.digit(args):
                height = args - widget.pos().y()
            else:
                if type(args) == dict:
                    if 'top' in args:
                        height = args['top'].geometry().top() - widget.pos().y() - 1
                        y_margin -= (y_margin * 2) - 2
                    else:
                        height = args['bottom'].geometry().bottom() - widget.pos().y()
                else:
                    height = args.geometry().bottom() - widget.pos().y()
            POS.set_geo(widget, widget.pos().x(), widget.pos().y(), widget.width(), height + y_margin)

        def top(widget, args, kwgs):
            y_margin = POS.extra(y_margin=kwgs)
            if POS.digit(args):
                extra = widget.pos().y() - args
                POS.set_geo(widget, widget.pos().x(), args, widget.width(), widget.height() + extra)
            else:
                if type(args) == dict:
                    if 'top' in args:
                        extra = widget.pos().y() - args['top'].geometry().top()
                    else:
                        extra = widget.pos().y() - args['bottom'].geometry().bottom() - 1
                        y_margin -= (y_margin * 2) - 2
                else:
                    extra = widget.pos().y() - args.geometry().top()
                y = widget.pos().y() - extra + y_margin
                POS.set_geo(widget, widget.pos().x(), y, widget.width(), widget.height() + extra - y_margin)

        for var, fn in dict(right=right, left=left, bottom=bottom, top=top).items():
            if var in args:
                fn(widget, args[var], kwgs)


    @staticmethod
    def after(working_widget, preceeding_widget, kwgs):
        """
        position widget after preceeding_widget,
        y cordinates will be honored
        :param preceeding_widget: must be a widget
        """
        x_margin = POS.extra(x_margin=kwgs)
        x = preceeding_widget.geometry().right() + 1 + x_margin # because we count start (zero) as first pixel
        y = preceeding_widget.geometry().top()
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def before(working_widget, following_widget, kwgs):
        """
        position widget before following_widget,
        y cordinates will be honored
        :param preceeding_widget: must be a widget
        """
        x_margin = POS.extra(x_margin=kwgs)
        x = following_widget.geometry().left() - working_widget.width() - 1 - x_margin  # subtracting first pixel
        y = following_widget.geometry().top()
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def above(working_widget, widget_under, kwgs):
        """
        position widget above the widget under it, honoring x cordinates
        :param widget_above: must be a widget
        """
        y_margin = POS.extra(y_margin=kwgs)
        x = widget_under.geometry().left()
        y = widget_under.geometry().top() - working_widget.height() - y_margin
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def below(working_widget, widget_above, kwgs):
        """
        position widget below the widget above it, honoring x cordinates
        :param widget_above: must be a widget
        """
        y_margin = POS.extra(y_margin=kwgs)
        x = widget_above.geometry().left()
        y = widget_above.geometry().bottom() + 1 + y_margin # not sharing same pixel
        w = working_widget.width()
        h = working_widget.height()
        POS.set_geo(working_widget, x,y,w,h)

    @staticmethod
    def under(*args):
        POS.below(*args)

    @staticmethod
    def center(widget, args, kwgs):
        pointa = args[0]
        pointb = args[1]

        if not POS.digit(pointa):
            if type(pointa) == dict:
                if next(iter(pointa)) == 'left':
                    pointa = pointa['left'].geometry().left()
                else:
                    pointa = pointa['right'].geometry().right()
            else:
                pointa = pointa.geometry().right()

        if not POS.digit(pointb):
            if type(pointb) == dict:
                if next(iter(pointb)) == 'left':
                    pointb = pointb['left'].geometry().left()
                else:
                    pointb = pointb['right'].geometry().right()
            else:
                pointb = pointb.geometry().left()

        rest = pointb - pointa - widget.width()
        rest = rest * 0.5

        x = pointa + rest
        y = widget.geometry().top()
        w = widget.width()
        h = widget.height()

        POS.set_geo(widget, x,y,w,h)

    @staticmethod
    def between(widget, list_with_two_widgets, kwgs):
        """
        if third index == True or 'x' widget is inserted between 0 and 1 in the row
        if third index == False or 'y' widget is put between 0 and 1 stacked on top of each others
        :param list_with_two_widgets: object, object, string/bool (defaults to True, honoring x)
        """
        if list_with_two_widgets[-1] in {False, 'y'}:
            pointa = list_with_two_widgets[0].geometry().bottom() + 1 # else same pixel
            pointb = list_with_two_widgets[1].geometry().top()

            rest = (pointb - pointa) - widget.height()

            if rest > 1:
                x = widget.geometry().left()
                y = pointa + (rest * 0.5)
                POS.set_geo(widget, x, y, widget.width(), widget.height())

        else:
            pointa = list_with_two_widgets[0].geometry().right()
            pointb = list_with_two_widgets[1].geometry().left() + 1 # else same pixel

            rest = (pointb - pointa) - widget.width()

            if rest > 1:
                x = pointa + (rest * 0.5)
                y = widget.geometry().top()
                POS.set_geo(widget, x, y, widget.width(), widget.height())

    @staticmethod
    def move(widget, args, kwgs):
        """
        moving cordinates will be calculated from current position
        :param args: list or tuple
        """
        x = widget.geometry().left() + args[0]
        y = widget.geometry().top() + args[1]
        w = widget.width()
        h = widget.height()
        POS.set_geo(widget, x,y,w,h)

    @staticmethod
    def background(widget, args, kwgs):
        tech.style(widget, background=args)

    @staticmethod
    def color(widget, args, kwgs):
        tech.style(widget, color=args)

    @staticmethod
    def font(widget, args, kwgs):
        if POS.digit(args):
            args = str(args) + 'pt'
        tech.style(widget, font=args)

POS = DIRECTPOSITION()

class CustomThreadPool:
    def __init__(self, threads=1, short_sleep=0.05, long_sleep=0.5, deep_sleep_delay=30, *args, **kwargs):
        self.max_threads = threads
        self.warden = threading.Thread(target=self.thread_runner, daemon=True)

        self.deep_sleep_delay = deep_sleep_delay
        self.short_sleep = short_sleep

        if self.short_sleep > long_sleep:  # if long_sleep isnt explicitly bigger long_sleep == short_sleep
            self.long_sleep = self.short_sleep
        else:
            self.long_sleep = long_sleep

        self.queue = Queue()
        self.warden.start()

    def __call__(self, slave_fn=None, *args, **kwargs):
        # all args needs to be inside a tuple when *unpacking at execution time, solution if you
        # are forwarding a tuple as-is: put it in yet another tuple before entering threadpool

        thread = threading.Thread(target=self.slave_execution, daemon=True)
        thread.signals = self.WorkerSignals()
        thread.signals.start.connect(self.execution_begin)
        thread.signals.finished.connect(self.master_execution)

        self.setup_slaves_orders(thread, slave_fn, *args, **kwargs)
        self.setup_masters_orders(thread, *args, **kwargs)
        self.setup_pre_sleep_orders(thread, *args, **kwargs)
        self.setup_post_sleep_orders(thread, *args, **kwargs)
        thread._kwargs = dict(thread=thread)
        self.queue.put(thread)

    class WorkerSignals(QObject):
        finished = pyqtSignal(object)
        start = pyqtSignal(object)

    def thread_runner(self):
        self.running = threading.local()
        self.running.threads = []
        self.running.night_shift = time.time() + self.deep_sleep_delay

        while True:

            if self.max_threads > len(self.running.threads) and self.queue.queue:
                thread = self.queue.get()
                self.running.threads.append(thread)
                self.running.night_shift = time.time() + self.deep_sleep_delay
                thread.signals.start.emit(thread)

            for thread in [x for x in self.running.threads if not x.is_alive() and x._started.is_set()]:
                self.running.threads = [x for x in self.running.threads if x != thread]
                self.queue.task_done()
                self.running.night_shift = time.time() + self.deep_sleep_delay
                thread.signals.finished.emit(thread)

                if thread.post_sleep:
                    time.sleep(thread.post_sleep)  # the entire threadpool will suffer this wait
                    break

            if not self.queue.queue and not self.running.threads:
                if time.time() > self.running.night_shift:
                    time.sleep(self.long_sleep)
                    continue

            time.sleep(self.short_sleep)

    def execution_begin(self, thread):
        if thread.dummy:
            self.dummy()

        thread.start()

    def slave_execution(self, thread):

        if thread.pre_sleep:
            time.sleep(thread.pre_sleep)

        for job in thread.slave_executions:
            self.execute(job)

    def master_execution(self, thread):
        for job in thread.master_executions:
            self.execute(job)

    def execute(self, job):
        if type(job) == dict:

            fn = job['fn'] if 'fn' in job else None
            args = job['args'] if 'args' in job else ()
            kwargs = job['kwargs'] if 'kwargs' in job else {}
        else:
            fn, args, kwargs = job, (), {}

        if fn:
            if args and kwargs:
                fn(*args, **kwargs)
            elif args:
                fn(*args)
            elif kwargs:
                fn(**kwargs)
            else:
                fn()

    def setup_slaves_orders(self, thread, slave_fn=None, slave_args=(), slave_kwargs={}, *args, **kwargs):
        if type(slave_fn) in {list, tuple, set}:
            thread.slave_executions = [x for x in slave_fn]  # meaning you have a list with proper dictionaries
        else:
            if type(slave_args) != tuple:
                slave_args = (slave_args,)

            thread.slave_executions = [dict(fn=slave_fn, args=slave_args, kwargs=slave_kwargs)]

    def setup_masters_orders(self, thread, master_fn=None, master_args=(), master_kwargs={}, *args, **kwargs):
        if type(master_fn) in {list, tuple, set}:
            thread.master_executions = [x for x in master_fn]  # meaning you have a list with proper dictionaries
        else:
            if type(master_args) != tuple:
                master_args = (master_args,)

            thread.master_executions = [dict(fn=master_fn, args=master_args, kwargs=master_kwargs)]

    def setup_pre_sleep_orders(self, thread, dummy=None, pre_sleep=None, *args, **kwargs):
        if dummy:
            thread.dummy = True
        else:
            thread.dummy = False

        for i in [pre_sleep, dummy]:
            if i and type(i) in {float, int, bool}:
                if type(i) == bool:
                    thread.pre_sleep = 0
                else:
                    thread.pre_sleep = float(i)
                return
            else:
                thread.pre_sleep = None

    def setup_post_sleep_orders(self, thread, sleep=None, post_sleep=None, *args, **kwargs):
        for i in [sleep, post_sleep]:
            if i and type(i) in {float, int, bool}:
                if type(i) == bool:
                    thread.post_sleep = 0
                else:
                    thread.post_sleep = float(i)
                return
            else:
                thread.post_sleep = None

    def dummy(self):
        return True

class ViktorinoxTechClass:
    def __init__(self):
        self.dev_mode = True if 'dev_mode' in sys.argv else False
        self.techdict = {}
        self.signal = self.ConfigSignals()
        self.signal.save_config.connect(self._save_config)
        self._save_config(('dummy', None, 'default', True, None,))

    class ConfigSignals(QObject):
        save_config = pyqtSignal(tuple)

    @staticmethod
    def pos(widget=None, kwgs=None, new=False, **kwargs):
        def subraction_to_addition():
            """
            if 'sub' in kwargs it will make sub into add and makes sure the value
            is negative due human logic, yeah this can become buggy later on
            """
            if kwargs['sub'] > 0:
                kwargs['add'] = -kwargs['sub']
            else:
                kwargs['add'] = kwargs['sub']

        if 'sub' in kwargs:
            subraction_to_addition()

        if not kwgs:
            kwgs = [kwargs]

        if new:
            widget = QtWidgets.QLabel(new, lineWidth=0, midLineWidth=0)
            widget.show()

        for args in kwgs:
            for k, v in args.items():
                fn = getattr(POS, k, False)

                if not fn:
                    continue

                fn(widget, v, kwgs)

        return widget

    def printout_downloaded_this_file(self, url, full_path='', force=False):
        if self.dev_mode or force:
            clock = tech.timeconverter(time.time(), clock=True,)
            BROWN, GREEN, CYAN, GRAY, END = '\033[0;33m', '\033[92m', '\033[96m', '\033[0;37m', '\033[0m'
            text = f'{clock} {GRAY}DOWNLOADED {CYAN}{url}{GRAY} ---::]{END}'
            if full_path and os.path.exists(full_path):
                text += f' {GREEN}{full_path} {GRAY}{round(os.path.getsize(full_path) / 1000)}kb{END}'
            print(text)

    @staticmethod
    def generate_dict_qrcode(path):
        img = Image.open(path).convert('L')
        width = img.size[0]
        height = img.size[1]
        datas = img.getdata()
        d = []
        count = 0
        for y in range(height):
            row = dict(y=1, r=[])
            for x in range(width):
                item = datas[count]

                if item > 200:
                    current = 0
                else:
                    current = 1

                if row['r'] and row['r'][-1]['v'] == current:
                    row['r'][-1]['x'] += 1
                else:
                    row['r'].append(dict(x=1, v=current))
                count += 1

            if d and d[-1]['r'] == row['r']:
                d[-1]['y'] += 1
            else:
                d.append(row)

        optimized = dict(work=[], width=width, height=height)
        for i in d:
            optimized['work'].append({i['y']: [(x['x'], x['v'],) for x in i['r']]})

        return optimized

    @staticmethod
    def create_qrcode_image(qrcode_data=None, tmpfile=None):
        if not qrcode_data:
            qrcode_data = qrcodedata

        background_color = (255, 255, 255,)
        img = Image.new('RGB', (qrcode_data['width'], qrcode_data['height']), background_color)

        datas = []
        for work in qrcode_data['work']:
            for y_count, rowlist in work.items():
                for y in range(y_count):
                    for draw in rowlist:
                        for x in range(draw[0]):
                            if draw[1] == 1:
                                datas.append((0, 0, 0,))
                            else:
                                datas.append(background_color)
        img.putdata(datas)
        if not tmpfile:
            tmpfile = tech.tmp_file(file_of_interest='QRCODE', hash=True, delete=True, extension='webp')

        img.save(tmpfile, "webp", quality=70, method=6)
        img.close()
        return tmpfile

    @staticmethod
    def close_and_pop(thislist, keep_fortified=True):
        for count in range(len(thislist) - 1, -1, -1):

            if keep_fortified and 'fortified' in dir(thislist[count]) and thislist[count].fortified:
                continue

            thislist[count].signal.killswitch.emit()
            thislist[count].close()
            thislist.pop(count)

    @staticmethod
    def digit_prolonger(numeric_value, digits=2):
        if numeric_value == None:
            return 'N/A'

        numeric_value = float(numeric_value)
        numeric_value += 0.00

        if numeric_value >= 100:
            digits = 0

        numeric_value = str(f"%.{digits}f" % numeric_value)
        return numeric_value

    @staticmethod
    def tooltip(label, tooltip, background='white', color='black', fontsize=10):
        if not label.styleSheet():
            stylesheet = label.metaObject().className() + '{background-color:dummy;color:dummy}'
            label.setStyleSheet(stylesheet)

        QtWidgets.QToolTip.setFont(QtGui.QFont('Consolas', fontsize))
        tech.style(label, tooltip=True, background=background, color=color, font=fontsize)
        label.setToolTip(f"{tooltip}")

    @staticmethod
    def separate_file_from_folder(local_path):
        """
        local_path can already be THIS object
        :param local_path must be full path including filename
        :return: object.string: full_path, db_folder, filename, naked_filename, sep (separator)
        """
        if type(local_path) != str:
            return local_path


        class LOCATIONS:
            def __init__(self, local_path):
                self.full_path = os.path.abspath(os.path.expanduser(local_path))
                self.path = self.full_path
                self.sep = os.sep
                tmp = self.path.split(self.sep)

                self.filename = tmp[-1]

                if len(tmp) > 1:
                    self.folder = self.sep.join(tmp[0:-1])
                else:
                    self.folder = tmp[0]

                tmp = tmp[-1].split('.')

                if len(tmp) > 1:
                    self.ext = tmp[-1]
                    self.naked_filename = ".".join(tmp[:-1])
                else:
                    self.ext = ""
                    self.naked_filename = tmp[0]

            def __str__(self):
                return self.full_path

            def __bool__(self):
                return os.path.exists(self.full_path)


        return LOCATIONS(local_path)

    @staticmethod
    def timeconverter(unixtime=None, stringdate=None, long=False, clock=False):
        """
        unixtime: 1640991600.0 (returns string 2021-01-07, long adds hours and seconds)
        stringdate: 2022-01-01 (returns epoch)
        """
        if unixtime:
            if type(unixtime) == str:
                try: unixtime = int(unixtime)
                except: return ""
            if long or clock:
                if clock:
                    return datetime.fromtimestamp(unixtime).strftime('%H:%M:%S')
                else:
                    return datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d @ %H:%M:%S')
            else:
                return datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d')
        elif stringdate.count('-') >= 2:
            stringdate = stringdate.split('-')
            stringdate += [0,0,0,0]
            stringdate = (int(x) for count, x in enumerate(stringdate) if count < 7)
            return datetime(*stringdate).timestamp()

    @staticmethod
    def uni_search(fromlist, userinput, key):
        """
        makes list of userinput and searches
        each key for each part of the userinput
        :param fromlist:
        :param userinput:
        :param key:
        :return: drawlist
        """
        searchlist = userinput.strip().lower().split()
        drawlist = []

        if searchlist:
            for datacount, eachsource in enumerate(fromlist):
                source = str(eachsource[key])
                for usercount, eachinput in enumerate(searchlist):

                    if source == None or eachinput == None:
                        continue

                    search_value = source.lower().find(eachinput)

                    if search_value != -1:
                        source = source[0:search_value] + source[search_value+len(eachinput):]
                        if usercount == len(searchlist) -1:
                            drawlist.append(fromlist[datacount])
                    else:
                        break
        else:
            return fromlist

        return drawlist

    @staticmethod
    def correct_broken_font_size(object, presize=True, maxsize=24, minsize=5, x_margin=10, y_margin=0, shorten=False):
        if presize:
            tech.style(object, font=str(maxsize) + 'pt')

        if shorten:
            for count in range(len(object.text())):
                object.show()
                if object.fontMetrics().boundingRect(object.text()).width() + x_margin > object.width():
                    text = object.text()
                    object.setText(text[0:-3] + '..')
                elif count == 0:
                    return False
                else:
                    return True

        for count in range(maxsize,minsize,-1):
            object.show()
            if object.fontMetrics().boundingRect(object.text()).width() + x_margin > object.width():
                tech.style(object, font=str(count) + 'pt')
            elif object.fontMetrics().boundingRect(object.text()).height() + y_margin > object.height():
                tech.style(object, font=str(count) + 'pt')
            else:
                return count + 1

    @staticmethod
    def highlight_style(widget, name):
        if name in default_dict['highlight']:
            for preset in default_dict['highlight'][name]:
                for k,v in preset.items():
                    setattr(widget, k, v)

    @staticmethod
    def style(widget, name=None, background=None, color=None, font=None, tooltip=None, curious=False, construct=None):

        def new_construct():
            return {
                'base':{
                    'background-color:': None,
                    'color:': None,
                    'font:': None,
                    },
                'tooltip':{
                    'background-color:': None,
                    'color:': None,
                    'font:': None,
                    },
                }

        def do_somoething(string, construct):
            if string:
                string = string.replace(" ", "")

            if string and '{' in string and '}' in string: # clamps stylesheet
                if 'QToolTip' in string:
                    tmp = string.split('QToolTip')
                    if len(tmp) > 1:
                        ttrv = tmp[1]
                    else:
                        ttrv = tmp[0]

                    ttrv = 'QToolTip' + "".join(ttrv[0:ttrv.find('}')+1])
                    string = string.replace(ttrv, "")
                    ttrv = ttrv.replace('QToolTip', "").replace('{', "").replace('}', "")
                    ttlist = ttrv.split(';')

                    for i in ['background-color:', 'color:', 'font:']:
                        tmp = [x for x in ttlist if x and x.startswith(i)]
                        if tmp:
                            value = "".join(tmp).split(':')
                            construct['tooltip'][i] = value[-1]

                string = string.replace('}', "").split('{')
                base = "".join(string[1:]).split(';')
                for i in ['background-color:', 'color:', 'font:']:
                    tmp = [x for x in base if x and x.startswith(i)]
                    if tmp:
                        value = "".join(tmp).split(':')
                        construct['base'][i] = value[-1]

            elif string: # legacy stylesheet
                one = string.split(';')
                for i in ['background-color:', 'color:', 'font:']:
                    tmp = [x for x in one if x and x.startswith(i)]
                    if tmp:
                        value = "".join(tmp).split(':')
                        if tooltip:
                            construct['tooltip'][i] = value[-1]
                        else:
                            construct['base'][i] = value[-1]

        if not construct:
            construct = new_construct()

        elif construct and type(construct) != dict:
            construct, tmpobject = new_construct(), construct
            do_somoething(tmpobject.styleSheet(), construct)

        current = widget.styleSheet().replace(" ", "")
        do_somoething(current, construct) # extract current stylesheet first

        if name: # then extract stylesheet from config
            rv = tech.config(name)
            do_somoething(rv, construct)

        # lastly apply arguments above any previous
        if tooltip:
            target = 'tooltip'
        else:
            target = 'base'

        for k,v in {'background-color:': background, 'color:': color, 'font:': font}.items():
            if v: construct[target][k] = str(v)

        for dictionary in [construct['base'], construct['tooltip']]: # fixes forgotten PT-string in font
            if dictionary['font:'] and 'pt' not in dictionary['font:'].lower():
                dictionary['font:'] += 'pt'

        base = [k+v for k,v in construct['base'].items() if v]
        ttmp = [k+v for k,v in construct['tooltip'].items() if v]

        if ttmp or base:
            string = ""
            if base:
                string += widget.metaObject().className() + '{' + ";".join(base) + '}'
            if ttmp:
                string += 'QToolTip{' + ";".join(ttmp) + '}'
            if curious:
                return construct
            else:
                if widget.styleSheet() != string:  # huge performance boost by checking before applying
                    widget.setStyleSheet(string)
            return string

    @staticmethod
    def fontsize(widget):
        construct = tech.style(widget, curious=True)
        font = construct['base']['font:'] or construct['tooltip']['font:']
        if font:
            tmp = [x for x in font if x.isdigit()]
            tmp = "".join(tmp)
            if tmp:
                return int(tmp)

    def thread(self, *args, **kwargs):
        if 'threadpools' not in self.techdict:
            self.techdict['threadpools'] = {}

        if 'name' not in kwargs:
            name = 'default_threadpool'
        else:
            name = kwargs['name']

        if name not in self.techdict['threadpools']:
            self.techdict['threadpools'][name] = CustomThreadPool(**kwargs)

        self.techdict['threadpools'][name](*args, **kwargs)

    def start_thread(self, *args, **kwargs):  # backwards compatible
        self.thread(*args, **kwargs)

    @staticmethod
    def shrink_label_to_text(label, x_margin=2, y_margin=2, no_change=False, width=True, height=False):
        label.show()

        if height:
            rvsize = label.fontMetrics().boundingRect(label.text()).height() + y_margin
            if no_change:
                return rvsize
            tech.pos(label, height=rvsize)

        if width:
            rvsize = label.fontMetrics().boundingRect(label.text()).width() + x_margin
            if no_change:
                return rvsize
            tech.pos(label, width=rvsize)

        return rvsize

    @staticmethod
    def download_file(url, file=None, headers={}, reuse=True, days=False, minutes=False):

        def method_one(url, file, headers, gcontext=None, runner=0):
            while not os.path.exists(file.full_path) and runner < 5:
                runner += 1
                if runner == 1:  # first run do this!
                    try:
                        with requests.get(url, stream=True, headers=headers) as r:
                            r.raw.read = partial(r.raw.read, decode_content=True)
                            with open(file.full_path, 'wb') as f:
                                shutil.copyfileobj(r.raw, f)
                    except:
                        time.sleep(random.uniform(1.15, 2))
                else:
                    urlobj = Request(url, headers=headers)
                    try:
                        with urlopen(urlobj, context=gcontext) as response, open(file.full_path, 'wb') as f:
                            shutil.copyfileobj(response, f)
                    except:
                        time.sleep(random.uniform(1.15, 2))

                if os.path.exists(file.full_path):
                    if os.path.getsize(file.full_path) > 0:
                        if tech.dev_mode:
                            tech.printout_downloaded_this_file(url, file.full_path)
                        break
                    else:
                        os.remove(file.full_path)

                headers = tech.header_generator(randominize=True)
                gcontext = ssl.SSLContext()

        if not file:
            file = tech.tmp_file(file_of_interest=url, reuse=reuse, days=days, minutes=minutes)

        headers = tech.header_generator(**headers)

        file = tech.separate_file_from_folder(file)

        method_one(url, file, headers)
        if os.path.exists(file.full_path):
            return file.full_path
        else:
            print('DOWNLOAD ERROR:', url, '->', file.full_path)

    def swapper(self, key, value=None, secondary=False):
        """
        first time the key is seen, it stores the value into primary slot, all other times the value
        is stored into secondary slot. by default it returns the primary value unless asked for secondary
        :param key: dict-key
        :param value: anything
        :param secondary: bool (defaults to primary)
        """
        if not 'storestuff' in self.techdict:
            self.techdict['storestuff'] = {}

        if value:
            if key not in self.techdict['storestuff']:
                self.techdict['storestuff'][key] = dict(primary=copy.copy(value), secondary=None)
            else:
                self.techdict['storestuff'][key]['secondary'] = copy.copy(value)

        if key in self.techdict['storestuff']:
            if secondary:
                return self.techdict['storestuff'][key]['secondary']
            else:
                return self.techdict['storestuff'][key]['primary']

    @staticmethod
    def blob_path_from_blob_object(blob, *args, **kwargs):
        """ :return: string full_path """
        tmpfile = tech.tmp_file(*args, **kwargs)
        loc = tech.separate_file_from_folder(tmpfile)
        if not os.path.exists(tmpfile):
            with open(loc.full_path, 'wb') as output_file:
                output_file.write(blob)
        return loc.full_path

    @staticmethod
    def make_image_into_blob(image_path, width=None, height=None, quality=70, method=6):
        try: image = Image.open(image_path)
        except: return False

        if width and image.size[0] < width:
            height = round(image.size[1] * (width / image.size[0]))
        elif height and image.size[1] < height:
            width = round(image.size[0] * (height / image.size[1]))
        elif height:
            width = image.size[1] * (image.size[0] / image.size[1])
        elif width:
            height = image.size[0] * (image.size[1] / image.size[0])
        else:
            width = image.size[0]
            height = image.size[1]

        image_size = int(width), int(height)
        image.thumbnail(image_size, Image.ANTIALIAS)

        tmp_file = tech.tmp_file(part1='webpcover_', part2='.webp', new=True)
        image.save(tmp_file, 'webp', method=method, quality=quality)

        with open(tmp_file, 'rb') as file:
            blob = file.read()
            os.remove(tmp_file)
            return blob

    @staticmethod
    def md5_hash_string(string=None, random=False, upper=False, under=False):
        if not string or random:
            salt = 'how_much_is_the_fi2H'
            string = f'{uuid.uuid4()}{time.time()}{salt}{string or ""}'

        hash_object = hashlib.md5(string.encode())
        rv = hash_object.hexdigest()

        if upper:
            rv = rv.upper()

        if under:
            rv = '_' + rv

        return rv

    def save_config(self, setting, value=None, theme='default', delete=False, signal=None):
        self.signal.save_config.emit((setting, value, theme, delete, signal,))

    def _save_config(self, signal_tuple):
        setting, value, theme, delete, signal = signal_tuple

        if not setting or type(setting) == str and setting[0] == '_':
            return  # we dont do __dunder__

        if not 'config' in self.techdict:
            blob = sqlite.execute('select * from settings where id is 1')
            if blob and blob[1]:
                self.techdict['config'] = pickle.loads(blob[1])
            else:
                self.techdict['config'] = {}

        if not theme in self.techdict['config']:
            self.techdict['config'][theme] = {}

        if setting in self.techdict['config'][theme]:
            thing = self.techdict['config'][theme][setting]
        else:
            thing = {'activated': True, 'value': None}
            self.techdict['config'][theme][setting] = thing

        if type(value) == bool:
            thing['activated'] = value
        else:
            thing['value'] = value

        if delete:
            self.techdict['config'][theme].pop(setting)

        if setting != 'dummy':
            data = pickle.dumps(self.techdict['config'])
            sqlite.execute('update settings set config = (?) where id is 1', values=data)

        if signal:
            signal.finished.emit()

    def config(self, setting, theme='default', curious=False, raw=False):


        for container in [self.techdict['config'], default_dict]:
            if theme in container:
                if setting in container[theme]:
                    thing = container[theme][setting]

                    if raw:
                        return thing

                    elif thing['activated'] or curious:

                        if thing['value'] == None:
                            return thing['activated']
                        else:
                            return thing['value']


    @staticmethod
    def zero_prefiller(value, lenght=5):
        string = str(value)
        string = ('0' * (lenght - len(string))) + string
        return string


    @staticmethod
    def signal_highlight(name='_global', message='_'):
        signal = tech.signals(name)
        signal.highlight.emit(message)

    def signals(self, name=None, reset=False, delete_afterwards=False, delete=False):
        if 'signals' not in self.techdict:
            self.techdict.update(dict(signals={ }))

        if name == None:
            name = 0
            while name in self.techdict['signals']:
                name += 1

        if name not in self.techdict['signals']:
            newsignal = WorkerSignals()
            newsignal.name = name
            self.techdict['signals'][name] = [newsignal]

        elif name in self.techdict['signals'] and reset or delete or delete_afterwards:
            newsignal = WorkerSignals()
            newsignal.name = name
            self.techdict['signals'][name].append(newsignal)
            if delete_afterwards:
                return self.techdict['signals'][name][-2]

        return self.techdict['signals'][name][-1]

    @staticmethod
    def google_session(url, printout=True):
        session = tech.swapper('google_session')

        if session:
            response = session.get(url)
            if printout:
                tech.printout_downloaded_this_file(url)
            return response

        session = requests.Session()
        session.headers = tech.header_generator(operatingsystem='windows')

        if tech.config('google_session'):
            blob = tech.config('google_session')
            blob = pickle.loads(blob)
            cj = requests.cookies.RequestsCookieJar()
            cj._cookies = blob
            session.cookies = cj
            response = session.get(url)
            tech.swapper('google_session', value=session)
            return response

        elif not 'google.com/search?q=' in url:
            tech.google_session('https://www.google.com/search?q=sp500')
            response = tech.google_session(url)
            return response

        response = session.get(url)

        if not response:
            print("GOOGLE SESSION FAILED!")
        else:
            data = {}

            co = tech.Cutouter(response.content.decode(), first_find='action="https://consent.google.com/s"')

            while co:
                co(find_first='input type="hidden" name="', then_find='"', forward=True, plow=True)
                if co and co.text not in data:
                    data[co.text] = None

                if co.back_focus > co.org_contents.find('<input type="submit" value="'):
                    break

            for key, value in data.items():
                co = tech.Cutouter(response.content.decode(), find_first=f'input type="hidden" name="{key}" value="', then_find='"', forward=True)
                if co:
                    data[key] = co.text

                if co.back_focus > co.org_contents.find('<input type="submit" value="'):
                    break

            if 'v' in data and data['v'] and 't' in data and data['t']:
                cookie_obj = requests.cookies.create_cookie(domain='.google.com', name=data['v'], value=data['t'])
                session.cookies.set_cookie(cookie_obj)
                response = session.post('https://consent.google.com/s', data=data)

                print("SAVING COOKIES, this shouldnt happen more than once a year!")
                blob = pickle.dumps(session.cookies._cookies)
                tech.save_config('google_session', blob)
                tech.swapper('google_session', value=session)
                return response

    @staticmethod
    def header_generator(operatingsystem='windows', randominize=False):
        agents = [
            dict(agent='Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0', os='linux'),
            dict(agent='Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0', os='windows'),
            dict(agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:10.0) Gecko/20100101 Firefox/10.0', os='mac'),
            dict(agent='Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0', os='android'),
            dict(agent='Mozilla/5.0 (Android 4.4; Tablet; rv:41.0) Gecko/41.0 Firefox/41.0', os='tablet'),
            dict(agent='Mozilla/5.0 (iPhone; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 \
            (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4', os='iphone'),
            dict(agent='Mozilla/5.0 (iPad; CPU iPhone OS 8_3 like Mac OS X) AppleWebKit/600.1.4 \
            (KHTML, like Gecko) FxiOS/1.0 Mobile/12F69 Safari/600.1.4', os='ipad'),
        ]
        if randominize:
            random.shuffle(agents)
        else:
            agents = [x for x in agents if x['os'] == operatingsystem] or agents

        return {'User-Agent' : agents[0]['agent']}

    class ChangeColor(QtWidgets.QLabel):
        def __init__(self, main, parent, type):
            super().__init__(main)
            self.setWindowTitle('Change colors')
            self.main = main
            self.parent = parent
            self.type = type
            self.old_position = False
            self.show()

            self.init_dual_widgets()

        def changing_color(self):
            self.text_color = QColor.getRgb(self.foreground.currentColor())
            self.background_color = QColor.getRgb(self.background.currentColor())

            rgb = ""
            rgba = ""

            for i,j in {"background-color":self.background_color, "color": self.text_color}.items():
                rgb += f"{i}: rgb{j[0:-1]} ; "
                rgba +=  f"{i}: rgba{j} ; "

            a = (b'#' + b16encode(bytes(self.background_color)))
            a_hex = str(a)[2:-3]

            b = (b'#' + b16encode(bytes(self.text_color)))
            b_hex = str(b)[2:-3]

            self.parent._styles = dict(
                                            RGB=rgb.rstrip('; '),
                                            RGBA=rgba.rstrip('; '),
                                            AHEX=a_hex,
                                            BHEX=b_hex,
            )
            self.parent.setStyleSheet(self.parent._styles['RGBA'])

        def init_dual_widgets(self):
            self.main._color_widget = self

            self.background = QtWidgets.QColorDialog(self)
            self.background.setWindowFlags(QtCore.Qt.SubWindow)
            self.background.setOption(4 | 2 | 1)
            self.background.setCurrentColor(QColor(255, 255, 255, 255))
            self.background.currentColorChanged.connect(partial(self.changing_color))
            self.background.setStyleSheet('background-color: rgb(40,40,40) ; color: white')
            self.background.show()

            self.foreground = QtWidgets.QColorDialog(self)
            self.foreground.setWindowFlags(QtCore.Qt.SubWindow)
            self.foreground.setOption(4 | 2 | 1)
            self.foreground.setCurrentColor(QColor(255, 255, 255, 255))
            self.foreground.currentColorChanged.connect(partial(self.changing_color))
            self.foreground.setStyleSheet('background-color: rgb(140,140,140) ; color: white')
            self.foreground.show()

            lh = 36

            self.background.setGeometry(0,lh,self.background.width(), self.background.height() + lh)
            self.foreground.setGeometry(self.background.width(),lh,self.foreground.width(),self.foreground.height()+lh)

            self.label_bg = QtWidgets.QLabel(self, text='BACKGROUND COLOR')
            self.label_bg.setAlignment(QtCore.Qt.AlignVCenter)
            self.label_bg.setGeometry(0,0,self.background.width(), lh)
            self.label_bg.setStyleSheet('background-color: rgb(40,40,40) ; color: white ; font: 18pt')
            self.label_bg.show()

            self.label_fo = QtWidgets.QLabel(self, text='TEXT/THING COLOR')
            self.label_fo.setAlignment(QtCore.Qt.AlignVCenter)
            self.label_fo.setGeometry(self.background.width(),0,self.background.width(), lh)
            self.label_fo.setStyleSheet('background-color: rgb(140,140,140) ; color: white ; font: 18pt')
            self.label_fo.show()

            self.setFixedSize(self.foreground.width() * 2, self.foreground.height() + lh)

        def drag_widget(self, ev):
            if not self.old_position:
                self.old_position = ev.globalPos()

            delta = QtCore.QPoint(ev.globalPos() - self.old_position)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_position = ev.globalPos()

        def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.drag_widget(ev)

        def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
            self.raise_()
            self.old_position = ev.globalPos()

            if ev.button() == 2:
                if '_styles' in dir(self.parent):
                    tech.style(save=True, widget=self.parent)
                    tech.save_config(self.type, self.parent._styles['RGB'], stylesheet=True)

                self.close()

    @staticmethod
    def flagfile(country):
        swap = {
            'Hong Kong': 'China',
            'Palestinian Territory': 'Palestine',
            'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
            "Cote D'Ivoire": 'Ivory Coast',
            }

        if country in swap:
            country = swap[country]

        loc = tech.separate_file_from_folder(f"{os.environ['INI_FILE_DIR']}flagimages/{country}.webp")
        if os.path.exists(loc.full_path):
            return loc.full_path
        else:
            print(f"Couln't find flagfile: {country}.webp")

    @staticmethod
    def tmp_folder(
            folder_of_interest=None,
            reuse=False,
            delete=False,
            hash=False,
            create_dir=True,
            return_base=False,
        ):
        """
        generates a temporary folder for user
        i prefer to keep my trash inside /mnt/ramdisk
        if conflict, 0,1,2,3 + _ can be added to the END of the file
        :param folder_of_interest: string or none
        :param reuse: bool -> doesnt delete folder if its present, uses cache
        :param delete: bool -> will rmtree the folder before treating
        :param hash: bool -> md5 hashing folder_or_interest for clean dirs
        :return: full path (string)
        """
        if not folder_of_interest:
            md5 = tech.md5_hash_string() # uuid + random + hash
            folder_of_interest = md5.upper()

        elif folder_of_interest and hash:
            md5 = tech.md5_hash_string(folder_of_interest)
            folder_of_interest = md5.upper()

        if os.path.exists(os.environ['TMP_DIR']):
            base_dir = os.environ['TMP_DIR']
        else:
            base_dir = tempfile.gettempdir()

        complete_dir = base_dir + '/' + os.environ['PROGRAM_NAME'] + '/' + folder_of_interest
        complete_dir = os.path.abspath(os.path.expanduser(complete_dir))

        if os.path.exists(complete_dir) and not reuse:
            try:
                if delete:
                    shutil.rmtree(complete_dir)
            except PermissionError:
                pass
            except NotADirectoryError:
                pass
            finally:
                counter = 0
                while os.path.exists(complete_dir):
                    counter += 1
                    tmp = complete_dir + '_' + str(counter)
                    if not os.path.exists(tmp):
                        complete_dir = tmp

        if not os.path.exists(complete_dir) and create_dir:
            pathlib.Path(complete_dir).mkdir(parents=True)

        if return_base:
            return base_dir
        else:
            return complete_dir

    @staticmethod
    def tmp_file(
            file_of_interest=None,
            hash=True,
            reuse=False,
            days=False,
            minutes=False,
            delete=False,
            new=False,
            extension=None,
            tmp_folder=None,
            part1=None, part2=None
        ):
        """
        :param file_of_interest: string can be anything fuck_a_duck.txt
        :param reuse, doesnt delete file if its present, uses cache
        :param days int, file is no more than x days to reuse
        :param part1, part2 becomes part1_0004_part2.webp with new=True
        :param new, keeps old files and puts a counter on/in new filename
        :param if extension, its added AFTER hashing
        :return: full path (string)
        """
        if not tmp_folder:
            tmp_folder = tech.tmp_folder(folder_of_interest='tmp_files', reuse=True)

        if part1 and part2:
            if file_of_interest:
                file_of_interest += part1 + part2
            else:
                file_of_interest = part1 + part2

        if not file_of_interest:
            md5 = tech.md5_hash_string() # uuid + random + hash
            file_of_interest = md5.upper()

        if hash:
            file_of_interest = tech.md5_hash_string(file_of_interest)

        if extension and extension[0] != '.':
            extension = '.' + extension

        if extension:
            file_of_interest += extension

        complete_path = tmp_folder + '/' + file_of_interest
        complete_path = os.path.abspath(os.path.expanduser(complete_path))

        def delete_file_checker(complete_path):
            if os.path.exists(complete_path):
                if days and os.path.getmtime(complete_path) < time.time() - (days * 86400):
                    os.remove(complete_path)
                    return

                if minutes and os.path.getmtime(complete_path) < time.time() - (minutes * 60):
                    os.remove(complete_path)
                    return

                if delete:
                    os.remove(complete_path)
                    return

        delete_file_checker(complete_path)  # deletes first

        if reuse:
            return complete_path

        if os.path.exists(complete_path):
            if os.path.isfile(complete_path):
                try:
                    if not new:
                        os.remove(complete_path)
                except PermissionError:
                    pass
                except IsADirectoryError:
                    pass
                finally:

                    def zero_prefiller(value, lenght=4):
                        string = str(value)
                        string = ('0' * (lenght - len(string))) + string
                        return string

                    counter = 0
                    while os.path.exists(complete_path):
                        counter += 1
                        if part1 and part2:
                            _tmp_path = tmp_folder + '/' + part1 + zero_prefiller(counter) + part2
                            _tmp_path = os.path.abspath(os.path.expanduser(_tmp_path))
                        else:
                            _tmp_path = complete_path + '_' + zero_prefiller(counter)

                        if extension:
                            _tmp_path += extension

                        if not os.path.exists(_tmp_path):
                            complete_path = _tmp_path

        return complete_path

    class Cutouter:
        def __init__(self, contents, *args, **kwargs):
            self.org_contents = contents
            self.cache = None
            self.reset()
            self(*args, **kwargs)

        def __call__(self,

                        first_find=None,
                        find_first=None,
                        then_find=False,
                        start_from=False,
                        search_range=False,
                        preshrink=False,
                        plow=False,
                        rewind=0,
                        forward=0,
                        *args,
                        **kwargs,

                        ):

            self.plow_mode(plow)

            if find_first or first_find:
                self.set_starting_point(start_from)
                self.set_ending_point(search_range, preshrink)
                self.find_first_target(find_first or first_find, rewind, forward, search_range)

            if then_find:
                self.find_second_target(then_find)

        def __bool__(self):
            return self.status

        def __str__(self):
            if self.status:
                return self.text

        def reset(self):
            self.status, self.focus, self.back_focus = False, 0, -1

        def plow_mode(self, plow):
            """ will discard previous tracks as machine only plow forward, never backwards """
            if self.status and plow and max(self.focus, self.back_focus) > 0:
                self.org_contents = self.org_contents[max(self.focus, self.back_focus):]
                self.reset()

        def set_starting_point(self, start_from):
            """ set cache beginning, starting point will be fixed from here on """
            if start_from and len(self.org_contents) > start_from:
                self.cache = self.org_contents[start_from:]
            else:
                self.cache = self.org_contents

        def set_ending_point(self, search_range, preshrink=False):
            """ this only happens if first target has been discovered unless foreced """
            if search_range and len(self.cache) > search_range:
                if preshrink or self.focus > -1:

                    if self.focus > -1:
                        self.cache = self.cache[self.focus:]
                        self.focus = 0

                    if len(self.cache) > search_range:
                        self.cache = self.cache[0:search_range]

        def find_first_target(self, find_first, rewind=0, forward=0, search_range=False):
            if type(find_first) == str:
                find_first = [find_first]

            for query in find_first or []:

                self.status = False
                self.focus = self.cache[self.focus:].find(query) + self.focus

                if self.focus > -1:

                    if type(rewind) == str:
                        self.focus += (0 - len(rewind))
                    elif type(rewind) == bool and rewind:
                        self.focus += (0 - len(query))

                    if type(forward) == str:
                        self.focus += len(forward)
                    elif type(forward) == bool and forward:
                        self.focus += len(query)

                    self.set_ending_point(search_range)

                    self.text = self.cache[self.focus:]
                    self.status = True
                else:
                    return False

        def find_second_target(self, then_find):
            """then_find usually a string, but if its a list
            or tuple its a combined/additional first_find """
            if then_find and self.focus > -1:

                if type(then_find) == str:
                    then_find = [then_find]

                for count, query in enumerate(then_find or []):
                    self.status = False

                    if count+1 < len(then_find):
                        self.find_first_target(query)  # backwards compatible
                        if not self.status:
                            return False
                    else:
                        self.back_focus = self.cache[self.focus:].find(query) + self.focus

                        if self.back_focus > self.focus:
                            self.text = self.cache[self.focus:self.back_focus]
                            self.status = True
                        else:
                            return False

tech = ViktorinoxTechClass()

class WorkerSignals(QObject):
    highlight = pyqtSignal(str)
    activated = pyqtSignal()
    deactivated = pyqtSignal()
    finished = pyqtSignal()
    killswitch = pyqtSignal()
    leadsignal = pyqtSignal(str)
    progress = pyqtSignal(dict)
    error = pyqtSignal(dict)
    result = pyqtSignal(object)
    dictdelivery = pyqtSignal(dict)
    listdelivery = pyqtSignal(list)
    stringdelivery = pyqtSignal(str)