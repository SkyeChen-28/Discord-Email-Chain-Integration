# Discord packaages
import discord as dc
from discord.ext import commands

# File manipulation packages
import json
import pandas as pd

# Email packages
import smtplib
import aioimaplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.parser import BytesHeaderParser, BytesParser

# Misc
import os
from os.path import basename
import getpass
import asyncio
from asyncio import get_event_loop, wait_for
from collections import namedtuple
from typing import Collection, Union
import re
from htmlvalidation import HTMLValidator
from markdownify import markdownify
from datetime import datetime as dt
from datetime import timedelta
from dateutil import parser

# Set global variables
class DeciConsts:
    '''
    A class containing global constants for DECI
    
    Attributes:
        `deci_config_dir`
        `email_user`
        `email_pass`
        `COMMAND_PREFIX`
        `bot` (Only if enter_fields is true)
    '''
    
    def __init__(self, enter_fields = False):
        '''
        Define the attributes of DeciConsts

        Args:
            enter_fields (bool, optional): If true, will prompt admin to input some values for some fields. Defaults to False.
        '''
        self.deci_config_dir = 'deci_config.json'
        self.email_user = os.getenv('DC_OUTLOOK_ADDR')
        self.email_pass = os.getenv('DC_OUTLOOK_PASS')
            
        # Discord related constants
        intents = dc.Intents.default()
        self.COMMAND_PREFIX = '<:9beggingLuz:872186647679230042>' 
         
        if enter_fields:
            # Initialize a Discord client
            self.bot = commands.Bot(command_prefix=self.COMMAND_PREFIX, intents = intents) 
            if (self.email_pass is None):
                self.email_pass = getpass.getpass()
            if (self.email_user is None):
                print('No email set in environment variable `DC_OUTLOOK_ADDR`')
                self.email_user = input('Enter the managing email address here: ')                     

# deci_config_dir = 'deci_config.json'

# email_user = os.getenv('DC_OUTLOOK_ADDR')
# if (email_user is None):
#     print('No email set in environment variable `DC_OUTLOOK_ADDR`')
#     email_user = input('Enter the managing email address here: ')
# email_pass = os.getenv('DC_OUTLOOK_PASS')
# if (email_pass is None):
#     email_pass = getpass.getpass()
    


# # Initialize a Discord client
# intents = dc.Intents.default()
# COMMAND_PREFIX = '<:9beggingLuz:872186647679230042>'
# bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents = intents)

# Helper functions for dynamic memory files vvv
def read_config_file(config_dir: str) -> dict:
    '''
    Reads in the given ...config.json file

    Args:
        config_dir (str): File path to the ...config.json file

    Returns:
        dict: Contains the configuration parameters for the bot
    '''
    
    with open(config_dir) as fp:
        config_dict = json.load(fp)
    
    return config_dict

def update_config_file(config_dir: str, config_dict: dict) -> None:
    '''
    Updates the ...config.json file using config_dict

    Args:
        config_dir (str): File path to the ...config.json file
        config_dict (dict): Dictionary containing the config settings for the bot
    '''
    
    with open(config_dir, mode = 'w') as fp:
        json.dump(config_dict, fp)
        
def read_csv_set_idx(csv_file_path: str, idx_keys: Union[str, list] = None) -> pd.DataFrame:
    '''
    Reads in a csv as a Pandas Dataframe and sets the index to idx_keys

    Args:
        csv_file_path (str): Path to the csv file
        idx_keys (str, optional): Key column to set as index. Defaults to None. 
                                 If None, returns the dataframe with the 
                                 pandas default generated index.

    Returns:
        pd.DataFrame: Dataframe with it's index set to idx_keys
    '''
    if idx_keys is None:
        df = pd.read_csv(csv_file_path)
    else:
        df = pd.read_csv(csv_file_path).set_index(idx_keys)
    return df
# Helper functions for dynamic memory files ^^^

# Helper functions vvv
async def is_valid_html_colour(ctx, colour: str) -> bool:
    '''
    Determines whether the given colour string is a valid html colour code
    
    Replies with a helpful colour selector url if colour is not html valid

    Args:
        ctx (Discord.Context): An object representing the message that called this command
        colour (str): string representation of an html colour code
    Returns:
        bool: whether or not the colour is valid
    '''
    html_str = f'<!DOCTYPE html><html lang="en-us"><head><meta charset="UTF-8"><title>test</title></head><body><p style="color:{colour};">test</p></body></html>'
    hv = HTMLValidator()
    response_dict = (hv.validate_html(html_str))
    res_len = len(response_dict['messages'])
    if res_len == 0:
        return True
    else:
        err_msg = f'ERROR: `{colour}` is not recognized as a valid HTML colour.\n'
        err_msg += 'Either enter a valid colour code name, the hex code, RGB code, \n'
        err_msg += 'or another valid html value for the colour you wish to pick. See \n'
        err_msg += 'https://htmlcolorcodes.com/color-names/ for help in selecting a valid colour.'
        err_msg += ''
        await ctx.reply(err_msg)
        return False
    
