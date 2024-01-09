# Mixformer2

This repository is based on [MCG-NJU/MixFormerV2](https://github.com/MCG-NJU/MixFormerV2).

As there is no any inference framework that support real time online learning, therefore the main goal here is to build a tracking as a service with python client and C++ client.

The code for server is in /mixformerv2/tracking/app.py




![rdm-figure](assets/ok.gif)


## Usage


#### Pre-requsite 
docker

nvidia docker

OpenCV

cmake (optional)


#### 1. Build the image for tracking server
```
sudo docker build --network=host -t tracking_server .
```
#### 2. Run the container
```
sudo docker run --gpus all -p 8002:8002 -it --rm tracking_server:latest
```

#### 3A. Run python client
```
python python_client.py /home/nicky/cutted_football.mp4
```

#### 3B. Run C++ client
```
mkdir build
cd build
cmake .. 
make 
./cpp_client /home/nicky/cutted_football.mp4

```
