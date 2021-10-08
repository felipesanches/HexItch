import curses
import os
import sys

PROGRAM_NAME = "HexItch"
VERSION = "v0.0.1"
RELEASE_YEAR = "2021"

context = {
    "filesize": "14532k", #FIXME
    "filesize_hex": "000830F6", #FIXME
    "filename": "~/nonfree/MSDOS/GAMES/PFANT/TABLE1.PRG",
    "address": 0x00000000,
    "page_address": 0x00000000
}

def draw_ui(screen):
    key = None
    cursor_x = 0
    cursor_y = 2

    # Clear and refresh the screen for a blank canvas
    screen.clear()
    screen.refresh()

    COLOR_HEADER = 1
    COLOR_SUBHEADER = 2
    COLOR_ADDRESS = 3
    COLOR_ADDRESS_HIGHLIGHT = 4
    COLOR_TEXT = 5
    COLOR_TEXT_HIGHLIGHT = 6
    COLOR_MENU_NUMBERS = 7
    COLOR_MENU_WORDS = 8

    # Start colors in curses
    curses.start_color()
    curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(COLOR_SUBHEADER, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(COLOR_ADDRESS, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_ADDRESS_HIGHLIGHT, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_TEXT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_TEXT_HIGHLIGHT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_MENU_NUMBERS, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_MENU_WORDS, curses.COLOR_BLACK, curses.COLOR_CYAN)

    # Loop where `key` is the last character pressed
    while (key != ord('q')):

        # Initialization
        screen.clear()
        height, width = screen.getmaxyx()

        if key == curses.KEY_DOWN:
            cursor_y = cursor_y + 1
        elif key == curses.KEY_UP:
            cursor_y = cursor_y - 1
        elif key == curses.KEY_RIGHT:
            cursor_x = cursor_x + 1
        elif key == curses.KEY_LEFT:
            cursor_x = cursor_x - 1

        cursor_x = max(0, cursor_x)
        cursor_x = min(width-1, cursor_x)

        cursor_y = max(0, cursor_y)
        cursor_y = min(height-1, cursor_y)

        # Rendering some text
        header_str = f"Selected : 00000000h - -= {PROGRAM_NAME} {VERSION} GPLv3+ Felipe Sanches {RELEASE_YEAR} =- - 0  -   {context['filesize']}"
        subheader_str = f"{context['address']}/{context['filesize_hex']}  Hex        0%   {context['filename']}"

        def pad_str(s, width):
            return s + " " * (width - len(s) - 1)

        screen.addstr(0, 0, pad_str(header_str, width), curses.color_pair(COLOR_HEADER))
        screen.addstr(1, 0, pad_str(subheader_str, width), curses.color_pair(COLOR_SUBHEADER))

        # Render menu bar
        menu = { "1": "Info  ",
                " 2": "Save  ",
                " 3": "File  ",
                " 4": "Mode  ",
                " 5": "Goto  ",
                " 6": "Header",
                " 7": "Search",
                " 8": "Replac",
                " 9": "CalcIt",
                "10": "      "}
        x = 0
        for number, text in menu.items():
            screen.addstr(height - 1, x,
                          number, curses.color_pair(COLOR_MENU_NUMBERS))
            x += len(number)
            screen.addstr(height - 1, x,
                          text, curses.color_pair(COLOR_MENU_WORDS))
            x += len(text)

        screen.addstr(height - 1, x,
                      " " * (width - x - 1), curses.color_pair(COLOR_MENU_WORDS))

        screen.move(cursor_y, cursor_x)

        # Refresh the screen
        screen.refresh()

        # Wait for next input
        key = screen.getch()

def main():
    curses.wrapper(draw_ui)

if __name__ == "__main__":
    main()