async def check_repair_config_files(dcts: DeciConsts):
    '''
    Checks for missing files and creates them if missing

    Args:
        deci_config_dir (str): _description_
    '''
    
    deci_config_dir = dcts.deci_config_dir
    deci_config = read_config_file(deci_config_dir)
    imap_host = deci_config['em_srv_parms']['imap_host']
    dir_paths = deci_config['dir_paths']
    for k in dir_paths:
        path = deci_config['dir_paths'][k]
        if not os.path.exists(path):
            os.makedirs(path)
            
            # Set the max_uid_path
            if k == 'max_uid_path':
                imap_client = aioimaplib.IMAP4_SSL(host=imap_host, timeout=30)
                await imap_client.wait_hello_from_server()
                await imap_client.login(dcts.email_user, dcts.email_pass)
                await imap_client.select('INBOX')
                ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject', 'Message-ID', 'In-Reply-To', 'References'}
                FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
                response = await imap_client.uid('fetch', '%d:*' % (1),
                                     '(UID FLAGS BODY.PEEK[HEADER.FIELDS (%s)])' % ' '.join(ID_HEADER_SET))
                for i in range(0, len(response.lines) - 1, 3):
                    fetch_command_without_literal = b'%s %s' % (response.lines[i], response.lines[i + 2])
                    uid = int(FETCH_MESSAGE_DATA_UID.match(fetch_command_without_literal).group('uid'))
                    with open(k, mode='w') as f:
                        f.write(str(uid))
            elif k == 'deci_config_dir':
                print(f'Check the GitHub Repo for the latest version of {path}')
            elif k == 'guilds_dir':
                pass
            elif k == 'chain_users_dir':
                df = pd.Dataframe(columns = ['Server_ID','User_ID','Name','Email','Colour'])
                df.to_csv(path)
    return
    
# Helper functions ^^^

# Check Discord function vvv
def sendDiscordMessageAsEmail(dcts: DeciConsts, subject: str, body: str, attachments: list) -> str:
    '''
    Simple send email script

    Args:
        subject (str): Subject of the email to be sent
        body (str): Body of email to be sent in html format
        attachments (list): List of strings containing the file paths to the attachments
                            to be sent

    Returns:
        str: A confirmation message
    '''
    
    # Load in the recipients
    deci_config = read_config_file(dcts.deci_config_dir)
    chainUsers = read_csv_set_idx(deci_config['dir_paths']['chain_users_dir'])
    email_recipients = chainUsers['Email']
    emRecipients = ', '.join(email_recipients)

    if subject is None:
        email_subject = body
    else: 
        email_subject = subject
    email_body = body
    
    emMsg = MIMEMultipart()
    email_user, email_pass = dcts.email_user, dcts.email_pass
    emMsg['From'] = email_user
    emMsg['To'] = emRecipients
    emMsg['Subject'] = email_subject
    
    emMsg.attach(MIMEText(email_body, 'html'))

    for f in attachments or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        emMsg.attach(part)

    # Read in the necessary variables from deci_config
    smtp_host = deci_config['em_srv_parms']['smtp_host']
    smtp_port = deci_config['em_srv_parms']['smtp_port']
    
    email_server = smtplib.SMTP(host = smtp_host, port = smtp_port)
    email_server.ehlo()
    email_server.starttls()
        
    email_server.login(email_user, email_pass)
    email_server.sendmail(email_user, email_recipients, emMsg.as_string())
    confirmationMsg = f'Email [{email_subject}] successfully sent!'
    print(confirmationMsg)
    email_server.quit()
    
    for i in attachments:
        os.remove(i)   
        print(f'Removed file: {i}')
        
    return confirmationMsg
# Check Discord function ^^^

# Check Email function vvv
async def sendEmailAsDiscordMsg(dcts: DeciConsts, subject: str, sender: str, emailMsg: str, att_paths: list):
    '''
    Sends an email message as a Discord message

    Args:
        subject (str): The subject of the email
        sender (str): The sender of the email
        emailMsg (str): The body of the email
        att_paths (list):   A list of all attachments contained in the email. 
                            Stored as a list of strs representing the filepaths
                            to the attachments.
    '''
    
    # Read in the necessary variables from deci_config
    bot = dcts.bot
    deci_config = read_config_file(dcts.deci_config_dir)
    guilds_dir = deci_config['dir_paths']['guilds_dir']
    guilds_conf = read_config_file(guilds_dir)
    channels = []
    for i in guilds_conf:
        for j in guilds_conf[i]['email_channel']:
            channels.append(j)
            
    # Modify replying subject string
    re_subj = 'Re: '
    if re_subj in subject:
        while re_subj in subject:
            subject = subject[4:]
        subject = re_subj + subject
            
    # Set channel
    for guild in bot.guilds:
        
        # Edit the subject line
        guilds_conf[str(guild.id)]['currentSubject'] = subject     
        update_config_file(guilds_dir, guilds_conf)
        
        for ch in channels:
            channel = bot.get_channel(int(ch))
            
            # Format message for Discord
            if emailMsg[-1] == '\n':
                emailMsg = emailMsg[:-1]
            emailMsg = emailMsg.replace('\n', '\n> ')
            discMsg = f'New message from _{sender}_:\n'
            discMsg += f'**Subject: {subject}**\n'
            discMsg += f'> {emailMsg}'
            # Send body text as Discord message
            await channel.send(discMsg)  
            
            # Send attachments one by one
            att_paths_len = len(att_paths)
            if att_paths_len != 0:   
                for i in att_paths: 
                    with open(i, mode='rb') as f:
                        await channel.send(f'[image: {i}]', file = dc.File(f)) 
                    os.remove(i)   
                    print(f'Removed file: {i}')

