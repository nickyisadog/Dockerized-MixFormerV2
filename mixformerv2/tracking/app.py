import os
import sys
import argparse

prj_path = os.path.join(os.path.dirname(__file__), '..')
if prj_path not in sys.path:
    sys.path.append(prj_path)


from flask import Flask, request, jsonify
import cv2
import numpy as np
import os
import sys
import argparse
import socket
import json
import re


app = Flask(__name__)
IMAGE_SIZE_x=512
IMAGE_SIZE_y=512
TOTAL_SIZE=IMAGE_SIZE_x*IMAGE_SIZE_y*3

from lib.test.evaluation import Tracker


def _build_init_info(box):
    return {'init_bbox': box}


def extract_string_within_braces(text):
    # This regular expression matches any content inside the first pair of curly braces
    match = re.search(r'\{.*?\}', text)
    if match:
        return match.group(0)  # Returns the matched text including the curly braces
    return None  # Return None if there are no curly braces in the text


def main():

    have_image=False
    track_result = None
    inited=False
    can_track=False


    server_ip = "0.0.0.0"  # Change to your server's IP address
    server_port = 8002  # Change to your desired port number

    tracker_params={'model': 'models/mixformerv2_base.pth.tar', 'update_interval': 25, 'online_size': 1, 'search_area_scale': 4.5, 'max_score_decay': 1.0, 'vis_attn': 0}
    tracker_class = Tracker("mixformer2_vit_online", "288_depth8_score", "video", tracker_params=tracker_params)


    params = tracker_class.params
    params.tracker_name = tracker_class.name
    params.param_name = tracker_class.parameter_name
    tracker = tracker_class.create_tracker(params)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(1)

    print("Server listening on {}:{}".format(server_ip, server_port))


    client_socket, client_address = server_socket.accept()
    print("Connected by:", client_address)


    while True:
        data = client_socket.recv(1024)  # Receive data from the client
        total_received_bytes = len(data)
        if not data:
            print("Client disconnected")
            client_socket, client_address = server_socket.accept()

        else:

            # Process the received data
            data_type = data[:4]  # Extract the first 4 bytes as the data type flag

            if inited==True and have_image==True:
                try:
                    print("INITINITINITINITINITINT")
                    tracker.initialize(image,_build_init_info([x,y,w,h]))
                    inited=False
                    can_track=True
                except:
                    print("something went wrong")

            if data_type == b"TEXT":
                try:

                    print("TEXTTEXTTEXTTEXTTEXT")
                    print(data)		
                    json_message=data[4:].decode()
                    json_message=extract_string_within_braces(json_message)
                    print("===============")
                    print("Received text:", json_message)
                    print(len(json_message))
                    json_message = json.loads(json_message)
                except:
                    print("something went wrong")


                if int(json_message['w'])>10 and int(json_message['h']>10):

                    x,y,w,h=int(json_message['x']),int(json_message['y']),int(json_message['w']),int(json_message['h'])
                can_track=False
                have_image=False
                inited=True

            elif data_type == b"RGB ":
                while total_received_bytes < TOTAL_SIZE+4:
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    total_received_bytes += len(chunk)
                print("Received:", total_received_bytes, "out of", 786432, "bytes")
                print(data[0:4])
                image_data = data[4:TOTAL_SIZE+4]  # Extract the image data after the data type flag
                # Convert the image bytes to a NumPy array
                image = np.frombuffer(image_data, dtype=np.uint8) 

                # Reshape the NumPy array to the original image dimensions
                image = image.reshape((IMAGE_SIZE_x, IMAGE_SIZE_y, 3))

                have_image=True

                if can_track==True:
                    track_result = tracker.track(image)
                    x, y, w, h = track_result["target_bbox"]
                    print(track_result["conf_score"])
                    
                    if track_result["conf_score"]<0.55:
                    	x=0
                
                    if x==0:
                        tracked_data = {
                            'x': 0,
                            'y': 0,
                            'w': 0,
                            'h': 0,
                            'end':1
                        }
                    else:
                        tracked_data = {
                            'x': x,
                            'y': y,
                            'w': w,
                            'h': h,
                            'end':0
                        }

                    tracked_data_json = json.dumps(tracked_data)

                    # Prepend the "TRK " flag and send the tracked_data JSON
                    tracked_data_message = b"TRK " + tracked_data_json.encode()
                    client_socket.send(tracked_data_message)



    # server_socket.close()
if __name__ == '__main__':
    main()
