#include <iostream>
#include <dirent.h>
#include <cmath>
#include <string>
#include <chrono>
#include <vector>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <future>
#include <opencv2/opencv.hpp>
#include <opencv2/core.hpp>

#include <curl/curl.h>
#include <chrono>
#include <sstream>
#include <nlohmann/json.hpp>

nlohmann::json trackedData;
static int client_socket;
// Server configurations
const char* server_ip = "127.0.0.1"; // Change this to the server's IP
const int server_port = 8002;
cv::Rect gTrackBbox;
bool bResult=false;
bool have_box=false;


static void sleepMs(int ms)
{
    struct timeval delay;
    delay.tv_sec = 0;
    delay.tv_usec = ms * 1000; // ms
    select(0, NULL, NULL, NULL, &delay);
}

int socket_init(){
    // Create a socket
    client_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (client_socket == -1) {
        perror("Error creating socket");
        return 1;
    }
    
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(server_port);
    server_addr.sin_addr.s_addr = inet_addr(server_ip);
    // Connect to the server
    if (connect(client_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) == -1) {
        perror("Error connecting to server");
        return 1;
    }
    return 0;
}

void boundingBoxThread(){
    std::cout << "Started bounding box thread" << std::endl;
    char buffer[1024];
    while (true) {
          // Clear the buffer
        
        if (bResult) {
            int bytesRead = recv(client_socket, buffer, sizeof(buffer), 0);
            
            if (bytesRead == -1) {
                std::cerr << "Error receiving data." << std::endl;
                break;
            } else if (bytesRead == 0) {
                // Connection closed by the server
                std::cout << "Server closed the connection." << std::endl;
                break;
            }

            // Process the received data
            std::string receivedData(buffer, bytesRead);
            // std::cout << "Raw Received Data: " << receivedData << std::endl;
            // Check if the received data is empty or too small
            if (receivedData.empty() || receivedData.size() < 5) {
                continue;
            }

            if (receivedData.substr(0, 4) == "TRK ") {
                std::string jsonData = receivedData.substr(4);
                
                try {
                    trackedData = nlohmann::json::parse(jsonData);
                    // Process parsedJson

                    // Example: Pri nt the parsed data
                    // std::cout << "Received JSON: " << trackedData << std::endl;
                    have_box = true;
                } catch (const nlohmann::json::parse_error& e) {
                    std::cerr << "JSON Parsing Error: " << e.what() << std::endl;
                    // Handle the parsing error gracefully
                }
            }
            memset(buffer, 0, sizeof(buffer));
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(3));
    }
}

void sendImage(int client_socket, const cv::Mat& image) {
    int rows = image.rows;
    int cols = image.cols;

    // Prepend the "RGB " flag and image dimensions
    std::string data = "RGB ";

    // Get a pointer to the image data
    const uchar* imageData = image.ptr();

    // Append raw image data to the string
    data.append(reinterpret_cast<const char*>(imageData), image.total() * image.elemSize());

    // std::cout<<data.size()<<std::endl;
    // Send the data
    send(client_socket, data.c_str(), data.size(), 0);
}

void sendMessages(int client_socket, const char* message) {
    std::string data = "TEXT" + std::string(message); // Prepend "TEXT" flag
    send(client_socket, data.c_str(), data.size(), 0);
}

bool advance_track_init(cv::Mat _frame){

    float x,y,w,h;
    x =  gTrackBbox.x * 1.0;
    y =  gTrackBbox.y * 1.0;
    w =  gTrackBbox.width * 1.0;
    h =  gTrackBbox.height * 1.0;

    std::string json_message = "{\"x\": " + std::to_string(x) + ", \"y\": " + std::to_string(y) +
                        ", \"w\": " + std::to_string(w) + ", \"h\": " + std::to_string(h) + "}";


    const char* cString = json_message.c_str();

    // // Copy the JSON message to shared memory
    // std::strcpy(json_data, json_message.c_str());

    sendMessages(client_socket,cString);
    cv::Mat frameTemp = _frame.clone();
    //frameTemp = frameTemp(cv::Range(26, 1050), cv::Range(786, 1810)).clone();   // 1024 * 1024
    cv::resize(frameTemp, frameTemp, cv::Size(512, 512), 0, 0, cv::INTER_AREA); // 512 * 512
    sendImage(client_socket, frameTemp);



    return true;
}


bool advance_track_result(){
    
    // std::cout<<trackedData<<std::endl;
    // Access individual fields
    int x = trackedData["x"];
    int y = trackedData["y"]; 
    int w = trackedData["w"];
    int h = trackedData["h"];
    int end = trackedData["end"];

    std::cout << "Received tracked data:" << std::endl;
    std::cout << "x: " << x << ", y: " << y << ", w: " << w << ", h: " << h << ", end: " << end << std::endl;\

    // if (end==1){
    //     current_papilla.x = -1;
    //     current_papilla.y = -1;
    //     return true;
    // }


    // current_papilla.x = x + w/2.0;
    // current_papilla.y = y + h/2.0;

    gTrackBbox.width  = w;
    gTrackBbox.height = h;
    gTrackBbox.x = x;
    gTrackBbox.y = y;


    return true;
}





int main(int argc, char **argv)
{   


    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <video_file_path>" << std::endl;
        return 1;
    }

    std::string videoFilePath = argv[1];


    //init socket
    socket_init();

    //init bounding box thread
    std::thread myThread(boundingBoxThread);
    sleepMs(200);// 等待设备m
    myThread.detach();


    // Read video
    cv::VideoCapture video(videoFilePath);
     
    // Exit if video is not opened
    if(!video.isOpened())
    {
        std::cout << "Could not read video file" << std::endl; 
        return 1; 
    } 
 
    // Read first frame 
    cv::Mat frame; 
    bool ok = video.read(frame); 

    // Resize the frame
    cv::Mat resized_frame;
    cv::resize(frame, resized_frame, cv::Size(512, 512), 0, 0, cv::INTER_LINEAR);
 
    // Define initial bounding box 
    cv::Rect2d bbox(287, 23, 86, 320); 
    gTrackBbox = cv::selectROI(resized_frame, false); 
    bResult = advance_track_init(resized_frame);


    // tracker->init(frame, bbox);
     
    while(video.read(frame))
    {     

        cv::resize(frame, resized_frame, cv::Size(512, 512), 0, 0, cv::INTER_LINEAR);
        sendImage(client_socket, resized_frame);
        if(have_box){
            advance_track_result();
        }

        cv::rectangle(resized_frame, gTrackBbox, cv::Scalar( 255, 0, 0 ), 2, 1 ); 
        cv::imshow("Tracking", resized_frame);
         
        // Exit if ESC pressed.
        int k = cv::waitKey(1);
        if(k == 27)
        {
            break;
        }
 
    }
}