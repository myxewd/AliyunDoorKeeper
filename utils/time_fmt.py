def format_time(n: int) -> str:
    units = [
        ('day', 86400),  # 1 day = 86400 seconds
        ('hour', 3600),  # 1 hour = 3600 seconds
        ('minute', 60),  # 1 minute = 60 seconds
        ('second', 1)    # 1 second = 1 second
    ]

    time_components = []

    for unit, seconds_in_unit in units:
        value = n // seconds_in_unit
        if value > 0:
            n %= seconds_in_unit
            time_components.append(f"{value} {unit}{'s' if value > 1 else ''}")

    if len(time_components) == 0:
        return "0 seconds"
    elif len(time_components) == 1:
        return time_components[0]
    else:
        return ', '.join(time_components[:-1]) + ' and ' + time_components[-1]