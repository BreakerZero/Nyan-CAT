import unittest
import requests


class MyTestCase(unittest.TestCase):
    def test_something(self):
        requests.get("http://localhost:5000/login/")


if __name__ == '__main__':
    unittest.main()
