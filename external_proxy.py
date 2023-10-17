"""
Proxy WebSocket server by Mervin van Brakel, 2023.
This WebSocket server receives data from clients and forwards it to a special 
connected proxy client. An ID is shared between the two proxies so that
data can be forwarded to the correct connected client.
"""

import asyncio
import json
import logging
import uuid

import websockets

PROXY_PORT = 00000
CONNECTIONS = {}
CONNECTION_CHECKS = set()

logging.basicConfig(level=logging.INFO)


async def websocket_connection_handler(websocket):
    """This function gets executed when a new websocket connection opens."""

    created_uuid = str(uuid.uuid4())
    CONNECTIONS[created_uuid] = websocket
    logging.info(f"New client {created_uuid} has connected.")

    try:
        await CONNECTIONS["proxy"].send(
            json.dumps({"body": "new_connection", "id": created_uuid})
        )

        # Wait for acknowledgment from the proxy
        while created_uuid not in CONNECTION_CHECKS:
            await asyncio.sleep(0.1)

        CONNECTION_CHECKS.remove(created_uuid)

    except KeyError:
        logging.error("New client tried connecting but there is no connected proxy.")

    while True:
        # We keep running this loop while the connection is open.
        try:
            message = await websocket.recv()

        except websockets.exceptions.ConnectionClosed:
            # If a client disconnects, remove the ID from memory.
            try:
                if websocket != CONNECTIONS["proxy"]:
                    await CONNECTIONS["proxy"].send(
                        json.dumps({"body": "del_connection", "id": created_uuid})
                    )
                    logging.info(f"Client {created_uuid} has disconnected.")
                    return

                # If the proxy disconnects, remove the special proxy key.
                else:
                    CONNECTIONS.pop("proxy")
                    logging.log(50, "Proxy client has disconnected.")
                    return
            except KeyError:
                logging.error(
                    "Tried sending delete call without connected client proxy."
                )

        except Exception as e:
            logging.error(
                f"An error occurred trying to receive data from a client: {str(e)}"
            )

        try:
            parsed_message = json.loads(message)

            match parsed_message["body"]:
                case "identify":
                    # Runs when the proxy identifies itself
                    CONNECTIONS.pop(created_uuid)
                    CONNECTIONS["proxy"] = websocket
                    logging.log(50, "Proxy client connected.")

                case "return":
                    # Runs when the proxy returns data to a client
                    try:
                        await CONNECTIONS[parsed_message["id"]].send(
                            parsed_message["data"]
                        )
                        logging.info("Returning data to client.")
                    except Exception as e:
                        logging.error(
                            f"An error occured while returning data to a client: {e}"
                        )

                case "acknowledge_new_connection":
                    client_id = parsed_message["id"]
                    CONNECTION_CHECKS.add(client_id)
                    logging.info(
                        f"Received acknowledgment for new connection {client_id}."
                    )

                case _:
                    # Forwards all other client messages to the proxy.
                    try:
                        await CONNECTIONS["proxy"].send(
                            json.dumps(
                                {
                                    "body": "data",
                                    "id": created_uuid,
                                    "data": parsed_message,
                                }
                            )
                        )
                        logging.info("Forwarding client data to proxy.")

                    except Exception as e:
                        logging.error(f"Couldn't send data to proxy: {e}")

        except Exception as e:
            logging.error(f"An error occured while parsing client data: {e}")


async def start_websocket_server():
    async with websockets.serve(websocket_connection_handler, "", PROXY_PORT):
        await asyncio.Future()


asyncio.run(start_websocket_server())
