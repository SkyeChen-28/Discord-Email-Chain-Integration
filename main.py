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

# Text conversion and parsing packages
from htmlvalidation import HTMLValidator
from markdownify import markdownify
import re

# Datetime packages
from datetime import datetime as dt
from datetime import timedelta, tzinfo, date
from dateutil import parser

# Misc
import os
from os.path import basename
import getpass
import asyncio
from asyncio import get_event_loop, wait_for
from collections import namedtuple
from typing import Collection, Union
import logging as log

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
        self.email_user = os.getenv('DC_EMAIL_ADDR')
        self.email_pass = os.getenv('DC_EMAIL_PASS')
        self.bot_token = os.getenv('DISCORD_BOT')
            
        # Discord related constants
        intents = dc.Intents.default()
        self.COMMAND_PREFIX = '<:9beggingLuz:872186647679230042>' 
         
        if enter_fields:
            # Initialize a Discord client
            self.bot = commands.Bot(command_prefix=self.COMMAND_PREFIX, intents = intents)
            if (self.email_user is None):
                warn_msg = 'No email set in environment variable `DC_EMAIL_ADDR`.\n'
                warn_msg += 'It\'s recommended that you set that EnvVar as your managing email address\n'
                log_and_print(warn_msg, terminal_print=True)
                self.email_user = input('Enter the managing email address: ')     
            if (self.email_pass is None):
                warn_msg = 'No email password set in environment variable `DC_EMAIL_PASS`.\n'
                warn_msg += 'It\'s recommended that you set that EnvVar as your managing email password\n'
                log_and_print(warn_msg, terminal_print=True)
                self.email_pass = getpass.getpass()
            if (self.bot_token is None):     
                warn_msg = 'No bot token in environment variable `DISCORD_BOT`.\n'
                warn_msg += 'It\'s recommended that you set that EnvVar as your bot\'s token\n'
                warn_msg += 'If you don\'t have a bot, create one here: https://discord.com/developers/applications/\n'
                log_and_print(warn_msg, terminal_print=True)
                self.email_user = input('Enter your bot token: ')              

