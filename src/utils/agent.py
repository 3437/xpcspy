from pathlib import Path
from collections import OrderedDict

import frida
import click

from lib.types import Event


_pending_events = OrderedDict()  # A map of stacks, each stack holding events for that particular timestamp


class Agent:
    def __init__(self, target, device, os, filter):
        self.device = device
        self._script_path = Path.joinpath(Path().absolute(), '../_agent.js') 
        with open(self._script_path) as src_f:
            self._script_src = src_f.read()
        session = frida.attach(target)  # `target` is str or int depending on whether it's a name or pid
        self._script = session.create_script(self._script_src)
        self._script.on('message', Agent.on_message)
        self._script.load() 
        self._script.exports.set_up(os, filter)
    

    @staticmethod
    def on_message(message, data):
        print(message)
        timestamp = message['payload']['message']['timestamp']

        if message['payload']['type'] == 'agent:trace:symbol':
            symbol = message['payload']['message']['symbol']
            if timestamp in _pending_events:
                _pending_events[timestamp].append(Event(symbol)) 
                #print(f"Update {timestamp}")
            else:
                _pending_events.update({ timestamp: [Event(symbol)] })
                #print(f"Add {timestamp}")

        elif message['payload']['type'] == 'agent:trace:data':
            data = message['payload']['message']['data']
            _pending_events[timestamp][-1].data = data

        Agent.flush_pending_events()


    @staticmethod
    def flush_pending_events():
        """Flush pending events that are ready, i.e. have received both its symbol and data"""
        for ts, events_stack in list(_pending_events.items()):
            while len(events_stack) > 0:
                last_event = events_stack[-1]  # Peek
                if last_event.data == None:
                    return
                #print(f"Pop {ts}")
                print('\n' + '-' * 60)
                print(f"{last_event.symbol}\n{last_event.data['conn']}\n{last_event.data['message']}")
                print('-' * 60 + '\n')
                events_stack.pop()
            del _pending_events[ts]
