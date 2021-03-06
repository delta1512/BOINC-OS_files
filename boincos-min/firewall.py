'''
BOINC OS Helper firewall configuration script.
Provides and interface to modifying the firewall within the system.
Authors:
  - Delta
'''

import subprocess as sp
import curses

### DEFINITIONS ###
UP = curses.KEY_UP
DN = curses.KEY_DOWN

### FUNCTIONS ###
# Check ip address function for ensuring correct ipv4 address structure
def check_addr(address):
    # Initialise defaults
    contents = ''
    numcount = 0
    correct_nums = True
    dot_count = 0
    for i, char in enumerate(address):
        if not (char == '.' or char == '/'): # If an alphanumeric character found
            contents += char # Add it to an accumulating string to check later
            numcount += 1 # Count a single (supposedly) number
        else:
            if char == '.': # Check if there is a correct amoung of dots by counting them
                dot_count += 1
            if numcount > 3: # Check if more than 3 digits were input between dots
                correct_nums = False
            numcount = 0 # Reset the counter for numbers
    try:
        int(contents) # Try casting to int
        is_int = True # If it succeeded, mark successful
    except:
        is_int = False # Else mark unsuccessful
    if '/' in address: # If an ip mask exists, check that it is in the correct place
        slash_check = (len(address)-3 <= address.index('/') <= len(address)-2)
    else:
        slash_check = True # If none exists, mark as successful
    return is_int and correct_nums and slash_check and (dot_count == 3) # Return the logic

### START CODE ###
def fw_config():
    # Initiate screen variables
    selection = None
    cursor = [4, 3]
    screen = curses.initscr()
    status_code = None
    # Move into main loop
    while selection != ord('q'):
        screen.keypad(1)
        screen.clear()
        screen.border(0)
        if status_code == None:
            status_code = sp.call('sudo ufw status | grep inactive', shell=True)
        if status_code > 0:
            state = 'ON'
        else:
            state = 'OFF'
        # Add all components to display
        # Navigation labels and buttons
        screen.addstr(1, 1, 'Firewall Configuration:')
        screen.addstr(4, 3, '->\t Current firewall state')
        screen.addstr(6, 3, '->\t Firewall: ' + state)
        screen.addstr(8, 3, '->\t Add firewall rules')
        screen.addstr(10, 3, '->\t Revert to defaults')
        screen.refresh()
        # Fetch and handle user selection
        selection = screen.getch(cursor[0], cursor[1])
        if (selection == UP) and (4 < cursor[0] <= 10):
            cursor[0] -= 2
        elif (selection == DN) and (4 <= cursor[0] < 10):
            cursor[0] += 2
        elif (selection == ord(' ')):
            # Start a new screen
            screen.clear()
            screen.border(0)
            if (cursor[0] == 4):
                screen.addstr(1, 1, 'Current firewall status from UFW:')
                # The following fetches firewall information and prints it to the screen
                fw_state = sp.check_output('sudo ufw status', shell=True) # Get status
                # Initialise defaults
                line_count = 0
                offset = 4
                line = ''
                for char in fw_state: # Go through all the characters of the status
                    if char == '\n': # Check if newline
                        screen.addstr(line_count+offset, 3, line) # Print the line just before it
                        line_count += 1 # Move down a line
                        line = '' # Reset the accumulator
                    else: # If anything else
                        line += char # Add it to the string accumulator
                offset += 1 # Add some padding
                screen.addstr(line_count+offset, 1, 'Press any button to continue...')
                screen.refresh()
                screen.getch(line_count+offset, 32) # Wait for any button
            elif (cursor[0] == 6):
                if state == 'ON':
                    sp.call('fwset off', shell=True)
                else:
                    sp.call('fwset on', shell=True)
                status_code = None
            elif (cursor[0] == 8):
                done = False
                # Move into a new screen loop
                while not done:
                    done = True # Reset the done state
                    # Present the form to the user
                    screen.addstr(1, 1, 'Adding custom firewall rule:')
                    screen.addstr(4, 3, 'Specify port to open:')
                    screen.addstr(6, 3, 'Specify origin address (leave blank for anywhere):')
                    screen.refresh()
                    port = screen.getstr(4, 25, 5)
                    try: # Perform validation
                        done = done and (0 < int(port) < 65536)
                    except:
                        done = done and False
                    ip = screen.getstr(6, 54, 15)
                    if len(ip) > 0: # Perform validation
                        done = done and (7 <= len(ip) <= 18) and check_addr(ip)
                    else:
                        ip = 'Anywhere'
                    if not done:
                        # Notify the user if there was an error
                        screen.addstr(8, 8, '--- Error: invalid entries detected. ---')
                # Move to the command-line screen
                screen.clear()
                screen.border(0)
                screen.addstr(1, 2, 'Attempting to add firewall rule...')
                screen.refresh()
                # Compute a specific line of UFW code
                if ip == 'Anywhere':
                    exit_code = sp.call('sudo ufw allow ' + port, shell=True)
                else:
                    exit_code = sp.call('sudo ufw allow from ' + ip + ' to any port ' + port, shell=True)
                if exit_code == 0:
                    screen.addstr(2, 2, 'Firewall rule added successfully.')
                else:
                    screen.addstr(2, 2, 'Firewall failed to add rule.')
                screen.addstr(4, 2, 'Press any button to continue...')
                screen.refresh()
                screen.getch(4, 33) # Wait for any button
            elif (cursor[0] == 10):
                screen.addstr(1, 2, 'To reset firewall, exit BOINC OS Helper and type "fwset reset"')
                screen.addstr(3, 2, 'Press any button to continue...')
                screen.refresh()
                screen.getch(3, 33)
    curses.endwin()
