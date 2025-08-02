from nordvpn_switcher import initialize_VPN, rotate_VPN, terminate_VPN
import time

instructions = initialize_VPN(area_input=["Croatia"])


# Denmark
# Korea
# Algeria
# Andorra
# Brazil
# Senegal  

# [Denmark,South Korea,Brazil,Algeria,Andorra,Brazil]
rotate_VPN(instructions)
time.sleep(20)