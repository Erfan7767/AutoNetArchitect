from enum import Enum
class CloudProvider(str,Enum):
    AWS="aws"; AZURE="azure"; GCP="gcp"
class ConnectivityMethod(str,Enum):
    VPN="vpn"; DEDICATED="dedicated"; HYBRID="hybrid"; MULTI_CLOUD="multi_cloud"
