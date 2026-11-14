import os
import shlex
import subprocess
import curses
import _curses
import curses.textpad

import cardsboard.config as config
from cardsboard.fsdb import fsDB

COLORS = {
    "black": curses.COLOR_BLACK,
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE,
}


class Textbox(curses.textpad.Textbox):
    """
    Textbox that can be aborted with <esc> and can't be submitted empty.
    """

    aborted = False

    def do_command(self, ch):
        if ch == 27:
            self.aborted = True
            return 0
        # ignore <enter> on empty text, the user has to abort with <esc>
        if ch in (10, 13) and self.gather().strip() == "":
            return 1
        return super().do_command(ch)


class TUI:
    def __init__(self):
        """
        Initialize database and focus.
        """
        self.db = fsDB(config.DATADIR)
        self.focused_col = 0
        self.focused_row = 0

        # (keys, label, description, action), also used for the shortcuts screen
        # fmt: off
        self.shortcuts = [
            ([ord("q")], "q, ctrl + c", "quit", self.quit),
            ([ord("?")], "?", "show shortcuts", self.show_shortcuts),
            ([curses.KEY_LEFT], "arrow left", "focus left", self.focus_left),
            ([curses.KEY_RIGHT], "arrow right", "focus right", self.focus_right),
            ([curses.KEY_UP], "arrow up", "focus up", self.focus_up),
            ([curses.KEY_DOWN], "arrow down", "focus down", self.focus_down),
            ([ord("g")], "g", "focus top item", self.focus_top),
            ([ord("G")], "G", "focus bottom item", self.focus_bottom),
            ([curses.KEY_HOME], "home", "focus first column", self.focus_first),
            ([curses.KEY_END], "end", "focus last column", self.focus_last),
            ([curses.KEY_SLEFT], "shift + arrow left", "move item left", self.move_left),
            ([curses.KEY_SRIGHT], "shift + arrow right", "move item right", self.move_right),
            ([curses.KEY_SR], "shift + arrow up", "move item up", self.move_up),
            ([curses.KEY_SF], "shift + arrow down", "move item down", self.move_down),
            ([10, 13, curses.KEY_ENTER], "enter", "open focused item", self.open_item),
            ([ord("r")], "r", "reload data from disk", self.reload_data),
            ([ord("o")], "o", "insert item below", self.insert_item_below),
            ([ord("i")], "i", "rename focused item", self.rename_item),
            ([ord("d")], "dd", "delete focused item", self.delete),
            ([ord("c")], "c", "insert column right", self.insert_column_right),
            ([ord("I")], "I", "rename focused column", self.rename_column),
            ([ord("h")], "h", "move column left", self.move_column_left),
            ([ord("l")], "l", "move column right", self.move_column_right),
            # handled in delete() and Textbox, only listed for the shortcuts screen
            ([], "dc", "delete column", None),
            ([], "esc", "abort input", None),
        ]
        # fmt: on
        self.keymap = {
            curses.KEY_RESIZE: self.handle_resize,
            **{key: action for keys, _, _, action in self.shortcuts for key in keys},
        }

    def border(self, window):
        """
        Helper function to make border edges rounded.
        Curses can not do this natively:
        https://stackoverflow.com/questions/60350904/use-utf-8-character-for-curses-border
        """
        window.border()
        lines, cols = window.getmaxyx()
        window.addch(0, 0, "╭")
        window.addch(lines - 1, 0, "╰")
        window.addch(0, cols - 1, "╮")
        # https://stackoverflow.com/questions/36387625/curses-fails-when-calling-addch-on-the-bottom-right-corner
        try:
            window.addch(lines - 1, cols - 1, "╯")
        except _curses.error:
            pass

    def refresh_pad(self):
        """
        Refresh the pad based on current size of stdscr and position of focused item.
        """
        scroll_col = (self.focused_col + 1) * (config.COLUMN_WIDTH + 1) - 1 - self.cols
        scroll_row = (self.focused_row + 1) * config.ITEM_HEIGHT + 4 - self.rows
        self.pad.refresh(scroll_row, scroll_col, 0, 0, self.rows - 1, self.cols - 1)

    def draw_item(self, item, file):
        text_width = config.ITEM_WIDTH - 3
        position_icon = config.ITEM_WIDTH - 3

        if file["has_content"]:
            item.addstr(1, position_icon, "≡")
            position_icon -= 2
            text_width -= 3

        if file["tag"] is not None:
            item.addstr(1, position_icon, "⬤", self.COLOR_TAGGED)
            text_width -= 2

        item.addstr(1, 2, file["title"][:text_width])

    def draw_board(self):
        """
        Fully redraw all columns and items on the pad.
        """
        lines, _ = self.pad.getmaxyx()

        for i, folder in enumerate(self.data):
            column = self.pad.derwin(
                lines, config.COLUMN_WIDTH, 0, i * (config.COLUMN_WIDTH + 1)
            )
            self.border(column)
            text = folder["title"][: config.COLUMN_WIDTH - 2]
            column.addstr(
                1,
                (config.COLUMN_WIDTH - 2) // 2 - len(text) // 2,
                text,
                curses.A_BOLD | (self.COLOR_FOCUSED if self.focused_col == i else 0),
            )
            # draw a separation below the title
            column.hline(2, 1, curses.ACS_HLINE, config.COLUMN_WIDTH - 1)
            column.addch(2, 0, curses.ACS_LTEE)
            column.addch(2, config.COLUMN_WIDTH - 1, curses.ACS_RTEE)
            # save column
            self.data[i]["column"] = column

            for j, file in enumerate(folder["items"]):
                item = column.derwin(
                    config.ITEM_HEIGHT,
                    config.ITEM_WIDTH,
                    3 + config.ITEM_HEIGHT * j,
                    1,
                )
                self.border(item)

                self.draw_item(item, file)

                if i == self.focused_col and j == self.focused_row:
                    item.bkgd(" ", self.COLOR_FOCUSED)

                # Save item
                self.data[i]["items"][j]["item"] = item

    def run(self):
        """
        Entry point to start the UI.
        """
        try:
            curses.wrapper(self.main)
        except KeyboardInterrupt:
            pass

    def main(self, stdscr):
        """
        Initialize curses setup and start the UI.
        """
        curses.set_escdelay(1)
        curses.curs_set(0)
        curses.init_pair(
            1,
            COLORS[config.COLOR_FOCUSED_FG],
            COLORS[config.COLOR_FOCUSED_BG],
        )
        curses.init_pair(2, COLORS[config.COLOR_WARN_FG], COLORS[config.COLOR_WARN_BG])
        curses.init_pair(
            3, COLORS[config.COLOR_NORMAL_FG], COLORS[config.COLOR_NORMAL_BG]
        )
        curses.init_pair(
            4, COLORS[config.COLOR_TAGGED_FG], COLORS[config.COLOR_TAGGED_BG]
        )
        self.COLOR_FOCUSED = curses.color_pair(1)
        self.COLOR_DELETE = curses.color_pair(2)
        self.COLOR_NORMAL = curses.color_pair(3)
        self.COLOR_TAGGED = curses.color_pair(4)

        # draw the initial screen
        self.stdscr = stdscr
        self.stdscr.refresh()
        self.rows, self.cols = stdscr.getmaxyx()

        # read data
        self.data = self.db.parse()

        while True:
            # set up the pad - this needs to be re-sized according to new content
            try:
                highest_number_of_items = max([len(c["items"]) for c in self.data])
            except ValueError:
                highest_number_of_items = 1
            column_height = max(
                self.rows, config.ITEM_HEIGHT * highest_number_of_items + 4
            )
            self.pad = curses.newpad(
                column_height, max(1, len(self.data)) * (config.COLUMN_WIDTH + 1)
            )
            self.draw_board()
            # deleted popups touch stdscr, sync it now so getch() doesn't repaint it
            self.stdscr.noutrefresh()
            self.refresh_pad()

            if self.handle_keypress() is False:
                break

    def handle_keypress(self):
        key = self.stdscr.getch()
        if (action := self.keymap.get(key)) is not None:
            return action()

    def quit(self):
        return False

    def handle_resize(self):
        """
        Erase and redraw the standard screen upon resize.
        Also update the current screen size.
        """
        self.stdscr.erase()
        # refresh the screen to get the current window size
        self.stdscr.refresh()
        self.rows, self.cols = self.stdscr.getmaxyx()

    def reload_data(self):
        self.data = self.db.parse()

    def show_shortcuts(self):
        """
        Replace the screen with a list of shortcuts until <esc> or ? is pressed.
        """
        label_width = max(len(label) for _, label, _, _ in self.shortcuts) + 2
        while True:
            self.stdscr.erase()
            self.border(self.stdscr)
            title = "Shortcuts"
            self.stdscr.addstr(
                1, max(2, self.cols // 2 - len(title) // 2), title, curses.A_BOLD
            )
            # only show as many shortcuts as fit on the screen
            shortcuts = self.shortcuts[: max(0, self.rows - 4)]
            for i, (_, label, description, _) in enumerate(shortcuts):
                line = label.ljust(label_width) + description
                self.stdscr.addstr(3 + i, 2, line[: max(0, self.cols - 4)])
            self.stdscr.refresh()

            key = self.stdscr.getch()
            if key in (27, ord("?")):
                break
            if key == curses.KEY_RESIZE:
                self.handle_resize()
        # clear the screen in case the pad is smaller than the screen
        self.stdscr.erase()

    def focus_left(self):
        self.focused_col = max(0, self.focused_col - 1)
        # if the column we jump to has less items then the one we are coming from
        self.focused_row = min(
            self.focused_row, max(0, len(self.data[self.focused_col]["items"]) - 1)
        )

    def focus_right(self):
        self.focused_col = min(max(0, len(self.data) - 1), self.focused_col + 1)
        # if the column we jump to has less items then the one we are coming from
        self.focused_row = min(
            self.focused_row, max(0, len(self.data[self.focused_col]["items"]) - 1)
        )

    def focus_up(self):
        self.focused_row = max(0, self.focused_row - 1)

    def focus_down(self):
        self.focused_row = min(
            max(0, len(self.data[self.focused_col]["items"]) - 1), self.focused_row + 1
        )

    def focus_top(self):
        self.focused_row = 0

    def focus_bottom(self):
        self.focused_row = max(0, len(self.data[self.focused_col]["items"]) - 1)

    def focus_first(self):
        self.focused_col = 0
        # if the column we jump to has less items then the one we are coming from
        self.focused_row = min(
            self.focused_row, max(0, len(self.data[self.focused_col]["items"]) - 1)
        )

    def focus_last(self):
        self.focused_col = max(0, len(self.data) - 1)
        # if the column we jump to has less items then the one we are coming from
        self.focused_row = min(
            self.focused_row, max(0, len(self.data[self.focused_col]["items"]) - 1)
        )

    def move_down(self):
        if self.focused_row < len(self.data[self.focused_col]["items"]) - 1:
            self.db.swap(self.focused_col, self.focused_row, self.focused_row + 1)
            self.focused_row += 1

    def move_up(self):
        if self.focused_row > 0:
            self.db.swap(self.focused_col, self.focused_row, self.focused_row - 1)
            self.focused_row -= 1

    def move_left(self):
        if len(self.data[self.focused_col]["items"]) == 0:
            return
        if self.focused_col > 0:
            self.db.move_to_column(
                self.focused_col, self.focused_row, self.focused_col - 1
            )
            self.focused_col -= 1
            self.focused_row = len(self.data[self.focused_col]["items"]) - 1

    def move_right(self):
        if len(self.data[self.focused_col]["items"]) == 0:
            return
        if self.focused_col < len(self.data) - 1:
            self.db.move_to_column(
                self.focused_col, self.focused_row, self.focused_col + 1
            )
            self.focused_col += 1
            self.focused_row = len(self.data[self.focused_col]["items"]) - 1

    def open_item(self):
        if len(self.data) == 0:
            return
        if len(self.data[self.focused_col]["items"]) == 0:
            return
        file = self.db.get_path(self.focused_col, self.focused_row)
        # if configured use the custom command, e.g. a popup
        if config.CMD is not None:
            subprocess.run(config.CMD.format(file), shell=True)
        # else, hand the terminal over to the editor until it is closed
        else:
            editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
            curses.endwin()
            try:
                subprocess.run([*shlex.split(editor), file])
            except FileNotFoundError:
                # the terminal is in normal mode here, so just print the error
                print(f'cardsboard: editor "{editor}" not found.')
                print("Set $VISUAL or $EDITOR, or `cmd` in the config.")
                print("Press enter to return.")
                input()
            # force a full repaint, the main loop resumes curses and redraws the board
            self.stdscr.clear()
        # reparse because new content might have been added
        self.data = self.db.parse()

    def insert_item_below(self):
        """
        Insert a new item below the focused one.
        The title can be input in a popup.
        """
        # TODO dont do this in a popup but in a new item in the column
        # don't create items if no column exists
        if len(self.data) == 0:
            return
        text = self._centered_popup()
        # don't create empty items
        if text == "":
            return
        # save item
        self.db.insert_item_below(self.focused_col, self.focused_row, text)
        if len(self.data[self.focused_col]["items"]) > 1:
            self.focused_row += 1

    def rename_item(self):
        if len(self.data) == 0 or len(self.data[self.focused_col]["items"]) == 0:
            return
        item = self.data[self.focused_col]["items"][self.focused_row]
        item["item"].erase()
        self.refresh_pad()

        popup = self.stdscr.derwin(
            config.ITEM_HEIGHT,
            config.ITEM_WIDTH,
            3 + config.ITEM_HEIGHT * self.focused_row,
            min(
                1 + (config.COLUMN_WIDTH + 1) * self.focused_col,
                self.cols - (config.COLUMN_WIDTH - 1),
            ),
        )
        popup.erase()
        self.border(popup)
        popup.bkgd(" ", self.COLOR_FOCUSED)

        textwin = popup.derwin(1, config.ITEM_WIDTH - 3, 1, 2)
        text = item["title"][: config.ITEM_WIDTH - 3]
        textwin.addstr(0, 0, text)

        textbox = Textbox(textwin, insert_mode=True)
        popup.refresh()
        curses.curs_set(1)
        new_name = textbox.edit().strip()
        curses.curs_set(0)

        if textbox.aborted:
            return
        self.db.rename_item(self.focused_col, self.focused_row, new_name)

    def rename_column(self):
        if len(self.data) == 0:
            return

        column = self.data[self.focused_col]

        popup = self.stdscr.derwin(
            config.ITEM_HEIGHT,
            config.COLUMN_WIDTH,
            0,
            min(
                (config.COLUMN_WIDTH + 1) * self.focused_col,
                # If the pad is alrger than the screen we are always at the right edge
                self.cols - config.COLUMN_WIDTH,
            ),
        )
        popup.erase()
        self.border(popup)
        popup.addch(2, 0, curses.ACS_LTEE)
        try:
            popup.addch(2, config.COLUMN_WIDTH - 1, curses.ACS_RTEE)
        except _curses.error:
            pass
        popup.bkgd(" ", self.COLOR_FOCUSED)

        textwin = popup.derwin(1, config.ITEM_WIDTH - 3, 1, 2)
        text = column["title"][: config.ITEM_WIDTH - 3]
        textwin.addstr(0, 0, text)

        textbox = Textbox(textwin, insert_mode=True)
        popup.refresh()
        curses.curs_set(1)
        new_name = textbox.edit().strip()
        curses.curs_set(0)

        if textbox.aborted:
            return
        self.db.rename_column(self.focused_col, new_name)

    def delete(self):
        key2 = self.stdscr.getch()
        if key2 == ord("d"):
            return self.delete_item()
        if key2 == ord("c"):
            return self.delete_column()

    def delete_item(self):
        item = self.data[self.focused_col]["items"][self.focused_row]["item"]
        item.erase()
        self.border(item)
        item.addstr(1, 2, "Delete? [Ny]")
        item.bkgd(" ", self.COLOR_DELETE)
        self.refresh_pad()

        key3 = self.stdscr.getch()
        if key3 == ord("y"):
            self.db.remove(self.focused_col, self.focused_row)
            self.focused_row = max(0, self.focused_row - 1)

    def delete_column(self):
        column = self.data[self.focused_col]["column"]
        column.addstr(
            1, 2, "Delete? [Ny]".center(config.COLUMN_WIDTH - 4), self.COLOR_DELETE
        )
        self.refresh_pad()

        key3 = self.stdscr.getch()
        if key3 == ord("y"):
            self.db.remove_column(self.focused_col)
            self.focused_col = max(0, self.focused_col - 1)
            self.focused_row = 0
            # clear screen in case the pad is smaller than the screen
            self.stdscr.erase()
            self.stdscr.refresh()

    def insert_column_right(self):
        # TODO dont do this in a popup but in a new item in the column
        text = self._centered_popup()
        # Don't create empty items
        if text == "":
            return
        # save item
        self.db.insert_column_right(self.focused_col, text)
        self.focused_row = 0
        if len(self.data) > 1:
            self.focused_col += 1

    def move_column_left(self):
        if self.focused_col > 0:
            self.db.swap_column(self.focused_col, self.focused_col - 1)
            self.focused_col -= 1

    def move_column_right(self):
        if self.focused_col < len(self.data) - 1:
            self.db.swap_column(self.focused_col, self.focused_col + 1)
            self.focused_col += 1

    def _centered_popup(self):
        popup = self.stdscr.derwin(
            config.ITEM_HEIGHT,
            config.ITEM_WIDTH,
            self.rows // 2 - config.ITEM_HEIGHT // 2,
            self.cols // 2 - config.ITEM_WIDTH // 2,
        )
        popup.erase()
        self.border(popup)
        popup.bkgd(" ", self.COLOR_FOCUSED)
        textwin = popup.derwin(1, config.ITEM_WIDTH - 3, 1, 2)
        textbox = Textbox(textwin, insert_mode=True)
        popup.refresh()
        # https://stackoverflow.com/questions/36121802/python-curses-make-enter-key-terminate-textbox
        curses.curs_set(1)
        text = textbox.edit().strip()
        text = text.replace("/", "|")
        curses.curs_set(0)
        popup.erase()
        popup.refresh()
        # callers don't create anything for an empty text
        if textbox.aborted:
            return ""
        return text
