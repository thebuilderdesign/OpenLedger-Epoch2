from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, base64, uuid, json, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class OepnLedger:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "*/*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Storage-Access": "active",
            "User-Agent": FakeUserAgent().random
        }
        self.EXTENSION_ID = "chrome-extension://ekbbplmjjgoobhdlffmgeokalelnmjjc"
        self.BROWSER_ID = {}
        self.WORKER_ID = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Ping {Fore.BLUE + Style.BRIGHT}OpenLedger - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<by. Chan Cr>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def generate_register_payload(self, address: str):
        register_message = {
            "workerID":self.WORKER_ID[address],
            "msgType":"REGISTER",
            "workerType":"LWEXT",
            "message":{
                "id":self.BROWSER_ID[address],
                "type":"REGISTER",
                "worker":{
                    "host":self.EXTENSION_ID,
                    "identity":self.WORKER_ID[address],
                    "ownerAddress":address,
                    "type":"LWEXT"
                }
            }
        }
        return register_message
    
    def generate_heartbeat_payload(self, address: str):
        heartbeat_message = {
            "message":{
                "Worker":{
                    "Identity":self.WORKER_ID[address],
                    "ownerAddress":address,
                    "type":"LWEXT",
                    "Host":self.EXTENSION_ID,
                    "pending_jobs_count":0
                },
                "Capacity":{
                    "AvailableMemory":round(random.uniform(0, 32), 2),
                    "AvailableStorage":str(round(random.uniform(0, 500), 2)),
                    "AvailableGPU":"",
                    "AvailableModels":[]
                }
            },
            "msgType":"HEARTBEAT",
            "workerType":"LWEXT",
            "workerID":self.WORKER_ID[address]
        }
        return heartbeat_message
    
    def generate_browser_id(self):
        browser_id = str(uuid.uuid4())
        return browser_id
        
    def generate_worker_id(self, adrress: str):
        identity = base64.b64encode(adrress.encode("utf-8")).decode("utf-8")
        return identity
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account

    def print_message(self, account, proxy, color, message):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}[ Account:{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(account)} {Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT}-{Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT} Proxy: {Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT}{proxy}{Style.RESET_ALL}"
            f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}Status:{Style.RESET_ALL}"
            f"{color + Style.BRIGHT} {message} {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}]{Style.RESET_ALL}"
        )

    def print_question(self):
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

    async def nodes_communicate(self, address: str, token: str, payload: dict, use_proxy: bool, proxy=None, retries=3):
        url = "https://apitn.openledger.xyz/ext/api/v2/nodes/communicate"
        data = json.dumps(payload)
        headers = {
            **self.headers,
            "Authorization": f"Bearer {token}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        while True:
            for attempt in range(retries):
                connector = ProxyConnector.from_url(proxy) if proxy else None
                try:
                    async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                        async with session.post(url=url, headers=headers, data=data, ssl=False) as response:
                            response.raise_for_status()
                            return await response.json()
                except (Exception, ClientResponseError) as e:
                    if "403" in str(e):
                        self.print_message(address, proxy, Fore.RED, f"Communicate Failed: {Fore.YELLOW + Style.BRIGHT}Ip Blocked By OpenLedger Server")
                        await asyncio.sleep(5)
                    else:
                        if attempt < retries - 1:
                            await asyncio.sleep(30)
                            continue
                        self.print_message(address, proxy, Fore.RED, f"Communicate Failed: {Fore.YELLOW + Style.BRIGHT}{str(e)}")
                    proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                    continue
        
    async def process_registering_node(self, address: str, token: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        payload = self.generate_register_payload(address)

        registered = await self.nodes_communicate(address, token, payload, use_proxy, proxy)
        if registered:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            self.print_message(address, proxy, Fore.GREEN, "Communicate Success" 
                f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Node Registered{Style.RESET_ALL}"
            )

        return True
        
    async def process_send_heartbeat(self, address: str, token: str, use_proxy: bool):
        payload = self.generate_heartbeat_payload(address)
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            heartbeat = await self.nodes_communicate(address, token, payload, use_proxy, proxy)
            if heartbeat:
                proxy = self.get_next_proxy_for_account(address) if use_proxy else None
                self.print_message(address, proxy, Fore.GREEN, "Communicate Success" 
                    f"{Fore.MAGENTA + Style.BRIGHT} - {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}Heartbeat Sended{Style.RESET_ALL}"
                )

            await asyncio.sleep(5 * 60)
        
    async def process_accounts(self, address: str, token: str, use_proxy: bool):
        is_registered = await self.process_registering_node(address, token, use_proxy)
        if is_registered:
            await self.process_send_heartbeat(address, token, use_proxy)

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}")
                return
            
            use_proxy_choice = self.print_question()

            use_proxy = False
            if use_proxy_choice in [1, 2]:
                use_proxy = True

            self.clear_terminal()
            self.welcome()
            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
            )

            if use_proxy:
                await self.load_proxies(use_proxy_choice)

            self.log(f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"*75)

            while True:
                tasks = []
                for account in accounts:
                    if account:
                        address = account["Address"]
                        token = account["Token"]

                        if address and token:
                            self.WORKER_ID[address] = self.generate_worker_id(address)
                            self.BROWSER_ID[address] = self.generate_browser_id()

                            tasks.append(asyncio.create_task(self.process_accounts(address, token, use_proxy)))

                await asyncio.gather(*tasks)
                await asyncio.sleep(10)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = OepnLedger()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Open Ledger - BOT{Style.RESET_ALL}                                       "                              
        )