def log_and_print(message: str, level: str = 'info', terminal_print: bool = False) -> None:
    '''
    str, str -> None
    
    Custom function for logging and printing a message. Function doesn't output anything.
    Possible levels:
    - debug
    - info
    - warning
    - error
    - critical
    '''
    
    if terminal_print:
        print(message)
    
    # Encode emojis differently    
    log_message = message#.encode('unicode_escape') # No longer required
    if level == 'debug':
        log.debug(log_message)
    elif level == 'info':
        log.info(log_message)
    elif level == 'warning':
        log.warning(log_message)
    elif level == 'error':
        log.error(log_message)
    elif level == 'critical':
        log.critical(log_message)   

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
        dcts (DeciConsts): Class containing global variables for the bot
    '''
    
    # Load in required variables
    deci_config_dir = dcts.deci_config_dir
    deci_config = read_config_file(deci_config_dir)
    imap_host = deci_config['em_srv_parms']['imap_host']
    dir_paths = deci_config['dir_paths']
    
    for k in dir_paths:
        path = deci_config['dir_paths'][k]
        
        # Check if each required file exists
        if not os.path.exists(path):
            path_dirname = os.path.dirname(path)
            if path_dirname == '' and ('.' not in path):
                path_dirname = path
            os.makedirs(path_dirname, exist_ok=True)
            log_and_print(f"Directory {path_dirname} created")
            
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
                    with open(path, mode='w') as f:
                        f.write(str(uid))        
                log_and_print(f'Created {path}')
            elif k == 'deci_config_dir':
                log_and_print(f'Check the GitHub Repo for the latest version of {path}')
            elif k == 'guilds_dir':
                with open(path, 'w') as fp:
                    fp.write('{}')
                log_and_print(f'Created {path}')
            elif k == 'chain_users_dir':
                df = pd.DataFrame(columns = ['Server_ID','User_ID','Name','Email','Colour'])
                df.to_csv(path, index = False)
                log_and_print(f'Created {path}')    

def send_email(email_recipients: list, subject: str, body: str, attachments: list = []) -> str:
    '''
    Simple send email script

    Args:
        email_recipients (list):    A list of strings. 
                                    The emails of all intended recipients of the email.
        subject (str): Subject of the email to be sent
        body (str): Body of email to be sent in html format
        attachments (list): List of strings containing the file paths to the attachments
                            to be sent

    Returns:
        str: A confirmation message
    '''
    
    # Load in required variables
    dcts = DeciConsts()
    deci_config = read_config_file(dcts.deci_config_dir)
    
    # Define email variables
    if subject is None:
        email_subject = body
    else: 
        email_subject = subject
    email_body = body
    email_msg = MIMEMultipart()
    email_user, email_pass = dcts.email_user, dcts.email_pass
    email_msg['From'] = email_user
    email_recips = ', '.join(email_recipients)
    email_msg['To'] = email_recips
    email_msg['Subject'] = email_subject
    email_msg.attach(MIMEText(email_body, 'html'))

    # Add attachments
    for f in attachments or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        email_msg.attach(part)

    # Read in the necessary variables from deci_config
    smtp_host = deci_config['em_srv_parms']['smtp_host']
    smtp_port = deci_config['em_srv_parms']['smtp_port']
    
    # Connect to SMTP to send email
    email_server = smtplib.SMTP(host = smtp_host, port = smtp_port)
    email_server.ehlo()
    email_server.starttls()
    email_server.login(email_user, email_pass)
    
    # Send the email and a confirmation message
    email_server.sendmail(email_user, email_recipients, email_msg.as_string())
    confirm_msg = f'Email [{email_subject}] successfully sent!'
    log_and_print(confirm_msg)
    email_server.quit()
    
    # Remove each attachment now that we don't need them anymore
    for i in attachments:
        os.remove(i)   
        log_and_print(f'Removed file: {i}')
        
    return confirm_msg

def send_disc_msg_as_email(ctx, dcts: DeciConsts, subject: str, body: str, attachments: list) -> str:
    '''
    Simple send email script

    Args:
        ctx (Discord.Context): An object representing the message that called this command
        dcts (DeciConsts): Class containing global variables for the bot
        subject (str): Subject of the email to be sent
        body (str): Body of email to be sent in html format
        attachments (list): List of strings containing the file paths to the attachments
                            to be sent

    Returns:
        str: A confirmation message
    '''
    
    # Load in the recipients
    deci_config = read_config_file(dcts.deci_config_dir)
    chain_usrs = read_csv_set_idx(deci_config['dir_paths']['chain_users_dir'])
    srv_id = ctx.guild.id
    email_recipients = chain_usrs.loc[chain_usrs['Server_ID'] == srv_id, 'Email'].values
    
    # Send the email
    confirm_msg = send_email(email_recipients, subject, body, attachments)
        
    return confirm_msg

async def send_email_as_disc_msg(dcts: DeciConsts, subject: str, sender: str, email_msg: str, att_paths: list):
    '''
    Sends an email message as a Discord message

    Args:
        dcts (DeciConsts): Class containing global variables for the bot
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
    chain_users_dir = deci_config['dir_paths']['chain_users_dir']
    guilds_conf = read_config_file(guilds_dir)
    chain_users = read_csv_set_idx(chain_users_dir)
    
    # Extract the sender's email address
    try:
        sender_email = sender[sender.find("<")+1:sender.find(">")]
    except:
        sender_email = sender
    
    # Send the email to all servers that the sender is listed in
    chain_users = chain_users[chain_users['Email'] == sender_email]
    guild_ids = chain_users['Server_ID'].values
    channels = []
    for i in guild_ids:
        channels.append(guilds_conf[str(i)]['email_channel'])
            
    # Modify replying subject string
    re_subj = 'Re: '
    if re_subj in subject:
        while re_subj in subject:
            subject = subject[4:]
        subject = re_subj + subject
            
    # Set server
    guild = guild_ids[0]
        
    # Edit the subject line
    guilds_conf[str(guild)]['currentSubject'] = subject     
    update_config_file(guilds_dir, guilds_conf)
        
    # Theoretically, this loop allows the bot to send an email to multiple channels
    # But I've restricted it to only 1 channel when called from other functions in this .py file
    for ch in channels:
        channel = bot.get_channel(int(ch))
        
        # Format message for Discord
        if email_msg[-1] == '\n':
            email_msg = email_msg[:-1]
        email_msg = email_msg.replace('\n', '\n> ')
        disc_msg = f'New message from _{sender}_:\n'
        disc_msg += f'**Subject: {subject}**\n'
        disc_msg += f'> {email_msg}'
        
        # Send body text as Discord message
        await channel.send(disc_msg)  
        
        # Send attachments one by one, then remove them
        att_paths_len = len(att_paths)
        if att_paths_len != 0:   
            for i in att_paths: 
                with open(i, mode='rb') as f:
                    await channel.send(f'[image: {i}]', file = dc.File(f)) 
                os.remove(i)   
                log_and_print(f'Removed file: {i}')

