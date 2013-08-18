import sys
from protexted import session
from protexted import selectors, operators
from protexted.selection import Selection
from protexted import current
import curses
from curses.textpad import Textbox


class UserInterface:
    def __init__(self):
        current.session = session.Session(sys.argv[1])
        current.session.read()
        current.session.selection = Selection()
        current.session.selection.add((0, 1))

        self.reduce_mode = False
        self.extend_mode = False

    def main(self, stdscr):
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, curses.COLOR_BLACK)
            # stdscr.addstr("Foo", curses.color_pair(i))

        self.stdscr = stdscr
        curses.curs_set(0)
        y, x = self.stdscr.getmaxyx()
        self.text_win = curses.newwin(y - 1, x, 0, 0)
        self.status_win = curses.newwin(1, x, y - 1, 0)
        self.stdscr.refresh()
        while 1:
            modes = []
            if self.extend_mode:
                modes.append("EXTEND")
            if self.reduce_mode:
                modes.append("REDUCE")
            self.set_status(" ".join(modes))
            self.draw_text_win()
            self.normal_mode()

    def select(self, selector):
        # BUGGED !!!
        if self.reduce_mode and self.extend_mode:
            pass
        elif self.reduce_mode:
            current.session.selection.reduce(selector(current.session.selection))
        elif self.extend_mode:
            current.session.selection.extend(selector(current.session.selection))
        else:
            current.session.selection = selector(current.session.selection)

    def normal_mode(self):
        key = self.stdscr.getch()
        if key == ord('j'):
            self.select(selectors.move_to_next_line)
        elif key == ord('k'):
            self.select(selectors.move_to_previous_line)
        elif key == ord('l'):
            self.select(selectors.move_to_next_char)
        elif key == ord('h'):
            self.select(selectors.move_to_previous_char)
        elif key == ord('w'):
            self.select(selectors.select_next_word)
        elif key == ord('b'):
            self.select(selectors.select_previous_word)
        elif key == 27:
            self.select(selectors.single_character)
        elif key == ord('i'):
            self.insert_mode(operators.insert_before)
        elif key == ord('a'):
            self.insert_mode(operators.insert_after)
        elif key == ord('s'):
            self.insert_mode(operators.insert_around)
        elif key == ord('c'):
            self.insert_mode(operators.insert_in_place)
        elif key == ord('r'):
            self.reduce_mode = not self.reduce_mode
        elif key == ord('e'):
            self.extend_mode = not self.extend_mode
        elif key == ord(':'):
            scope = vars(current.session)
            for name in vars(session.Session).keys():
                scope.update({name: eval('current.session.' + name)})
            scope.update({'current': current})
            command = self.prompt(":")
            try:
                exec(command, scope)
            except Exception as e:
                self.set_status(command + " : " + str(e))

    def insert_mode(self, operator):
        insert_text = ""
        operation = None
        while 1:
            key = self.stdscr.getch()
            if key == 27:
                if operation != None:
                    current.session.apply(operation)
                    current.session.selection = operation.new_selection
                break;
            elif key == curses.KEY_BACKSPACE:
                if len(insert_text) > 0:
                    insert_text = insert_text[:-1]
            else:
                insert_text += chr(key)
            operation = operator(current.session, current.session.selection, insert_text)
            self.draw_text_win(operation)

    def prompt(self, prompt_string=">"):
        self.status_win.clear()
        y, x = self.stdscr.getmaxyx()
        self.status_win.addstr(0, 0, prompt_string)
        self.status_win.refresh()
        l = len(prompt_string)
        text_box_win = curses.newwin(1, x - l, y - 1, l)
        text_box = Textbox(text_box_win)
        text_box.edit()
        return text_box.gather()[:-1]

    def draw_text_win(self, pending_operation=None):
        # TODO rewrite this method
        self.text_win.move(0, 0)

        lower_bound = 0
        y, x = self.text_win.getmaxyx()
        upper_bound = y * x
        bounded_selection = current.session.selection.bound(lower_bound, upper_bound)
        bounded_partition = current.session.selection.partition(current.session.text).bound(lower_bound, upper_bound)
        selection_index = 0
        try:
            for beg, end in bounded_partition:
                if (beg, end) in bounded_selection:
                    if pending_operation == None:
                        self.text_win.addstr(current.session.text[beg:end], curses.color_pair(0) | curses.A_REVERSE)
                    else:
                        self.text_win.addstr(pending_operation.new_content[selection_index], curses.color_pair(1) | curses.A_REVERSE)
                    selection_index += 1
                else:
                    self.text_win.addstr(current.session.text[beg:end])
            self.text_win.addstr("EOF", curses.A_BOLD)
            self.text_win.addstr(str(current.session.selection), curses.A_BOLD)  # DEBUG
        except:
            pass
        self.text_win.clrtobot()
        self.text_win.refresh()

    def set_status(self, string):
        try:
            self.status_win.addstr(0, 0, string)
        except:
            pass
        self.status_win.clrtobot()
        self.status_win.refresh()

ui = UserInterface()
curses.wrapper(ui.main)
