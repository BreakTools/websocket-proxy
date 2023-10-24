# websocket-proxy
Ever needed to connect to a websocket server that is hosted inside a firewalled network that you can't open ports to but you do have access to a computer on another network that you *can* open ports to? Use these two simple python scripts to make the websocket server on the firewalled network work externally! I initially wrote this for my [Deadline Web App backend](https://github.com/BreakTools/deadline-web-app-backend).

## Installation instructions
1. Make sure you have Python 3.10 or newer installed on both computers.
2. Install the Python Websockets library by running `pip install websockets`.
3. To set up the proxy on your external network, download and open external_proxy.py and change the PROXY_PORT variable to the port you wish to run it on. Then run `python external-proxy.py` to start the websocket server.
4. To set up the proxy on your internal network, download and open internal_proxy.py and change PROXY_URL to the URL of your external proxy, and change BACKEND_URL to the URL of the websocket server that is running on your internal network. Then run `python internal-proxy.py` to start the websocket client.

That's it! The external websocket server will forward all data to the internal websocket client, which will then spoof connections to the internal websocket server. A bit janky, sure, but you must do something when your IT department won't open any ports for you. 