async def fetch_email_messages(dcts: DeciConsts, imap_client: aioimaplib.IMAP4_SSL, max_uid: int) -> int:
    '''
    Fetches new email messages and calls sendEmailAsDiscordMsg() if the email was sent by
    someone on the mailing list.
    
    Args:
        dcts (DeciConsts): Class containing global variables for the bot.
        imap_client (IMAP4_SSL): Object representing an imap instance 
                                 for listening to incoming emails.
        max_uid (int): The max uid of all emails in the current inbox.
        
    Returns:
        The new max_uid (int)
    '''
    
    # The code block that fetches emails. I don't understand this but it works
    ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject', 'Message-ID', 'In-Reply-To', 'References'}
    FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
    # FETCH_MESSAGE_DATA_SEQNUM = re.compile(rb'(?P<seqnum>\d+) FETCH.*')
    # FETCH_MESSAGE_DATA_FLAGS  = re.compile(rb'.*FLAGS \((?P<flags>.*?)\).*')
    # msg_attributes_tup = namedtuple('MessageAttributes', 'uid flags sequence_number')

    response = await imap_client.uid('fetch', '%d:*' % (max_uid + 1),
                                     '(UID FLAGS BODY.PEEK[HEADER.FIELDS (%s)])' % ' '.join(ID_HEADER_SET))
    new_max_uid = max_uid
    
    
    if response.result == 'OK':
        for i in range(0, len(response.lines) - 1, 3):
            fetch_command_without_literal = b'%s %s' % (response.lines[i], response.lines[i + 2])

            # Define variables for important email parameters
            uid = int(FETCH_MESSAGE_DATA_UID.match(fetch_command_without_literal).group('uid'))
            # flags = FETCH_MESSAGE_DATA_FLAGS.match(fetch_command_without_literal).group('flags')
            # seqnum = FETCH_MESSAGE_DATA_SEQNUM.match(fetch_command_without_literal).group('seqnum')
            # # these attributes could be used for local state management
            # message_attrs = msg_attributes_tup(uid, flags, seqnum)
            
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
                chain_usrs = read_csv_set_idx(deci_config['dir_paths']['chain_users_dir'])
                email_recipients = chain_usrs['Email']
                
                # If not, return with the current uid
                if (from_email_addr not in email_recipients.values):
                    log_and_print(f'Email received from an address that\'s not on the mailing list: {from_email_addr}')
                    return uid
                
                # Begin parsing the email's contents
                log_and_print(f'Incoming email headers:\n{message_headers}')
                dwnld_resp = await imap_client.uid('fetch', str(uid), 'BODY.PEEK[]')
                thread_msg = BytesParser().parsebytes(dwnld_resp.lines[1])
                email_timestamp = parser.parse(thread_msg.get('Date'))
                html_email = False
                email_msg = thread_msg
                
                # Try to retrieve the HTML representation of the email
                while email_msg.is_multipart():
                    if len(email_msg.get_payload()) == 2:
                        if 'html' in email_msg.get_payload(1).get('Content-Type'):
                            email_msg = email_msg.get_payload(1)
                        else:
                            email_msg = email_msg.get_payload(0)     
                    else:
                        email_msg = email_msg.get_payload(0) 
                        
                if 'html' in email_msg.get('Content-Type'):
                    html_email = True                                                     

                # Extract message body
                msg_body = email_msg
                email_seen = False 
                while type(msg_body) != str:
                    if type(msg_body) == list:
                        msg_body = msg_body[0]
                        continue
                    
                    # I think this filters out emails that were "just opened by a person on Outlook/GMail"
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
                    log_and_print(f'Email Body:\n{msg_body}\n')
                    
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
                                log_and_print('Downloaded file:', filename)
                        except:
                            pass
                    if len(att_paths) == 2: 
                        att_paths = att_paths[::-1]    
                                 
                    # Set the subject                                                         
                    subject = message_headers.get('subject')      
                    
                    # If sender is in more than one server, send an error message
                    try:
                        sender_email = email_from[email_from.find("<")+1:email_from.find(">")]
                    except:
                        sender_email = email_from
                    sender_df = chain_usrs[chain_usrs['Email'] == sender_email]
                    sender_srvs = pd.unique(sender_df["Server_ID"].values)
                    sender_srvs_count = len(sender_srvs)                   
                    if sender_srvs_count > 1:
                        err_msg = 'Error: You\'re in more than 1 server mailing list.\n'
                        err_msg += 'Please remove yourself from all but one server\'s mailing list\n'
                        err_msg += 'or contact the bot admin.'
                        send_email(email_recipients = [email_from], subject = f'Re: {subject}', body = err_msg)
                    
                    # Forward email to all other emails in server mailing list and to the Discord server
                    else:
                        srv_id = sender_srvs[0]
                        email_recipients = chain_usrs.loc[chain_usrs['Server_ID'] == srv_id, 'Email'].values
                        email_recipients = list(set(email_recipients) - set([sender_email]))
                        # Forward emails if there are recipients
                        if email_recipients != []:
                            send_email(email_recipients = email_recipients, subject = f'Fw: {subject}', body = msg_body, attachments = att_paths)
                        await send_email_as_disc_msg(dcts, subject, email_from, msg_body, att_paths)

                # Set the new max uid
                new_max_uid = uid
    else:
        log_and_print('error %s' % response)
    return new_max_uid

