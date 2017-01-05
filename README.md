DeflateHTTPServer
====================

This is a modified SimpleHTTPServer with added deflate and multiprocessing/multithreading 

## Usage

````
python DeflateHTTPServer.py [-h] [-port PORT] [-mode MODE] www_root
````
python DeflateHTTPServer.py .
```
This will start a multithreading server on port 8000, serving current working directory.
You should see this in your terminal:

````
[MainProcess]	[MultiThreadedDeflateHTTPServer] started on 0.0.0.0 port 8000 ...
````

To run on a different port use:
````
python DeflateHTTPServer.py . -port 8080
````

For a multiprocessing server run:

python DeflateHTTPServer.py . -mode mp

[MainProcess]	[MultiProcessingDeflateHTTPServer] started on 0.0.0.0 port 8080 ...
[Process-1]	starting server process ...
[MainProcess]	starting server process ...
[Process-2]	starting server process ...
[Process-3]	starting server process ...
