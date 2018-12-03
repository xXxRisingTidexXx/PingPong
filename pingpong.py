from random import choice
from time import sleep
from tkinter import *
from tkinter.ttk import Separator
from yaml import load, dump
from datetime import datetime


class App:
    DATA_PATH = 'res/app.yaml'
    RESOURCE_MANAGER = None
    WIDGET_MANAGER = None
    CACHE = None

    def __init__(self):
        App.RESOURCE_MANAGER = ResourceManager()
        App.WIDGET_MANAGER = WidgetManager(App.RESOURCE_MANAGER)
        App.CACHE = Cache(App.RESOURCE_MANAGER)
        data = App.RESOURCE_MANAGER[App]
        self.tk = App.WIDGET_MANAGER.prepare_tk(data['tk'])
        self.delay = data['delay']
        self.main_menu = MainMenu(self.tk)

    def start(self):
        while self.main_menu.active:
            self.tk.update_idletasks()
            self.tk.update()
            sleep(self.delay)


class ResourceManager:
    FONTS = 'fonts'
    STYLES = 'styles'
    POSITIONS = 'positions'

    def __init__(self):
        self.data = {
            ResourceManager.FONTS: self.read('res/fonts.yaml'),
            ResourceManager.STYLES: self.read('res/styles.yaml'),
            ResourceManager.POSITIONS: self.read('res/positions.yaml'),
            App: self.read(App.DATA_PATH),
            MainMenu: self.read(MainMenu.DATA_PATH),
            Game: self.read(Game.DATA_PATH),
            # Summary: self.read(Summary.DATA_PATH),
            InfoMenu: self.read(InfoMenu.DATA_PATH),
            HelpMenu: self.read(HelpMenu.DATA_PATH)
        }

    def __getitem__(self, res):
        return self.data[res]

    # noinspection PyMethodMayBeStatic
    def read(self, path):
        with open(path) as stream:
            return load(stream)

    # noinspection PyMethodMayBeStatic
    def write(self, data, path):
        with open(path, 'w') as stream:
            dump(data, stream, default_flow_style=False)


class WidgetManager:
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager

    # noinspection PyMethodMayBeStatic
    def prepare_tk(self, data):
        tk = Tk()
        tk.title(data['title'])
        tk.geometry('{}x{}'.format(tk.winfo_screenwidth(), tk.winfo_screenheight()))
        tk.resizable(data['resizable']['width'], data['resizable']['height'])
        tk.wm_attributes(*data['wm_attributes'])
        tk.configure(background=data['background'])
        return tk

    def prepare_frame(self, master, data):
        frame = Frame(master, self.resource_manager[ResourceManager.STYLES][data['style']])
        frame.place(self.resource_manager[ResourceManager.POSITIONS][data['position']])
        frame.update()
        return frame

    def prepare_button(self, master, data, command):
        button = Button(master, self.resource_manager[ResourceManager.STYLES][data['style']])
        button.configure(
            text=data['text'], font=self.resource_manager[ResourceManager.FONTS][data['font']], command=command
        )
        button.pack(self.resource_manager[ResourceManager.POSITIONS][data['position']])
        button.update()
        return button

    # noinspection PyMethodMayBeStatic
    def prepare_canvas(self, master, data):
        canvas = Canvas(master, width=master.winfo_width(), height=master.winfo_height())
        canvas.configure(self.resource_manager[ResourceManager.STYLES][data['style']])
        canvas.pack(self.resource_manager[ResourceManager.POSITIONS][data['position']])
        canvas.update()
        return canvas

    def prepare_label(self, master, data):
        label = Label(master, self.resource_manager[ResourceManager.STYLES][data['style']])
        label.configure(text=data['text'], font=self.resource_manager[ResourceManager.FONTS][data['font']])
        label.pack(self.resource_manager[ResourceManager.POSITIONS][data['position']])
        label.update()
        return label

    def prepare_separator(self, master, data):
        separator = Separator(master, orient=data['orient'])
        separator.pack(self.resource_manager[ResourceManager.POSITIONS][data['position']])
        return separator


class Cache:
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.data = {Table.CONTENT: self.resource_manager.read(Table.CONTENT_PATH)}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def update(self, key, value, updater):
        self[key] = updater(self[key], value)

    def save(self, key, path):
        self.resource_manager.write(self[key], path)


class Menu:
    def __init__(self, tk):
        self.tk = tk
        self.hidden = False
        self.frame = None
        self.frame_place_info = None

    def hide(self):
        if not self.hidden:
            self.hidden = True
            self.frame_place_info = self.frame.place_info()
            self.frame.place_forget()

    def visualize(self):
        if self.hidden:
            self.hidden = False
            self.frame.place(self.frame_place_info)


