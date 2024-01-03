"""
The demonstration how to use sqlalchemy ORM.
Tutorial: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-orm
"""

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from swiftbots.types import IChatView
from swiftbots.controllers import Controller

from examples.notes_in_database.models.notes import Note


engine = create_async_engine("sqlite+aiosqlite:///examples/notes_in_database/database/notes.sqlite3")
# TODO: await engine.dispose()


class Notes(Controller):

    compiled_note_pattern = re.compile(rf'^(\S+)\s+(\S+.*)$', re.IGNORECASE | re.DOTALL)

    async def create(self, view: IChatView, context: IChatView.Context):
        message = context.arguments

        match = self.compiled_note_pattern.match(message)

        if not match:
            await view.reply_async("There are no name or text of new note. "
                                   "Use the command like '+note note_name text_of_note'", context)
            return

        name = match.group(1)
        text = match.group(2)

        async_session = async_sessionmaker(engine, expire_on_commit=False)

        async with async_session() as session:
            result = await session.scalars(select(Note)
                                           .where(Note.name.is_(name))
                                           .limit(1))
            note = result.one_or_none()

            # Note already exists
            if note is not None:
                await view.reply_async(f"Note '{name}' already exists. And it's overwritten. "
                                       f"Its previous text is:\n{note.text}", context)
                note.text = text

            # Note doesn't exist
            else:
                session.add(Note(name=name, text=text))

            await session.commit()
            await view.reply_async("Notes updated", context)

    async def read(self, view: IChatView, context: IChatView.Context):
        pass

    async def update(self, view: IChatView, context: IChatView.Context):
        pass

    async def delete(self, view: IChatView, context: IChatView.Context):
        pass

    async def list_notes(self, view: IChatView, context: IChatView.Context):
        pass

    cmds = {
        '+note': create,
        'note': read,
        '++note': update,
        '-note': delete,
        'notes': list_notes,
    }


"""
import json, re
from superplugin import SuperPlugin, admin_only, superadmin_only
class Notes(SuperPlugin):
    def __init__(self, bot):
        super().__init__(bot)

    @superadmin_only
    def show_notes(self):
        file = open('./../resources/notes.json', 'r', encoding='utf-8')
        data = json.load(file)
        file.close()
        notes =''
        for note in list(data.keys()):
            notes += note + '\n'
        if notes=='':
            self.sender.send(self.user_id, "There's no notes")
            return
        self.sender.send(self.user_id, notes)

    @superadmin_only
    def add_note(self):
        file = open('./../resources/notes.json', 'r', encoding='utf-8')
        data = json.load(file)
        file.close()
        msg = self.message
        if msg == '':
            self.sender.send(self.user_id, "there's empty note. Nor name neither text")
            return
        name = re.split(' |\n', msg)[0]
        if len(msg) <= len(name)+1:
            self.sender.send(self.user_id, "there's only name of note")
            return
        text = msg[len(name)+1:]
        
        data.update({name : text})
        file = open('./../resources/notes.json', 'w', encoding='utf-8')
        file.write(json.dumps(data))
        file.close()
        self.sender.send(self.user_id, 'notes updated')

    @superadmin_only
    def read_note(self):
        file = open('./../resources/notes.json', 'r', encoding='utf-8')
        data = json.load(file)
        file.close()
        msg = self.message
        if msg == '':
            self.sender.send(self.user_id, "there's no note's name")
            return
        name = re.split(' |\n', msg)
        if len(name) > 1:
            self.sender.send(self.user_id, "What's the trash you wrote except name ?? ")
            return
        name = name[0]
        if name not in data:
            self.sender.send(self.user_id, "There's no such note")
            return
        self.sender.send(self.user_id, data.get(name))

    @superadmin_only
    def remove_note(self):
        file = open('./../resources/notes.json', 'r', encoding='utf-8')
        data = json.load(file)
        file.close()
        msg = self.message
        if msg == '':
            self.sender.send(self.user_id, "there's no name")
            return
        name = re.split(' |\n', msg)
        if len(name) > 1:
            self.sender.send(self.user_id, "What's the trash you wrote except name ?? ")
            return
        name = name[0]
        if name not in data.keys():
            self.sender.send(self.user_id, "there's no such note")
            return
        del data[name]
        
        file = open('./../resources/notes.json', 'w', encoding='utf-8')
        file.write(json.dumps(data))
        file.close()
        self.sender.send(self.user_id, 'notes updated')
    
    @superadmin_only
    def update_note(self):
        file = open('./../resources/notes.json', 'r', encoding='utf-8')
        data = json.load(file)
        file.close()
        msg = self.message
        if msg == '':
            self.sender.send(self.user_id, "there's empty note. Nor name neither text")
            return
        name = re.split(' |\n', msg)
        if len(name) == 1:
            self.sender.send(self.user_id, "there's only name of note")
            return
        name = name[0]
        text = msg[len(name)+1:]
        if name not in data.keys():
            self.sender.send(self.user_id, "there's no such note")
            return
        text = data[name] + '\n' + text
        data.update({name : text})
        file = open('./../resources/notes.json', 'w', encoding='utf-8')
        file.write(json.dumps(data))
        file.close()
        self.sender.send(self.user_id, 'notes updated')
        

    prefixes = {
        "addnote" : add_note,
        "add note" : add_note,
        "+нот" : add_note,
        "note" : read_note,
        "нот" : read_note,
        "remove note" : remove_note,
        "delete note" : remove_note,
        "-нот" : remove_note,
        "upnote" : update_note,
        "++нот" : update_note
    }
    cmds = {
        "notes" : show_notes,
        "нотс" : show_notes
    }
"""