import urllib.request
import json
from typing import Dict, Any, Optional, List
from config import config

class AIVerseHubClient:
    """Asynchronous/Synchronous client wrapper for AIVerseHub API."""
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or config.aiverse_base_url
        self.api_key = api_key or config.aiverse_api_key

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "TelegramDigitalStore/1.0"
        }

    def get_account_info(self) -> Dict[str, Any]:
        """Fetch account balance and Telegram user info."""
        url = f"{self.base_url}/api/v1/me"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if "data" in data and isinstance(data["data"], dict):
                    return data["data"]
                return data
        except Exception as e:
            return {"error": str(e)}

    def get_products(self) -> List[Dict[str, Any]]:
        """Fetch list of products and current stock levels."""
        url = f"{self.base_url}/api/v1/products"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode())
                if "services" in res:
                    services = res["services"]
                elif "data" in res and "services" in res["data"]:
                    services = res["data"]["services"]
                else:
                    services = []
                
                # Apply profit markup calculation
                for svc in services:
                    wholesale_price = float(svc.get("price", 0.0))
                    markup = config.profit_markup_percent / 100.0
                    svc["retail_price"] = round(wholesale_price * (1 + markup), 2)
                return services
        except Exception as e:
            print(f"Error getting products: {e}")
            return []

    def place_order(self, service_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Place an order for a digital product."""
        url = f"{self.base_url}/api/v1/order"
        payload = json.dumps({
            "service": service_id,
            "quantity": quantity
        }).encode("utf-8")
        
        req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode())
                return {"error": err_body.get("message", e.reason)}
            except Exception:
                return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    def get_orders(self) -> Dict[str, Any]:
        """Fetch order history."""
        url = f"{self.base_url}/api/v1/orders"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}