class MainMenu(Menu):
    DATA_PATH = 'res/main_menu.yaml'

    def __init__(self, tk):
        super().__init__(tk)
        self.active = True
        data = App.RESOURCE_MANAGER[MainMenu]
        self.frame = App.WIDGET_MANAGER.prepare_frame(self.tk, data['frame'])
        self.buttons = self.prepare_buttons(data['buttons'])
        self.last_player = {'name': 'Danya', 'result': 5}  # later we will delete it
        self.info_menu = None
        self.help_menu = None

    def prepare_buttons(self, data):
        return (
            App.WIDGET_MANAGER.prepare_button(self.frame, data['play_button'], self.__play),
            App.WIDGET_MANAGER.prepare_button(self.frame, data['info_button'], self.__info),
            App.WIDGET_MANAGER.prepare_button(self.frame, data['help_button'], self.__help),
            App.WIDGET_MANAGER.prepare_button(self.frame, data['exit_button'], self.__exit)
        )

    def __play(self):
        self.hide()
        Game(self).play()  # later we will extract game statistics from cache, and self.last_player will be deleted
        App.CACHE.update(Table.CONTENT, self.last_player, self.__appender)

    # noinspection PyMethodMayBeStatic
    def __appender(self, lst, value):
        lst.append(value)
        return lst

    def __info(self):
        self.hide()
        if self.info_menu is None:
            self.info_menu = InfoMenu(self)
        else:
            self.info_menu.update()
        self.info_menu.visualize()

    def __help(self):
        self.hide()
        if self.help_menu is None:
            self.help_menu = HelpMenu(self)
        self.help_menu.visualize()

    def __exit(self):
        App.CACHE.save(Table.CONTENT, Table.CONTENT_PATH)
        self.active = False


class Game:
    DATA_PATH = 'res/game.yaml'

    def __init__(self, main_menu):
        self.main_menu = main_menu
        self.tk = self.main_menu.tk
        data = App.RESOURCE_MANAGER[Game]
        self.canvas = App.WIDGET_MANAGER.prepare_canvas(self.tk, data['canvas'])
        self.session = Session()
        self.paddle = self.prepare_paddle(data['paddle'])
        self.ball = self.prepare_ball(data['ball'])
        self.score = self.prepare_score(data['score'])
        self.delay = data['delay']

    def prepare_paddle(self, data):
        paddle = Paddle(self.canvas, data)
        self.session[Paddle] = {'id': paddle.id}
        return paddle

    def prepare_ball(self, data):
        ball = Ball(self.canvas, data, self.session)
        self.session[Ball] = {'id': ball.id}
        return ball

    def prepare_score(self, data):
        score = Score(self.canvas, data)
        self.session[Score] = {'id': score.id}
        return score

    def play(self):
        while self.ball.flies():
            self.ball.move()
            self.tk.update_idletasks()
            self.tk.update()
            sleep(self.delay)
        self.canvas.pack_forget()
        self.main_menu.visualize()  # delete it later
        # Summary(self.resource_manager, self.tk, self.main_menu, ...)  put statistics here


class Session:
    def __init__(self):
        self.data = {}
        self.start = datetime.now()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value


class Paddle:
    def __init__(self, canvas, data):
        self.canvas = canvas
        self.id = self.prepare_rectangle(data['rectangle'])
        self.dxl = data['dxl']
        self.dxr = data['dxr']
        self.canvas.bind_all(data['left_arrow'], self.__move_left)
        self.canvas.bind_all(data['right_arrow'], self.__move_right)

    def prepare_rectangle(self, data):
        _id = self.canvas.create_rectangle(
            data['x1'], data['y1'], data['x2'], data['y2'], App.RESOURCE_MANAGER[ResourceManager.STYLES][data['style']]
        )
        self.canvas.move(_id, data['x0'], data['y0'])
        return _id

    # noinspection PyUnusedLocal
    def __move_left(self, event):
        self.canvas.move(self.id, self.dxl if self.hit_left_border() else 0, 0)

    def hit_left_border(self):
        return self.canvas.coords(self.id)[0] > 0

    # noinspection PyUnusedLocal
    def __move_right(self, event):
        self.canvas.move(self.id, self.dxr if self.hit_right_border() else 0, 0)

    def hit_right_border(self):
        return self.canvas.coords(self.id)[2] < self.canvas.winfo_width()


