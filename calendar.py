from datetime import datetime as dt
from sys import exit
import json
from random import randint
import locale

# CLASSES  --------------------------------------------------------------------------------------------------------------

class Page:
    '''Each of the app's pages are stored here'''

    @staticmethod
    def main_menu():
        global now
        now = dt.now()

        p(10)
        print('===================================================')
        p(1)
        welcome_text = [
            Text('Welcome to TerminalCal. 🗓️'),
            Text('').get_date(),
            Text('What would you like to do?')
        ]
        for line in welcome_text: print(line)

        options = OptionGroup([
            Option('Create Event', '1', Page.create_event),
            Option('View Events', '2', Page.view_events),
            Option('View Calendar', '3', Page.view_calendar),
            Option('Settings', '4', Page.settings),
            Option('Quit', 'Q', exit)
        ])

        options.display()

    @staticmethod
    def settings():
        settings = Setting.get_all()
        print(title('Settings'))
        options = OptionGroup([])
        for setting in settings:
            name,value = Text(setting.name).get(),Text(str(setting.value)).get()
            option = Option(f'{name}: {value}', str(setting.id+1), Setting.change_setting)
            option.assign_object(setting)
            options.add(option)
        options.add([
            Option('','',()), # Empty option creates a gap between settings to choose (above) and page navigation (below)
            Option('Main menu', 'M', Page.main_menu),
            Option('Quit', 'Q', exit)
        ])
        options.display()

    @staticmethod
    def create_event(prior_id=None):

        event_name = input('\nWhat is the event called?\n')
        event_date = input('\nWhen is the event? (Please type the date in YYYY-MM-DD format.)\n')

        try:
            info = [int(x) for x in event_date.split('-')]
            event_date = dt(info[0], info[1], info[2])
        except:
            print('Input failed.')
            exit()

        if prior_id == None: id = Event.generate_id()
        else: id = prior_id

        event = Event(event_name, event_date, id)
        event.save()
        Page.main_menu()

    @staticmethod
    def edit_event():
        all_events = sort_events_by_date(Event.get_all()) #type: ignore
        indices = list(range(len(all_events)))
        events = {i:e for i,e in zip(indices,all_events)}
        options = OptionGroup([
            Option((event.name, event.date.strftime('%x')), str(index), event.edit) for index,event in events.items()
        ])
        print('\nSelect event to edit:')
        options.display()
        Page.main_menu()

    @staticmethod
    def view_calendar():
        global month_to_display
        quit_viewing_calendar = False
        month_to_display = (now.year, now.month)

        while quit_viewing_calendar == False:
            if quit_viewing_calendar: break
            display_month(month_to_display)
            show_this_months_events(month_to_display)

            def show_prev_month():
                global month_to_display
                month_to_display = change_month(month_to_display,-1)

            def show_next_month():
                global month_to_display
                month_to_display = change_month(month_to_display,1)

            def show_this_month():
                global month_to_display
                month_to_display = (now.year, now.month)

            def show_specific_month():
                global month_to_display
                month_input = input('\nWhat month should be displayed? (Acceptable input formats: "2025-3", "Sep 2025", "October 2025")\n')
                month_to_display = validate_month_input(month_input)

            def return_to_main_menu():
                global quit_viewing_calendar
                quit_viewing_calendar = True
                Page.main_menu()

            options = OptionGroup([
                Option('Show previous month', '<', show_prev_month),
                Option('Show next month', '>', show_next_month),
                Option('Show this month', '.', show_this_month),
                Option('Show specific month', 'S', show_specific_month),
                Option('Main menu', 'M', return_to_main_menu),
                Option('Quit', 'Q', exit)
            ])

            options.display()

    @staticmethod
    def view_events():
        all_events = get_saved_events(asEvents=True)
        events_by_month = organise_events_by_month(all_events)
        for k,v in events_by_month.items():
            print('\n'+get_month_string(k))
            for event in v:
                print(f'{event.weekday_abv} {event.date.day} -- {event.name}')
        
        options = OptionGroup([
            Option('Main Menu', 'M', Page.main_menu),
            Option('Edit event', 'E', Page.edit_event),
            Option('Quit', 'Q', exit)
        ])

        options.display()

