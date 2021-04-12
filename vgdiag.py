#!/usr/bin/env python3
"""
vgdiag by Alexis CHERON

https://github.com/norech/vgdiag
"""

import sys
import os
import subprocess
import re

subprocess_command = ['valgrind'] + sys.argv[1:]

def parse_size_number(size):
    return int(size.replace(",", ""))

def print_log(arg, **kwargs):
    if len(arg) > 0:
        print("==" + str(os.getpid()) + "== > " + arg, file=sys.stderr, **kwargs)
    else:
        print("==" + str(os.getpid()) + "== " + arg, file=sys.stderr, **kwargs)

def give_equivalent_size(size):
    print_log(str(size) + " bytes usually correspond to one of these primitive types: ")
    if size == 1:
        print_log("  - bool")
    if size == 1:
        print_log("  - char")
    if size == 2:
        print_log("  - short")
    if size == 2 or size == 4:
        print_log("  - int")
    if size == 4:
        print_log("  - float")
    if size == 4:
        print_log("  - long (on 32bit systems)")
    if size == 8:
        print_log("  - long")
    if size == 8:
        print_log("  - double")
    if size == 10:
        print_log("  - long double")
    if size >= 8 and size <= 10:
        print_log("  - pointer")
    print_log("but it may also correspond to an array of smaller elements")
    print_log("or a structure, or any other kind of memory allocation")

def check_address(address):
    if address == 0:
        print_log("Address is NULL. Looks like a NULL pointer!")
    elif address < 10000:
        print_log("Address seems suspiciously small (" + str(address) + " in decimal).")
        print_log("It may imply an access to an array element or a structure")
        print_log("property using a NULL pointer?")
        print_log("Or maybe arithmetics with a NULL pointer?")

def scan_invalid_read_or_write(output):
    err = re.search('Invalid (read|write) of size ([0-9,]+)', output)
    if err:
        action = err.group(1)
        size = parse_size_number(err.group(2))
        overflow_expr = re.search('Address 0x([0-9A-Fa-f]+) is ([0-9,]+) bytes (before|after) (a block|an unallocated block) of size ([0-9,]+)', output)
        if overflow_expr:
            block_size = parse_size_number(overflow_expr.group(5))
            array_size = block_size // size
            incorrect_offset = parse_size_number(overflow_expr.group(2))
            before_or_after = overflow_expr.group(3)
            if before_or_after == "before":
                index = -incorrect_offset // size
            else:
                index = incorrect_offset // size + block_size // size
            print_log("It may be the result of an out of bounds.")
            if overflow_expr.group(4) != "an unallocated block":
                print_log(" ")
                print_log("In the case of an array (with " + str(size) + " bytes wide elements):")
                print_log("  Array size: " + str(array_size))
                print_log("  Invalid index: " + str(index) + " (" + str(incorrect_offset // size + (0 if before_or_after == "before" else 1)) + " elements " + before_or_after + " the bound)")
                if block_size % size != 0:
                    print_log("  WARNING: Array size is not round. If this is an array, have you allocated the correct size?")
                if incorrect_offset % size != 0:
                    print_log("  WARNING: Offset does not represent a whole element.")
        address_expr = re.search('Address 0x([0-9A-Fa-f]+) is', output)
        if address_expr:
            address = int(address_expr.group(1), 16)
            check_address(address)
            print_log(" ")
            give_equivalent_size(size)

def scan_general_protection_fault(output):
    err = re.search('General Protection Fault', output)
    if err:
        print_log("You may have statically allocated an array so big that it")
        print_log("overflown the heap.")

def scan_bad_permissions(output):
    err = re.search('Bad permissions for mapped region at address 0x([0-9A-F]+)', output)
    if err:
        print_log("You may have overflown the heap or tried to write on a read-only value.")
        print_log("In the case of a read-only value, you can only write on a copy.")
        address = int(err.group(1), 16)
        check_address(address)

def scan_access_not_within_mapped_region(output):
    err = re.search('Access not within mapped region at address 0x([0-9A-F]+)', output)
    if err:
        print_log("It may be the result of an access to a failed heap allocation")
        print_log("or a NULL pointer.")
        address = int(err.group(1), 16)
        check_address(address)

def scan_block(output):
    scan_access_not_within_mapped_region(output)
    scan_bad_permissions(output)
    scan_general_protection_fault(output)
    scan_invalid_read_or_write(output)

is_valgrind_block = True
valgrind_block = ""

p = subprocess.Popen(subprocess_command, stdin=sys.stdin, stdout=sys.stdout, stderr=subprocess.PIPE, env=os.environ)
for line in iter(p.stderr.readline, b''):
    line = line.decode('ascii')
    prefix = "==" + str(p.pid) + "== "
    pos = line.find(prefix)
    startoffset = pos + len(prefix)
    if pos == -1 or line[pos + len(prefix)] == "\n":
        if pos != -1:
            print(line, file=sys.stderr, end="")
        if is_valgrind_block:
            is_valgrind_block = False
            print("\n".join(prefix + a for a in valgrind_block.split("\n")), file=sys.stderr, end="")
            print_log("")
            scan_block(valgrind_block)
            valgrind_block = ""
        print(line, file=sys.stderr, end="")
    else:
        is_valgrind_block = True
        valgrind_block += str(line[startoffset:])
