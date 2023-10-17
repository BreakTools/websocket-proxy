"""
Proxy WebSocket client by Mervin van Brakel, 2023.
This WebSocket client receives data from the server, 
then spoofs client connections to an internal backend.
I wrote this to avoid having to rework the logic of my 
deadline web app backend.
"""

import asyncio
import json
import logging

import websockets

PROXY_URL = "wss://external-proxy.com"
BACKEND_URL = "ws://internal-websocket-server-ip"
CONNECTIONS = {}
logging.basicConfig(level=logging.INFO)


class spoofed_client:
    def __init__(self, parent_websocket, id) -> None:
        self.parent_websocket = parent_websocket
        self.id = id

    async def connect_to_backend(self) -> None:
        """This function creates a new websocket connection to the backend.
        Whenever it receives a message, it forwards it to the WebSocket server
        together with the correct ID so the data goes to the right client upstream."""

        try:
            async with websockets.connect(BACKEND_URL) as websocket:
                self.websocket = websocket

                await self.parent_websocket.send(
                    (json.dumps({"body": "acknowledge_new_connection", "id": self.id}))
                )
                logging.info(f"A new client has connected with ID {self.id}.")

                while True:
                    try:
                        message = await websocket.recv()

                        await self.parent_websocket.send(
                            json.dumps(
                                {"body": "return", "id": self.id, "data": message}
                            )
                        )

                    except websockets.exceptions.ConnectionClosed:
                        logging.error(f"Client {self.id} disconnected!")
                        return

                    except Exception as e:
                        logging.error(f"Retrieving client message failed: {e}")

        except ConnectionRefusedError:
            logging.error("Backend refused connection, is it running?")

    async def send_data(self, data: dict) -> None:
        """This function sends data to the websocket that is stored in this class."""
        await self.websocket.send(json.dumps(data))


async def connect_to_websocket_server() -> None:
    while True:
        try:
            async with websockets.connect(PROXY_URL) as websocket:
                await websocket.send((json.dumps({"body": "identify"})))
                logging.log(50, "Successfully connected to WebSocket server!")

                while True:
                    try:
                        message = await websocket.recv()
                    except websockets.exceptions.ConnectionClosed:
                        logging.error("Connection to server closed.")
                        break
                    except Exception as e:
                        logging.info(f"Couldn't retrieve message from server: {e}")
                        break

                    try:
                        parsed_message = json.loads(message)

                        match parsed_message["body"]:
                            case "new_connection":
                                CONNECTIONS[parsed_message["id"]] = spoofed_client(
                                    websocket, parsed_message["id"]
                                )
                                asyncio.create_task(
                                    CONNECTIONS[
                                        parsed_message["id"]
                                    ].connect_to_backend()
                                )

                            case "del_connection":
                                try:
                                    CONNECTIONS.pop(parsed_message["id"])
                                    logging.info(
                                        f"Deleted connection with client {parsed_message['id']}"
                                    )
                                except Exception as e:
                                    logging.error(
                                        f"Deleting client from memory failed: {e}"
                                    )

                            case "data":
                                print("new data")
                                try:
                                    await CONNECTIONS[parsed_message["id"]].send_data(
                                        parsed_message["data"]
                                    )
                                    logging.info(
                                        f"Forwarded from {parsed_message['id']} to backend."
                                    )
                                except AttributeError:
                                    logging.error(
                                        "Error: tried sending data to ID that was not yet initialized."
                                    )

                                except Exception as e:
                                    logging.error(
                                        f"Error while forwarding data to backend: {e}"
                                    )

                    except Exception as e:
                        logging.error(f"Error while parsing received data: {e}")

        except Exception as e:
            logging.error(f"Connection to server failed, retrying in 5 seconds: {e}")

        await asyncio.sleep(5)


asyncio.run(connect_to_websocket_server())
