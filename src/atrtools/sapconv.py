"""
This is converter of indexed gif files (1-8 colors) to Atari .asm data file.
Requires pillow package to be installed.
"""

import os
import re
import argparse
import logging
import itertools
from collections import namedtuple

RGX = re.compile(r'([A-Z]*)\s"?([^"]*)')
MusicData = namedtuple('MucicData', 'address_start address_end music_data')


def log():
	return logging.getLogger(__name__)

    
class AtariSAPConverter:
    "Atari SAP Converter class"
    
    def __init__(self, args):
        self.args=args
        self.sap=args.source.read()
        self.header = {}
        self.labels = {}
        self.data = []

    def process(self):
        log().debug('Processing music data')
        assert self.sap[0:3] == b'SAP', 'This is not a SAP file!'
        index = self.sap.index(b'\xff\xff')

        if self.args.verbose:
            print("Binary index: %d" % index)
            print("Binary data total length: %d" % len(self.sap))
        logging.debug("Binary index: %d", index)
        logging.debug("Binary data total length: %d", len(self.sap))

        header = self.sap[0: index].decode()
        for line in header.split('\r\n'):
            match = RGX.match(line)
            if match:
                k = match.group(1).upper()
                v  = match.group(2).upper()
                if k == 'TYPE':
                    assert v == 'B', 'Type {} is not supported'.format(v)
                if k in self.args.labels:
                    self.labels[k] = v
                else:
                    self.header[k] = v
        index +=2

        for label in self.labels:
                logging.debug("%s: %s", label, self.labels[label])
                if self.args.verbose:
                    print("{}: {}".format(label, self.labels[label]))
        for header in self.header:
                logging.debug("%s: %s", header, self.header[header])
                if self.args.verbose:
                    print("{}: {}".format(header, self.header[header]))

        while True:
            beg_byte_low, beg_byte_high = self.sap[index:index+2]
            index += 2
            end_byte_low, end_byte_high = self.sap[index:index+2]
            index += 2
            address_start = "{:02x}{:02x}".format(beg_byte_high, beg_byte_low)
            address_end = "{:02x}{:02x}".format(end_byte_high, end_byte_low)
            size_bytes = (end_byte_high*256+end_byte_low)-(beg_byte_high*256+beg_byte_low)
            if self.args.verbose:
                print("Start address: $%s" % address_start)
                print("End address: $%s" % address_end)
                print("Size: $%04x" % size_bytes)
            logging.debug("Start address: $%s", address_start)
            logging.debug("End address: $%s", address_end)
            logging.debug("Size: $%04x", size_bytes)
 
            self.data.append(MusicData(address_start=address_start,
                                       address_end=address_end, 
                                       music_data=self.sap[index: index+size_bytes+1]))
            index += size_bytes
            if index == len(self.sap)-1:
                break

    def generate_music_data(self, data):
        log().debug('Generating music data')
        buf = []
        for i in data:
            buf.append(i)
            if len(buf)==20:
                bts = ['${:02x}'.format(n) for n in buf]
                yield ".byte {}".format(','.join(bts))
                buf = []
        if buf:
            bts = ['${:02x}'.format(n) for n in buf]
            yield ".byte {}".format(','.join(bts))

    def __write(self, value):
        self.args.destination.write(("{}{}".format(value, os.linesep)).encode())

    def __save_asm(self):
        "Save asm file"
        for k in self.labels:
                self.__write('SAP_MUSIC_{} = ${}'.format(k, self.labels[k]))
        self.__write("\n\t.local sap_music_header")
        for k in self.header:
                self.__write('{}\t.byte "{}"'.format(k, self.header[k]))
        self.__write("\t.endl")

        for idx, data in enumerate(self.data):
            self.__write("\n\torg ${}\n".format(data.address_start))
            self.__write("\t.local sap_music_data{} ; start=${}, end=${}".format(idx, data.address_start, 
                                                                 data.address_end))
            gen_data = self.generate_music_data(data.music_data)
            for row in gen_data:
                self.__write("\t{}".format(row))
            self.__write("\t.endl")

    def __save_bin(self):
        "Save binary file"  
        for _, data in enumerate(self.data):
            self.args.destination.write(data.music_data)

    def save(self):
        "Save music"
        log().debug('Saving music data to file')
        if self.args.type == 'asm':
            self.__save_asm()
        elif self.args.type == 'bin':
            self.__save_bin()

def add_parser_args(parser):
    "Add cli arguments to parser"
    parser.add_argument('-s', '--source', type=argparse.FileType('rb'), help='path to source sap file', required=True)
    parser.add_argument('-d', '--destination', type=argparse.FileType('wb'), help='path to destination asm file', required=True)
    parser.add_argument('-l', '--labels', nargs='+', default=['INIT', 'PLAYER'], help='labelled header keys', required=False)
    parser.add_argument('-t', '--type', choices=('asm', 'binary'), help='select output type', default='asm')
    parser.add_argument('-e', '--verbose', action='store_true', help='generate more verbose output')

def get_parser():
    "Create parser and add cli arguments"
    parser = argparse.ArgumentParser()
    add_parser_args(parser)
    return parser

def process(args):
    "Main processing"
    log().debug("Start processing")
    sap_converter = AtariSAPConverter(args)
    sap_converter.process()
    sap_converter.save()
    log().debug("Done")

def main():
    "Parse arguments and process data"
    parser = get_parser()
    args = parser.parse_args()
    process(args)

if __name__ == '__main__':
    main()
