#!/usr/bin/env python3

from gi.repository import Gtk  # , Gdk, GLib
import hashlib
import json
import os
import sqlite3
import sys
import yaml
from zipfile import ZipFile

HOME = os.path.expanduser('~')
CONFIG_DIRECTORY = HOME + '/.config/gcemanager/'
ROM_DATABASE = HOME + '/.local/share/gcemanager/data/rom.json'


class GUI:

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('ui/main.glade')
        self.about = About()
        self.preferences = Preferences()
        self.window = self.builder.get_object('window_gce')
        self.builder.connect_signals(self)
        self.window.show_all()
        self.rom_database = RomDatabase()
        self.database = Database()

    def show_preferences(self, widget):
        self.preferences.show()

    def show_about(self, widget):
        self.about.show()

    @staticmethod
    def destroy(widget):
        Gtk.main_quit()

    def import_directory(self, directory):
        hasher = hashlib.md5()
        for local_file in os.listdir(directory):
            rom = None
            if local_file[-4:] == '.zip':
                z = ZipFile(os.path.join(directory, local_file))
                for compressed_file in z.namelist():
                    if compressed_file[-4:] == '.nes':
                        hasher.update(z.open(compressed_file, 'r').read())
                        rom = self.rom_database.get_rom_by_hash(hasher.hexdigest())
            elif local_file[-4:] == '.nes':
                with open(os.path.join(directory, local_file), 'rb') as afile:
                    hasher.update(afile.read())
                rom = self.rom_database.get_rom_by_hash(hasher.hexdigest())
            if rom is not None:
                self.database.import_rom(rom)
        self.database.database.commit()


class Preferences:
    library_location = os.path.join(HOME, "roms")
    directory_layout = '{system}/{object}/{name}.{type}'

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('ui/preferences.glade')
        self.window = self.builder.get_object('window_preferences')
        self.configuration_file = os.path.join(CONFIG_DIRECTORY, 'gcemanager.yml')
        self.parse_config()
        self.initialize_interface()
        self.builder.connect_signals(self)

    def show(self):
        self.window.show_all()

    def hide(self):
        self.window.hide()

    def on_delete(self, window, event):
        self.hide()
        return True

    def initialize_interface(self):
        self.builder.get_object('entry_library_location').set_text(self.library_location)

    def parse_config(self):
        # Create the file if it doesn't already exist and accept defaults.
        if not os.path.isfile(self.configuration_file):
            return self.save()
        # Load the file contents
        with open(self.configuration_file, 'r+') as file:
            preferences = yaml.load(file)
        # Set preferences to self.
        for key in preferences:
            setattr(self, key, preferences[key])

    def save(self):
        with open(self.configuration_file, 'w') as file:
            yaml.dump(
                {
                    'library_location': self.library_location,
                    'directory_layout': self.directory_layout
                },
                file
            )

    def on_button_cancel_clicked(self, widget):
        self.hide()
        self.initialize_interface()

    def on_button_apply_clicked(self, widget):
        self.library_location = self.builder.get_object('entry_library_location').get_text()
        self.save()

    def on_button_ok_clicked(self, widget):
        self.on_button_apply_clicked(widget)
        self.hide()


class About:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('ui/about.glade')
        self.window = self.builder.get_object('aboutdialog_gce')

    def show(self):
        self.window.show_all()

    def hide(self):
        self.window.hide()

    def destroy(self, widget):
        self.hide()


class Game:
    name = None
    system = None
    year = None
    genre = None
    language = None
    hash_key = None

    def __init__(self, name, system, year, genre, language, hash_key):
        self.name = name
        self.system = system
        self.year = year
        self.genre = genre
        self.language = language
        self.hash_key = hash_key


class RomDatabase:
    def __init__(self):
        with open(ROM_DATABASE) as file:
            self.database = json.load(file)

    def get_rom_by_hash(self, hash_key):
        for rom in self.database:
            if rom['hash'] == hash_key:
                return rom


class Database:
    def __init__(self):
        self.inserts = 0
        self.updates = 0
        self.database = sqlite3.connect(os.path.join(CONFIG_DIRECTORY, 'gce.db'))
        if not self._is_initialized():
            self._initialize()

    def __del__(self):
        self.database.close()

    def _initialize(self):
        cursor = self.database.cursor()
        cursor.execute('''
create table
  rom (
    name text,
    system text,
    year integer,
    genre text,
    language text,
    hash text
  )
        ''')

    def _is_initialized(self):
        return self._has_table('rom')

    def _has_table(self, table):
        cursor = self.database.cursor()
        cursor.execute('select count(*) from sqlite_master where type=\'table\' and name=\'%s\'' % table)
        return cursor.fetchone()[0] == 1

    def _check_by_hash(self, hash_key):
        cursor = self.database.cursor()
        cursor.execute('select count(*) from rom where hash=\'%s\'' % hash_key)
        return cursor.fetchone()[0] == 1

    def import_rom(self, rom):
        if self._check_by_hash(rom['hash']):
            self._update_rom(rom)
        else:
            self._insert_rom(rom)

    def _update_rom(self, rom):
        cursor = self.database.cursor()
        cursor.execute('''
update
  rom
set
  name = ?,
  system = ?,
  year = ?,
  genre = ?,
  language = ?
where
  hash = ?
        ''', (rom['name'], rom['system'], rom['year'], rom['genre'], rom['language'], rom['hash']))
        self.updates += 1

    def _insert_rom(self, rom):
        cursor = self.database.cursor()
        cursor.execute('''
insert into
  rom (
    name,
    system,
    year,
    genre,
    language,
    hash
  ) values (
    ?,
    ?,
    ?,
    ?,
    ?,
    ?
  )
        ''', (rom['name'], rom['system'], rom['year'], rom['genre'], rom['language'], rom['hash']))
        self.inserts += 1


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "listroms":
            g = GUI()
            g.import_directory(sys.argv[2])
            sys.exit(0)
    if not os.path.isdir(CONFIG_DIRECTORY):
        os.mkdir(CONFIG_DIRECTORY)
    GUI()
    Gtk.main()

    return 0

if __name__ == "__main__":
    sys.exit(main())
