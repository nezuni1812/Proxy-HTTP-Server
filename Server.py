from socket import *
import sys

if len(sys.argv) < 2:
    print('Usage : "python Server.py [Adress of Server]')
    sys.exit(0)

size = 1024
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

def handle_http_request(client, message):
    request_line = message.split('\r\n')[0]
    request, url, version = request_line.split()

    # Check if HTTP request is supported
    if request not in ['GET', 'POST', 'HEAD']:
        # HTTP request not supported
        client.close()
        print("Not support HTTP request")
        return

    # Extract hostname from URL
    hostname = url.split('/')[2]
    print(f"HTTP Request: {request}")
    print(f"URL: {url}")
    print(f"Host: {hostname}\n")
    
    # Whitelist
    if not check_whitelist(url, whitelist):
        client.close()
        print("Not whitelist")
        return

def main():
    # Tạo proxy server và client socket
    proxy_server = socket(AF_INET, SOCK_STREAM)
    
    # Reuse a local address that is still in the TIME_WAIT state
    proxy_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    proxy_server.bind((server_ip, server_port))
    proxy_server.listen(5)

    # Nhận HTTP request từ client liên tục
    while True:
        #chấp nhận một kết nối đến từ client và trả về một 
        #đối tượng kết nối để giao tiếp với client và địa chỉ của client (client_addr).
        client, client_addr = proxy_server.accept()
        print('Received a connection from:', client_addr)
        request = client.recv(size)
        message = request.decode('ISO-8859-1') 

        # Handle request
        handle_http_request(client, message)
    
    proxy_server.close()

if __name__ == '__main__':
    main()