class Setting:

    def __init__(self, id, name, value, possible_settings):
        self.id = id
        self.name = name
        self.value = value
        self.possible_settings = possible_settings

    @staticmethod
    def get_all():
        with open('settings.json') as file:
            return [Setting(**item) for item in json.load(file)]

    @staticmethod
    def get(setting_name):
        return [setting for setting in Setting.get_all() if setting.name == setting_name][0]

    def update(self):
        other_settings = [setting for setting in Setting.get_all() if setting.name != self.name] 
        other_settings.insert(self.id, self)
        with open('settings.json', 'w') as file:
            json.dump([setting.__dict__ for setting in other_settings],file,indent=2)
    
    @staticmethod
    def get_target_language() -> str:
        lang_abbreviations = {
            'English': 'en',
            'Cymraeg': 'cy',
            'español': 'es',
            'Deutsch': 'de',
            'français': 'fr'
        }
        target_lang = lang_abbreviations[Setting.get("Language").value]
        return target_lang
    
    @staticmethod
    def set_locale():
        global locale

        match Setting.get_target_language():
            case "de":
                locale.setlocale(locale.LC_ALL, 'de_DE')
            case "es":
                locale.setlocale(locale.LC_ALL, 'es_ES')
            case "en", "cy":
                locale.setlocale(locale.LC_ALL, 'en_GB')

    def toggle_bool_setting(self, message_if_true, message_if_false):
        '''Toggles a boolean setting and provides a message depending on whether setting is being changed from True to False or False to True. Requires input of "Y" to toggle the setting. Alternative strings can be mapped to the "True" or "False" states respectively.'''

        if len(self.possible_settings) != 2:
            return Exception('Setting.toggle_bool_setting() requires a setting with only 2 options.')

        if self.value == self.possible_settings[0]:
            inp = input(message_if_true)
            if inp.upper() == 'Y': self.value = self.possible_settings[1]
        else:
            inp = input(message_if_false)
            if inp.upper() == 'Y': self.value = self.possible_settings[0]

        return self

    @staticmethod
    def save_lang_setting(lang_name):
        lang_setting = Setting.get('Language')
        lang_setting.value = lang_name
        lang_setting.update()

    def choose_setting_from_options(self, desired_func):
        options = OptionGroup([])
        trigger_count = 1
        for setting_option in self.possible_settings:
            option = Option(setting_option, str(trigger_count), desired_func)
            option.assign_object(setting_option)
            options.add(option)
            trigger_count += 1
        options.display()

    def change_setting(self):
        
        match self.name:
            case '12-hour Clock':
                self.toggle_bool_setting(
                    '\nUse 24-hour clock? [Y]/[N]\n',
                    '\nUse 12-hour clock? [Y]/[N]\n')
                self.update()
            case 'Week Start':
                self.toggle_bool_setting(
                    '\nStart week on Sunday? [Y]/[N]\n',
                    '\nStart week on Monday? [Y]/[N]\n')
                self.update()
            case 'Language':
                print('\n', Text('Choose language').get())
                self.choose_setting_from_options(Setting.save_lang_setting)
                Page.main_menu()
            case _:
                print('Error, unable to change this setting at this time.')
        
        Page.settings()

class Text:
    '''Checks setting language and returns translation if necessary'''

    target_lang = Setting.get_target_language()

    def __init__(self, text):
        self.text = text
        self.has_args = False

    def add_args(self, *args):
        self.args = args
        return self
    
    def text_with_args(self, given_text: str) -> str:
        if '{}' in given_text:
            for arg in self.args:
                given_text = given_text.replace('{}', f'{arg}', 1)
        return given_text
    
    def get_date(self) -> str:
        Setting.set_locale()
        Text.target_lang = Setting.get_target_language()
        self.text =  "Today is {}, the {} of {}, {}"
        base_text = self.get_translation()[Text.target_lang]
        args = [now.strftime(arg) for arg in ['%A', '%-d', '%B', '%Y']]
        if Text.target_lang == 'cy':
            with open('welsh_date_translations.json') as file:
                welsh_translations = json.load(file)
            args = [welsh_translations[arg] if arg in welsh_translations.keys() else arg for arg in args]
            args[0] = 'Dydd '+args[0]
            args[2] = self.treiglad(args[2])
        self.add_args(*args)
        return self.text_with_args(base_text)
    
    def treiglad(self, input_string):
        '''Adds a soft mutation to text if language set to Welsh to comply with Welsh grammar.'''
        mutations = {
            'M': 'F', 'G': '', 'T': 'D', 'Rh': 'R'
        }
        if input_string[:2] in mutations.keys():
            output = input_string.replace(input_string[:2], mutations[input_string[:2]])
            return output.title()
        elif input_string[0] in mutations.keys():
            output = input_string.replace(input_string[0], mutations[input_string[0]])
            return output.title()

        
    def get(self) -> str:
        if Text.target_lang == "en" or self.get_translation()=="Error": 
            return self.text_with_args(self.text)
        else:
            text = self.get_translation()[Text.target_lang]
            return self.text_with_args(text)

    def get_translation(self):
        try:
            with open('translations.json') as file:
                translation = [translation for translation in json.load(file) if translation['en'] == self.text][0]
            return translation
        except:
            return "Error"
        
    def __str__(self) -> str:
        return self.get()

