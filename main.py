import json
import re
from abc import ABC, abstractmethod
from json.decoder import JSONDecodeError
from adresbook_classes import Name, Phone, Record, Birthday, AddressBook
from note_classes import Note, NoteBook, Tag


CONTACTS_DATA = 'contacts.json'
NOTES_DATA = 'note.json'




class Serialization(ABC):
    @abstractmethod
    def read_file():
        raise NotImplementedError
    
    @abstractmethod
    def save_file():
        raise NotImplementedError



class JSONSerialization(Serialization):

    def read_file(file_name):
        try:
            with open(file_name, 'r') as f:
                cls = json.load(f)
        except (FileNotFoundError, AttributeError, JSONDecodeError):
            cls = {}
        return cls

    def save_file(file_name, notebook):
        with open(file_name, 'w') as f:
            if notebook:
                json.dump(notebook, f)


class Worker(ABC):
    @abstractmethod
    def add_record():
        pass
    
    @abstractmethod
    def change_record():
        pass

    @abstractmethod
    def show_record():
        pass

    @abstractmethod
    def remove_record():
        pass

    @abstractmethod
    def find_record():
        pass


class PhoneWorker(Worker):

    def add_record(*args, **kwargs):
        contacts = kwargs['contacts']
        name = Name(args[0].strip().lower())
        phones = []
        bday = None
        if args[1:]:
            for arg in args[1:]:
                if len(arg) > 5:
                    match_phone = re.findall(
                        r'\b\+?\d{1,3}-?\d{1,3}-?\d{1,4}\b', str(arg))
                    if match_phone:

                        phones.extend([Phone(phone.strip().lower())
                                    for phone in match_phone])
                match_bd = re.search(r'\b(\d{1,2})\s(January|February|March|April|May|June|July|August|September|October|November|December)\s(\d{4})\b', ' '.join(
                    args[1:]), re.IGNORECASE)
                if match_bd:
                    bday = f"{match_bd.group(1)} {match_bd.group(2)} {match_bd.group(3)}"

        rec = Record(name, phones, bday)
        if not contacts.get(str(name)):
            contacts.add_record(rec)
            JSONSerialization.save_file(CONTACTS_DATA, contacts.to_dict())
            return f"Contact {name} with phone {phones} and birthday '{bday}' successfully added", contacts
        if phones:
            contact = contacts.get(str(name))
            contact.add_phone(*phones)
            JSONSerialization.save_file(CONTACTS_DATA, contacts.to_dict())
            return f"Phone {phones} added to contact {name}.", contacts
        elif bday:
            contact = contacts.get(str(name))
            contact.bday = Birthday(bday)
            JSONSerialization.save_file(CONTACTS_DATA, contacts.to_dict())
            return f"Birthday {bday} added to contact {name}.", contacts
    
    def change_record(*args, **kwargs):
        contacts = kwargs['contacts']

        if args[0]:
            name = Name(args[0].strip().lower())
        else:
            raise IndexError()
    
        old_phone = Phone(args[1].strip().lower())

        new_phone = Phone(args[2].strip().lower())

        rec = contacts.get(str(name))
        if rec:
            rec.edit_phone(old_phone, new_phone)
            JSONSerialization.save_file(CONTACTS_DATA, contacts.to_dict())
            return f"Phone for contact {name} changed successfully.\nOld phone {old_phone}, new phone {new_phone}", contacts
        return f"Contact {name} doesn't exist", contacts

    def find_record(*args, **kwargs):
        contacts = kwargs["contacts"]
        n = args[0].strip().lower()
        result = []
        for key, value in contacts.items():
            if n in "{} {} {}".format(str(value.name).lower(),
                                    str(value.phones),
                                    str(value.bday)):
                result.append(f"{key} : {value.phones}, {value.bday}")
        return '\n'.join(result) or f"There are no results with {n}", contacts


    def remove_record(*args, **kwargs):
        contacts = kwargs['contacts']
        name = Name(args[0].strip().lower())
        contacts.pop(str(name))
        JSONSerialization.save_file(CONTACTS_DATA, contacts.to_dict())
        return f"Contact {name} successfully deleted", contacts

    def show_all(*args, **kwargs):
        contacts = kwargs['contacts']
        if contacts:
            if len(args) > 0:
                try:
                    records_num = int(args[0].strip())
                    for record in contacts.paginator(records_num):
                        return record, contacts
                except ValueError:
                    pass
            for record in contacts.paginator(records_num=len(contacts)):
                return record, contacts
        return "No contacts", contacts


