#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Relations tab.

"""
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext
from gi.repository import Gtk
import time
from gramps.gui.listmodel import ListModel, INTEGER
from gramps.gui.managedwindow import ManagedWindow
from gramps.gui.utils import ProgressMeter

from gramps.gui.plug import tool
from gen.display.name import displayer as name_displayer
from gramps.gen.relationship import get_relationship_calculator
from gramps.gen.config import config
import number

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class RelationTab(tool.Tool, ManagedWindow):

    def __init__(self, dbstate, user, options_class, name, callback=None):
        uistate = user.uistate
        self.label = _("Relation and distances with root")
        tool.Tool.__init__(self, dbstate, options_class, name)
        if uistate:
            ManagedWindow.__init__(self,uistate,[],
                                                 self.__class__)
            titles = [
                (_('Rel_id'), 0, 75, INTEGER), # would be INTEGER
                (_('Relation'), 1, 300),
                (_('Name'), 2, 200),
                (_('up'), 3, 35, INTEGER),
                (_('down'), 4, 35, INTEGER),
                (_('Common MRA'), 5, 75, INTEGER),
                (_('Rank'), 6, 75, INTEGER),
                ]

            treeview = Gtk.TreeView()
            model = ListModel(treeview, titles)
            window = Gtk.Window()
            window.set_default_size(880, 600)
            s = Gtk.ScrolledWindow()
            s.add(treeview)
            window.add(s)

        stats_list = []
        max_level = config.get('behavior.generation-depth')

        default_person = dbstate.db.get_default_person()

        if default_person:
            plist = dbstate.db.get_person_handles(sort_handles=True)
            relationship = get_relationship_calculator()
            progress = ProgressMeter(self.label, can_cancel=True,
                                 parent=window)
            count = 0
            length = len(plist)
            progress.set_pass(_('Generating relation map...'), length)
            step_one = time.clock()
            for handle in plist:
                if progress.get_cancelled():
                    progress.close()
                    return
                count += 1
                progress.step()
                step_two = time.clock()
                wait = ((step_two - step_one)/count) * length
                #if count > 99:
                    #progress.set_message(_("%s/%s. Estimated time: %s seconds") % (count, length, wait))
                person = dbstate.db.get_person_from_handle(handle)
                timeout_one = time.clock()
                dist = relationship.get_relationship_distance_new(
                          dbstate.db, default_person, person, only_birth=True)
                timeout_two = time.clock()
                limit = timeout_two - timeout_one
                if limit > 0.035:
                    #progress.set_message("Sorry! '%s' needs %s second" % (handle, limit))
                    continue
                rel = relationship.get_one_relationship(
                                            dbstate.db, default_person, person)
                rank = dist[0][0]
                if rank == -1: # not related people
                    continue
                rel_a = dist[0][2]
                Ga = len(rel_a)
                rel_b = dist[0][4]
                Gb = len(rel_b)
                mra = 1

                for letter in rel_a:
                    if letter == 'f':
                        mra = mra * 2
                    if letter == 'm':
                        mra = mra * 2 + 1

                name = name_displayer.display(person)
                kekule = number.get_number(Ga, Gb, rel_a, rel_b)

                # work-around
                if kekule == "u": # cousin(e)s need a key
                   kekule = 0
                if kekule == "nb": # non-birth
                   kekule = -1
                try:
                   test = int(kekule)
                except: # 1: related to mother; 0.x : no more girls lineage
                   kekule = 1

                stats_list.append((int(kekule), rel, name, int(Ga),
                                    int(Gb), int(mra), int(rank)))
            progress.close()

        for entry in stats_list:
            model.add(entry, entry[0])
        window.show_all()
        self.set_window(window, None, self.label)
        self.show()

    def build_menu_names(self, obj):
        return (self.label,None)

#------------------------------------------------------------------------
#
#
#
#------------------------------------------------------------------------
class RelationTabOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)