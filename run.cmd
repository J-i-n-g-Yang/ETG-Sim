@echo off
cd /d "%~dp0"
:: --threads must be >> expected concurrent users because each SSE connection
:: (one per player tab + projector + control) holds a thread for its lifetime.
waitress-serve --listen=127.0.0.1:8060 --threads=500 --url-prefix=/GOHub/townhall app:app