class Ball:
    def __init__(self, canvas, data, session):
        self.canvas = canvas
        self.id = self.prepare_oval(data['oval'])
        self.paddle_id = session[Paddle]['id']
        self.dx = choice(data['dx'])
        self.dy = choice(data['dy'])
        self.dt = data['dt']

    def prepare_oval(self, data):
        _id = self.canvas.create_oval(
            data['x1'], data['y1'], data['x2'], data['y2'], App.RESOURCE_MANAGER[ResourceManager.STYLES][data['style']]
        )
        self.canvas.move(_id, data['x0'], data['y0'])
        return _id

    def flies(self):
        return self.canvas.coords(self.id)[1] <= self.canvas.winfo_height()

    def move(self):
        coords = self.canvas.coords(self.id)
        self.dx = self.move_x(coords)
        self.dy = self.move_y(coords)
        self.canvas.move(self.id, self.dx, self.dy)

    def move_x(self, coords):
        return 1 if self.hit_left_border(coords) else -1 if self.hit_right_border(coords) else self.dx

    # noinspection PyMethodMayBeStatic
    def hit_left_border(self, coords):
        return coords[0] <= 0

    def hit_right_border(self, coords):
        return coords[2] >= self.canvas.winfo_width()

    def move_y(self, coords):
        return 1 if self.hit_top_border(coords) else -1 if self.hit_paddle(coords) else self.dy

    # noinspection PyMethodMayBeStatic
    def hit_top_border(self, coords):
        return coords[1] <= 0

    def hit_paddle(self, coords):
        paddle_coords = self.canvas.coords(self.paddle_id)
        return self.upon_paddle(coords, paddle_coords) and self.touch_paddle(coords, paddle_coords)

    # noinspection PyMethodMayBeStatic
    def upon_paddle(self, coords, paddle_coords):
        return coords[2] >= paddle_coords[0] and coords[0] <= paddle_coords[2]

    # noinspection PyMethodMayBeStatic
    def touch_paddle(self, coords, paddle_coords):
        return paddle_coords[1] <= coords[3] <= paddle_coords[3]


class Score:
    def __init__(self, canvas, data):
        self.canvas = canvas
        self.id = self.prepare_text(data)

    def prepare_text(self, data):
        _id = self.canvas.create_text(
            data['x1'], data['y1'], text=data['text'], font=App.RESOURCE_MANAGER[ResourceManager.FONTS][data['font']]
        )
        self.canvas.itemconfigure(_id, App.RESOURCE_MANAGER[ResourceManager.STYLES][data['style']])
        return _id

    def increment(self):
        value = self.canvas.itemcget(self.id, 'text')
        self.canvas.itemconfigure(self.id, text=str(value + 1))


# class Summary:
#     DATA_PATH = 'res/summary.yaml'
#
#     def __init__(self, resource_manager, tk, main_menu, statistics):
#         self.resource_manager = resource_manager
#         self.tk = tk
#         self.main_menu = main_menu
#         data = self.resource_manager[Summary]
#         self.frame = self.main_menu.prepare_frame(...)
#         pass
#
#     def __ok(self):
#         self.frame.place_forget()
#         self.main_menu.last_player = (...)
#         self.main_menu.visualize()
#         pass


class InfoMenu(Menu):
    DATA_PATH = 'res/info_menu.yaml'

    def __init__(self, main_menu):
        super().__init__(main_menu.tk)
        self.main_menu = main_menu
        data = App.RESOURCE_MANAGER[InfoMenu]
        self.frame = App.WIDGET_MANAGER.prepare_frame(self.tk, data['frame'])
        self.table = Table(self, data['table'])
        self.back_button = App.WIDGET_MANAGER.prepare_button(self.frame, data['back_button'], self.__back)

    def __back(self):
        self.hide()
        self.main_menu.visualize()

    def update(self):
        self.table.update()


class Table:
    CONTENT = 'content'
    CONTENT_PATH = 'res/table.yaml'

    def __init__(self, info_menu, data):
        self.info_menu = info_menu
        self.rows = data['rows']
        self.header_label = App.WIDGET_MANAGER.prepare_label(self.info_menu.frame, data['header_label'])
        self.carcass = self.prepare_carcass(data['separator'], data['name_label'], data['result_label'])
        self.update()

    # noinspection PyUnusedLocal
    def prepare_carcass(self, separator_data, name_label_data, result_label_data):
        return [{
            'separator': App.WIDGET_MANAGER.prepare_separator(self.info_menu.frame, separator_data),
            'name_label': App.WIDGET_MANAGER.prepare_label(self.info_menu.frame, name_label_data),
            'result_label': App.WIDGET_MANAGER.prepare_label(self.info_menu.frame, result_label_data)
        } for i in range(self.rows)]

    def update(self):
        content = self.limit(App.CACHE[Table.CONTENT])
        self.fill(content)
        App.CACHE[Table.CONTENT] = content

    def fill(self, content):
        for i in range(self.rows):
            self.carcass[i]['name_label'].configure(text=content[i]['name'])
            self.carcass[i]['result_label'].configure(text=content[i]['result'])

    def limit(self, content):
        return sorted(content, key=lambda r: r['result'], reverse=True)[:self.rows]


class HelpMenu(Menu):
    DATA_PATH = 'res/help_menu.yaml'

    def __init__(self, main_menu):
        super().__init__(main_menu.tk)
        self.main_menu = main_menu
        data = App.RESOURCE_MANAGER[HelpMenu]
        self.frame = App.WIDGET_MANAGER.prepare_frame(self.tk, data['frame'])
        self.header_label = App.WIDGET_MANAGER.prepare_label(self.frame, data['header_label'])
        self.wrapper_label = App.WIDGET_MANAGER.prepare_label(self.frame, data['wrapper_label'])
        self.back_button = App.WIDGET_MANAGER.prepare_button(self.frame, data['back_button'], self.__back)

    def __back(self):
        self.hide()
        self.main_menu.visualize()


if __name__ == '__main__':
    App().start()
