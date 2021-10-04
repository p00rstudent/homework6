import socket
import logging
from http import HTTPStatus

logging.basicConfig(level=logging.DEBUG)

HOST = "127.0.0.1"
PORT = 10991
BUFFER = 1024


def parse_data(r_data: str) -> dict:
    status_code = 200
    status_name = 'OK'
    rows = r_data.split('\r\n')
    try:
        stats = rows[0].split('/?status=')
        if len(stats) == 2:
            stat_code = int(stats[1].split()[0])
            for stat in HTTPStatus:
                if stat_code == stat.value:
                    status_code = stat_code
                    status_name = stat.name
    except (ValueError, IndexError):
        pass

    return {
        'method': r_data.split()[0],
        'status_code': status_code,
        'status_name': status_name,
        'headers': ''.join([row + '\r\n' for row in rows[1:]])[:-2],
        'request_source': [rows[1].split(':')[1].lstrip(), rows[1].split(':')[2]]
    }


def generate_response(r_data: dict) -> str:
    header = f"HTTP/1.1 {r_data['status_code']} {r_data['status_name']}\r\n"
    method = f"Request Method: {r_data['method']}\r\n"
    source = f"Request Source: ('{r_data['request_source'][0]}',{r_data['request_source'][1]})\r\n"
    status = f"Response Status: {r_data['status_code']} {r_data['status_name']}\r\n"
    return f"{header}{method}{source}{status}{r_data['headers']}"


def generate_html(resp: str):
    body = ''.join([f'<br /> {line}' for line in resp.split('\r\n')[1:]])
    return f'<html>{body}</html>'


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Binding server on {HOST}:{PORT}")
    s.bind((HOST, PORT))

    while True:
        s.listen()
        conn, addr = s.accept()
        with conn:
            data = conn.recv(BUFFER)
            print("Received", data, "from", addr)
            data = data.decode("utf-8")
            data = parse_data(data)
            response = generate_response(data)
            response = f'{response}{generate_html(response)}'
            conn.send(response.encode("utf-8"))
            logging.info(f"Sent '{response}' to {addr}")
            conn.close()
