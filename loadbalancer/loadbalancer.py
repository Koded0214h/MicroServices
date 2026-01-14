import socket
import threading
import time

class UniversalLoadBalancer:
    def __init__(self, bind_address, port, backends):

        self.address = bind_address
        self.port = port
        
        # FIX 1: Use the same name 'all_backends' everywhere
        self.all_backends = backends  
        
        # FIX 2: Initialize this immediately so it exists for the first request
        self.healthy_backends = list(backends) 
        
        self.current = 0
        self.lock = threading.Lock()

        # Start the background health checker
        threading.Thread(target=self.health_check, daemon=True).start()

    def health_check(self):

        while True:
            alive = []
            for server in self.all_backends:
                try:
                    # Timeout=1 is key so we don't hang the thread on a dead server
                    with socket.create_connection(server, timeout=1):
                        alive.append(server)
                except:
                    print(f"--- SERVER {server[1]} IS DOWN! ---")
            
            with self.lock:
                self.healthy_backends = alive
            
            time.sleep(5) 
        
    def get_next_server(self):

        with self.lock:
            if not self.healthy_backends:
                print("!!! NO HEALTHY BACKENDS AVAILABLE !!!")
                return None
            
            # Use modulo to cycle through only the healthy ones
            server = self.healthy_backends[self.current % len(self.healthy_backends)]
            self.current += 1
            return server

    def proxy_data(self, source, destination):

        try:
            while True:
                data = source.recv(4096)
                if not data:
                    break
                destination.sendall(data)
        except Exception:
            pass
        finally:
            source.close()
            destination.close()

    def handle_request(self, client_conn):

        server_info = self.get_next_server()
        if not server_info:
            client_conn.close()
            return

        backend_host, backend_port = server_info
        backend_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            backend_conn.connect((backend_host, backend_port))
            
            t1 = threading.Thread(target=self.proxy_data, args=(client_conn, backend_conn))
            t2 = threading.Thread(target=self.proxy_data, args=(backend_conn, client_conn))
            
            t1.start()
            t2.start()
        except Exception as e:
            print(f"Failed to connect to backend {backend_port}: {e}")
            client_conn.close()

    def run(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Allow address reuse so you can restart the LB immediately
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.address, self.port))
            s.listen(100)
            print(f"Load Balancer active on {self.address}:{self.port}")
            
            while True:
                client_conn, addr = s.accept()
                threading.Thread(target=self.handle_request, args=(client_conn,)).start()

my_servers = [
    ('127.0.0.1', 8001), 
    ('127.0.0.1', 8002),
    ('127.0.0.1', 8003)
]

lb = UniversalLoadBalancer('0.0.0.0', 80, my_servers)
lb.run()