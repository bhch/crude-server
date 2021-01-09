""" Crude Server

This is supplementary code for a tutorial about writing HTTP servers from scratch.

To get a better understanding, read the tutorial at this link: 

https://bhch.github.io/posts/2017/11/writing-an-http-server-from-scratch/

"""

import os
import socket
import mimetypes

 
class TCPServer:
    """Base server class for handling TCP connections. 
    The HTTP server will inherit from this class.
    """

    def __init__(self, host='127.0.0.1', port=8888):
        self.host = host
        self.port = port

    def start(self):
        """Method for starting the server"""

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)

        print("Listening at", s.getsockname())

        while True:
            conn, addr = s.accept()
            print("Connected by", addr)
            
            # For the sake of this tutorial, 
            # we're reading just the first 1024 bytes sent by the client.
            data = conn.recv(1024) 

            response = self.handle_request(data)

            conn.sendall(response)
            conn.close()

    def handle_request(self, data):
        """Handles incoming data and returns a response.
        Override this in subclass.
        """
        return data


class HTTPServer(TCPServer):
    """The actual HTTP server class."""

    headers = {
        'Server': 'CrudeServer',
        'Content-Type': 'text/html',
    }

    status_codes = {
        200: 'OK',
        404: 'Not Found',
        501: 'Not Implemented',
    }

    def handle_request(self, data):
        """Handles incoming requests"""

        request = HTTPRequest(data) # Get a parsed HTTP request

        try:
            # Call the corresponding handler method for the current 
            # request's method
            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = self.HTTP_501_handler

        response = handler(request)
        return response

    def response_line(self, status_code):
        """Returns response line (as bytes)"""
        reason = self.status_codes[status_code]
        response_line = 'HTTP/1.1 %s %s\r\n' % (status_code, reason)

        return response_line.encode() # convert from str to bytes

    def response_headers(self, extra_headers=None):
        """Returns headers (as bytes).

        The `extra_headers` can be a dict for sending 
        extra headers with the current response
        """
        headers_copy = self.headers.copy() # make a local copy of headers

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ''

        for h in headers_copy:
            headers += '%s: %s\r\n' % (h, headers_copy[h])

        return headers.encode() # convert str to bytes

    def handle_OPTIONS(self, request):
        """Handler for OPTIONS HTTP method"""

        response_line = self.response_line(200)

        extra_headers = {'Allow': 'OPTIONS, GET'}
        response_headers = self.response_headers(extra_headers)

        blank_line = b'\r\n'

        return b''.join([response_line, response_headers, blank_line])

    def handle_GET(self, request):
        """Handler for GET HTTP method"""

        path = request.uri.strip('/') # remove slash from URI

        if not path:
            # If path is empty, that means user is at the homepage
            # so just serve index.html
            path = 'index.html'

        if os.path.exists(path) and not os.path.isdir(path): # don't serve directories
            response_line = self.response_line(200)

            # find out a file's MIME type
            # if nothing is found, just send `text/html`
            content_type = mimetypes.guess_type(path)[0] or 'text/html'

            extra_headers = {'Content-Type': content_type}
            response_headers = self.response_headers(extra_headers)

            with open(path, 'rb') as f:
                response_body = f.read()
        else:
            response_line = self.response_line(404)
            response_headers = self.response_headers()
            response_body = b'<h1>404 Not Found</h1>'

        blank_line = b'\r\n'

        response = b''.join([response_line, response_headers, blank_line, response_body])

        return response

    def HTTP_501_handler(self, request):
        """Returns 501 HTTP response if the requested method hasn't been implemented."""

        response_line = self.response_line(status_code=501)

        response_headers = self.response_headers()

        blank_line = b'\r\n'

        response_body = b'<h1>501 Not Implemented</h1>'

        return b"".join([response_line, response_headers, blank_line, response_body])


class HTTPRequest:
    """Parser for HTTP requests. 
    
    It takes raw data and extracts meaningful information about the incoming request.

    Instances of this class have the following attributes:

        self.method: The current HTTP request method sent by client (string)

        self.uri: URI for the current request (string)

        self.http_version = HTTP version used by  the client (string)
    """

    def __init__(self, data):
        self.method = None
        self.uri = None
        self.http_version = '1.1' # default to HTTP/1.1 if request doesn't provide a version

        # call self.parse method to parse the request data
        self.parse(data)

    def parse(self, data):
        lines = data.split(b'\r\n')

        request_line = lines[0] # request line is the first line of the data

        words = request_line.split(b' ') # split request line into seperate words

        self.method = words[0].decode() # call decode to convert bytes to string

        if len(words) > 1:
            # we put this in if block because sometimes browsers
            # don't send URI with the request for homepage
            self.uri = words[1].decode() # call decode to convert bytes to string

        if len(words) > 2:
            # we put this in if block because sometimes browsers
            # don't send HTTP version
            self.http_version = words[2]



if __name__ == '__main__':
    server = HTTPServer()
    server.start()
