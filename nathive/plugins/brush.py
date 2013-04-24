#!/usr/bin/env python
#coding=utf-8

# Nathive (and this file) is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or newer.
#
# You should have received a copy of the GNU General Public License along with
# this file. If not, see <http://www.gnu.org/licenses/>.


import gtk

from nathive.lib.plugin import *
from nathive.lib.layer import Layer
from nathive.libc import brush
from nathive.gui import utils as gutils
from nathive.gui.multiwidget import *


class Brush(PluginTool):

    def __init__(self):

        # Subclass it.
        PluginTool.__init__(self)

        # Plugin attributes.
        self.name = 'brush'
        self.author = 'nathive-dev'
        self.icon = 'tool-brush.png'

        # Setting up the plugin.
        self.brush = None
        self.layer = None
        self.default()
        main.config.push_to_plugin(self)

        # Init apply limits (left, top, right, bottom).
        self.apply = [0, 0, 0, 0]

        # Able simple overriding for subclassed plugins like eraser.
        self.composite_mode = 1
        self.color_updated_todo = main.color.updated_todo


    def enable(self):

        self.color_updated_todo.append(self.new_color)
        self.new()


    def disable(self):

        self.color_updated_todo.remove(self.new_color)
        hud = main.documents.active.canvas.hud
        hud.remove_cursor()


    def default(self):

        self.shape = 1
        self.size = 100
        self.opacity = 100
        self.soft = 100
        self.spacing = 0


    def update(self):

        self.gui_shape.set_value(self.shape)
        self.gui_size.set_value(self.size)
        self.gui_opacity.set_value(self.opacity)
        self.gui_soft.set_value(self.soft)
        self.gui_spacing.set_value(self.spacing)
        self.new()


    @property
    def color(self):
        """Redirect self.color to global color value to able
        simple overriding in subclassed plugins like eraser."""

        return main.color.rgb


    def set_then_new(self, variable, value):

        setattr(self, variable, value)
        self.new()


    def new(self):

        del(self.brush)
        self.brush = Layer('brush', None, self.size, self.size)

        brush.new(
            self.brush.pointer,
            True,
            self.shape,
            self.size,
            self.opacity,
            self.soft,
            self.color[0],
            self.color[1],
            self.color[2])

        if not main.documents.active: return
        hud = main.documents.active.canvas.hud
        fixed_size = self.size - ((self.size * (self.soft/2) / 100) / 2)
        if self.shape == 0: hud.set_cursor('square', fixed_size)
        elif self.shape == 1: hud.set_cursor('circle', fixed_size)


    def new_color(self):
        """Change brush color with no opacity re-calculation for better
        performance at color change."""

        brush.new(
            self.brush.pointer,
            False,
            0,
            self.size,
            0,
            0,
            self.color[0],
            self.color[1],
            self.color[2])


    def button_primary(self, x, y, ux, uy):

        main.documents.active.actions.begin('layer-content')
        self.layer = main.documents.active.layers.active
        self.motion_primary(x, y, ux, uy)


    def motion_primary(self, x, y, ux, uy):

        # Update apply limits.
        if not self.apply[0] or x < self.apply[0]: self.apply[0] = x
        if not self.apply[1] or y < self.apply[1]: self.apply[1] = y
        if not self.apply[2] or x > self.apply[2]: self.apply[2] = x
        if not self.apply[3] or y > self.apply[3]: self.apply[3] = y

        # Set apply coordinates.
        x = x - (self.size / 2)
        y = y - (self.size / 2)

        # Brush.
        self.brush.composite(
            self.composite_mode,
            self.layer,
            x - self.layer.xpos,
            y - self.layer.ypos,
            x - self.layer.xpos,
            y - self.layer.ypos,
            self.brush.width,
            self.brush.height)

        # Redraw expired area.
        main.documents.active.canvas.redraw(
            x,
            y,
            self.size,
            self.size,
            True,
            True)


    def release_primary(self):

        # Calc apply area rectangle.
        area = [
            self.apply[0] - (self.brush.width/2),
            self.apply[1] - (self.brush.height/2),
            self.apply[2] + (self.brush.width) - self.apply[0],
            self.apply[3] + (self.brush.height) - self.apply[1]]

        # Apply layer offset.
        layer = main.documents.active.layers.active
        area[0] -= layer.xpos
        area[1] -= layer.ypos

        # End action and reset area vars.
        main.documents.active.actions.end(area)
        self.apply = [0, 0, 0, 0]


    def button_secondary(self, x, y, ux, uy):

        self.resizing_root = [x, y]


    def motion_secondary(self, x, y, ux, uy):

        root_x, root_y = self.resizing_root
        rel_x = root_x - x
        rel_y = root_y - y
        self.size += rel_y - rel_x
        self.resizing_root = [x, y]
        if self.size < 1: self.size = 1
        if self.size > 100: self.size = 100
        if gtk.events_pending(): return
        hud = main.documents.active.canvas.hud
        hud.create_cursor()
        hud.move_cursor(x, y)
        hud.dump_cursor()
        self.gui_size.set_value(self.size, True)


    def gui(self):

        self.box = gtk.VBox(False, 0)

        self.gui_shape = MultiWidgetToggle(
            self.box,
            _('Shape'),
            ['square', 'circle'],
            self.shape,
            lambda x: self.set_then_new('shape', x))

        gutils.separator(self.box)

        self.gui_size = MultiWidgetSpin(
            self.box,
            _('Size'),
            True,
            1,
            100,
            self.size,
            lambda x: self.set_then_new('size', int(x)))

        self.gui_soft = MultiWidgetSpin(
            self.box,
            _('Smoothing'),
            True,
            0,
            100,
            self.soft,
            lambda x: self.set_then_new('soft', int(x)))

        self.gui_opacity = MultiWidgetSpin(
            self.box,
            _('Opacity'),
            True,
            1,
            100,
            self.opacity,
            lambda x: self.set_then_new('opacity', int(x)))

        gutils.separator(self.box)

        self.gui_spacing = MultiWidgetCombo(
            self.box,
            _('Spacing'),
            ['not ported'],
            self.spacing,
            lambda x: None)

        return self.box