class Event:

    def __init__(self, name, date, id=None):
        self.name = name
        self.date = date
        self.weekday_abv = self.date.strftime('%a')
        self.month_tuple = (self.date.year, self.date.month)
        if id == None:
            self.id = Event.generate_id()
        else:
            self.id = id

    def as_object(self):
        return {'id': self.id, 'name': self.name, 'date': self.date.__str__()}

    @staticmethod
    def get_all(asEvents=True):
        with open('events.json') as file:
            all_events = json.load(file)
        if asEvents:
            return [Event(event['name'], string_to_date(event['date']), event['id']) for event in all_events]
        else:
            return all_events
        
    @staticmethod
    def generate_id():
        ids = [event.id for event in Event.get_all()]
        id_found = False
        while not id_found:
            id = randint(1000,9999)
            if id not in ids: id_found = True

        return id #type: ignore
    
    def save(self):

        all_events = Event.get_all(False)
        all_events.append(self.as_object())

        with open('events.json', 'w') as file:
            json.dump(all_events, file, indent=2)

    def delete(self, print_message=True):

        if proceed():
            events_to_keep = [self.as_object() for event in Event.get_all() if event.id != self.id]
            with open('events.json', 'w') as file:
                json.dump(events_to_keep, file, indent=2)
            if print_message: print('Event deleted!')

    
    def edit(self):
        print('\nEDITING EVENT ✏️\n')

        event_details = {'Name': self.name, 'Date': date_to_string(self.date)}
        for k,v in event_details.items(): print(f'{k.upper()}: {v}')

        options = OptionGroup([
            Option('Edit Event Name', 'N', self.edit_name),
            Option('Edit Date', 'D', self.edit_date),
            Option('Delete Event', 'X', self.delete)
        ])
        options.display()

    def edit_name(self):
        inp = input('\nWhat should the event be called?\n')
        self.name = inp
        self.save()
        print('\nEvent name saved successfully.')

    def edit_date(self):
        inp = input('\nWhat is the new date of the event? (Please use YYYY-MM-DD format.\n')
        try:
            info = [int(x) for x in inp.split('-')]
            self.date = dt(info[0], info[1], info[2])
            self.save()
            print('\nEvent date saved successfully.')
        except:
            print('Input failed.')
            exit()



class Option:

    def __init__(self, title, trigger, action):
        self.title = Text(title).get()
        self.trigger = trigger
        self.action = action
        self.has_object = False

    def action_with_argument(self, argument):
        self.action_with_argument(argument)

    def assign_object(self, object):
        self.object = object
        self.has_object = True

class OptionGroup:

    def __init__(self, list_of_options):
        self.all = list_of_options

    def add(self, option):
        if type(option) == list:
            self.all.extend(option)
        else:
            self.all.append(option)

    def display(self):

        p(1)
        
        for option in self.all:
            if option.title == '':
                p(1)
            else:
                print(f'[{option.trigger}] {option.title}')
        p(1)

        inp = input()

        for option in self.all:
            if inp.upper() == option.trigger:
                if option.has_object:
                    option.action(option.object)
                else:
                    option.action()


# FUNCTIONS  ----------------------------------------------------------------------------------------------------------------

def p(x: int) -> None:
    for i in range(x): print()

def title(string: str) -> str:
    return '\n-- '+string.upper()+' --\n'

def stringlist(given_list) -> list[str]:
    return [str(x) for x in given_list]

def get_saved_events(asEvents=False) -> list[dict] | list[Event]:
    with open('events.json') as file:
        all_events = json.load(file)
    if asEvents:
        return [Event(event['name'], string_to_date(event['date']), event['id']) for event in all_events]
    else:
        return all_events

def string_to_date(given_string: str) -> dt:
    # given string should be in format "YYYY-MM-DD HH:MM:SS"
    time = given_string.split(' ')[1]
    date = given_string.split(' ')[0].split('-')
    year,month,day = tuple([int(x) for x in date])
    return dt(year, month, day)

def display_time(datetime_object) -> str:
    clock_setting = Setting.get('12-hour Clock').value
    if clock_setting:
        am_pm = datetime_object.strftime('%p').lower()
        return datetime_object.strftime(f'%-I:%M{am_pm}')
    else: 
        return datetime_object.strftime('%H:%M')

def change_month(month_tuple, num):
    inp = month_tuple[1]+num
    if inp == 12:
        dm = (0,12)
    elif inp == 0:
        dm = (-1,12)
    else:
        dm = divmod(inp, 12)

    year = month_tuple[0]+dm[0]
    month = dm[1]

    return (year, month)

def date_to_string(datetime_object, short_form=True) -> str:
    if short_form:
        return datetime_object.strftime('%a, %-d %b %Y')
    else:
        ordinal_date = add_ordinal_ending(datetime_object.strftime('%-d'))
        return datetime_object.strftime(f'%A, the {ordinal_date} of %B %Y')

