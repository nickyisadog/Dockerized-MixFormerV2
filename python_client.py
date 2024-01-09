import cv2
import json
import socket
import threading
import argparse


# Global variable for tracked_data
tracked_data = None
ok=False
tracked_data_lock = threading.Lock()



##sending text(bounding box) to tracking server
def send_text_data(client_socket, text_data):
    # Prepend the "TEXT" flag to the text data and send it
    data_to_send = b"TEXT" + text_data.encode()
    client_socket.send(data_to_send)


##sending image(RGB) to tracking server
def send_image_data(client_socket, frame):
        # Flatten the image to a 1D NumPy array
    flattened_image = frame.flatten()

    # Convert the flattened image to bytes and prepend the "RGB " flag
    data_to_send = b"RGB " + flattened_image.tobytes()

    # Send the image data
    client_socket.send(data_to_send)
    

##receive boundingbox from server
def receive_tracking_data(client_socket):
    global tracked_data
    global ok
    while True:
        data = client_socket.recv(1024)

        if not data:
            print("Connection closed by the server.")
            break

        if data.startswith(b"TRK "):
            ok=True
            tracked_data_json = data[4:]
            tracked_data = json.loads(tracked_data_json)

def generate_text_data(x, y, w, h):
    text_data = f'{{"x":{x}, "y":{y}, "w":{w}, "h":{h}}}'
    return text_data



if __name__ == "__main__":


    # Create an argument parser
    parser = argparse.ArgumentParser(description='Process a video file.')

    # Add the video path argument
    parser.add_argument('video_path', type=str, help='Path to the video file')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Open the video file
    video_path =  args.video_path # Replace with your video file path
    cap = cv2.VideoCapture(video_path)



    # Server IP and port
    server_ip = "127.0.0.1"  # Replace with the actual server IP address
    server_port = 8002 # Replace with the actual server port

    # Create a TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((server_ip, server_port))
    print("Connected to the server.")


    # Check if the video opened successfully
    if not cap.isOpened(): 
        print("Error opening video file.")
        exit()

    # Get the video's frame dimensions
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # Define the cropping parameters (adjust as needed)
    crop_x, crop_y, crop_width, crop_height = 694, 34, 1172, 1024

    ##550
    ##100
    ##skipping the first frame
    for i in range(1):
        ret, frame = cap.read()

    print("OK")
    # cropped_frame = frame[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
    cropped_frame = frame
    # Resize the cropped frame to 512x512
    resized_frame = cv2.resize(cropped_frame, (512, 512))
    # Select the bounding box in the first frame
    bbox = cv2.selectROI(resized_frame, False)
    print(bbox)
    text_data = generate_text_data(bbox[0],bbox[1],bbox[2],bbox[3])


    ##init sending bounding box and image to the server
    send_text_data(client_socket, text_data)
    send_image_data(client_socket, resized_frame)

    # Start a thread for receiving tracking data
    tracking_thread = threading.Thread(target=receive_tracking_data, args=(client_socket,))
    tracking_thread.start()



    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print('cannot read the video')

        # Crop the frame
        # cropped_frame = frame[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
        cropped_frame = frame

        # Resize the cropped frame to 512x512
        resized_frame = cv2.resize(cropped_frame, (512, 512))
        send_image_data(client_socket, resized_frame)

        
        if ok ==True:
            if tracked_data['x']!=0:
                print(tracked_data)
                cv2.rectangle(resized_frame, (int(tracked_data['x']), int(tracked_data['y'])), (int(tracked_data['x']+tracked_data['w']), int(tracked_data['y']+tracked_data['h'])), (0, 255, 0), 2) 

                
        # Display the resized frame
        cv2.imshow('Tracking Window', resized_frame)



        # Break the loop when the 'q' key is pressed
        if cv2.waitKey(120) & 0xFF == ord('q'):
            break

    # Release the video capture and writer objects
    cap.release()

    # Close all OpenCV windows
    cv2.destroyAllWindows()


    # Close the client socket
    client_socket.close()