class NoteWorker(Worker):

    def add_record(*args, **kwargs):
        notebook: NoteBook = kwargs["notebook"]
    
        try:
            if args[0]:
                title = ' '.join(args)
        except IndexError:
            raise IndexError('Заголовок не може бути пустим') from None

        text = input("Введіть текст нотатку :")
        str_tags = input("Введіть теги нотатку через кому :")
        tags = [Tag(tag.strip()) for tag in str_tags.split(',')]
        nt = Note(title=title, text=text, tags=tags)
        notebook.add_notes(nt)
        JSONSerialization.save_file(NOTES_DATA, notebook.to_dict())
        return f"Note '{title}' successfully added", notebook
    
    def change_record(*args, **kwargs):
        """ Редагує поля нотатку """
        notebook: NoteBook = kwargs["notebook"]
        try:
            if args[0]:
                title = ' '.join(args)
        except IndexError:
            raise IndexError('Введіть корретно заголовок') from None
        
        note: Note = None

        for k, v in notebook.items():
            if title == k:
                note = v

        input_text = "Якщо бажаєте змінити заголовк нажтіть 't' якщо текст ноатку нажміть 'x' \
    а якщо теги тоді 'w' "
        choice = input(input_text+'\n >>>') 

        match choice:
            case 't':
                old_title = note.title
                new_title = input('Введіь новий заголовок: ')
                note.change_title(new_title)
                notebook.pop(old_title)
                notebook[new_title] = note
                JSONSerialization.save_file(NOTES_DATA, notebook.to_dict())
                return f"Успішно замінили {old_title} на {new_title}", notebook
            
            case 'x':
                old_text = note.text
                new_text = input('Введіь новий текст: ')
                note.change_text(new_text)
                notebook[note.title] = note
                JSONSerialization.save_file(NOTES_DATA, notebook.to_dict())
                return f"Успішно замінили {old_text} на {new_text}", notebook

            case 'w':
                old_tags = note.tags
                new_tags = input('Введіь новий текст: ')
                new_tags = [Tag(tag.strip()) for tag in new_tags.split(',')]   
                note.change_tags(new_tags)
                notebook[note.title] = note
                JSONSerialization.save_file(NOTES_DATA, notebook.to_dict())
                print(note.tags)
                return f"Успішно замінили {old_tags} на {new_tags}", notebook
            case _:
                raise IndexError('Введіть коррекно дані') from None

    def find_record(*args, **kwargs):
        """Пошук нотатків """
        notebook: NoteBook = kwargs["notebook"]
        result = notebook.find(args[0])
        return '\n'.join(result) , notebook
    
    def remove_record(*args, **kwargs):
        """ 
            Видаляє нотатку по заголовку. Треба ввести заголовок повністю
        """
        notebook: NoteBook = kwargs["notebook"]
        try:
            word , notebook = notebook.remove_note(' '.join(args) if len(args) > 1 else args[0])
        except IndexError:
            return 'Note not found', notebook
        JSONSerialization.save_file(NOTES_DATA, notebook.to_dict())
        return f'{word.capitalize()} successfully remove', notebook

    
    def show_all():
        pass




class Interface(ABC):
    pass

class TerminalInterface(Interface):

    def hello_func(*args, **kwargs):
        contacts = kwargs['contacts']
        return "How can I help you?", contacts


    def unknown_command(*args, **kwargs):
        contacts = kwargs['contacts']
        return "Sorry, unknown command. Try again", contacts


    def exit_func(*args, **kwargs):
        contacts = kwargs['contacts']
        return "Bye", contacts


    def help_func(*args, **kwargs):
        contacts = kwargs['contacts']
        return ''' 
                
                ''', contacts

# список функцій
NOTE_MODES = {'addnote': NoteWorker.add_record,
              'changenote': NoteWorker.change_record,
              'findnote': NoteWorker.find_record,
              'shownote': NoteWorker.show_all}

PHONE_MODES = {'addphone': PhoneWorker.add_record,
              'changephone': PhoneWorker.change_record,
              'findphone': PhoneWorker.find_record,
              'showphone': PhoneWorker.show_all}

INTERFACE_MODES = {'help': TerminalInterface.help_func,
                   'hello': TerminalInterface.hello_func,
                   'exit': TerminalInterface.exit_func}
# каррировання
MODES = {}
MODES.update(NOTE_MODES) 
MODES.update(PHONE_MODES)
MODES.update(INTERFACE_MODES)
# print(MODES)


def handler(text):
    for command, func in MODES.items():
        if text.lower().startswith(command):
            return func, text.replace(command, ' ').strip().split()
    return TerminalInterface.unknown_command, []


def main():
    contacts = AddressBook()
    contacts.from_dict(JSONSerialization.read_file(CONTACTS_DATA))
    
    # Загрузка NoteBook
    notebook = NoteBook()
    notebook.from_dict(JSONSerialization.read_file(NOTES_DATA))

    while True:
    
        func, text = handler(input('>>>'))
        print(func)
        print(text)
        if func in NOTE_MODES.values():
            result, notebook = func(*text, notebook = notebook)
            print(result)
        elif func in MODES.values():
            result, contacts = func(*text, contacts=contacts)
            print(result)
        if func == TerminalInterface.exit_func:
            JSONSerialization.save_file(CONTACTS_DATA, contacts.to_dict())
            JSONSerialization.save_file(NOTES_DATA, notebook.to_dict())
            break



if __name__ == '__main__':
    main()