def get_month_string(month_tuple, short=True) -> str:
    if short:
        global short_month_names
        months = short_month_names
    else:
        global long_month_names
        months = long_month_names
    return f'{months[month_tuple[1]-1]} {month_tuple[0]}'

def sort_dict_by_value(given_dict):
    sorted_values = sorted(given_dict.values())
    output = {}
    for val in sorted_values:
        key = [k for k,v in given_dict.items() if v == val][0]
        output[key] = val
    return output

def sort_events_by_date(list_of_events: list[Event]) -> list[Event]:
    dates = sorted(set([event.date for event in list_of_events]))
    output = []
    for date in dates:
        for event in list_of_events:
            if event.date == date:
                output.append(event)
    return output

def add_ordinal_ending(num) -> str:
    if type(num) == int: num = str(num)
    if num[-1] in '123':
        endings = {1: 'st', 2: 'nd', 3: 'rd'}
        return num+endings[int(num[-1])]
    else:
        return num+'th'

def validate_year(num):
    if type(num) != int: num = int(num)
    if num < 100:
        if num <= 50:
            return int('20'+str(num))
        else:
            return int('19'+str(num))
    else:
        return num


def validate_month_input(string):
    global long_month_names, short_month_names
    if '-' in string:
        return tuple([int(x) for x in string.split('-')])
    elif ' ' in string:
        string = string.split(' ')
        for element in string:
            if element in long_month_names:
                month = long_month_names.index(element)+1
            elif element in short_month_names:
                month = short_month_names.index(element)+1
            else:
                try:
                    year = int(element)
                    year = validate_year(year)
                except ValueError:
                    print('Action could not be completed')
        return (year, month) #type: ignore
    else:
        print('Error validating month input.')
    

def display_month(given_month=None):
    global now
    if given_month==None: given_month = (now.year, now.month)
    week_starts_on = Setting.get('Week Start').value
    
    def get_days_in_month(month=given_month[1]):
        if month == 2:
            year = now.year
            if year % 400 == 0: return 29
            elif year % 100 == 0: return 28
            elif year % 4 == 0: return 29
            else: return 28
        elif month in [9, 4, 6, 11]:
            return 30
        else:
            return 31

    def get_weeks(given_month=given_month):
        month_starts_on = dt(given_month[0], given_month[1], 1).weekday()
        if week_starts_on == 'Sunday': month_starts_on = (month_starts_on+1)%7
        days = (['']*month_starts_on) + stringlist(list(range(1, get_days_in_month()+1)))
        days = show_days_with_event(days)
        weeks = list(range(0,50,7))
        output = []
        for i in range(len(weeks)-1):
            week = days[weeks[i]:weeks[i+1]]
            if len(week) > 0: output.append(week)
        return output
    
    def show_days_with_event(days_array, month=given_month):
        event_dates = [string_to_date(event['date']) for event in get_saved_events()]
        this_months_events = [str(event.day) for event in event_dates if event.month == month[1] and event.year == month[0]]
        output = ['['+day+']'  if day in this_months_events else day for day in days_array]
        return output

    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    if week_starts_on == 'Sunday':
        weekdays = [weekdays[-1]]+weekdays[:-1]

    calendar_month = [weekdays]+get_weeks()
    print(f'\n{get_month_string(given_month, short=False)}\n')
    
    for week in calendar_month:
        print('\t'.join(week))


def show_this_months_events(given_month):
    all_events = get_saved_events(asEvents=True)
    try:
        this_months_events = organise_events_by_month(all_events)[given_month]
        print(f'\nEvents in {get_month_string(given_month)}:')
        for event in this_months_events:
            print(f'{event.weekday_abv} {event.date.day} -- {event.name}')
    except KeyError:
        pass

def organise_events_by_month(list_of_events) -> dict[tuple,list[Event]]:
    all_events = sort_events_by_date(list_of_events)
    all_months = sorted(set([event.month_tuple for event in all_events]))
    events_by_month = {}
    for month in all_months:
        for event in all_events:
            if event.month_tuple == month:
                if month not in events_by_month:
                    events_by_month[month] = [event]
                else:
                    events_by_month[month].append(event)
    return events_by_month


def proceed() -> bool:
    '''Confirms user input for destructive behaviour (e.g. deleting an event)'''
    inp = input('\nAre you sure? [Y]/[N]\n')
    if inp.upper() == 'Y':
        return True
    else:
        return False

        
# GLOBAL VARIABLES --------------------------------------------------------------------------------------------------------

chosen_option = 0
now = dt.now()
long_month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
short_month_names = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_to_display = (now.year, now.month)
Setting.set_locale()


# MAIN APP ----------------------------------------------------------------------------------------------------------------

p(5)
Page.main_menu()

p(5)
exit()