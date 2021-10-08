#!/usr/bin/env python3
#
# HexItch - hex-editor
#
# (c) 2021 Felipe Correa da Silva Sanches <juca@members.fsf.org>
# Released under the terms of the GNU General Public License version 3 or later

import curses
import os
import sys

PROGRAM_NAME = "HexItch"
VERSION = "v0.0.1"
RELEASE_YEAR = "2021"

context = {
    "file": None,
    "filesize_formatted": None,
    "filesize_hex": None,
    "address": None,
    "page_address": None
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
    curses.init_pair(COLOR_ADDRESS_HIGHLIGHT, curses.COLOR_CYAN, curses.COLOR_BLACK)
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
        percentage = 100*context['address']/context['filesize']
        percentage = f"{percentage:.1f}%"
        header_str = f"Selected : 00000000h - -= {PROGRAM_NAME} {VERSION} GPLv3+ Felipe Sanches {RELEASE_YEAR} =- - 0  -   {context['filesize_formatted']}"
        subheader_str = f"{context['address']}/{context['filesize_hex']}  Hex      {percentage}   {context['filename']}"

        def pad_str(s, width):
            return s + " " * (width - len(s) - 1)

        screen.addstr(0, 0, pad_str(header_str, width), curses.color_pair(COLOR_HEADER))
        screen.addstr(1, 0, pad_str(subheader_str, width), curses.color_pair(COLOR_SUBHEADER))

        line_addr = context["page_address"]
        for line_num in range(2,height-2):
            if line_num == cursor_y:
                addr_color = COLOR_ADDRESS_HIGHLIGHT
            else:
                addr_color = COLOR_ADDRESS

            screen.addstr(line_num, 0, f'{line_addr:08X}', curses.color_pair(addr_color))
            line_addr += 16


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


def format_filesize(size):
    if size > 1024*1024*1024:
        return f"{size/(1024*1024*1024):.1f}G"
    elif size > 1024*1024:
        return f"{size/(1024*1024):.1f}M"
    elif size > 1024:
        return f"{size/1024:.1f}k"
    else:
        return size


def load_file(filename):
    context["filename"] = filename
    context["file"] = open(filename, "rb")
    context["filesize"] = os.path.getsize(context["filename"])
    context["filesize_formatted"] = format_filesize(context["filesize"])
    context["filesize_hex"] = f'{context["filesize"]:08X}'
    context["address"] = 0x00000000
    context["page_address"] = 0x00000000


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
    else:
        load_file(sys.argv[1])
        curses.wrapper(draw_ui)

if __name__ == "__main__":
    main()

