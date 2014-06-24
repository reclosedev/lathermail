import os
import unittest


def main():
    all_tests = unittest.TestLoader().discover(os.path.dirname(__file__))
    unittest.TextTestRunner(failfast=True, buffer=True).run(all_tests)


main()
