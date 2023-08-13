from socket import *
import sys
from threading import Thread

if len(sys.argv) < 2:
    print('Usage : "python Server.py [Adress of Server]')
    sys.exit(0)

size = 65536
server_ip = sys.argv[1]
server_port = 8888

def readFile(file_path):
    whitelist = [] # emty list to store whitelisted websites
    # https://www.freecodecamp.org/news/with-open-in-python-with-statement-syntax-example/
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("whitelisting="):
                whitelist = line[len("whitelisting="):].split(', ')  # tach chuoi
    return whitelist

whitelist = readFile("config.txt")

def check_whitelist(input_website, whitelist):
    for website in whitelist:
        if website in input_website:
            return True
    return False

def send_image_response(client, image_path):
    #b'''HTTP/1.1 403 Forbidden\r\nContent-Type: image/jpeg\r\n\r\n'''
    #full_response = http_response + image_data
    with open(image_path, 'rb') as f:
        data = f.read()
        response = b'HTTP/1.1 403 Forbidden\r\n'
        response += b'Content-Type: image/jpeg\r\n\r\n'
        response += data
        client.sendall(response) 
        client.close()
        
def get_response_from_web(client, client_addr, hostname, request):
    print(request)
    # Create a new socket to connect to the web server
    web_server_socket = socket(AF_INET, SOCK_STREAM) #NHỚ ĐỔI TÊN BIẾN
    web_server_ip = gethostbyname(hostname)
    web_server_socket.connect((web_server_ip, 80)) #80 là port của HTTP

    # Send the request to the web server
    web_server_socket.sendall(request)

    # Receive the response from the web server
    
    response = b''
    response += web_server_socket.recv(size)
    print(response)
    print('\n')

    client.send(response)

    # Close the connection to the web server
    web_server_socket.close()
    client.close()

def handle_http_request(client, client_addr):
    request = client.recv(size)
    message = request.decode('ISO-8859-1') 
    if len(message.split()) > 1:
        request_line = message.split('\r\n')[0]
        method, url, version = request_line.split()
    else:
        client.close()
        return

    # Check if HTTP request is supported
    if method not in ['GET', 'POST', 'HEAD']:
        send_image_response(client, 'HTTPRequestError.jpg')
        # HTTP request not supported
        print("Not support HTTP request")
        return

    # Extract hostname from URL
    hostname = url.split('/')[2]
    print(f"HTTP Request: {method}")
    print(f"URL: {url}")
    print(f"Host: {hostname}")
    
    # Whitelist
    if not check_whitelist(hostname, whitelist):
        send_image_response(client, 'WhitelistError.jpg')
        print("Not whitelist")
        return
    
    get_response_from_web(client, client_addr, hostname, request)

def run():
    # Tạo proxy server và client socket
    proxy_server = socket(AF_INET, SOCK_STREAM)
    
    proxy_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    proxy_server.bind((server_ip, server_port))
    proxy_server.listen(5) 	#Cho socket đang lắng nghe tới tối đa 5 kết nối
    print(f"Proxy Server listen to {server_ip}:{server_port}")

    # Nhận HTTP request từ client liên tục
    while True:
        #chấp nhận một kết nối đến từ client và trả về một 
        #đối tượng kết nối để giao tiếp với client và địa chỉ của client (client_addr).
        client, client_addr = proxy_server.accept()
        print('Received a connection from:', client_addr)
        # Handle request
        
        thread = Thread(target=handle_http_request, args=(client, client_addr))
        thread.daemon = True
        thread.start()

    proxy_server.close()

def main():
    run()

if __name__ == '__main__':
    main()