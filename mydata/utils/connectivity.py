"""
Functionality related to checking network connectivity
"""
import netifaces

from ..logs import logger


def get_default_interface_type():
    """
    Get default interface type
    """
    default_interface_type = netifaces.AF_INET
    if default_interface_type not in netifaces.gateways()["default"].keys():
        default_interface_type = netifaces.AF_INET6
    if default_interface_type not in netifaces.gateways()["default"].keys():
        default_interface_type = netifaces.AF_LINK
    if default_interface_type not in netifaces.gateways()["default"].keys():
        default_interface_type = None
    return default_interface_type


def get_active_network_interfaces():
    """
    Get active network interfaces
    """
    logger.debug("Determining the active network interface...")
    active_interfaces = []
    default_interface_type = get_default_interface_type()
    if default_interface_type:
        active_interfaces.append(
            netifaces.gateways()["default"][default_interface_type][1]
        )
    return active_interfaces
