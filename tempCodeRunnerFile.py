

def send_image_response(client, image_path):
    #b'''HTTP/1.1 403 Forbidden\r\nContent-Type: image/jpeg\r\n\r\n'''
    #full_response = http_response + image_data
    with open(image_path, 'rb') as f:
        data = f.read()
        response = b'HTTP/1.1 403 Forb