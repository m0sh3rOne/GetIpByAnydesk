import os
import sys
import wmi
import psutil
import requests
import datetime
import netifaces

os.system('cls')
exclusionips = []
def get_local_ips() -> list:
    ips = []

    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface).get(netifaces.AF_INET)
        if addrs:
            for addr in addrs:
                exclusionips.append(addr['addr'])
                #print(addr)
            gateway = netifaces.gateways().get('default', {})
            if gateway:
                gateway_ip = gateway.get(netifaces.AF_INET, [])[0]
                if gateway_ip:
                    exclusionips.append(gateway_ip)
                    #print(gateway_ip)

    return ips

def get_ips() -> list:
    wmi_obj = wmi.WMI()
    ips = get_local_ips()

    for process in wmi_obj.Win32_Process():
        try:
            if 'anydesk' in process.Name.lower():
                for conn in psutil.Process(process.ProcessId).connections():
                    if conn.status in ('SYN_SENT', 'ESTABLISHED'):
                        conn_ip = conn.raddr.ip
                        if conn.raddr.port != 80 and not conn_ip.startswith('192.168') and conn_ip not in exclusionips:
                            ips.append(conn_ip)
        except psutil.NoSuchProcess:
            pass

    return ips

def get_ip_info(conn_ip: str) -> dict:
    try:
        response = requests.get(f'http://ip-api.com/json/{conn_ip}')
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        return {
            'NOW': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'IP': conn_ip,
            'Country': data.get('country', 'Unknown'),
            'Region': data.get('regionName', 'Unknown'),
            'City': data.get('city', 'Unknown'),
            'ISP': data.get('isp', 'Unknown')
        }
    except requests.RequestException as e:
        print(f"Error getting info for {conn_ip}: {e}")
        return {}

def try_exit() -> None:
    """Exit from the program"""
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

def main() -> None:
    msg = 'Anydesk is turned off or no one is trying to connect to your monitor, retry... [CTRL+C to exit]'
    while True:
        try:
            ips = get_ips()
            print(' ' * len(msg), flush=False, end='\r')
            if len(ips) > 0:
                for conn_ip in ips:
                    print("Connection Found, infos:")
                    infos = get_ip_info(conn_ip)
                    os.system('cls')
                    for key, value in infos.items():
                        print(f'{key}: {value}')
                    with open("log.txt", 'a') as f:
                        f.write('\n')  # Write an empty line
                        for key, value in infos.items():
                            f.write('%s:%s\n' % (key, value))
                        exclusionips.append(conn_ip)
            else:
                print(msg, flush=True, end='\r')
        except KeyboardInterrupt:
            print('\nProgram finished, exit...')
            try_exit()

if __name__ == '__main__':
    main()
