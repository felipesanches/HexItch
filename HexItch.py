#!/usr/bin/env python3
#
# HexItch - hex-editor
#
# Copyright 2021 Felipe Correa da Silva Sanches <juca@members.fsf.org>
# Copyright 2021 Ismael Luceno <ismael@iodev.co.uk>
# Released under the terms of the GNU General Public License version 3 or later

import curses
from pybfd3.bfd import Bfd
from pybfd3.opcodes import Opcodes
import os
import sys

PROGRAM_NAME = "HexItch"
VERSION = "v0.0.1"
RELEASE_YEAR = "2021"

COLOR_HEADER = 1
COLOR_SUBHEADER = 2
COLOR_ADDRESS = 3
COLOR_ADDRESS_HIGHLIGHT = 4
COLOR_TEXT = 5
COLOR_TEXT_HIGHLIGHT = 6
COLOR_MENU_NUMBERS = 7
COLOR_MENU_WORDS = 8


class HexItchContext:
    def __init__(self):
        self.filename = None
        self.cursor_x = None
        self.cursor_y = None
        self.file = None
        self.filesize = None
        self.filesize_hex = None
        self.filesize_formatted = None
        self.page_address = None
        self.address = None
        self.term_height = None
        self.term_width = None

context = HexItchContext()

class SaveExcursion:
    def __init__(self, curses_scr):
        self.scr = curses_scr
    def __enter__(self):
        self.y, self.x = self.scr.getyx()
    def __exit__(self, type, value, traceback):
        self.scr.move(self.y, self.x)


class FileWindow():
    def __init__(self, file_obj):
        self.address = 0
        self.cursor_pos = 0
        self.file_obj = file_obj


class Motion():
    UP    = curses.KEY_UP
    DOWN  = curses.KEY_DOWN
    LEFT  = curses.KEY_LEFT
    RIGHT = curses.KEY_RIGHT


def move_cursor(ctx, mode, motion):
    if motion in mode.navigation:
        ctx.cursor_x += mode.navigation[motion]()
        if ctx.cursor_x not in range(0, mode.line_len):
            ctx.cursor_y += ctx.cursor_x // mode.line_len - (ctx.cursor_x < 0)
            ctx.cursor_x %= mode.line_len
            if ctx.cursor_y < 0:
                ctx.cursor_y = 0;
                if ctx.page_address > 0:
                    ctx.page_address -= mode.line_len
            elif ctx.cursor_y > ctx.term_height - 5:
                ctx.cursor_y = ctx.term_height - 5;
                if ctx.page_address + (ctx.term_height - 4) * mode.line_len < ctx.filesize:
                    ctx.page_address += mode.line_len
                    ctx.address = ctx.page_address + ctx.cursor_y * mode.line_len + ctx.cursor_x
        if ctx.address >= ctx.filesize:
            ctx.cursor_x = ctx.filesize % mode.line_len


class CodeMode():
    def __init__(self):
        self.navigation = {
            Motion.UP:    (lambda: -self.x - self.prev_line_len),
            Motion.DOWN:  (lambda: self.line_len - self.x),
            Motion.LEFT:  (lambda: -1 if self.x > 0 else 0),
            Motion.RIGHT: (lambda: 1 if self.x < self.line_len else 0),
        }

    def run(self, screen, key):
        if "opcodes" not in context:
            return

        context.file.seek(context.page_address)
        content = context.file.read((context.term_height - 5) * 10)
        dasm = context.opcodes.disassemble(content, context.page_address)

        move_cursor(context, self, key)

        vma, instr_size, instr = dasm[context.cursor_y]
        context.address = context.page_address + context.cursor_y * 0x10 + context.cursor_x

        offset = 0
        for line_num in range(context.term_height - 3):
            if line_num == context.cursor_y:
                addr_color = COLOR_ADDRESS_HIGHLIGHT
                disasm_color = COLOR_TEXT_HIGHLIGHT
            else:
                addr_color = COLOR_ADDRESS
                disasm_color = COLOR_TEXT

            vma, size, instr = dasm[line_num]
            screen.addstr(2 + line_num, 0,
                        f"{vma:08X}", curses.color_pair(addr_color))
            screen.addstr(2 + line_num, 40,
                        instr, curses.color_pair(disasm_color))
            for i in range(size):
                if line_num == context.cursor_y and i == context.cursor_x:
                    text_color = COLOR_TEXT_HIGHLIGHT
                else:
                    text_color = COLOR_TEXT

                screen.addstr(2 + line_num, 10 + 2*i,
                            f"{content[offset]:02X}", curses.color_pair(text_color))
                offset += 1

        # Draw blinking cursor
        screen.move(2 + context.cursor_y, 10 + context.cursor_x*2)

