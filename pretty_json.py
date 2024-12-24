import sys
import json
import subprocess
from datetime import datetime
from collections import deque
import shutil
import os
import curses
from curses import wrapper
import time
from rich.console import Console
from rich.table import Table
from rich.text import Text

class Colors:
    # Curses color pairs
    HEADER = 1
    BLUE = 2
    CYAN = 3
    GREEN = 4
    YELLOW = 5
    RED = 6
    GRAY = 7
    WHITE = 8

def init_colors():
    """Initialize color pairs for curses"""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(Colors.HEADER, curses.COLOR_MAGENTA, -1)
    curses.init_pair(Colors.BLUE, curses.COLOR_BLUE, -1)
    curses.init_pair(Colors.CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(Colors.GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(Colors.YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(Colors.RED, curses.COLOR_RED, -1)
    curses.init_pair(Colors.GRAY, curses.COLOR_WHITE, -1)
    curses.init_pair(Colors.WHITE, curses.COLOR_WHITE, -1)

# Command line arguments
raw = "--raw" in sys.argv
test = "--test" in sys.argv
error = "--error" in sys.argv

# Variable tracking
var_history = {}
MAX_VARS = 10
MAX_HISTORY = 5

def format_timestamp(time_str):
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
        return dt.strftime("%H:%M:%S.%f")[:-3]  # Show only up to milliseconds
    except:
        return time_str

def print_separator(pad, y):
    width = curses.COLS - 1
    pad.addstr(y, 0, "─" * width, curses.color_pair(Colors.GRAY))
    return y + 1

def update_var_history(variables):
    """Update variable history with new values"""
    for var, value in variables.items():
        if var not in var_history:
            if len(var_history) >= MAX_VARS:
                oldest = next(iter(var_history))
                del var_history[oldest]
            var_history[var] = deque(maxlen=MAX_HISTORY)
        var_history[var].appendleft(value)

def extract_sm_vars(parsed_json):
    """Extract variables from the log message"""
    sm_vars = {}
    
    # Handle --SM messages
    if parsed_json.get('message2', '').startswith('--SM'):
        # Get the variable names from message2
        var_names = parsed_json['message2'].replace('--SM', '').strip().split(',')
        var_names = [name.strip() for name in var_names]
        
        # Get values from subsequent messages
        for i, var_name in enumerate(var_names, start=3):  # start from message3
            message_key = f'message{i}'
            var_value = parsed_json.get(message_key, '').strip()
            
            if var_value:
                try:
                    # Try to parse JSON value
                    json_value = json.loads(var_value)
                    var_value = json.dumps(json_value, separators=(',', ':'))
                except:
                    pass
            sm_vars[var_name] = var_value
    
    # Handle messages with file paths and values
    elif parsed_json.get('message1', '') and 'LOGGG<<' in parsed_json['message1']:
        parts = parsed_json['message1'].split('LOGGG<<')[1].split('>>')[0].split(':')
        if len(parts) >= 3:
            var_name = parts[-2]  # Get the function name
            if parsed_json.get('message3', ''):
                var_value = parsed_json['message3']
                try:
                    # Try to parse JSON value
                    json_value = json.loads(var_value)
                    var_value = json.dumps(json_value, separators=(',', ':'))
                except:
                    pass
                sm_vars[var_name] = var_value
    
    return sm_vars

def split_path(value):
    """Split a path into segments that can be wrapped"""
    if '=>' in value:
        # Split by => for stack traces
        return value.split('=>')
    elif '/' in value:
        # Split by / for file paths
        return [part + '/' for part in value.split('/') if part]
    else:
        # Default to word splitting
        return value.split()

def draw_var_table(stdscr):
    """Draw the variable history table at the top of the screen"""
    width = curses.COLS - 1
    y = 0
    
    # Draw table border
    stdscr.addstr(y, 0, "┌" + "─" * (width - 2) + "┐", curses.color_pair(Colors.GRAY))
    y += 1
    
    # Draw header
    header = " Variable History "
    stdscr.addstr(y, 0, "│", curses.color_pair(Colors.GRAY))
    stdscr.addstr(header, curses.color_pair(Colors.WHITE) | curses.A_BOLD)
    stdscr.addstr(" " * (width - len(header) - 2) + "│", curses.color_pair(Colors.GRAY))
    y += 1
    
    if not var_history:
        stdscr.addstr(y, 0, "│" + " " * (width - 2) + "│", curses.color_pair(Colors.GRAY))
        y += 1
    else:
        # Sort variables alphabetically
        sorted_vars = sorted(var_history.items(), key=lambda x: x[0].lower())
        
        # Draw variables
        for var, history in sorted_vars:
            # Start the line with variable name
            stdscr.addstr(y, 0, "│ ", curses.color_pair(Colors.GRAY))
            stdscr.addstr(var, curses.color_pair(Colors.YELLOW))
            stdscr.addstr(": ", curses.color_pair(Colors.WHITE))
            
            indent = len(var) + 4  # "│ " + var + ": "
            current_x = indent
            
            # Add history values with arrows (reversed order)
            history_list = list(history)  # Convert deque to list for easier indexing
            for i, value in enumerate(history_list):
                # Calculate remaining width for this value
                remaining_width = width - current_x - 2  # -2 for right border and space
                if i < len(history_list) - 1:
                    remaining_width -= 3  # Space for " ← "
                
                # If value fits in remaining width
                if len(value) <= remaining_width:
                    stdscr.addstr(value, curses.color_pair(Colors.CYAN))
                    current_x += len(value)
                    if i < len(history_list) - 1:
                        stdscr.addstr(" ← ", curses.color_pair(Colors.GRAY))
                        current_x += 3
                else:
                    # Value needs to wrap
                    segments = split_path(value)
                    line = ""
                    
                    for segment in segments:
                        # If this segment would make the line too long, wrap
                        if len(line) + len(segment) + 1 > remaining_width and line:
                            # Fill current line
                            stdscr.addstr(line.rstrip(), curses.color_pair(Colors.CYAN))
                            # Move to next line
                            y += 1
                            stdscr.addstr(y, 0, "│ ", curses.color_pair(Colors.GRAY))
                            stdscr.addstr(" " * (indent - 2), curses.color_pair(Colors.WHITE))
                            line = segment
                            current_x = indent
                            remaining_width = width - current_x - 2
                        else:
                            # Add segment to current line
                            if line:
                                line += segment
                            else:
                                line = segment
                    
                    # Output any remaining text
                    if line:
                        stdscr.addstr(line.rstrip(), curses.color_pair(Colors.CYAN))
                        current_x += len(line)
                    
                    # Add arrow if needed
                    if i < len(history_list) - 1:
                        if current_x + 3 > width - 2:
                            y += 1
                            stdscr.addstr(y, 0, "│ ", curses.color_pair(Colors.GRAY))
                            stdscr.addstr(" " * (indent - 2), curses.color_pair(Colors.WHITE))
                            current_x = indent
                        stdscr.addstr(" ← ", curses.color_pair(Colors.GRAY))
                        current_x += 3
            
            # Fill remaining space on the last line
            padding = width - current_x - 1
            if padding > 0:
                stdscr.addstr(" " * padding)
            stdscr.addstr("│", curses.color_pair(Colors.GRAY))
            y += 1
    
    # Draw table footer
    stdscr.addstr(y, 0, "└" + "─" * (width - 2) + "┘", curses.color_pair(Colors.GRAY))
    y += 1
    
    return y + 1  # Return next line position

def format_log_line(pad, y, line, attrs=0):
    """Format a single line of log with proper color attributes"""
    try:
        # Get maximum width of the pad
        max_width = pad.getmaxyx()[1] - 1
        
        # If line is longer than pad width, wrap it
        if len(line) > max_width:
            # Write as much as we can
            pad.addstr(y, 0, line[:max_width], attrs)
            # Continue on next line(s)
            remaining = line[max_width:]
            while remaining:
                y += 1
                chunk = remaining[:max_width]
                pad.addstr(y, 0, chunk, attrs)
                remaining = remaining[max_width:]
        else:
            pad.addstr(y, 0, line, attrs)
    except curses.error:
        pass  # Ignore curses errors
    
    return y + 1

def format_log_message(pad, y, parsed_json, line):
    """Format the log message with proper structure and colors"""
    if parsed_json.get('message1') and 'LOGGG' in parsed_json['message1']:
        # Format based on message type
        if parsed_json.get('message2') and '--SM' in parsed_json['message2']:
            for key, value in parsed_json.items():
                if key == 'time_micro':
                    continue
                if "message" in key:
                    key = key.replace('message', 'M')
                if key == 'M1':
                    value = value.replace('LOGGG<<', '').replace('>>LOGGG', '').split(':')
                    pad.addstr(y, 0, f" {key}: ", curses.color_pair(Colors.YELLOW))
                    pad.addstr(value[0], curses.color_pair(Colors.GREEN))
                    pad.addstr(f" {value[1]} ", curses.A_BOLD)
                    pad.addstr(value[2], curses.color_pair(Colors.GREEN))
                    pad.addstr(": ", curses.color_pair(Colors.WHITE))
                    y += 1
                elif value and value != '--SM':  # Skip empty values and bare --SM
                    value = value.replace('--SM', '').strip()
                    if value:  # Only print if there's content after removing --SM
                        pad.addstr("│", curses.color_pair(Colors.GRAY))
                        pad.addstr(value, curses.color_pair(Colors.CYAN))
                        pad.addstr("│", curses.color_pair(Colors.GRAY))
        else:
            # Add timestamp for non-SM messages
            if 'time_micro' in parsed_json:
                timestamp = format_timestamp(parsed_json['time_micro'])
                y = format_log_line(pad, y, f"[{timestamp}]", curses.color_pair(Colors.GRAY))
            
            y = format_log_line(pad, y, "┌──", curses.color_pair(Colors.GRAY))
            for key, value in parsed_json.items():
                if "message" in key:
                    key = key.replace('message', 'M')
                if key == 'time_micro':
                    key = 'T'
                if key == 'M1':
                    value = value.replace('LOGGG<<', '').replace('>>LOGGG', '').split(':')
                    line = f" {key}: {value[0]} {value[1]} {value[2]}"
                    y = format_log_line(pad, y, line, curses.color_pair(Colors.GREEN))
                else:
                    if (value.startswith('{') or value.startswith('[')) and (value.endswith('}') or value.endswith(']')) and not raw:
                        try:
                            formatted_json = json.dumps(json.loads(value), indent=2)
                            y = format_log_line(pad, y, f" {key}: {formatted_json}", curses.color_pair(Colors.CYAN))
                        except:
                            y = format_log_line(pad, y, f" {key}: {value}", curses.color_pair(Colors.CYAN))
                    else:
                        y = format_log_line(pad, y, f" {key}: {value}", curses.color_pair(Colors.CYAN))
            y = format_log_line(pad, y, "└──", curses.color_pair(Colors.GRAY))
        
        y = print_separator(pad, y)
    else:
        # For non-LOGGG messages, just add the raw line
        y = format_log_line(pad, y, line.strip())
    
    return y

def process_logs(stdscr):
    # Initialize curses
    init_colors()
    curses.curs_set(0)  # Hide cursor
    stdscr.scrollok(True)
    stdscr.idlok(True)
    
    # Set up container and process
    container = 'tests-php-1' if test else 'rcms-126931-php-1'
    process = subprocess.Popen(
        ['docker', 'logs', '-f', '--tail', '10', container],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stream = process.stdout if test else process.stderr
    
    # Create a pad for scrolling logs with extra width for long messages
    pad_height = 1000  # Adjust as needed
    pad_width = max(curses.COLS * 2, 500)  # Make pad wider than screen
    log_pad = curses.newpad(pad_height, pad_width)
    log_pad.scrollok(True)
    current_pad_line = 0
    
    # Draw initial table
    log_start_y = draw_var_table(stdscr)
    stdscr.refresh()
    
    try:
        for line in stream:
            try:
                if "lite_mode=1" in line:
                    continue
                
                parsed_json = json.loads(line)
                blacklist = ['time', 'site_id', 'app', 'level', 'severity', 'mode', 'rcms_request_id', 
                           'remote_addr', 'ua', 'sess_id', 'member_id', 'host', 'uri', 'message']
                for key in blacklist:
                    parsed_json.pop(key, None)

                # Extract and update variables
                sm_vars = extract_sm_vars(parsed_json)
                if sm_vars:
                    # Update variables and redraw table
                    update_var_history(sm_vars)
                    stdscr.clear()  # Clear the screen before redrawing
                    log_start_y = draw_var_table(stdscr)
                    stdscr.refresh()
                
                # Format and display log
                current_pad_line = format_log_message(log_pad, current_pad_line, parsed_json, line)
                
                # Calculate visible area
                visible_lines = curses.LINES - log_start_y
                scroll_pos = max(0, current_pad_line - visible_lines)
                
                # Refresh the pad display with horizontal scroll support
                try:
                    log_pad.refresh(scroll_pos, 0,  # source start line and column
                                  log_start_y, 0,   # destination start line and column
                                  curses.LINES - 1, curses.COLS - 1)  # destination end line and column
                except curses.error:
                    pass  # Ignore refresh errors
                
            except json.JSONDecodeError:
                current_pad_line = format_log_line(log_pad, current_pad_line, line.strip())
                try:
                    log_pad.refresh(max(0, current_pad_line - curses.LINES + log_start_y), 0,
                                  log_start_y, 0,
                                  curses.LINES - 1, curses.COLS - 1)
                except curses.error:
                    pass
                
    except KeyboardInterrupt:
        process.terminate()


def main():
    try:
        wrapper(process_logs)
    finally:
        # Clean up
        os.system('clear')

if __name__ == "__main__":

        main()
