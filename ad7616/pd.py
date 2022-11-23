##
## This file is part of the libsigrokdecode project.
##
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

import sigrokdecode as srd

class Decoder(srd.Decoder):
    api_version = 3
    id = 'ad7616'
    name = 'AD7616'
    longname = 'Analog Devices AD7616'
    desc = 'Analog Devices AD7616 16-bit ADC.'
    license = 'gplv2+'
    inputs = ['spi']
    outputs = []
    tags = ['IC', 'Analog/digital']
    annotations = (
        ('voltage', 'Voltage'), # 0
        ('control', 'Control'), # 1
    )
    annotation_rows = (
         ('mosi', 'MOSI', (1,)),
         ('miso', 'MISO', (0,)),
    )
    RANGE_2_5V = '+/- 2.5V'
    RANGE_5V = '+/- 5.0V'
    RANGE_10V = '+/- 10V'
    options =  (
        {'id': 'range', 'desc': 'Voltage Range:', 'default': RANGE_5V, 'values': (RANGE_2_5V, RANGE_5V, RANGE_10V)},
    )

    range_display = ('10V', '2.5V', '5V', '10V')
    range_reg_display = ('Range A: Ch3-0', 'Range A: Ch7-4', 'Range B: Ch3-0', 'Range B: Ch7-4')

    def __init__(self,):
        self.reset()

    def reset(self):
        self.miso = 0
        self.mosi = 0
        self.ss = None
        self.has_mosi = False
        self.has_miso = False


    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode(self, ss, es, data):
        ptype = data[0]
        if self.options['range'] == Decoder.RANGE_2_5V:
            self.range = 2.5
        elif self.options['range'] == Decoder.RANGE_5V:
            self.range = 5.
        else:
            self.range = 10.


        if ptype == 'CS-CHANGE':
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 0 and cs_new == 1:
                if self.has_miso:
                    self.miso >>= 1
                    volts = self.miso * self.range
                    volts /= 32767
                    self.put(self.ss, self.es, self.out_ann, [0, ['%.3fV' % volts]])

                if self.has_mosi:
                    self.mosi >>=1
                    ctl_reg = (self.mosi >> 9) & 0x3F
                    if ctl_reg == 3:
                        cha = self.mosi & 0x0F
                        chb = (self.mosi >> 4) & 0x0F
                        self.put(self.ss, self.ss+(self.bit_width*8), self.out_ann, [1, ['Ch Sel (%02x)' % ctl_reg]])
                        self.put(self.ss+(self.bit_width*8), self.ss+(self.bit_width*12), self.out_ann, [1, ['ChB:%02x' % chb]])
                        self.put(self.ss+(self.bit_width*12), self.ss+(self.bit_width*16), self.out_ann, [1, ['ChA:%02x' % cha]])
                    elif ctl_reg >= 4 and ctl_reg <= 7:
                        self.put(self.ss, self.ss+(self.bit_width*8), self.out_ann, [1, [Decoder.range_reg_display[ctl_reg-4]]])
                        for i in range(4):
                            rng_ss = self.ss+(self.bit_width*8)
                            rng = (self.mosi >> 6-(i*2)) &0x03

                            self.put(rng_ss+(self.bit_width*2*i), 
                                rng_ss+(self.bit_width*2*(i+1)), 
                                self.out_ann, 
                                [1, [Decoder.range_display[rng]]]
                            )

                self.miso = 0
                self.mosi = 0
                self.ss = None

        elif ptype == 'BITS':
            mosi = data[1]
            miso = data[2]
            self.has_mosi = mosi != None
            self.has_miso = miso != None

            self.es = es
            if self.ss == None:
                self.ss = ss

            if self.has_miso:
                self.bit_width = (es - ss) // len(miso)
                for bit in reversed(miso):
                    self.miso = self.miso | bit[0]
                    self.miso <<= 1

            if self.has_mosi:
                self.bit_width = (es - ss) // len(mosi)
                for bit in reversed(mosi):
                    self.mosi = self.mosi | bit[0]
                    self.mosi <<= 1
