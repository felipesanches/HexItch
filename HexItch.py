#!/usr/bin/env python3
#
# HexItch - hex-editor
#
# (c) 2021 Felipe Correa da Silva Sanches <juca@members.fsf.org>
# Released under the terms of the GNU General Public License version 3 or later

import curses
from pybfd3.bfd import Bfd
from pybfd3.opcodes import Opcodes
import os
import sys

PROGRAM_NAME = "HexItch"
VERSION = "v0.0.1"
RELEASE_YEAR = "2021"

context = {}
COLOR_HEADER = 1
COLOR_SUBHEADER = 2
COLOR_ADDRESS = 3
COLOR_ADDRESS_HIGHLIGHT = 4
COLOR_TEXT = 5
COLOR_TEXT_HIGHLIGHT = 6
COLOR_MENU_NUMBERS = 7
COLOR_MENU_WORDS = 8


def CodeMode(screen, cursor_x, cursor_y, height):
    if "opcodes" not in context:
       return

    context["file"].seek(context["page_address"])
    content = context["file"].read((height-5) * 10)
    dasm = context["opcodes"].disassemble(content, context["page_address"])

    offset = 0
    for line_num in range(height-5):
        if line_num == cursor_y:
            addr_color = COLOR_ADDRESS_HIGHLIGHT
            text_color = COLOR_TEXT_HIGHLIGHT
        else:
            addr_color = COLOR_ADDRESS
            text_color = COLOR_TEXT

        vma, size, instr = dasm[line_num]
        screen.addstr(3 + line_num, 0,
                      f"{vma:08X}", curses.color_pair(addr_color))
        screen.addstr(3 + line_num, 40,
                      instr, curses.color_pair(text_color))
        for i in range(size):
            screen.addstr(3 + line_num, 11 + 2*i,
                          f"{content[offset]:02X}", curses.color_pair(text_color))
            offset += 1
        


def HexMode(screen, cursor_x, cursor_y, height):
    # Draw column addresses on the top:
    for column in range(16):
        if column == cursor_x:
            addr_color = COLOR_ADDRESS_HIGHLIGHT
        else:
            addr_color = COLOR_ADDRESS
        screen.addstr(2, 11 + column*3 + int(column/4),
                      f"{column:02X}", curses.color_pair(addr_color))
        screen.addstr(2, 64 + column,
                      f"{column:1X}", curses.color_pair(addr_color))

    line_addr = context["page_address"]
    for line_num in range(height-4):
        if line_num == cursor_y:
            addr_color = COLOR_ADDRESS_HIGHLIGHT
        else:
            addr_color = COLOR_ADDRESS

        screen.addstr(3 + line_num, 0, f'{line_addr:08X}', curses.color_pair(addr_color))

        line_addr += 0x10

    # Draw file contents:
    for line_num in range(height-4):
        for column in range(16):
            if column == cursor_x and line_num == cursor_y:
                addr_color = COLOR_TEXT_HIGHLIGHT
            else:
                addr_color = COLOR_TEXT
            addr = context["page_address"] + 0x10 * line_num + column

            hex_value = "  "
            char_value = " "
            if addr < context["filesize"]:
                context["file"].seek(addr)
                value = context["file"].read(1)
                try:
                    char_value = value.decode('ascii')
                    if not char_value.isprintable():
                        char_value = "."
                except:
                    char_value = "."
                hex_value = f"{ord(value):02X}"

            screen.addstr(3 + line_num, 11 + column*3 + int(column/4),
                          hex_value, curses.color_pair(addr_color))
            screen.addstr(3 + line_num, 64 + column,
                          char_value, curses.color_pair(addr_color))


def draw_ui(screen):
    screen.clear()

    key = None
    cursor_x = 0
    cursor_y = 0

    def highlight(color):
        return color + 8

    # Start colors in curses
    curses.start_color()
    curses.init_pair(COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(COLOR_SUBHEADER, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(COLOR_ADDRESS, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_ADDRESS_HIGHLIGHT, highlight(curses.COLOR_BLUE), curses.COLOR_BLACK)
    curses.init_pair(COLOR_TEXT, highlight(curses.COLOR_BLACK), curses.COLOR_BLACK)
    curses.init_pair(COLOR_TEXT_HIGHLIGHT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_MENU_NUMBERS, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_MENU_WORDS, curses.COLOR_BLACK, curses.COLOR_CYAN)

    # Loop where `key` is the last character pressed
    while (key != ord('q')):

        # Initialization
        height, width = screen.getmaxyx()
        screen.clear()

        if key == curses.KEY_DOWN:
            cursor_y += 1
        elif key == curses.KEY_UP:
            cursor_y -= 1
        elif key == curses.KEY_RIGHT:
            cursor_x += 1
        elif key == curses.KEY_LEFT:
            cursor_x -= 1

        if cursor_x > 15:
            cursor_x = 0
            cursor_y += 1
        elif cursor_x < 0:
            if cursor_y == 0:
                if context["page_address"] > 0:
                    cursor_x = 15
                    cursor_y -= 1
                else:
                    cursor_x = 0
            else:
                cursor_x = 15
                cursor_y -= 1

        if cursor_y < 0:
            cursor_y = 0;
            if context["page_address"] > 0:
                context["page_address"] -= 0x10

        elif cursor_y > height-5:
            cursor_y = height-5;
            if context["page_address"] + (height-4) * 0x10 < context["filesize"]:
               context["page_address"] += 0x10

        context['address'] = context["page_address"] + cursor_y * 0x10 + cursor_x

        if context['address'] >= context["filesize"]:
            cursor_x = context["filesize"] % 16
            context['address'] = context['filesize']

        # Rendering some text
        percentage = 100*context['address']/context['filesize']
        percentage = f"{percentage:.1f}%"
        header_str = f"Selected : 00000000h - -= {PROGRAM_NAME} {VERSION} GPLv3+ Felipe Sanches {RELEASE_YEAR} =- - 0  -   {context['filesize_formatted']}"
        subheader_str = f"{context['address']:08X}/{context['filesize_hex']}  Hex      {percentage}   {context['filename']}"

        def pad_str(s, width):
            return s + " " * (width - len(s) - 1)

        screen.addstr(0, 0, pad_str(header_str, width), curses.color_pair(COLOR_HEADER))
        screen.addstr(1, 0, pad_str(subheader_str, width), curses.color_pair(COLOR_SUBHEADER))
        screen.addstr(2, 0, "<Active>", curses.color_pair(COLOR_ADDRESS_HIGHLIGHT))

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


        CodeMode(screen, cursor_x, cursor_y, height)
        # HexMode(screen, cursor_x, cursor_y, height)

        # Draw blinking cursor
        screen.move(3 + cursor_y, 11 + cursor_x*3 + int(cursor_x/4))

        # Wait for next input
        key = screen.getch()

        # Refresh the screen
        screen.refresh()


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
    context["filesize"] = os.path.getsize(filename)
    context["filesize_formatted"] = format_filesize(context["filesize"])
    context["filesize_hex"] = f'{context["filesize"]:08X}'
    context["address"] = 0x00000000
    context["page_address"] = 0x00000000
    try:
        bfd = Bfd(filename)
        section = bfd.sections.get(".text")
        context["bfd"] = bfd
        context["section"] = section
        context["opcodes"] = Opcodes(bfd)
        context["page_address"] = bfd.start_address
    except:
        pass


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <filename>")
    else:
        load_file(sys.argv[1])
        curses.wrapper(draw_ui)

if __name__ == "__main__":
    main()

