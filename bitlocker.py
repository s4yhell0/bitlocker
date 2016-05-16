# Volatility plugin: bitlocker
#
# Author:
# Marcin Ulikowski <marcin@ulikowski.pl>
#
# Based on the research by:
# Jesse Kornblum <research@jessekornblum.com>
#
# Special thanks:
# Piotr Chmylkowski <piotr.chmylkowski@gmail.com>
# Romain Coltel <romain.coltel@hsc.fr>
#
# This plugin is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this plugin.  If not, see <http://www.gnu.org/licenses/>.


import os
import volatility.plugins.common as common
import volatility.utils as utils
import volatility.obj as obj
import volatility.poolscan as poolscan
import volatility.debug as debug


class bitlocker(common.AbstractWindowsCommand):
    '''Extracts BitLocker FVEK (Full Volume Encryption Key)'''

    sbox = [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67,
            0x2b, 0xfe, 0xd7, 0xab, 0x76, 0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59,
            0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0, 0xb7,
            0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1,
            0x71, 0xd8, 0x31, 0x15, 0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05,
            0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75, 0x09, 0x83,
            0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29,
            0xe3, 0x2f, 0x84, 0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
            0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf, 0xd0, 0xef, 0xaa,
            0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c,
            0x9f, 0xa8, 0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc,
            0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2, 0xcd, 0x0c, 0x13, 0xec,
            0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19,
            0x73, 0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee,
            0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb, 0xe0, 0x32, 0x3a, 0x0a, 0x49,
            0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
            0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4,
            0xea, 0x65, 0x7a, 0xae, 0x08, 0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6,
            0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a, 0x70,
            0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9,
            0x86, 0xc1, 0x1d, 0x9e, 0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e,
            0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf, 0x8c, 0xa1,
            0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0,
            0x54, 0xbb, 0x16]

    Rcon = [0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36,
            0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97,
            0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72,
            0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66,
            0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04,
            0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d,
            0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3,
            0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61,
            0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a,
            0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40,
            0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc,
            0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5,
            0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a,
            0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d,
            0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c,
            0xd8, 0xab, 0x4d, 0x9a, 0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35,
            0x6a, 0xd4, 0xb3, 0x7d, 0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4,
            0xd3, 0xbd, 0x61, 0xc2, 0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc,
            0x83, 0x1d, 0x3a, 0x74, 0xe8, 0xcb, 0x8d, 0x01, 0x02, 0x04, 0x08,
            0x10, 0x20, 0x40, 0x80, 0x1b, 0x36, 0x6c, 0xd8, 0xab, 0x4d, 0x9a,
            0x2f, 0x5e, 0xbc, 0x63, 0xc6, 0x97, 0x35, 0x6a, 0xd4, 0xb3, 0x7d,
            0xfa, 0xef, 0xc5, 0x91, 0x39, 0x72, 0xe4, 0xd3, 0xbd, 0x61, 0xc2,
            0x9f, 0x25, 0x4a, 0x94, 0x33, 0x66, 0xcc, 0x83, 0x1d, 0x3a, 0x74,
            0xe8, 0xcb ]

    def __init__(self, config, *args, **kwargs):
        common.AbstractWindowsCommand.__init__(self, config, *args, **kwargs)
        config.add_option('DUMP-DIR', default = None, help = 'Directory in which to dump FVEK')

    @staticmethod
    def is_valid_profile(profile):
        return profile.metadata.get('major', 0) >= 6

    def rotate(self, word):
        return word[1:] + word[:1]

    def core(self, word, iteration):
        word = self.rotate(word)
        for i in range(4):
            word[i] = self.sbox[word[i]]
        word[0] = word[0] ^ self.Rcon[iteration]
        return word

    def validSchedule(self, keySchedule, size, expandedKeySize):
        keySchedule = map(ord, keySchedule)
        key = keySchedule[:size]
        currentSize = 0
        rconIteration = 1
        expandedKey = [0] * expandedKeySize

        for j in range(size):
            expandedKey[j] = key[j]
        currentSize += size

        while currentSize < expandedKeySize:
            t = expandedKey[currentSize-4:currentSize]

            if currentSize % size == 0:
                t = self.core(t, rconIteration)
                rconIteration += 1

            if size == 32 and ((currentSize % size) == 16):
                for l in range(4):
                    t[l] = self.sbox[t[l]]

            for m in range(4):
                expandedKey[currentSize] = expandedKey[currentSize - size] ^ t[m]

                if expandedKey[currentSize] != keySchedule[currentSize]:
                    return False

                currentSize += 1

        return True

    def calculate(self):
        addr_space = utils.load_as(self._config)

        windows_version = (addr_space.profile.metadata.get('major', 0), addr_space.profile.metadata.get('minor', 0))

        if windows_version <= (6, 1):
            pool_tag = 'FVEc'
        else:
            pool_tag = 'Cngb'

        scanner = poolscan.SinglePoolScanner()
        scanner.checks = [
          ('PoolTagCheck', dict(tag = 'FVEc')),
          ('CheckPoolSize', dict(condition = lambda x: x > 184)),
        ]

        for addr in scanner.scan(addr_space):
            pool = obj.Object('_POOL_HEADER', offset = addr, vm = addr_space)

            pool_alignment = obj.VolMagic(pool.obj_vm).PoolAlignment.v()
            pool_size = int(pool.BlockSize * pool_alignment)

            debug.debug('Scanning potential BitLocker pool @ {0:#010x}'.format(pool.obj_offset))

            aes = []
            buf = addr_space.zread(addr, pool_size)

            for i in range(8, pool_size - 176):
                if self.validSchedule(buf[i:i+176], 16, 176):
                    aes.append(buf[i:i+16])

            for i in range(8, pool_size - 240):
                if self.validSchedule(buf[i:i+240], 32, 240):
                    aes.append(buf[i:i+32])

            debug.debug('AES keys found: {}'.format(len(aes)))

            if 0 < len(aes) <= 2:
                yield pool, aes[0], aes[1] if len(aes) > 1 else ''

    def render_text(self, outfd, data):
        data = sorted(data, key = lambda x: x[1])

        outfd.write('\n')

        for pool, fvek, tweak in data:
            outfd.write('Address : {0:#010x}\n'.format(pool.obj_offset))
            outfd.write('Cipher  : AES-{}\n'.format(len(fvek) * 8))
            outfd.write('FVEK    : {}\n'.format(''.join('{:02x}'.format(ord(i)) for i in fvek)))
            if tweak:
                outfd.write('TWEAK   : {}\n'.format(''.join('{:02x}'.format(ord(i)) for i in tweak)))

            if self._config.DUMP_DIR:
                full_path = os.path.join(self._config.DUMP_DIR, '{0:#010x}.fvek'.format(pool.obj_offset))

                with open(full_path, "wb") as fvek_file:
                    fvek_file.write(fvek + tweak)

                outfd.write('FVEK dumped to file: {}\n'.format(full_path))

            outfd.write('\n')
