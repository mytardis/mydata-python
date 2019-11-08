"""
Functionality related to checking network connectivity
"""
import netifaces

from ..logs import logger


def GetDefaultInterfaceType():
    """
    Get default interface type
    """
    defaultInterfaceType = netifaces.AF_INET
    if defaultInterfaceType not in netifaces.gateways()['default'].keys():
        defaultInterfaceType = netifaces.AF_INET6
    if defaultInterfaceType not in netifaces.gateways()['default'].keys():
        defaultInterfaceType = netifaces.AF_LINK
    if defaultInterfaceType not in netifaces.gateways()['default'].keys():
        defaultInterfaceType = None
    return defaultInterfaceType


def GetActiveNetworkInterfaces():
    """
    Get active network interfaces
    """
    logger.debug("Determining the active network interface...")
    activeInterfaces = []
    defaultInterfaceType = GetDefaultInterfaceType()
    if defaultInterfaceType:
        activeInterfaces.append(
            netifaces.gateways()['default'][defaultInterfaceType][1])
    return activeInterfaces
