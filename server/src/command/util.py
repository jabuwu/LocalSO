from random import randint

from mailbox import mail_header
from net import packet
from net.buffer import write_string, write_byte

CHAT_RESPONSE_COLOR = 1
CHAT_PUBLIC_COLOR = 2

class CommandError(RuntimeError):
    pass

class UsageError(RuntimeError):
    pass

class Command:
    def __init__(self, name, handler, arg_str='', max_args=0, description='', min_admin_level=250):
        self.name = name
        self.handler = handler
        self.arg_str = arg_str
        self.max_args = max_args
        self.description = description
        self.min_admin_level = min_admin_level

    def handle(self, client, tokens):
        if client.admin < self.min_admin_level:
            _unknown_cmd(client)
            return

        try:
            if len(tokens) - 1 > self.max_args:
                raise UsageError('too many arguments.')
            else:
                self.handler(client, tokens)
                client.logger.info('good command "!%s"' % (' '.join(tokens)))

        except CommandError as e:
            client.logger.info('command error "!%s": %s' % (' '.join(tokens), str(e)))
            _send_chat_response(client, 'Error: %s' % str(e))

        except UsageError as e:
            client.logger.info('usage error "!%s": %s' % (' '.join(tokens), str(e)))
            if len(str(e)) > 0:
                _send_chat_response(client, 'Error: %s' % str(e))
            _send_chat_response(client, 'Usage: %s' % self)

    def __str__(self):
        return '!%s %s' % (self.name, self.arg_str)

def _send_chat_response(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_RESPONSE_COLOR)
    client.send_tcp_message(buff)

def _unknown_cmd(client):
    _send_chat_response(client, 'Unknown command. Type !help for a list of commands.')

def _cmd_error(client):
    _send_chat_response(client, 'An unknown error occured while processing your command.')

# Note: game_server.broadcast locks the game_server.clients list. Be careful not
# to cause deadlocks when using this method
def _send_public_chat(client, chat_str):
    buff = [packet.MSG_CHAT]
    write_string(buff, chat_str)
    write_byte(buff, CHAT_PUBLIC_COLOR)
    client.game_server.broadcast(buff)

def _spawn(client, mob):
    spawn_y = client.get_bbox().bottom() - mob['height'] * mob['scale']
    spawn_x = client.get_bbox().hcenter() + randint(0, 100) - 50
    client.world.send_mail_message(mail_header.MSG_ADD_MOB, (mob['id'], spawn_x, spawn_y, None))