async def handle_server_push(push_messages: Collection[str]) -> None: 
    for msg in push_messages:
        if msg.endswith(b'EXISTS'):
            log_and_print('new email: %s' % msg) # could fetch only the message instead of max_uuid:* in the loop
        elif msg.endswith(b'EXPUNGE'):
            log_and_print('email removed: %s' % msg)
        elif b'FETCH' in msg and b'\Seen' in msg:
            log_and_print('email seen %s' % msg)
        else:
            log_and_print('unprocessed push email : %s' % msg)

async def imap_loop(dcts: DeciConsts, host: str, user: str, password: str) -> None:
    '''
    Listens for incoming emails by calling fetch_email_messages()

    Args:
        dcts (DeciConsts): Class containing global variables for the bot
        host (str): The address of the email host server
        user (str): The email used for sending and receiving messages from/to Discord
        password (str): Password of email address. 
                        This should NEVER be stored in plain text outside of the program!
    '''
    
    # Set up the imap client
    log_and_print('Listening for emails using imap_loop...', terminal_print=True)
    imap_client = aioimaplib.IMAP4_SSL(host=host, timeout=30)
    await imap_client.wait_hello_from_server()
    await imap_client.login(user, password)
    await imap_client.select('INBOX')

    # Read in the necessary variables from deci_config
    deci_config = read_config_file(dcts.deci_config_dir)
    max_uid_path = deci_config['dir_paths']['max_uid_path']

    # Set the current max uid
    persistent_max_uid = 1
    with open(max_uid_path) as f:
        persistent_max_uid = int(f.read())
        log_and_print(f'persistent_max_uid = {persistent_max_uid}')
        
    # Loop the email fetch function
    while True:
        persistent_max_uid = await fetch_email_messages(dcts, imap_client, persistent_max_uid)
        log_and_print('%s starting idle' % user)
        idle_task = await imap_client.idle_start(timeout=60)
        await handle_server_push(await imap_client.wait_server_push())
        imap_client.idle_done()
        await wait_for(idle_task, timeout=5)
        log_and_print('%s ending idle' % user)

