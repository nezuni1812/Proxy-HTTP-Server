from socket import *
import sys
import os
from threading import Thread
import datetime
import time

if len(sys.argv) < 2:
    print('Usage : "python Server.py [Address of Server]')
    sys.exit(0)

size = 4096
server_ip = sys.argv[1]
server_port = 8888

path = "image_cache/"
isExist = os.path.exists(path)
if not isExist: #Create if not exist, remove all file otherwise.
   os.makedirs(path)
   print("The new directory is created!")
else:
    for file in os.listdir("image_cache/"):
        os.remove("image_cache/" + file)

def read_config_file(filename):
    whitelist = []
    cache_duration = None
    time_start = None
    time_end = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('CACHE'):
                cache_duration = int(line.split()[1])
            elif line.startswith('TIME_START'):
                time_start = int(line.split()[1])
            elif line.startswith('TIME_END'):
                time_end = int(line.split()[1])
            else:
                whitelist.append(line)
    return whitelist, cache_duration, time_start, time_end

whitelist, cache_duration, time_start, time_end = read_config_file("config.txt")

def cache_manager():
    while True:
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            time_start = os.path.getctime(file_path)
            time_end = time.time()
            if time_end - time_start > cache_duration:
                os.remove(file_path)
                print(f'Your Image Caching of {file_name} has been reset')

def check_whitelist(input_website, whitelist):
    for website in whitelist:
        if website in input_website:
            return True
    return False

def is_within_time_range(start_time, end_time):
    # https://favtutor.com/blogs/get-current-time-python#:~:text=Python%20includes%20a%20datetime.,DD%20HH%3AMM%3ASS.
    
    current_time = datetime.datetime.now()
    now = current_time.strftime('%H')
    now = int(now) # Ép kiểu

    if start_time < end_time:
        if start_time <= now < end_time:
            return True
    else:
        if now >= start_time or now < end_time:
            return True

    return False

def send_image_response(client, image_name):
    #b'''HTTP/1.1 403 Forbidden\r\nContent-Type: image/jpeg\r\n\r\n'''
    #full_response = http_response + image_data
    image_path = os.path.join("403Forbidden", image_name)
    with open(image_path, 'rb') as f:
        data = f.read()
        response = b'HTTP/1.1 403 Forbidden\r\n'
        response += b'Content-Type: image/jpeg\r\n\r\n'
        response += data
        client.sendall(response) 
        client.close()
        
def get_response_from_web(client, client_addr, hostname, request, fileName, isImage):
    # Socket từ Proxy tới Server
    web_server = socket(AF_INET, SOCK_STREAM)
    
    web_ip = gethostbyname(hostname)
    web_server.connect((web_ip, 80)) #80 là port của HTTP

    # Send the request to the web server
    web_server.sendall(request)

    response = b""
    response += web_server.recv(size)
    client.sendall(response) 
    if b"Content-Length:" in response: 
        # Tách các dòng trong response
        lines = response.decode('ISO-8859-1').split('\r\n')
        
        for line in lines:
            if "Content-Length" in line:
                content_length_line = line

        content_length = int(content_length_line.split(': ')[1])
        
        while len(response) < content_length:
            data = web_server.recv(size)
            client.sendall(data)
            response += data
    else: 
        while response.find(b"\r\n0\r\n\r\n") == -1:
            data = web_server.recv(size)
            if not data:
                return
            client.sendall(data)
            response += data
       
    if isImage:
        with open("image_cache/" + fileName, 'wb') as file:
            file.write(response)
    web_server.close()
    client.close()

def handle_http_request(client, client_addr):
    try:
        request = client.recv(size)
        message = request.decode('ISO-8859-1') 
        if len(message.split()) > 1:
            request_line = message.split('\r\n')[0]
            method, url, version = request_line.split()
        else:
            client.close()
            return

        # Time Range
        if not is_within_time_range(time_start, time_end):
            send_image_response(client, 'TimeAccessError.jpg')
            print("Access denied\n")
            return
        
        # Check if HTTP request is supported
        if method not in ['GET', 'POST', 'HEAD']:
            send_image_response(client, 'HTTPRequestError.jpg')
            # HTTP request not supported
            print("Not support HTTP request\n")
            return

        # Extract hostname from URL
        hostname = url.split('/')[2]
        print(f"HTTP Request: {method}")
        print(f"URL: {url}")
        print(f"Host: {hostname}")
        fileName = url.replace('http://', '').replace('/', '_')
        if '?' in fileName:
            fileName = fileName.split('?')[0]
        
        # Whitelist
        if not check_whitelist(hostname, whitelist):
            send_image_response(client, 'WhitelistError.jpg')
            print("Not whitelist\n")
            return
        
        isImage = False
        if b".ico" in request or b".png" in request or b".jpg" in request: #Bổ sung định dạng khác sau
            isImage = True
            if os.path.exists("image_cache/" + fileName):
                with open("image_cache/" + fileName, 'rb') as file:
                    cached_response = file.read()
                if cached_response:
                    print(f'Image of {url} already been cached!\n')
                    client.sendall(cached_response)
                    return
                
        get_response_from_web(client, client_addr, hostname, request, fileName, isImage)
    finally:
        client.close()

def run():
    # Tạo proxy server và client socket
    proxy_server = socket(AF_INET, SOCK_STREAM)
    
    proxy_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    proxy_server.bind((server_ip, server_port))
    proxy_server.listen(5) 	#Cho socket đang lắng nghe tới tối đa 5 kết nối
    print(f"Proxy Server listen to {server_ip}:{server_port}")
    
    cache_thread = Thread(target=cache_manager)
    cache_thread.start()

    # Nhận HTTP request từ client liên tục
    while True:
        #chấp nhận một kết nối đến từ client và trả về một 
        #đối tượng kết nối để giao tiếp với client và địa chỉ của client (client_addr).
        client, client_addr = proxy_server.accept()
            
        print('Received a connection from:', client_addr)
        
        # Handle request
        thread = Thread(target=handle_http_request, args=(client, client_addr))
        thread.start()

    proxy_server.close()

def main():
    run()

if __name__ == '__main__':
    main()