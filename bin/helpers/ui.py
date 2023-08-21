import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
import json

with open('./bin/config.json', 'r') as f:
    config = json.load(f)
    style_config = config['Style']

auto_update = config['Auto Update']

FREQUENCY_OPTIONS = config['Frequency Options']

BG = style_config['bg']
#BG2 = style_config['bg2'] Not implemented, not sure if i ever will
#FG1 = style_config['fg1']
#FG2 = style_config['fg2']
#BRIGHT = style_config['bright']
#BORDERWIDTH = style_config['borderwidth']
FONTSIZE = style_config['fontsize']

class TextWithVariable(tk.Text):
    def __init__(self, *args, variable: tk.StringVar, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        self._variable = variable

        self.bind('<KeyRelease>', self._update)

    def _update(self, _) -> None:
        self._variable.set(self.get('1.0', tk.END + '-1c'))

class QuestObject(ttk.Frame):
    def __init__(self, *args, index: int, **kwargs):
        ttk.Frame.__init__(self, *args, **kwargs)

        self.index = index

        self.title = tk.StringVar(self, value = '')
        self.frequency = tk.StringVar(self, value = FREQUENCY_OPTIONS[1]) # not sure why, but had to include a blank value for index 0
        self.chooseable = tk.IntVar(self, value = 0)
        self.input = tk.StringVar(self)
        self.output = tk.StringVar(self)

        self._font = tkfont.nametofont('TkDefaultFont')
        self._font.configure(size = FONTSIZE)

        self._options_frame = ttk.Frame(self)

        self._title_label = ttk.Label(self._options_frame, text = 'Title: ')
        self._title_entry = ttk.Entry(self._options_frame, textvariable = self.title)
        self._frequency_optionmenu = ttk.OptionMenu(self._options_frame, self.frequency, *FREQUENCY_OPTIONS)
        self._chooseable_check = ttk.Checkbutton(self._options_frame, text = 'Chooseable', variable = self.chooseable)
        self._options_spacer_frame = ttk.Frame(self._options_frame, width = 125)
        self._delete_button = ttk.Button(self._options_frame, text = '×', width = 3, command = self.destroy)

        self._title_label.grid(row = 0, column = 0, padx = 5)
        self._title_entry.grid(row = 0, column = 1, padx = 5)
        self._frequency_optionmenu.grid(row = 0, column = 2, padx = 5)
        self._chooseable_check.grid(row = 0, column = 3, padx = 5)
        self._options_spacer_frame.grid(row = 0, column = 4)
        self._delete_button.grid(row = 0, column = 5)

        self._options_frame.grid(row = 0, column = 0, pady = 8, sticky = tk.W)

        self._io_frame = ttk.Frame(self)

        self._input_text = TextWithVariable(self._io_frame, font = self._font, variable = self.input, width = 37, height = 8)
        self._arrow = tk.PhotoImage(file = './bin/icons/Arrow.png', format = 'PNG')
        self._arrow_label = ttk.Label(self._io_frame, image = self._arrow)
        self._output_text = TextWithVariable(self._io_frame, font = self._font, variable = self.output, width = 37, height = 8)

        self._input_text.grid(row = 0, column = 0)
        self._arrow_label.grid(row = 0, column = 1)
        self._output_text.grid(row = 0, column = 2)

        self._io_frame.grid(row = 1, column = 0, sticky = tk.W)

        self.grid(row = self.index, column = 0, padx = 15, pady = 15)

# must call mainloop (done so you can bind things to it outside of this module)
class App:
    def __init__(self):
        self._quest_objects = []

        self.root = tk.Tk()
        self.root.title('Quest Infographic Maker')
        self.root.geometry('1000x500')
        #icon
        
        self._style = ttk.Style()

        self._style.configure('.', focuscolor = BG)
        self._style.configure('Block.TFrame', borderwidth = 1, relief = 'solid')

        self._font = tkfont.nametofont('TkDefaultFont')
        self._font.configure(size = FONTSIZE)

        #style

        self._main_frame = ttk.Frame(self.root)

        self._canvas_frame = ttk.Frame(self._main_frame)

        self._canvas = tk.Canvas(self._canvas_frame, bg = BG, width = 600,height = 50, scrollregion = (0, 0, 0, 50))
        self._scrollbar = ttk.Scrollbar(self._canvas_frame, orient = tk.VERTICAL)
        self._scrollbar.config(command = self._canvas.yview)
        self._canvas.config(yscrollcommand = self._scrollbar.set)

        self._scrollbar.place(relx = 1, rely = 0, width = 15, relheight = 1, anchor = tk.NE)
        self._canvas.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)

        self._canvas_contained_frame = ttk.Frame(self._canvas, style = 'Block.TFrame')
        self._canvas_contained_frame.bind("<Configure>", lambda _: self._canvas.configure(scrollregion = self._canvas.bbox('all')))
        self._canvas.bind_all("<MouseWheel>", lambda event: self._canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units'))

        self._add_quest_frame = ttk.Frame(self._canvas_contained_frame)
        self._add_quest_button = ttk.Button(self._add_quest_frame, text = '+', width = 3, command = self._add_graphic)
        self._add_quest_label = ttk.Label(self._add_quest_frame, text = 'Add a Quest')
        self._add_quest_button.grid(row = 0, column = 0)
        self._add_quest_label.grid(row = 0, column = 1, padx = 5)
        self._add_quest_frame.grid(row = 0, column = 1, padx = 10, pady = 5)

        self._canvas.create_window((0, 0), anchor = tk.NW, window = self._canvas_contained_frame, state = tk.NORMAL)

        self._canvas_frame.pack(side = tk.TOP, fill = tk.BOTH, expand = True)

        self._buttons_frame = ttk.Frame(self._main_frame)
        self.generate_button = ttk.Button(self._buttons_frame, text = 'Generate')
        self.preview_button = ttk.Button(self._buttons_frame, text = 'Preview')

        self.settings_menubutton = ttk.Menubutton(self._buttons_frame, text = '⚙')

        self.settings_menubutton.menu = tk.Menu(self.settings_menubutton, tearoff = False)
        self.settings_menubutton['menu'] = self.settings_menubutton.menu

        self.options_auto_update = tk.IntVar(self.root, value = auto_update)

        self.generate_button.grid(row = 0, column = 0)
        self.preview_button.grid(row = 0, column = 1)
        self.settings_menubutton.grid(row = 0, column = 2)

        self._buttons_frame.pack(side = tk.BOTTOM, fill = tk.X, padx = 10, pady = 10)

        self._main_frame.pack(fill = tk.BOTH, expand = True)
    
    def _add_graphic(self) -> None:
        quest_object = QuestObject(self._canvas_contained_frame, index = len(self._quest_objects))
        quest_object.bind('<Destroy>', lambda _: self._update_graphic_indexes())
        self._quest_objects.append(quest_object)

    def _update_graphic_indexes(self) -> None:
        self._quest_objects = [quest_object for quest_object in self._quest_objects if quest_object.winfo_exists()] # filters non-existing objects

        for index, quest_object in enumerate(self._quest_objects):
            quest_object.index = index
            quest_object.grid(row = index, column = 0, padx = 15, pady = 15)
    
    def get_quest_info(self) -> dict[str: str | int]:
        quest_dicts = []

        for quest_object in self._quest_objects:
            quest_dict = {
                'Input': [item_name.strip().replace("’", "'") for item_name in quest_object.input.get().split('\n')],
                'Output': [item_name.strip().replace("’", "'") for item_name in quest_object.output.get().split('\n')],
                'Title': quest_object.title.get(),
                'Icon': quest_object.frequency.get().strip(),
                'Chooseable': quest_object.chooseable.get()
            }
            quest_dicts.append(quest_dict)
        
        return quest_dicts