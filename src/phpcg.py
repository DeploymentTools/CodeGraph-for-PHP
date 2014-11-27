# The MIT License (MIT)

# Copyright (c) 2014 Bogdan Anton

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Usage: phpcg --source [PROJECT FOLDER PATH] --log [LOG FOLDER PATH]

Attributes:
    --source     The path to the PHP project that will be analyzed
    --log        The path to the writable folder to dump the JSON log into


"""

import sys
import optparse
from ClassExtractor import ClassExtractor

# boot-up
parser = optparse.OptionParser(version = "1.0.0rc2", usage = __doc__.strip())
parser.add_option('--source')
parser.add_option('--log')

options, args = parser.parse_args()

if not options.source or not options.log:
    sys.stdout.write(__doc__)
    sys.exit()

worker = ClassExtractor()
worker.setConfig('basepath', options.source)
worker.setConfig('logpath', options.log)
# worker.setConfig('debug', True)
worker.processMain()
print("Done :)")
