from socket import *
import os
from threading import Thread
import datetime
import time

server_ip = '127.0.0.1'
server_port = 8888
size = 4096

path = "Image_cache/"
isExist = os.path.exists(path)
if not isExist: # Tạo một folder mới nếu tên folder chưa tồn tại
   os.makedirs(path)
   print("The new directory is created!")
else: # Nếu folder đã tồn tại thì xóa hết File ở trong
    for file in os.listdir(path):
        os.remove(path + file)

#Lưu dữ liệu từ file Config
def read_config_file(filename):
    whitelist = []
    cache_duration = None
    time_start = None
    time_end = None
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('Cache_Time'):
                cache_duration = int(line.split()[1])
            elif line.startswith('Time_start'):
                time_start = int(line.split()[1])
            elif line.startswith('Time_end'):
                time_end = int(line.split()[1])
            else:
                whitelist.append(line)
    return whitelist, cache_duration, time_start, time_end

# Load các thông tin đọc từ File vào Global Varible
whitelist, cache_duration, time_start, time_end = read_config_file("config.txt")

# Hàm check Thời gian tồn tại của Cache file
def cache_manager():
    while True:
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            time_start = os.path.getctime(file_path) #Lấy thời gian file 
            time_end = time.time()
            if time_end - time_start > cache_duration:
                os.remove(file_path)
                print(f'Your Image Cached file: {file_name} has been reset')
        time.sleep(15*60)

# Hàm kiểm tra thời gian hiện tại có nằm trong thời gian hoạt động của Server
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

# Hàm kiểm tra Hostname có nằm trong danh sách Những web có hostname được truy cập
def check_whitelist(input_website, whitelist):
    for website in whitelist:
        if website in input_website:
            return True
    return False

# Hàm trả về HTTP Response kèm mã 403 Forbidden và nội dung của response (lý do bị 403)
def send_image_response(client, image_name):
    #b'HTTP/1.1 403 Forbidden\r\nContent-Type: image/jpeg\r\n\r\n'
    #full_response = http_response + image_data
    image_path = os.path.join("403Forbidden", image_name)
    with open(image_path, 'rb') as f:
        data = f.read()
        response = b'HTTP/1.1 403 Forbidden\r\n'
        response += b'Content-Type: image/jpeg\r\n\r\n'
        response += data
        client.sendall(response) 
        client.close()

# Hàm nhận phản hồi từ Web gửi về        
def get_response_from_web(client, client_addr, hostname, request, fileName, isImage):
    # Socket từ Proxy tới Server
    web_server = socket(AF_INET, SOCK_STREAM)
    
    web_ip = gethostbyname(hostname)
    web_server.connect((web_ip, 80)) # 80 là port của HTTP

    # Gửi request đến Server
    web_server.sendall(request)

    response = b""
    response += web_server.recv(size)
    client.sendall(response) 
    
    # Content Length
    if b"Content-Length:" in response: 
        # Tách các dòng trong response
        lines = response.decode('ISO-8859-1').split('\r\n')
        
        for line in lines:
            if "Content-Length" in line:
                content_length_line = line

        content_length = int(content_length_line.split(': ')[1])
        
        while len(response) < content_length:
            data = web_server.recv(size)
            if data:
                client.sendall(data)
            response += data
    else: #Transfer-Ecoding: chunked
        while response.find(b"\r\n0\r\n\r\n") == -1:
            data = web_server.recv(size)
            if not data:
                return
            client.sendall(data)
            response += data
    
    #Nếu đúng là định dạng ảnh thì lưu toàn bộ response vào file
    if isImage:
        with open(path + fileName, 'wb') as file:
            file.write(response)
    web_server.close()
    client.close()

# Hàm xử lý HTTP Request
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
            print("Out of Server's Active Time range. Access Denied!\n")
            return
        
        # Check if HTTP request is supported
        if method not in ['GET', 'POST', 'HEAD']:
            send_image_response(client, 'HTTPRequestError.jpg')
            # HTTP request not supported
            print("This HTTP Request is not supported!\n")
            return

        # Extract hostname from URL
        hostname = url.split('/')[2]
        # print(f"HTTP Request: {method}")
        # print(f"URL: {url}")
        # print(f"Host: {hostname}")
        fileName = url.replace('http://', '').replace('/', '_')
        if '?' in fileName:
            fileName = fileName.split('?')[0]
        
        # Whitelist
        if not check_whitelist(hostname, whitelist):
            send_image_response(client, 'WhitelistError.jpg')
            print("Hostname of the Website is not on the Whitelist!\n")
            return
        
        isImage = False
        if b".ico" in request or b".png" in request or b".jpeg" in request or b".jpg" in request or b".gif" in request or b".webp" in request or b".svg" in request: #Scalable Vector Graphics
            isImage = True
            if os.path.exists(path + fileName):
                with open(path + fileName, 'rb') as file:
                    cached_response = file.read()
                if cached_response:
                    print(f'Image of {url} already been cached!\n')
                    client.sendall(cached_response)
                    return
                
        get_response_from_web(client, client_addr, hostname, request, fileName, isImage)
    finally:
        client.close()

# Hàm tạo Proxy Server và Nhận kết nối từ Client
def run():
    # Tạo proxy server và client socket
    proxy_server = socket(AF_INET, SOCK_STREAM)
    
    proxy_server.bind((server_ip, server_port))
    proxy_server.listen(5) 	#Cho socket đang lắng nghe tới tối đa 5 kết nối
    print(f"Proxy Server listen to {server_ip}:{server_port}")
    print(f"Server's Active Time: {time_start} - {time_end}")
    
    cache_thread = Thread(target=cache_manager)
    cache_thread.start()

    # Nhận HTTP request từ client liên tục
    while True:
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