async def fetch_messages_headers(dcts: DeciConsts, imap_client: aioimaplib.IMAP4_SSL, max_uid: int) -> int:
    ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject', 'Message-ID', 'In-Reply-To', 'References'}
    FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
    FETCH_MESSAGE_DATA_SEQNUM = re.compile(rb'(?P<seqnum>\d+) FETCH.*')
    FETCH_MESSAGE_DATA_FLAGS  = re.compile(rb'.*FLAGS \((?P<flags>.*?)\).*')
    MessageAttributes = namedtuple('MessageAttributes', 'uid flags sequence_number')

    response = await imap_client.uid('fetch', '%d:*' % (max_uid + 1),
                                     '(UID FLAGS BODY.PEEK[HEADER.FIELDS (%s)])' % ' '.join(ID_HEADER_SET))
    new_max_uid = max_uid
    
    
    if response.result == 'OK':
        for i in range(0, len(response.lines) - 1, 3):
            fetch_command_without_literal = b'%s %s' % (response.lines[i], response.lines[i + 2])

            uid = int(FETCH_MESSAGE_DATA_UID.match(fetch_command_without_literal).group('uid'))
            flags = FETCH_MESSAGE_DATA_FLAGS.match(fetch_command_without_literal).group('flags')
            seqnum = FETCH_MESSAGE_DATA_SEQNUM.match(fetch_command_without_literal).group('seqnum')
            # these attributes could be used for local state management
            message_attrs = MessageAttributes(uid, flags, seqnum)
            
            # Read in the necessary variables from deci_config
            deci_config = read_config_file(dcts.deci_config_dir)
            max_uid_path = deci_config['dir_paths']['max_uid_path']
            with open(max_uid_path, mode='w') as f:
                f.write(str(uid))
                
            # uid fetch always includes the UID of the last message in the mailbox
            # cf https://tools.ietf.org/html/rfc3501#page-61
            if uid > max_uid:
                message_headers = BytesHeaderParser().parsebytes(response.lines[i + 1])
                email_from = message_headers.get('from')
                
                # Check if sender is in mailing list
                start = email_from.find('<') + 1
                end = email_from.find('>')
                from_email_addr = email_from[start:end]              
                chainUsers = read_csv_set_idx(deci_config['dir_paths']['chain_users_dir'])
                email_recipients = chainUsers['Email']
                if not(from_email_addr in email_recipients.values):
                    print(f'Email received from an address that\'s not on the mailing list: {from_email_addr}')
                    return uid
                
                
                print(message_headers)
                dwnld_resp = await imap_client.uid('fetch', str(uid), 'BODY.PEEK[]')
                thread_msg = BytesParser().parsebytes(dwnld_resp.lines[1])
                email_timestamp = parser.parse(thread_msg.get('Date'))
                html_email = False
                email_msg = thread_msg
                # If the email is a thread, take the most recent message
                while email_msg.is_multipart():
                    if len(email_msg.get_payload()) == 2:
                        if 'html' in email_msg.get_payload(1).get('Content-Type'):
                            html_email = True 
                            email_msg = email_msg.get_payload(1)
                        else:
                            email_msg = email_msg.get_payload(0)     
                    else:
                        email_msg = email_msg.get_payload(0) 
                        
                if 'html' in email_msg.get('Content-Type'):
                    html_email = True                                                     

                # Extract message body
                msg_body = email_msg
                email_seen = False # This variable doesn't actually do anything since I haven't figured it out
                while type(msg_body) != str:
                    if type(msg_body) == list:
                        msg_body = msg_body[0]
                        continue
                    
                    # This code doesn't work the way I want it to :(
                    elif not(msg_body.is_multipart()) and ('Content-Transfer-Encoding' in msg_body.keys()) and (msg_body.get('Content-Transfer-Encoding') != 'quoted-printable'):
                        email_seen = True
                        ''' Legacy Code
                        # msg_body = msg_body.get_payload(decode = True)
                        # msg_body = msg_body.decode('utf-8')
                        # msg_body = BeautifulSoup(msg_body, 'html.parser')
                        # msg_body = msg_body.text
                        '''
                        break
                    msg_body = msg_body.get_payload()
                    
                if not(email_seen):
                    # If html is found, then convert to markdown
                    if html_email:
                        x = msg_body.replace('=\r\n', '')
                        x = x.replace('\r\n', '')
                        x = x.replace('</div>', '</div><br />')
                        x = x.replace('<br />', '\n')
                        x = x.replace('<br>', '\n')
                        x = x.replace('<u>', '__')
                        x = x.replace('</u>', '__')
                        
                        # Parse image tags
                        img_tag = '<img'
                        while img_tag in x:
                            open_ab = x.find(img_tag)
                            start = x.find('alt=3D"', open_ab) + 7
                            end = x.find('"', start )
                            close_ab = x.find('>', end) + 1
                            x = x.replace(x[open_ab:close_ab], f'{[x[start:end]]}')
                            
                        msg_body = markdownify(x, convert = ['li', 'ol', 'ul', 'b', 'i', 'img'])
                        msg_body = msg_body.replace('\\_\\_', '__')
                        
                        # Remove redundant newlines
                        while msg_body[-3:] == '  \n':
                            msg_body = msg_body[:-3]
                        while msg_body[-1] == '\n':
                            msg_body = msg_body[:-1]
                        while msg_body[0] == '\n':
                            msg_body = msg_body[1:]
                    
                    # Remove read threads
                    email_thread_line_break = '\r\n\r\n\r\nOn '
                    email_thread_line_break2 = ']\r\n\r\nOn '      
                    email_thread_line_break3 = '\n\nGet Outlook for Android'   
                    email_thread_line_break4 = '\n\n\n\n\nOn '                     
                    if email_thread_line_break2 in msg_body:
                        idx = msg_body.find(email_thread_line_break2)+1
                        msg_body = msg_body[:idx]
                    elif email_thread_line_break in msg_body:
                        idx = msg_body.find(email_thread_line_break)
                        msg_body = msg_body[:idx]
                    elif email_thread_line_break3 in msg_body:
                        idx = msg_body.find(email_thread_line_break3)
                        msg_body = msg_body[:idx]
                    elif email_thread_line_break4 in msg_body:
                        idx = msg_body.find(email_thread_line_break4)
                        msg_body = msg_body[:idx]
                    print(f'Body:\n{msg_body}\n')
                    
                    # Extract attachments
                    att_paths = []
                    for part in thread_msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue

                        filename = part.get_filename()
                        em_atts_dir = deci_config['dir_paths']['em_atts_dir']
                        att_path = os.path.join(em_atts_dir, filename)
                        try: 
                            part_cont_dis = part.get('Content-Disposition')
                            
                            try:
                                idx = part_cont_dis.find('creation-date="')
                                start = part_cont_dis.find('"', idx) + 1
                                end = part_cont_dis.find('"', start)
                                part_timestamp = parser.parse(part_cont_dis[start:end])
                                outlook_atts_cond = abs(part_timestamp - email_timestamp) <= timedelta(seconds = 60)
                            except:
                                outlook_atts_cond = False
                                
                            gmail_atts_cond = filename in msg_body or part.get_content_maintype() == 'video'
                            if outlook_atts_cond or gmail_atts_cond:
                                with open(att_path, 'wb') as fp:
                                    fp.write(part.get_payload(decode=True))
                                att_paths.append(att_path)
                                print('Downloaded file:', filename)
                        except:
                            pass
                        # if filename in msg_body or part.get_content_maintype() == 'video':
                    if len(att_paths) == 2: 
                        att_paths = att_paths[::-1]    
                            
                    # thread_payload = thread_msg.get_payload()
                    # if (att_paths == []) and (len(thread_payload) == 2) and (thread_payload[1].get_content_maintype() == 'image'):
                    #     0
                        
                                            
                    subject = message_headers.get('subject')                 
                    await sendEmailAsDiscordMsg(dcts, subject, email_from, msg_body, att_paths)
            
                new_max_uid = uid
    else:
        print('error %s' % response)
    return new_max_uid

