#!/usr/bin/env python3
import re, sys


debug = False


class Store():
    LIVESTOCK   = ['BOS', 'OVIS', 'CAP']
    AGRICULTURE = ['FIC', 'OLIV', 'GRA']
    LIQUID      = ['VIN', 'OLE']
    location    = 'Knossos'
    # storage cells  [] of {'type': NNN, 'v': <int>, 'f': <fraction>}
    storage = []
    ptr = 0

    def __repr__(self):
        return "%s Store: %s <%d>" % (self.location, self.storage, self.ptr)

    def current_commodity(self):
        if self.ptr >= len(self.storage):
            return
        return self.storage[self.ptr].get('type')

    def store(self, commodity, value, deficit=False):
        if self.current_commodity() is None:
            rmax = self.ptr - len(self.storage) + 1
            for i in range(rmax):
                self.storage.append({})
            self.storage[self.ptr] = {'type': commodity, 'v': value}
        elif self.current_commodity() == commodity:
            self.storage[self.ptr]['v'] += value
        else:
            # move pointer
            self.move_pointer(commodity)
            self.store(commodity, value, deficit)

    def move_pointer(self, commodity):
        """ shifts the current ptr based on the current, existing, and new commodity types"""
        # have we seen this commodity?
        if commodity in [cell['type'] for cell in self.storage]:
            self.ptr = [ n for n,cell in enumerate(self.storage) if cell['type'] == commodity][0]
        elif self.gtr_than(commodity, self.current_commodity()):
            self.ptr += 1
        else:
            self.ptr -= 1 # TODO: this needs more loging

    def gtr_than(self, a, b):
        """ returns True if commodities a > b"""
        if debug:
            print("CHECK - %s > %s ?" % (a, b))
        if b in self.LIVESTOCK:
            return a in self.AGRICULTURE
        if b in self.AGRICULTURE:
            return a in self.LIQUID
        if b in self.LIQUID:
            return a in self.LIVESTOCK
        return False

    def get_current_value(self):
        return self.storage[self.ptr].get('v')

    def set_store_value(self, v):
        self.storage[self.ptr]['v'] = v


class Tablet():
    pointer = 0
    obverse = []
    reverse = []
    active = True

    def __init__(self, data):
        reverse = False
        for line in data.readlines():
            if line.strip():
                if line.startswith('A-DU'):
                    print(line.replace('A-DU', '\U00010607\U0001062C'))
                    continue
                elif 'U-MI-NA-SI' in line:
                    reverse = True
                    continue
                cells = [cell.strip() for cell in line.rstrip().split("\t")]
                if reverse:
                    self.reverse.append(cells)
                else:
                    self.obverse.append(cells)

    def get_line(self):
        return self.obverse[self.pointer]


def main():
    adu_file = sys.argv[1]
    debug = len(sys.argv) > 2
    with open(adu_file, 'r') as f:
        tablet = Tablet(f)

        inbuffer = ''

        names = {}
        last_name = ''
        store = Store()
        looped = False

        while tablet.active:
            d = tablet.get_line()
            if debug:
                print("DEBUG: %d > %s | %s --  %s" % (tablet.pointer, tablet.obverse, tablet.reverse, store))

            # input
            if d[0] == 'KI-RO':
                inbuffer = input('\U00010638\U00010601  ')
                if not inbuffer.strip():
                    continue
                try:
                    store.set_store_value(int(inbuffer))
                except ValueError:
                    store.set_store_value(ord(inbuffer[0]))
            # output and total check for looping
            elif 'KU-RO' in d[0]:
                if len(d) > 1 and d[1].strip(): # we have a commodity to move ptr to
                    store.move_pointer(d[1])
                out = store.get_current_value()
                total = 0 if len(d) < 3 else int(d[2])
                if total != out:
                    # TODO: a not equal KU-RO should loop back to last commodity introdction?
                    #     rather than the NAME? Looping back to name is simpler for now
                    if debug:
                        print(" !! %d != %d" % (total, out))
                        print(names[last_name])
                    tablet.pointer = names[last_name]
                if d[0] != 'PO-TO-KU-RO':
                    print(chr(out), end='')
                else:
                    print(out)

            elif not d[0].strip() and len(d) > 1:
                if len(d) > 3:
                    store.store(d[3], -1 * int(d[4]))
                else:
                    store.store(d[1], int(d[2]))
            # Name:
            else:
                last_name = d[0]
                names[d[0]] = tablet.pointer
                if debug:
                    print("NAME: %s" % d)
                if len(d) == 3:
                    store.store(d[1], int(d[2]))

            tablet.pointer += 1

            if tablet.pointer >= len(tablet.obverse):
                # check if there is a block on the reverse we need to run
                if tablet.reverse and looped == False:
                    looped = True
                    deficit_block = tablet.reverse
                    deficit_block[0][0] = '' # clear the name, we already have it on the obverse
                    deficit_block[0][2] = '-' + deficit_block[0][2]
                    tablet.obverse += deficit_block
                    continue
                # check if last line whether we should loop
                if debug:
                    print(" %s" % d)
                print()
                total = 0 if len(d) < 3 else int(d[2])
                if store.get_current_value() != total:
                    tablet.pointer = names[last_name]
                else:
                    tablet.active = False


if __name__ == '__main__':
    main()
