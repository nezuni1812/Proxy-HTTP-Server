import time


def readFile(file_path):
    whitelist = [] # emty list to store whitelisted websites
    # https://www.freecodecamp.org/news/with-open-in-python-with-statement-syntax-example/
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("whitelisting="):
                whitelist = line[len("whitelisting="):].split(', ')  # tach chuoi
    return whitelist

def check_whitelist(input_website, whitelist):
    for website in whitelist:
        if website in input_website:
            return True
    return False

file_path = "config.txt"
whitelist = readFile(file_path)
while True:
    input_website = input("Enter a website (or 'exit' to quit): ")
    if input_website.lower() == "exit":
        break
    if check_whitelist(input_website, whitelist):
        print("Connecting...")
    else:
        print("Access denied")