async def handle_server_push(push_messages: Collection[str]) -> None: # or str
    for msg in push_messages:
        if msg.endswith(b'EXISTS'):
            print('new message: %s' % msg) # could fetch only the message instead of max_uuid:* in the loop
        elif msg.endswith(b'EXPUNGE'):
            print('message removed: %s' % msg)
        elif b'FETCH' in msg and b'\Seen' in msg:
            print('message seen %s' % msg)
        else:
            print('unprocessed push message : %s' % msg)

async def imap_loop(dcts: DeciConsts, host: str, user: str, password: str) -> None:
    '''
    Listens for incoming emails by calling fetch_messages_headers()

    Args:
        dcts (DeciConsts): Class containing global variables for the bot
        host (str): The address of the email host server
        user (str): The email used for sending and receiving messages from/to Discord
        password (str): Password of email address. 
                        This should NEVER be stored in plain text outside of the program!
    '''
    
    print('imap_loop executing...')
    imap_client = aioimaplib.IMAP4_SSL(host=host, timeout=30)
    await imap_client.wait_hello_from_server()

    await imap_client.login(user, password)
    await imap_client.select('INBOX')

    # Read in the necessary variables from deci_config
    deci_config = read_config_file(dcts.deci_config_dir)
    max_uid_path = deci_config['dir_paths']['max_uid_path']

    persistent_max_uid = 1
    with open(max_uid_path) as f:
        persistent_max_uid = int(f.read())
        print(f'persistent_max_uid = {persistent_max_uid}')
        
    while True:
        persistent_max_uid = await fetch_messages_headers(dcts, imap_client, persistent_max_uid)
        print('%s starting idle' % user)
        idle_task = await imap_client.idle_start(timeout=60)
        await handle_server_push(await imap_client.wait_server_push())
        imap_client.idle_done()
        await wait_for(idle_task, timeout=5)
        print('%s ending idle' % user)
# Check Email function ^^^

# def main():        
#     # Initialize the global constants
#     dcts = DeciConsts()
    