class HexMode():
    def __init__(self):
        self.line_len = 16
        self.navigation = {
            Motion.UP:    (lambda: -self.line_len),
            Motion.DOWN:  (lambda: self.line_len),
            Motion.LEFT:  (lambda: -1),
            Motion.RIGHT: (lambda: 1),
        }

    def run(self, screen, key):
        move_cursor(context, self, key)

        # Draw column addresses on the top:
        for column in range(16):
            if column == context.cursor_x:
                addr_color = COLOR_ADDRESS_HIGHLIGHT
            else:
                addr_color = COLOR_ADDRESS
            screen.addstr(2, 11 + column*3 + int(column/4),
                        f"{column:02X}", curses.color_pair(addr_color))
            screen.addstr(2, 64 + column,
                        f"{column:1X}", curses.color_pair(addr_color))

        line_addr = context.page_address
        for line_num in range(context.term_height - 4):
            if line_num == context.cursor_y:
                addr_color = COLOR_ADDRESS_HIGHLIGHT
            else:
                addr_color = COLOR_ADDRESS

            screen.addstr(3 + line_num, 0, f'{line_addr:08X}', curses.color_pair(addr_color))

            line_addr += 0x10

        # Draw file contents:
        for line_num in range(context.term_height - 4):
            for column in range(16):
                if column == context.cursor_x and line_num == context.cursor_y:
                    addr_color = COLOR_TEXT_HIGHLIGHT
                else:
                    addr_color = COLOR_TEXT
                addr = context.page_address + 0x10 * line_num + column

                hex_value = "  "
                char_value = " "
                if addr < context.filesize:
                    context.file.seek(addr)
                    value = context.file.read(1)
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
        # Draw blinking cursor
        screen.move(3 + context.cursor_y, 11 + context.cursor_x*3 + int(context.cursor_x/4))


def draw_ui(screen):
    screen.clear()

    key = None
    context.cursor_x = 0
    context.cursor_y = 0

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

    mode = HexMode()
    #mode = CodeMode()
    # Loop where `key` is the last character pressed
    while (key != ord('q')):

        # Initialization
        context.term_height, context.term_width = screen.getmaxyx()
        screen.clear()

        mode.run(screen, key)

        # Rendering some text
        percentage = 100*context.address/context.filesize
        percentage = f"{percentage:.1f}%"
        header_str = f"Selected : 00000000h - -= {PROGRAM_NAME} {VERSION} GPLv3+ Felipe Sanches {RELEASE_YEAR} =- - 0  -   {context.filesize_formatted}"
        subheader_str = f"{context.address:08X}/{context.filesize_hex}  Hex      {percentage}   {context.filename}"

        def pad_str(s, width):
            return s + " " * (width - len(s) - 1)

        with SaveExcursion(screen):
            screen.addstr(0, 0, pad_str(header_str, context.term_width), curses.color_pair(COLOR_HEADER))
            screen.addstr(1, 0, pad_str(subheader_str, context.term_width), curses.color_pair(COLOR_SUBHEADER))
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
                screen.addstr(context.term_height - 1, x,
                              number, curses.color_pair(COLOR_MENU_NUMBERS))
                x += len(number)
                screen.addstr(context.term_height - 1, x,
                              text, curses.color_pair(COLOR_MENU_WORDS))
                x += len(text)

            screen.addstr(context.term_height - 1, x,
                          " " * (context.term_width - x - 1),
                          curses.color_pair(COLOR_MENU_WORDS))
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
    context.filename = filename
    context.file = open(filename, "rb")
    context.filesize = os.path.getsize(filename)
    context.filesize_formatted = format_filesize(context.filesize)
    context.filesize_hex = f'{context.filesize:08X}'
    context.address = 0x00000000
    context.page_address = 0x00000000
    try:
        context.bfd = Bfd(filename)
        context.opcodes = Opcodes(context.bfd)
        context.page_address = context.bfd.start_address
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

