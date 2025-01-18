def filter_x_forwarded_for(xff_header, ips_to_remove):
    """
    Resolves the X-Forwarded-For header, 
    strips out the specified IP address, 
    and returns the reassembled X-Forwarded-For format.
    
    :param xff_header: The original X-Forwarded-For header
    :param ip_to_remove: A list of IP addresses to exclude
    :return: The processed X-Forwarded-For header
    """
    
    ip_list = [ip.strip() for ip in xff_header.split(",")]
    filtered_ips = [ip for ip in ip_list if ip not in ips_to_remove]
    return ", ".join(filtered_ips)