#     # Read in the necessary variables from deci_config
#     deci_config = read_config_file(dcts)
#     imap_host = deci_config['em_srv_parms']['imap_host']
#     tasks = [
#         asyncio.ensure_future(check_repair_config_files(dcts)), # Create required files if they don't exist
#         asyncio.ensure_future(imap_loop(imap_host, dcts.email_user, dcts.email_pass)), # Email Listener Task
#         asyncio.ensure_future(bot.start(os.getenv('DISCORD_BOT'))) # Discord Bot Task
#     ]
#     loop = get_event_loop()
#     loop.run_until_complete(asyncio.wait(tasks))
    
# if __name__ == '__main__':
#     reminders = '[x] Remember to implement an "allowed emails" list so I don\'t spam the server with junk mail :)\n'
#     reminders += '[ ] Have the program create the dynamic memory files if they don\'t exist' 
#     print(reminders)
        
#     main()

def main():        
    # Initialize the global constants
    dcts = DeciConsts(True)
    
    # # Initialize a Discord client
    # intents = dc.Intents.default()
    # COMMAND_PREFIX = '<:9beggingLuz:872186647679230042>'
    # bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents = intents)  
    bot = dcts.bot
    
    # Discord commands vvv
    @bot.command()
    async def echo(ctx, text_to_echo: str):
        '''
        Replies with `text_to_echo`

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            text_to_echo (str): The text you want the bot to echo
        '''
        await ctx.reply(text_to_echo)
        
    @bot.command(brief = 'Sets the emailing channel')
    async def set_channel(ctx, channel_link):
        '''
        Sets the channel as the one used for email communications. 
        The bot will scan for new messages in this channel and will send them as emails.
        It will also scan for new emails and forward them to in this channel.
        
        Replies with a confirmation message
        
        WARNING: The bot will set the channel even if it has no permissions to
        read or message in that channel. I am too lazy to add anything to remedy this issue 
        so just be aware that it exists!

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            channel_link (str): The channel you wish to set as the emailing channel. 
                                Must be a mention of the format `#<channel_name>`
        '''
        
        try:
            channel_id = channel_link[2:-1]
            channel_id_int = int(channel_id)
            channel = bot.get_channel(channel_id_int)
            dcts = DeciConsts()
            deci_config = read_config_file(dcts.deci_config_dir)
            guilds_dir = deci_config['dir_paths']['guilds_dir']
            guilds_conf = read_config_file(guilds_dir)
            guild = str(ctx.guild.id)
            guilds_conf[guild]['email_channel'] = {str(channel_id): channel.name}
            update_config_file(guilds_dir, guilds_conf)
            await ctx.reply(f'{channel_link} has been successfully set as the channel for email communication!')
        except:
            if channel_link[:2] != '<#':
                await ctx.reply(f'Couldn\'t recognize channel. Try mentioning the channel by using `#<channel_name>`')
            else:
                await ctx.reply(f'Failed to set as the channel for email communication. Contact the bot developer for help.')      
        
    @bot.command()
    async def get_email_channel(ctx):
        '''
        Replies with the current mailing channel

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''

        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        
        try:
            for channel_id in guilds_conf[str(ctx.guild.id)]['email_channel'].keys():
                channel = bot.get_channel(int(channel_id))
                await ctx.reply(f'{channel.mention} is set as the current emailing channel')
                return
        except:
            await ctx.reply('No channel is set as the current emailing channel')
            
    @bot.command(brief = 'Replies with the current subject line')
    async def current_subject_line(ctx):
        '''
        Replies to the message with the current subject line

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        guild = str(ctx.guild.id)
        curr_subj = guilds_conf[guild]['currentSubject']
        await ctx.reply(f'The subject line is currently set to `{curr_subj}`')
            
    @bot.command()
    async def edit_subject_line(ctx, subject_line):
        '''
        Sets subject line to `subject_line`
        
        Replies with a confirmation message

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            subject_line (str): The subject line you wish to set for outgoing emails.
        '''
        
        # Read in the necessary variables from deci_config
        guild = str(ctx.guild.id)
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        guilds_conf[guild]['currentSubject'] = subject_line
        
        # Edit the subject line
        update_config_file(guilds_dir, guilds_conf)
        await ctx.reply(f'Subject line successfully switched to `{subject_line}`')
        
    @bot.command(hidden = True)
    async def add_user(ctx, mention_user, name: str, email: str, colour: str = 'DarkSlateGray'):
        '''
        Adds a user to the mailing list
        
        Replies with a confirmation message

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            mention_user (str): A str representing a user mention in Discord of the form `<@USER>`
            name (str): The name of the person. This will be displayed in forwarded emails
            email (str): Email of user
            colour (str, optional): The text colour that the user wishes to have their emails sent in. 
                                    Defaults to 'DarkSlateGray'.
        '''
        # Validate html colour
        valid_col = await is_valid_html_colour(ctx, colour)
        if not(valid_col):
            await ctx.reply('Please enter the command again')
            return 
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        chain_users_dir = deci_config['dir_paths']['chain_users_dir']
        chain_users_idx_keys = deci_config["chain_users_idx_keys"]
        
        # Read in the chain_users dataframe
        srv_id = ctx.guild.id
        chain_users_all = read_csv_set_idx(chain_users_dir, chain_users_idx_keys)
        try:
            chain_users = chain_users_all.loc[srv_id]
        except:
            chain_users = chain_users_all
        
        # Check if user is already in the csv
        user_id = int(mention_user[2:-1])
        if user_id in chain_users.index:
            await ctx.reply(f'{mention_user} is already on the mailing list. Use \n> {dcts.COMMAND_PREFIX}`edit_user` \nto edit users')
        # If user's not in the csv, then add the user to it
        else:
            user_info = {
                'Name': name,
                'Email': email,
                'Colour': colour
            }
            chain_users_all.loc[(srv_id, user_id), :] = user_info 
            chain_users_all.to_csv(chain_users_dir)
            await ctx.reply(f'{mention_user} was successfully added to the mailing list!')
        
    @bot.command()
    async def add_me(ctx, name: str, email: str, colour: str = 'DarkSlateGray'):
        '''
        Adds the user to the mailing list
        
        Replies with a confirmation message

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            name (str): The name of the person. This will be displayed in forwarded emails
            email (str): Email of user
            colour (str, optional): The text colour that the user wishes to have their emails sent in. 
                                    Defaults to 'DarkSlateGray'.
        '''
        
        # HTML colour is validated in add_user!
        await(add_user(ctx, f'<@{ctx.author.id}>', name, email, colour))
        
    @bot.command(brief = 'Retrieves a user\'s mailing list info', hidden = True)
    async def get_user_info(ctx, mention_user):
        '''
        Retrieves all info stored about a user in chainUsers.csv

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            mention_user (str): A str representing a user mention in Discord of the form `<@USER>`
        '''
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        chain_users_dir = deci_config['dir_paths']['chain_users_dir']
        chain_users_idx_keys = deci_config["chain_users_idx_keys"]
        
        # Read in the chain_users dataframe
        srv_id = ctx.guild.id
        chain_users_all = read_csv_set_idx(chain_users_dir, chain_users_idx_keys)
        chain_users = chain_users_all.loc[srv_id]
        
        # Check if user is in the csv
        user_id = int(mention_user[2:-1])
        if user_id in chain_users.index:
            reply_msg = ''
            for i, v in chain_users.loc[user_id].items():   
                reply_msg += f'{i}: {v}\n'
            await ctx.reply(reply_msg)
        else:
            msg_reply = f'{mention_user} not found in mailing list. To add yourself, use:\n'
            msg_reply += f'> {dcts.COMMAND_PREFIX}`add_me <Name> <Email Address> <Colour (Optional)>`'
            await ctx.reply(msg_reply)
    
    @bot.command(brief = 'Retrieves the user\'s mailing list info')
    async def get_my_info(ctx):
        '''
        Retrieves all info stored about the user in chainUsers.csv

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''  
        await(get_user_info(ctx, f'<@{ctx.author.id}>'))
    
    @bot.command(hidden = True)
    async def edit_user(ctx, mention_user):
        '''
        Edit a user's info in chainUsers.csv

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            mention_user (str): A str representing a user mention in Discord of the form `<@USER>`
        '''
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        chain_users_dir = deci_config['dir_paths']['chain_users_dir']
        chain_users_idx_keys = deci_config["chain_users_idx_keys"]
        
        # Read in the chain_users dataframe
        srv_id = ctx.guild.id
        chain_users_all = read_csv_set_idx(chain_users_dir, chain_users_idx_keys)
        chain_users = chain_users_all.loc[srv_id]
        
        # Check if user is in the csv
        user_id = int(mention_user[2:-1])
        if user_id in chain_users.index:
            user_info_keys = chain_users.columns
            choices_msg = 'Type out one of the following fields to edit it:\n'
            for i in user_info_keys:
                choices_msg += f'- `{i}`\n'
            await ctx.reply(choices_msg)
            
            # Ask user to select a field to edit and check that the field exists in the csv
            selected_field = None
            while True:

                try:
                    user_response = await bot.wait_for('message', timeout=30)
                    selected_field = user_response.content
                except BaseException as e:
                    if type(e) == asyncio.exceptions.TimeoutError:
                        await ctx.reply('Response timed out. Please enter the command again')
                    print(f'Error: {e}')
                    return
                
                if selected_field in user_info_keys:
                    break
                else:
                    await ctx.reply(f'ERROR: Unrecognized info field.\n{choices_msg}')
                    print(f'user_response = {user_response}')
            
            # Ask the user to edit the field
            await ctx.reply(f'Enter the value that you want your `{selected_field}` to change to:')
            
            while True:
                try:
                    user_response = await bot.wait_for('message', timeout=30)
                    field_val = user_response.content
                except BaseException as e:
                    if type(e) == asyncio.exceptions.TimeoutError:
                        await ctx.reply('Response timed out. Please enter the command again')
                    print(f'Error: {e}')
                    return
                
                # If selected_field is Colour, then validate the entered value
                if selected_field == 'Colour':
                    colour = field_val
                    if not(await is_valid_html_colour(ctx, colour)):
                        await ctx.reply(f"Please try entering a colour for your `{selected_field}` again:")
                    else:
                        break
                else:
                    break 
                
            # Update the csv and send a confirmation message
            chain_users_all.loc[(srv_id, user_id), selected_field] = field_val 
            chain_users_all.to_csv(chain_users_dir)
            await ctx.reply(f'Successfully changed `{selected_field}` to `{field_val}` for {mention_user}')
                
        
        # Send an error message if user is not in csv  
        else:
            msg_reply = f'{mention_user} not found in mailing list. To add yourself, use:\n'
            msg_reply += f'> {dcts.COMMAND_PREFIX}`add_me <Name> <Email Address> <Colour (Optional)>`'
            await ctx.reply(msg_reply)
            
    @bot.command()
    async def edit_me(ctx):
        '''
        Edit the user's info in chainUsers.csv

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''
        
        await(edit_user(ctx, f'<@{ctx.author.id}>'))
        
        

    @bot.command(hidden = True)
    async def remove_user(ctx, mention_user):
        '''
        Removes a user from chainUsers.csv

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            mention_user (str): A str representing a user mention in Discord of the form `<@USER>`
        '''
        
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        chain_users_dir = deci_config['dir_paths']['chain_users_dir']
        chain_users_idx_keys = deci_config["chain_users_idx_keys"]
        
        # Read in the chain_users dataframe
        srv_id = ctx.guild.id
        chain_users_all = read_csv_set_idx(chain_users_dir, chain_users_idx_keys)
        chain_users = chain_users_all.loc[srv_id]
        
        # Check if user is in mailing list, update then reply appropriately
        user_id = int(mention_user[2:-1])
        if user_id in chain_users.index:
            chain_users_all = chain_users_all.drop((srv_id, user_id), axis = 'index')
            chain_users_all.to_csv(chain_users_dir)
            await ctx.reply(f'Successfully removed {mention_user} from the mailing list!')
        else:
            await ctx.reply(f'User was not found in the mailing list!')
        
    @bot.command()
    async def remove_me(ctx):
        '''
        Removes the user from chainUsers.csv

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''
        
        await remove_user(ctx, f'<@{ctx.author.id}>')
        
        

    @bot.event
    async def on_ready():
        '''
        This function executes when turned on if it was off before
        '''
        print(f'Logged in as {bot.user}')

    ''' Above code is equivalent to:
    async def on_ready():
        print(f'Logged in as {bot.user}')
        
    on_ready = bot.event(on_ready)
    '''

    @bot.event
    async def on_guild_join(guild):
        '''
        This function executes when invited to a new server.
        
        Adds the server to guilds_conf.json
        '''
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        
        guild_id = str(guild.id)
        guild_info = {
            'name': guild.name,
            'email_channel': None,
            'currentSubject': None
        }
        guilds_conf[guild_id] = guild_info
        update_config_file(guilds_dir, guilds_conf)
        print(f'Added to `{guild.name}`')
        
    @bot.event
    async def on_guild_remove(guild):
        '''
        This function executes when removed from a server.
        
        Removes the server from guilds_conf.json
        '''
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        
        guild_id = str(guild.id)
        popped_guild = guilds_conf.pop(guild_id)
        popped_guild_name = popped_guild['name']
        update_config_file(guilds_dir, guilds_conf)  
        
        # Update csv to remove all instances of the popped guild
        chain_users_dir = deci_config['dir_paths']['chain_users_dir']
        chain_users_idx_keys = deci_config['chain_users_idx_keys']
        chain_users_all = read_csv_set_idx(chain_users_dir, chain_users_idx_keys)
        chain_users_all = chain_users_all.drop(index = guild.id, level = 0)
        chain_users_all.to_csv(chain_users_dir)
        
        print(f'Removed from `{popped_guild_name}`')
                    
    @bot.event
    async def on_message(message: dc.Message):
        '''
        This function executes when a message is received
        '''
        
        # To prevent recursion of the bot replying to itself
        if bot.user == message.author:
            return
        
        # Detect the channel that the message was sent from
        guild = str(message.guild.id)
        channel_id_sent_from = str(message.channel.id)
        channel_sent_from = bot.get_channel(int(channel_id_sent_from)).name
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        email_channel = guilds_conf[guild]["email_channel"]
        email_attachments_dir = deci_config['dir_paths']['em_atts_dir']
        subject = guilds_conf[guild]["currentSubject"]
        chain_users_dir = deci_config["dir_paths"]["chain_users_dir"]
        chain_users_idx_keys = deci_config["chain_users_idx_keys"]
        
        # If email_channel is None, prompt user to add an email_channel
        if email_channel is None:
            if message.content.startswith(dcts.COMMAND_PREFIX):
                await bot.process_commands(message)
            else:
                msg_re = 'No channel is set for email communications. Please set a channel using\n'
                msg_re += f'> {dcts.COMMAND_PREFIX}`set_channel <#channel>`'
                await message.reply(msg_re)
            return
        
        # If the command prefix is detected, then execute the command
        # and don't execute the rest of on_message
        if message.content.startswith(dcts.COMMAND_PREFIX):
            if channel_id_sent_from in email_channel.keys():
                msg_re = f'It looks like you attempted to send a bot command in {message.channel.mention}\n'
                msg_re += 'I recommend that you use another channel since most messages that are sent here\n'
                msg_re += 'will be sent to the email chain!'
                await message.reply(msg_re)
            await bot.process_commands(message)
            return
        
        # Read in the chain_users dataframe
        srv_id = message.guild.id
        chain_users_all = read_csv_set_idx(chain_users_dir, chain_users_idx_keys)
        
        # Check if anyone is in the server mailing list
        if not(srv_id in chain_users_all.index.get_level_values('Server_ID')):
            msg_re = 'There\'s no one on the server mailing list. Consider adding yourself as the first using\n'
            msg_re += f'> {dcts.COMMAND_PREFIX}`add_me <Name> <Email Address> <Colour (Optional)>`'
            await message.reply(msg_re)
            return
        chain_users = chain_users_all.loc[srv_id]
        
        # Check if author is in mailing list
        author_id = message.author.id
        if not(author_id in chain_users.index):
            msg_re = 'You are not on the mailing list. To add yourself, use: \n'
            msg_re += f'> {dcts.COMMAND_PREFIX}`add_me <Name> <Email Address> <Colour (Optional)>`'
            await message.reply(msg_re)
            return
        
        # Check that the message was sent from the allowed channel
        if channel_id_sent_from in email_channel.keys():
            # If currentSubject is None, prompt user to add a currentSubject
            if subject is None:
                msg_re = 'No subject line is set for email communications. Please set a subject line using\n'
                msg_re += f'> {dcts.COMMAND_PREFIX}`edit_subject_line <subject_line>`'
                await message.reply(msg_re)
                return

            
            # If attachments are present, save them
            disc_atts = []
            for i in message.attachments:
                ext_idx = i.filename.find('.')
                file_extension = i.filename[ext_idx:]
                filename = f'{email_attachments_dir}/{message.channel.name}_{i.id}{file_extension}'
                with open(filename, mode = 'wb') as fp:
                    await i.save(fp)
                    print(f'Downloaded to {filename}')
                disc_atts.append(filename)
            
            # Convert message to html format
            msg_raw = message.content
            msg_raw = msg_raw.replace('\n', '<br />')
            while ('||' in msg_raw):
                msg_raw = msg_raw.replace('||', '<p style="color:white;background-color:white;">', 1)
                msg_raw = msg_raw.replace('||', '</p>', 1)
            while ('__' in msg_raw):
                msg_raw = msg_raw.replace('__', '<ins>', 1)
                msg_raw = msg_raw.replace('__', '</ins>', 1)
            while ('_' in msg_raw):
                msg_raw = msg_raw.replace('_', '<em>', 1)
                msg_raw = msg_raw.replace('_', '</em>', 1)
            while ('~~' in msg_raw):
                msg_raw = msg_raw.replace('~~', '<del>', 1)
                msg_raw = msg_raw.replace('~~', '</del>', 1)
            while ('**' in msg_raw):
                msg_raw = msg_raw.replace('**', '<strong>', 1)
                msg_raw = msg_raw.replace('**', '</strong>', 1)
            while ('*' in msg_raw):
                msg_raw = msg_raw.replace('*', '<em>', 1)
                msg_raw = msg_raw.replace('*', '</em>', 1)
            while ('```' in msg_raw):
                msg_raw = msg_raw.replace('```', '<pre><code>', 1)
                msg_raw = msg_raw.replace('```', '</pre></code>', 1)
            while ('`' in msg_raw):
                msg_raw = msg_raw.replace('`', '<code>', 1)
                msg_raw = msg_raw.replace('`', '</code>', 1)
            
            # When a new message is detected, email it and send a confirmation reply
            try:
                author_name = chain_users.Name[author_id]
            except:
                author_name = message.author.name
            author_colour = chain_users.loc[message.author.id, 'Colour']
            emBody = f'''<strong>New message from <span style="text-decoration: underline;">{author_name}</span>: </strong> <br /> <br />'''
            emBody += f'<p style="color:{author_colour};">{msg_raw}</p>'
            confirmationMsg = sendDiscordMessageAsEmail(dcts, subject, emBody, disc_atts)
            await message.reply(confirmationMsg)
            await message.add_reaction('\N{INCOMING ENVELOPE}')
            print('')
        else:
            print(f'Message detected in the restricted channel: {channel_sent_from}')
        
        await bot.process_commands(message)
        return
    
    # Read in the necessary variables from deci_config
    deci_config = read_config_file(dcts.deci_config_dir)
    imap_host = deci_config['em_srv_parms']['imap_host']
    tasks = [
        asyncio.ensure_future(check_repair_config_files(dcts)), # Create required files if they don't exist
        asyncio.ensure_future(imap_loop(dcts, imap_host, dcts.email_user, dcts.email_pass)), # Email Listener Task
        asyncio.ensure_future(dcts.bot.start(os.getenv('DISCORD_BOT'))) # Discord Bot Task
    ]
    loop = get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    # Discord commands ^^^
    
    
    
if __name__ == '__main__':
    reminders = '[x] Remember to implement an "allowed emails" list so I don\'t spam the server with junk mail :)\n'
    reminders += '[ ] Have the program create the dynamic memory files if they don\'t exist' 
    print(reminders)
    
    # # Initialize a Discord client
    # intents = dc.Intents.default()
    # COMMAND_PREFIX = '<:9beggingLuz:872186647679230042>'
    # bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents = intents)
        
    main()