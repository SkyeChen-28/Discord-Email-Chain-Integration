'''
    This code was copied and modified from Sudoblark/w3c-html-python-validator on GitHub:
    https://github.com/Sudoblark/w3c-html-python-validator/blob/main/src/HTMLValidator.py
    
    Sudoblark/w3c-html-python-validator is licensed under the   
    MIT License

    Copyright (c) 2021 Othneil Drew

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
'''

from urllib import request
import json

class HTMLValidator:
    def __init__(self):
        self.__w3_validator_url = "https://validator.w3.org/nu/?out=json"
        self.__headers = {
            "Content-Type": "text/html",
            "charset": "utf-8"
        }

    def validate_html(self, html_str):
        """
        Validates HTML for given file at path
        :param path_to_file: WindowsPath (or equal) reference to a file
        :return:  blank JSON for valid HTML, otherwise returns array of JSON error messages
        """
        return self.__call_w3_validator(bytes(html_str, "utf-8"))

    def __add_headers_to_validator(self, request_object):
        """
        Adds standard headers to validator
        :param request_object: urllib.request.Requests object to add headers to
        :return:
        """
        for key, value in self.__headers.items():
            request_object.add_header(key, value)

    def __call_w3_validator(self, html):
        """
        Passes provided HTML to W3 validator for validation
        :param html: bytes representation of html to valid
        :return: JSON representation of results
        """
        req = request.Request(self.__w3_validator_url, data=html)
        self.__add_headers_to_validator(req)
        req_data = request.urlopen(req).read()
        # After read, format bytes to proper string so we can return json
        req_string = req_data.decode('utf8').replace("'", '"')
        return json.loads(req_string)