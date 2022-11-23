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
        ('voltage', 'Voltage'),
    )

    def __init__(self,):
        self.reset()

    def reset(self):
        self.data = 0
        self.ss = None

    def start(self):
        self.out_ann = self.register(srd.OUTPUT_ANN)

    def decode(self, ss, es, data):
        ptype = data[0]

        if ptype == 'CS-CHANGE':
            cs_old, cs_new = data[1:]
            if cs_old is not None and cs_old == 0 and cs_new == 1:
                self.data >>= 1
                volts = self.data * 5 # Assume +-5V range
                volts /= 32767
                self.put(self.ss, self.es, self.out_ann, [0, ['%.3fV' % volts]])
                self.data = 0
                self.ss = None
        elif ptype == 'BITS':
            miso = data[2]
            self.es = es
            if self.ss == None:
                self.ss = ss
            for bit in reversed(miso):
                self.data = self.data | bit[0]
                self.data <<= 1