def main():    
    # Initialize the global constants and the bot
    dcts = DeciConsts(True)
    bot = dcts.bot
    bot_token = dcts.bot_token
    
    # Repair files
    tasks = [asyncio.ensure_future(check_repair_config_files(dcts)),] # Create required files if they don't exist
    loop = get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    
    # Configure logging
    root_logger= log.getLogger()
    root_logger.setLevel(log.INFO) 
    today = str(date.today())
    deci_config = read_config_file(dcts.deci_config_dir)
    log_file_path = deci_config["dir_paths"]["log_file_dir"] + f"/deci_log_{today}.log"
    if not(os.path.exists(log_file_path)):
        with open(log_file_path, mode = 'w') as fp:
            fp.write('')
    handler = log.FileHandler(log_file_path, 
                            mode = 'a', 
                            encoding = 'utf-8',
                            ) 
    handler.setFormatter(log.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
    root_logger.addHandler(handler)    
    
    # Discord commands vvv
    @bot.command()
    async def echo(ctx, *text_to_echo: str):
        '''
        Replies with `text_to_echo`

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            text_to_echo (str): The text you want the bot to echo
        '''
        text_to_echo = ' '.join(text_to_echo)
        log_and_print(f'echo(text_to_echo={text_to_echo}) was called')
        await ctx.reply(text_to_echo)
        log_and_print(f'Replied to {ctx.author.name} with: \n{text_to_echo}')
        
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
        
        log_and_print(f'set_channel(channel_link={channel_link}) was called')
        try:
            channel_id = channel_link[2:-1]
            channel_id_int = int(channel_id)
            channel = bot.get_channel(channel_id_int)
            dcts = DeciConsts()
            deci_config = read_config_file(dcts.deci_config_dir)
            guilds_dir = deci_config['dir_paths']['guilds_dir']
            guilds_conf = read_config_file(guilds_dir)
            guild = str(ctx.guild.id)
            guilds_conf[guild]['email_channel'] = channel_id
            update_config_file(guilds_dir, guilds_conf)
            reply_msg = f'{channel_link} has been successfully set as the channel for email communication!'
        except:
            if channel_link[:2] != '<#':
                reply_msg = f'Couldn\'t recognize channel. Try mentioning the channel by using `#<channel_name>`'
            else:
                reply_msg = f'Failed to set as the channel for email communication. Contact the bot developer for help.'      
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
        
        
        
    @bot.command()
    async def get_email_channel(ctx):
        '''
        Replies with the current mailing channel

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''

        log_and_print(f'get_email_channel() was called')
        
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        
        try:
            channel_id = guilds_conf[str(ctx.guild.id)]['email_channel']
            channel = bot.get_channel(int(channel_id))
            reply_msg = f'{channel.mention} is set as the current emailing channel'
        except:
            reply_msg = 'No channel is set as the current emailing channel'
            
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
            
    @bot.command(brief = 'Replies with the current subject line')
    async def current_subject_line(ctx):
        '''
        Replies to the message with the current subject line

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''
        
        log_and_print(f'current_subject_line() was called')
        # Read in the necessary variables from deci_config
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        guild = str(ctx.guild.id)
        curr_subj = guilds_conf[guild]['currentSubject']
        reply_msg = f'The subject line is currently set to `{curr_subj}`'
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
            
    @bot.command()
    async def edit_subject_line(ctx, *subject_line):
        '''
        Sets subject line to `subject_line`
        
        Replies with a confirmation message

        Args:
            ctx (Discord.Context): An object representing the message that called this command
            subject_line (str): The subject line you wish to set for outgoing emails.
        '''
        
        subject_line = ' '.join(subject_line)
        log_and_print(f'edit_subject_line(subject_line={subject_line}) was called')
        # Read in the necessary variables from deci_config
        guild = str(ctx.guild.id)
        dcts = DeciConsts()
        deci_config = read_config_file(dcts.deci_config_dir)
        guilds_dir = deci_config['dir_paths']['guilds_dir']
        guilds_conf = read_config_file(guilds_dir)
        guilds_conf[guild]['currentSubject'] = subject_line
        
        # Edit the subject line
        update_config_file(guilds_dir, guilds_conf)
        reply_msg = f'Subject line successfully switched to `{subject_line}`'
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
        
    @bot.command(hidden = True)
    async def add_user(ctx, mention_user, name: str = None, email: str = None, colour: str = 'DarkSlateGray'):
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
           
        log_and_print(f'add_user(mention_user={mention_user}, name={name}, email={email}, colour={colour}) was called')
        
        dcts = DeciConsts()
        if name is None or email is None:
            reply_msg = 'Invalid syntax error: The correct syntax for this command is\n'
            reply_msg += f'{dcts.COMMAND_PREFIX}add_user <@user> <Name> <Email> <Colour (optional)>'
            await ctx.reply(reply_msg)
            log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
        
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
            reply_msg = f'{mention_user} is already on the mailing list. Use \n> {dcts.COMMAND_PREFIX}`edit_user` \nto edit users'
        # If user's not in the csv, then add the user to it
        else:
            user_info = {
                'Name': name,
                'Email': email,
                'Colour': colour
            }
            chain_users_all.loc[(srv_id, user_id), :] = user_info 
            chain_users_all.to_csv(chain_users_dir)
            reply_msg = f'{mention_user} was successfully added to the mailing list!'
            
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
        
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
        
        log_and_print(f'get_user_info(mention_user={mention_user}) was called')
        
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
        else:
            reply_msg = f'{mention_user} not found in mailing list. To add yourself, use:\n'
            reply_msg += f'> {dcts.COMMAND_PREFIX}`add_me <Name> <Email Address> <Colour (Optional)>`'
        
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
    
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
        
        log_and_print(f'edit_user(mention_user={mention_user}) was called. The logging for this function is not comprehensive')
        
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
                    log_and_print(f'Error: {e}')
                    return
                
                if selected_field in user_info_keys:
                    break
                else:
                    err_reply = f'ERROR: Unrecognized info field.\n{choices_msg}'
                    log_and_print(err_reply, level="error", terminal_print=True)
                    await ctx.reply(err_reply)
                    log_and_print(f'user_response = {user_response}', terminal_print=True)
            
            # Ask the user to edit the field
            await ctx.reply(f'Enter the value that you want your `{selected_field}` to change to:')
            
            while True:
                try:
                    user_response = await bot.wait_for('message', timeout=30)
                    field_val = user_response.content
                except BaseException as e:
                    if type(e) == asyncio.exceptions.TimeoutError:
                        await ctx.reply('Response timed out. Please enter the command again')
                    log_and_print(f'Error: {e}')
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
        Edit the user's info in the mailing list

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
        
        log_and_print(f'remove_user(mention_user={mention_user}) was called')
        
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
            reply_msg = f'Successfully removed {mention_user} from the mailing list!'
        else:
            reply_msg = f'User was not found in the mailing list!'
            
        await ctx.reply(reply_msg)
        log_and_print(f'Replied to {ctx.author.name} with: \n{reply_msg}')
               
    @bot.command()
    async def remove_me(ctx):
        '''
        Removes the user from the mailing list

        Args:
            ctx (Discord.Context): An object representing the message that called this command
        '''
        
        await remove_user(ctx, f'<@{ctx.author.id}>')
        
    @bot.event
    async def on_ready():
        '''
        This function executes when turned on if it was off before
        '''
        log_and_print(f'Logged in as {bot.user}', terminal_print=True)

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
        log_and_print(f'Added to `{guild.name}`')
        
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
        
        log_and_print(f'Removed from `{popped_guild_name}`')
                    
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
            if channel_id_sent_from == email_channel:
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
        if channel_id_sent_from == email_channel:
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
                    log_and_print(f'Downloaded to {filename}')
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
            confirmationMsg = send_disc_msg_as_email(message, dcts, subject, emBody, disc_atts)
            await message.reply(confirmationMsg)
            await message.add_reaction('\N{INCOMING ENVELOPE}')
            print('')
        else:
            log_and_print(f'Message detected in the restricted channel: {channel_sent_from}')
        
        await bot.process_commands(message)
    
    # Read in the necessary variables from deci_config
    deci_config = read_config_file(dcts.deci_config_dir)
    imap_host = deci_config['em_srv_parms']['imap_host']
    tasks = [
        asyncio.ensure_future(imap_loop(dcts, imap_host, dcts.email_user, dcts.email_pass)), # Email Listener Task
        asyncio.ensure_future(dcts.bot.start(bot_token)) # Discord Bot Task
    ]
    loop = get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    # Discord commands ^^^
    
if __name__ == '__main__':        
    main()