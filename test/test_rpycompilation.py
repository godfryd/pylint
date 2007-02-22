from os.path import isfile, splitext, basename
from os import system, remove
from glob import glob

from logilab.common.testlib import TestCase, unittest_main

class RPyCompilation(TestCase):

    def setUp(self):
        self.trscript = self.find_pypy()

    def find_pypy(self):
        #trscript = '/home/adim/local/svn/pypy-dist/pypy/translator/goal/translate.py'
        trscript = '/home/syt/cvs_work/pypy-dist/pypy/translator/goal/translate.py'
        if not isfile(trscript):
            self.skip('translate.py not found')
        return trscript
    
    def _compile_fail(self, filename):
        status = system('%s --batch %s' % (self.trscript, filename))
        try:
            self.assertNotEquals(status, 0, "%s translation succeed !!" % filename)
        except AssertionError:
            exefile = '%s-c' % splitext(basename(filename))[0]
            status = system('./%s' % exefile)
            remove(exefile)
            self.assertNotEquals(status, 0, "%s run succeed !!" % exefile)
            
    def _compile_success(self, filename):
        status = system('%s --batch %s' % (self.trscript, filename))
        self.assertEquals(status, 0, "%s translation failed !!" % filename)
        exefile = '%s-c' % splitext(basename(filename))[0]
        status = system('./%s' % exefile)
        remove(exefile)
        self.assertEquals(status, 0, "%s run failed !!" % exefile)
            
            
    def test_translations(self):
        for filename in glob('rpythoninput/func_*.py'):
            if filename.startswith('rpythoninput/func_noerror'):
                yield self._compile_success, filename
            else:
                yield self._compile_fail, filename

    
if __name__ == '__main__':
    import sys
    if not '-cc' in sys.argv:
        sys.argv.append('-cc')
    unittest_main()
