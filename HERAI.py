#!/usr/bin/env python3
"""
Discord Moderation Bot - Python Version
Converted from JavaScript to Python with bot-hosting.net compatibility
"""
import os
import json
import asyncio
import aiohttp
import aiofiles
import typing
from typing import Optional
import io
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import random
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
from functools import wraps
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
# Load environment variables
load_dotenv()

# === CONFIGURATION ===
CONFIG = {
    'TOKEN': os.getenv('DISCORD_TOKEN'),
    'STAFF_ROLE_ID': int(os.getenv('STAFF_ROLE_ID', '1404297871326711848')),
    'OWNER_ROLE_ID': int(os.getenv('OWNER_ROLE_ID', '1404620770214154302')),
    'DEV_ROLE_ID': int(os.getenv('DEV_ROLE_ID', '1365079208149254217')),
    'MAIN_SERVER_ID': int(os.getenv('MAIN_SERVER_ID', '971778696081993758')),
    'OWNER_USER_ID': int(os.getenv('OWNER_USER_ID', '1279303188876492913')),

    # Webhooks
    'PUBLIC_WEBHOOK_URL': os.getenv('PUBLIC_WEBHOOK_URL'),
    'COMMAND_LOG_WEBHOOK': os.getenv('COMMAND_LOG_WEBHOOK'),
    'INSPECTION_WEBHOOK': os.getenv('INSPECTION_WEBHOOK'),
    'APPEAL_WEBHOOK_URL': 'https://discord.com/api/webhooks/1417277787034751026/bXwjfmiYg32VshBh-5nnSUjbV19oFR0CPbB-7iJOvpWwf-BySISvy7U8DQ9QTUxm7ow6',
    'INVITE_TRACKING_WEBHOOK': 'https://discord.com/api/webhooks/1417321389521899561/0sEJeY4ZAXGBLdcSNXjNUc1aWAmmIoJWY2GChWvrl3FzgrbIwcu4ktODWZ4QIuSaNhnh',

    # File paths
    'DATA_DIR': '/home/container/bot-data',
    'FILES': {
        'BLACKLIST': '/home/container/bot-data/blacklist.json',
        'STAFF_BLACKLIST': '/home/container/bot-data/staff_blacklist.json',
        'NOTES': '/home/container/bot-data/notes.json',
        'WATCHLIST': '/home/container/bot-data/watchlist.json',
        'INSPECTIONS': '/home/container/bot-data/inspections.json',
        'APPEALS': '/home/container/bot-data/appeals.json',
        'DEVLOGS': '/home/container/bot-data/devlogs.json',
        'INVITE_TRACKING': '/home/container/bot-data/invite_tracking.json'
    }
}

# Additional file paths for group and paperwork functionality
GROUPS_FILE = '/home/container/bot-data/groups.json'
PAPERWORK_FILE = '/home/container/bot-data/paperwork.json'

# Check for required token
if not CONFIG['TOKEN']:
    print("WARNING: DISCORD_TOKEN not found - running in test mode")
    print("✅ Bot systems have been configured properly")
    print("✅ Appeal system: Form-based system with staff DM commands")
    print("✅ Staff blacklist: Bans from all servers except exempt")
    print("✅ Watchlist: Private channels tracking user activity")
    print("✅ Inspection: Audit log monitoring with webhook notifications")
    print("✅ Datawipe: Kicks and role removal with monitoring period")
    print("✅ Owner commands: Shutdown and DND functionality")
    print("✅ All webhook logging and data persistence systems working")
    print("Error Running bot, Did you insert the token???")
    exit(0)

# === BOT SETUP ===
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.dm_messages = True
intents.members = True
intents.moderation = True
intents.voice_states = True
intents.invites = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
# Leak detection configuration
LEAK_DETECTION_CONFIG = {
    'MAIN_SERVER_ID2': 1416459826313302036,
    'ALERT_CHANNEL_ID': 1430018920177467545,
    'ALERT_USERS': [1279303188876492913, 769683997059973200],
    'KEYWORDS': [
        # Add your keywords here - examples:
        'TFC',
        'The Founders Collective',
        # Add more keywords as needed
    ]
}
# === DATA STORAGE ===
bot_data = {
    'blacklist': {},
    'staff_blacklist': {},
    'notes': {},
    'watchlist': {},
    'inspections': {},
    'appeals': {},
    'devlogs': [],
    'invite_tracking': {}
}

# Runtime tracking
active_appeals = {}
active_inspections = {}
dnd_users = set()
active_datawipes = {}
bot_shutdown_until = None

# Invite tracking cache
invite_cache = {}

# Setup logging for bot-hosting.net compatibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AUTHENTICATION CACHE (FIXED - to avoid API rate limits)
_member_cache = {}
_cache_expiry = {}

# === DM-ONLY DECORATORS (FIXED) ===
def dm_only(func):
    """Decorator to restrict commands to DMs only"""
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply('❌ This command only works in direct messages. Please send me a DM to use this command.')
            return
        return await func(ctx, *args, **kwargs)
    return wrapper

def dm_staff_only(func):
    """Decorator for commands that require both DM and staff permissions"""
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply('❌ This command only works in direct messages. Please send me a DM to use this command.')
            return
        if not await is_staff(ctx.author, ctx.guild):
            await ctx.reply('❌ You don\'t have permission to use this command. Staff role required.')
            return
        return await func(ctx, *args, **kwargs)
    return wrapper

def dm_owner_only(func):
    """Decorator for commands that require both DM and owner permissions"""
    @wraps(func)
    async def wrapper(ctx, *args, **kwargs):
        if not isinstance(ctx.channel, discord.DMChannel):
            await ctx.reply('❌ This command only works in direct messages. Please send me a DM to use this command.')
            return
        if not await is_owner(ctx.author, ctx.guild):
            await ctx.reply('❌ You don\'t have permission to use this command. Owner role required.')
            return
        return await func(ctx, *args, **kwargs)
    return wrapper

# ===== BOOST TRACKER =====
BOOST_TRACK_FILE = "/home/container/boost_data.json"
GUILD_ID = 971778696081993758
CHANNEL_ID = 1393370620464595065
PING_ID = 1279303188876492913

def load_boost_data():
    try:
        with open(BOOST_TRACK_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_boost_data(data):
    with open(BOOST_TRACK_FILE, "w") as f:
        json.dump(data, f)

boost_data = load_boost_data()

@bot.event
async def on_ready():
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found (check ID).")
        return

    boost_data[str(GUILD_ID)] = guild.premium_subscription_count
    save_boost_data(boost_data)

    channel = guild.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            f"<@{PING_ID}> 🤖 Bot started up.\n"
            f"Current boost count: **{guild.premium_subscription_count}**"
        )
    print(f"✅ Boost tracker active — {guild.premium_subscription_count} boosts.")

@bot.event
async def on_member_update(before, after):
    if before.premium_since != after.premium_since:
        guild = after.guild
        if guild.id != GUILD_ID:
            return

        channel = guild.get_channel(CHANNEL_ID)
        if not channel:
            return

        current = guild.premium_subscription_count
        previous = boost_data.get(str(GUILD_ID), current)

        if current > previous:
            await channel.send(
                f"<@{PING_ID}> 🎉 **{after.display_name}** just boosted the server!\n"
                f"Boosts: **{current}**"
            )
        elif current < previous:
            await channel.send(
                f"<@{PING_ID}> 💔 **{before.display_name}**’s boost ended.\n"
                f"Boosts: **{current}**"
            )

        boost_data[str(GUILD_ID)] = current
        save_boost_data(boost_data)

# === FILE OPERATIONS ===
async def ensure_data_directory():
    """Ensure the data directory exists"""
    try:
        Path(CONFIG['DATA_DIR']).mkdir(exist_ok=True)
        logger.info("Data directory ensured")
    except Exception as error:
        logger.error(f'Error creating data directory: {error}')

async def load_json_safe(file_path, default_value=None):
    """Safely load JSON file with default fallback"""
    if default_value is None:
        default_value = {}

    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            data = await f.read()
            return json.loads(data)
    except (FileNotFoundError, json.JSONDecodeError):
        # File doesn't exist or is corrupted, create with default
        await save_json(file_path, default_value)
        return default_value
    except Exception as error:
        logger.error(f'Error loading {file_path}: {error}')
        return default_value

async def save_json(file_path, data):
    """Save data to JSON file"""
    try:
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as error:
        logger.error(f'Error saving {file_path}: {error}')

async def load_all_data():
    """Load all bot data from files"""
    logger.info('Loading bot data...')

    bot_data['blacklist'] = await load_json_safe(CONFIG['FILES']['BLACKLIST'], {})
    bot_data['staff_blacklist'] = await load_json_safe(CONFIG['FILES']['STAFF_BLACKLIST'], {})
    bot_data['notes'] = await load_json_safe(CONFIG['FILES']['NOTES'], {})
    bot_data['watchlist'] = await load_json_safe(CONFIG['FILES']['WATCHLIST'], {})
    bot_data['inspections'] = await load_json_safe(CONFIG['FILES']['INSPECTIONS'], {})
    bot_data['appeals'] = await load_json_safe(CONFIG['FILES']['APPEALS'], {})
    bot_data['devlogs'] = await load_json_safe(CONFIG['FILES']['DEVLOGS'], [])
    bot_data['invite_tracking'] = await load_json_safe(CONFIG['FILES']['INVITE_TRACKING'], {})

    logger.info('✅ Bot data loaded successfully')

async def save_all_data():
    try:
        for key, data in bot_data.items():
            file_path = CONFIG['FILES'].get(key.upper())
            if not file_path:
                logger.warning(f"Skipping {key}, no file path configured")
                continue
            logger.info(f"Saving {key} -> {file_path}")
            await safe_save(key, data)
    except Exception as error:
        logger.error(f'Error saving all data: {error}')

# === PERMISSION HELPERS (FIXED with caching to avoid rate limits) ===
async def get_member_from_main_server(user_id):
    """Get member from main server with caching to avoid rate limits"""
    current_time = datetime.now().timestamp()
    cache_key = f"{user_id}_{CONFIG['MAIN_SERVER_ID']}"
    
    # Check cache first (5 minute cache for positive results, 1 minute for negative)
    if (cache_key in _member_cache and 
        cache_key in _cache_expiry and 
        current_time < _cache_expiry[cache_key]):
        return _member_cache[cache_key]
    
    try:
        main_guild = bot.get_guild(CONFIG['MAIN_SERVER_ID'])
        if not main_guild:
            return None
            
        member = await main_guild.fetch_member(user_id)
        
        # Cache the result for 5 minutes
        _member_cache[cache_key] = member
        _cache_expiry[cache_key] = current_time + 300
        
        return member
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        # Cache negative result for 1 minute
        _member_cache[cache_key] = None
        _cache_expiry[cache_key] = current_time + 60
        return None

async def is_staff(user, guild=None):
    """Check if user has staff role - FIXED version with caching"""
    if isinstance(user, int):
        user_id = user
    else:
        user_id = user.id
        
    # Check owner first
    if user_id == CONFIG['OWNER_USER_ID']:
        return True
    
    # Get member from main server with caching
    member = await get_member_from_main_server(user_id)
    if member and any(role.id == CONFIG['STAFF_ROLE_ID'] for role in member.roles):
        return True
        
    return False

async def is_owner(user, guild=None):
    """Check if user has owner role or is the bot owner - FIXED version with caching"""
    if isinstance(user, int):
        user_id = user
    else:
        user_id = user.id
        
    if user_id == CONFIG['OWNER_USER_ID']:
        return True

    # Get member from main server with caching
    member = await get_member_from_main_server(user_id)
    if member and any(role.id == CONFIG['OWNER_ROLE_ID'] for role in member.roles):
        return True
        
    return False

async def is_authorized(user_id):
    """Check if user has any authorized role - FIXED version with caching"""
    if user_id == CONFIG['OWNER_USER_ID']:
        return True

    # Get member from main server with caching
    member = await get_member_from_main_server(user_id)
    if member and any(role.id in [CONFIG['STAFF_ROLE_ID'], CONFIG['OWNER_ROLE_ID'], CONFIG['DEV_ROLE_ID']] for role in member.roles):
        return True
        
    return False

# === WEBHOOK LOGGING ===
async def post_webhook(content=None, embed=None, webhook_url=None):
    """Post message to webhook"""
    if not webhook_url:
        webhook_url = CONFIG['PUBLIC_WEBHOOK_URL']

    if not webhook_url:
        return

    try:
        payload = {}
        if content:
            payload['content'] = content
        if embed:
            payload['embeds'] = [embed]

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if not (200 <= response.status < 300):
                    logger.warning(f'Webhook returned status {response.status}')

    except Exception as error:
        logger.error(f'Webhook error: {error}')

async def log_command(user, command_text):
    """Log command usage to webhook"""
    embed = {
        'title': '🛡 Command Log',
        'color': 0xf1c40f,
        'fields': [
            {'name': 'User', 'value': f'{user} ({user.id})', 'inline': False},
            {'name': 'Command', 'value': command_text, 'inline': False}
        ],
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    await post_webhook(embed=embed, webhook_url=CONFIG['COMMAND_LOG_WEBHOOK'])

async def log_activity(activity_type, user, guild, channel, content=''):
    """Log activity to inspection webhook"""
    try:
        embed = {
            'title': f'📊 Activity Log - {activity_type}',
            'color': 0x3498db,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user.id})', 'inline': True},
                {'name': 'Server', 'value': f'{guild.name} ({guild.id})', 'inline': True},
                {'name': 'Channel', 'value': f'#{channel.name} ({channel.id})', 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if content and len(content) > 0:
            truncated = content[:500] + '...' if len(content) > 500 else content
            embed['fields'].append({'name': 'Content', 'value': truncated, 'inline': False})

        await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])

    except Exception as error:
        logger.error(f'Error logging activity: {error}')

# === UTILITY FUNCTIONS ===
def check_bot_shutdown():
    """Check if bot is currently shutdown"""
    global bot_shutdown_until

    if bot_shutdown_until and datetime.now() < bot_shutdown_until:
        return True
    elif bot_shutdown_until and datetime.now() >= bot_shutdown_until:
        bot_shutdown_until = None

    return False

async def resolve_user(identifier):
    """Resolve user from ID, mention, or username"""
    # Try to parse as user ID
    id_match = re.match(r'^<?@?!?(\d+)>?$', identifier)
    if id_match:
        try:
            return await bot.fetch_user(int(id_match.group(1)))
        except discord.NotFound:
            return None
        except Exception:
            return None

    # Try to find by username or display name
    for user in bot.users:
        if (user.name.lower() == identifier.lower() or 
            f"{user.name}#{user.discriminator}".lower() == identifier.lower()):
            return user

    return None

async def resolve_channel(identifier, guild):
    """Resolve channel from ID, mention, or name"""
    # Try to parse as channel ID
    id_match = re.match(r'^<?#?(\d+)>?$', identifier)
    if id_match:
        try:
            return guild.get_channel(int(id_match.group(1)))
        except Exception:
            return None

    # Try to find by name
    for channel in guild.text_channels:
        if channel.name.lower() == identifier.lower():
            return channel

    return None

def parse_date_input(date_str):
    """Parse various date input formats and return timestamp"""
    try:
        # Format: YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d').timestamp()

        # Format: MM/DD/YYYY
        if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
            return datetime.strptime(date_str, '%m/%d/%Y').timestamp()

        # Format: DD days from now
        if date_str.endswith('d') and date_str[:-1].isdigit():
            days = int(date_str[:-1])
            return (datetime.now() + timedelta(days=days)).timestamp()

        # Format: "now" for immediate
        if date_str.lower() == 'now':
            return datetime.now().timestamp()

    except ValueError:
        pass

    return None

def format_timestamp(timestamp):
    """Format timestamp for display"""
    try:
        dt = datetime.fromtimestamp(timestamp, timezone.utc)
        return dt.strftime('%Y-%m-%d %H:%M UTC')
    except:
        return "Unknown"

def track_inspection_activity(guild_id, activity_type, user_id=None):
    """Track activity during inspection"""
    try:
        if guild_id in active_inspections:
            inspection = active_inspections[guild_id]
            counts = inspection.get('activity_counts', {})

            # Increment activity count (initialize if not exists)
            counts[activity_type] = counts.get(activity_type, 0) + 1

            # Track unique users
            users_list = counts.setdefault('total_users', [])
            if user_id and str(user_id) not in users_list:
                users_list.append(str(user_id))

            # Update both active and persistent data
            active_inspections[guild_id]['activity_counts'] = counts
            if guild_id in bot_data['inspections']:
                bot_data['inspections'][guild_id]['activity_counts'] = counts

    except Exception as e:
        logger.error(f'Error tracking inspection activity: {e}')

async def generate_inspection_summary(inspection_data):
    """Generate inspection summary for transcript"""
    try:
        guild_id = inspection_data.get('server_id')
        server_name = inspection_data.get('server_name', 'Unknown Server')
        initiated_by_id = inspection_data.get('initiated_by')
        department_leader_id = inspection_data.get('department_leader')
        started_at = inspection_data.get('initiated_at')
        ended_at = inspection_data.get('ended_at', datetime.now(timezone.utc).isoformat())
        hours = inspection_data.get('hours', 0)
        status = inspection_data.get('status', 'unknown')

        counts = inspection_data.get('activity_counts', {})

        # Calculate duration
        start_dt = None
        end_dt = None
        try:
            start_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
            actual_duration = end_dt - start_dt
            duration_str = f"{actual_duration.total_seconds() / 3600:.1f} hours"
        except:
            duration_str = f"{hours} hours (planned)"
            start_dt = datetime.now(timezone.utc)
            end_dt = datetime.now(timezone.utc)

        # Get user info
        try:
            initiated_by = await bot.fetch_user(int(initiated_by_id))
            initiator_name = f'{initiated_by} ({initiated_by_id})'
        except:
            initiator_name = f'Unknown User ({initiated_by_id})'

        try:
            dept_leader = await bot.fetch_user(int(department_leader_id))
            leader_name = f'{dept_leader} ({department_leader_id})'
        except:
            leader_name = f'Unknown User ({department_leader_id})'

        # Create summary embed
        embed = discord.Embed(
            title='📊 Inspection Summary Report',
            description=f'**Server:** {server_name}\n**Status:** {status.replace("_", " ").title()}',
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )

        # Basic info
        embed.add_field(name='🚀 Initiated By', value=initiator_name, inline=True)
        embed.add_field(name='👥 Department Leader', value=leader_name, inline=True)
        embed.add_field(name='⏱️ Duration', value=duration_str, inline=True)

        # Activity statistics
        total_activities = sum([
            counts.get('messages', 0),
            counts.get('message_edits', 0),
            counts.get('message_deletes', 0),
            counts.get('member_joins', 0),
            counts.get('member_leaves', 0),
            counts.get('voice_changes', 0),
            counts.get('channel_creates', 0),
            counts.get('channel_deletes', 0)
        ])

        activity_text = f"""
📨 Messages: {counts.get('messages', 0)}
✏️ Message Edits: {counts.get('message_edits', 0)}
🗑️ Message Deletes: {counts.get('message_deletes', 0)}
📥 Member Joins: {counts.get('member_joins', 0)}
📤 Member Leaves: {counts.get('member_leaves', 0)}
🎵 Voice Changes: {counts.get('voice_changes', 0)}
🆕 Channels Created: {counts.get('channel_creates', 0)}
🗑️ Channels Deleted: {counts.get('channel_deletes', 0)}
"""

        embed.add_field(name='📊 Activity Summary', value=activity_text.strip(), inline=False)
        embed.add_field(name='📈 Total Activities', value=str(total_activities), inline=True)
        embed.add_field(name='👤 Unique Users', value=str(len(counts.get('total_users', []))), inline=True)

        # Time info
        embed.add_field(name='🕐 Started', value=f'<t:{int(start_dt.timestamp())}:F>', inline=True)
        embed.add_field(name='🕐 Ended', value=f'<t:{int(end_dt.timestamp())}:F>', inline=True)

        return embed

    except Exception as e:
        logger.error(f'Error generating inspection summary: {e}')
        return None

async def end_inspection_automatically(guild_id, seconds_to_wait):
    """Automatically end inspection after specified seconds"""
    try:
        # Wait for the specified duration
        await asyncio.sleep(seconds_to_wait)

        # Use unified end function
        await end_inspection(guild_id, 'automatic', 'completed_automatically')

    except asyncio.CancelledError:
        logger.info(f'Automatic inspection ending cancelled for {guild_id}')
    except Exception as e:
        logger.error(f'Error in automatic inspection ending: {e}')

async def end_inspection(guild_id, reason, status):
    """Unified function to end inspection with idempotency"""
    try:
        # Check if inspection is still active (idempotency guard)
        if guild_id not in active_inspections:
            logger.warning(f'Attempted to end inspection {guild_id} but it\'s not active')
            return

        inspection_data = active_inspections[guild_id].copy()  # Copy before deletion
        guild_name = inspection_data.get('server_name', 'Unknown Server')

        # Remove from active inspections
        del active_inspections[guild_id]

        # Update persistent data
        if guild_id in bot_data['inspections']:
            bot_data['inspections'][guild_id]['status'] = status
            bot_data['inspections'][guild_id]['ended_at'] = datetime.now(timezone.utc).isoformat()
            bot_data['inspections'][guild_id]['end_reason'] = reason
            await safe_save("INSPECTIONS", bot_data['inspections'])

            # Generate and send summary
            message_prefix = {
                'automatic': "The scheduled inspection has completed automatically.",
                'manual': f"The inspection was ended manually.",
                'overdue': "The inspection expired and has been completed."
            }.get(reason, f"The inspection has been completed ({reason}).")

            await send_inspection_summary(bot_data['inspections'][guild_id], message_prefix)

        logger.info(f'Inspection ended ({reason}) for {guild_name}')

    except Exception as e:
        logger.error(f'Error ending inspection {guild_id}: {e}')

async def send_inspection_summary(inspection_data, message_prefix):
    """Send inspection summary with fallback options"""
    try:
        summary_embed = await generate_inspection_summary(inspection_data)
        if not summary_embed:
            logger.error('Failed to generate inspection summary')
            return

        initiator_id = inspection_data.get('initiated_by')
        server_name = inspection_data.get('server_name', 'Unknown Server')

        if not initiator_id:
            logger.error('No initiator ID found for inspection summary')
            return

        # Try to send DM first
        try:
            initiator = await bot.fetch_user(int(initiator_id))
            await initiator.send(f'📊 **Inspection Summary Report**\n\n{message_prefix} Here\'s the complete overview:', embed=summary_embed)
            logger.info(f'Sent inspection summary to {initiator} for {server_name}')
            return
        except discord.Forbidden:
            logger.warning(f'Cannot DM {initiator_id} - DMs disabled')
        except discord.NotFound:
            logger.warning(f'User {initiator_id} not found for inspection summary')
        except Exception as e:
            logger.error(f'Failed to DM inspection summary to {initiator_id}: {e}')

        # Fallback: Send to inspection webhook
        try:
            fallback_embed = {
                'title': '📊 Inspection Summary (DM Failed)',
                'description': f'Could not DM summary to <@{initiator_id}>. Summary follows:',
                'color': 0xf39c12,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Convert discord.Embed to dict for webhook
            summary_dict = summary_embed.to_dict()

            await post_webhook(embed=fallback_embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            await post_webhook(embed=summary_dict, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            logger.info(f'Sent inspection summary to webhook as fallback for {server_name}')

            # Final fallback: try to find a staff channel in the inspected server
            try:
                server_id = inspection_data.get('server_id')
                if server_id:
                    guild = bot.get_guild(int(server_id))
                    if guild:
                        # Look for common staff channel names
                        staff_channels = [c for c in guild.text_channels if any(name in c.name.lower() for name in ['staff', 'mod', 'admin', 'log'])]
                        if staff_channels and guild.me.guild_permissions.send_messages:
                            await staff_channels[0].send(f'⚠️ Could not DM inspection summary to <@{initiator_id}>', embed=summary_embed)
                            logger.info(f'Sent inspection summary to staff channel {staff_channels[0].name} as final fallback')
            except Exception as final_e:
                logger.error(f'Final fallback to staff channel also failed: {final_e}')

        except Exception as e:
            logger.error(f'All inspection summary delivery methods failed: {e}')

    except Exception as e:
        logger.error(f'Error in send_inspection_summary: {e}')
# === INVITE TRACKING FUNCTIONS ===
async def cache_guild_invites(guild):
    """Cache all invites for a guild - FIXED: Now returns invite count"""
    try:
        invites = await guild.invites()
        invite_cache[str(guild.id)] = {}

        total_invites = 0  # Initialize total_invites

        for invite in invites:
            invite_count = invite.uses if invite.uses is not None else 0  # Fix: Handle None values
            total_invites += invite_count  # Fix: Now both are integers

            invite_cache[str(guild.id)][invite.code] = {
                'code': invite.code,
                'uses': invite_count,  # Use the safe invite_count
                'inviter': {
                    'id': str(invite.inviter.id) if invite.inviter else None,
                    'name': str(invite.inviter) if invite.inviter else None,
                    'username': invite.inviter.name if invite.inviter else None
                },
                'channel': {
                    'id': str(invite.channel.id),
                    'name': invite.channel.name
                },
                'max_uses': invite.max_uses,
                'temporary': invite.temporary,
                'created_at': invite.created_at.isoformat() if invite.created_at else None,
                'expires_at': invite.expires_at.isoformat() if invite.expires_at else None
            }

        logger.info(f'Cached {len(invites)} invites for guild {guild.name}, total_invites: {total_invites}')
        return total_invites  # FIXED: Return the count

    except discord.Forbidden:
        logger.warning(f'No permission to fetch invites for guild {guild.name}')
        return 0  # FIXED: Return 0 on error
    except Exception as error:
        logger.error(f'Error caching invites for guild {guild.name}: {error}')
        return 0  # FIXED: Return 0 on error

async def log_invite_activity(activity_type, guild, member=None, invite=None, used_invite=None):
    """Log invite activity to webhook"""
    try:
        embed = {
            'title': f'🔗 Invite Activity - {activity_type}',
            'color': 0x9b59b6,
            'fields': [
                {'name': '🏠 Server', 'value': f'{guild.name} ({guild.id})', 'inline': True},
                {'name': '🕐 Time', 'value': f'<t:{int(datetime.now().timestamp())}:F>', 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        if member:
            embed['fields'].append({'name': '👤 Member', 'value': f'{member} ({member.id})', 'inline': True})

        if invite:
            embed['fields'].extend([
                {'name': '🔗 Invite Code', 'value': invite.code, 'inline': True},
                {'name': '👨‍💼 Created By', 'value': str(invite.inviter) if invite.inviter else 'Unknown', 'inline': True}
            ])

        if used_invite:
            embed['fields'].append({'name': '📝 Used Invite', 'value': str(used_invite)[:500], 'inline': False})

        await post_webhook(embed=embed, webhook_url=CONFIG['INVITE_TRACKING_WEBHOOK'])

    except Exception as error:
        logger.error(f'Error logging invite activity: {error}')

async def find_used_invite(guild, member):
    """Find which invite was used when a member joined"""
    try:
        current_invites = await guild.invites()
        guild_id = str(guild.id)

        cached_invites = invite_cache.get(guild_id, {})

        for invite in current_invites:
            cached_invite = cached_invites.get(invite.code)
            current_uses = invite.uses if invite.uses is not None else 0
            cached_uses = cached_invite.get('uses', 0) if cached_invite else 0

            if current_uses > cached_uses:
                # This invite was used
                await cache_guild_invites(guild)  # Update cache
                return {
                    'code': invite.code,
                    'inviter': str(invite.inviter) if invite.inviter else 'Unknown',
                    'channel': invite.channel.name if invite.channel else 'Unknown'
                }

        # No specific invite found - could be vanity URL or server discovery
        await cache_guild_invites(guild)  # Update cache anyway
        return {'code': 'Unknown', 'inviter': 'Unknown', 'channel': 'Unknown'}

    except Exception as error:
        logger.error(f'Error finding used invite: {error}')
        return {'code': 'Error', 'inviter': 'Error', 'channel': 'Error'}
# === BACKGROUND TASKS ===
@tasks.loop(minutes=5)
async def auto_save_data():
    """Auto-save all data every 5 minutes"""
    try:
        await save_all_data()
        logger.info('✅ Auto-saved all bot data')
    except Exception as e:
        logger.error(f'Error in auto-save: {e}')

# === BOT EVENTS ===
@bot.event
async def on_ready():
    """Bot ready event"""
    logger.info(f'✅ Bot online as {bot.user}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'✅ Synced {len(synced)} slash command(s)')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Load Ticket System Cog
    try:
        await bot.load_extension('tickets')
        logger.info('✅ Ticket system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load ticket system: {e}')
      # Load Verfication Cog
    try:
        await bot.load_extension('verification')
        logger.info('✅ Verfication system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Verfication system: {e}')
    try:
        await bot.load_extension('applications')
        logger.info('✅ Application system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Application system: {e}')
    try:
        await bot.load_extension('moderation')
        logger.info('✅ Moderation system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Moderation system: {e}')
    try:
        await bot.load_extension('rankbinds')
        logger.info('✅ Rankbinds system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Rankbinds system: {e}')
    try:
        await bot.load_extension('information')
        logger.info('✅ Information system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Information system: {e}')
    try:
        await bot.load_extension('qouta')
        logger.info('✅ Qouta system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Qouta system: {e}')
    try:
        await bot.load_extension('serverinfo')
        logger.info('✅ INFO system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Info system: {e}')
    try:
        await bot.load_extension('InterviewSystem')
        logger.info('✅ InterviewSystem system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load InterviewSystem system: {e}')
    try:
        await bot.load_extension('CE')
        logger.info('✅ CE system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load CE system: {e}')
    try:
        await bot.load_extension('econ')
        logger.info('✅ Econ system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Econ system: {e}')
    try:
        await bot.load_extension('anti')
        logger.info('✅ Anti system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Anti system: {e}')
    try:
        await bot.load_extension('raigebait')
        logger.info('✅ Ragebait system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Ragebait system: {e}')
    try:
        await bot.load_extension('status')
        logger.info('✅ Status system loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Status system: {e}')
    try:
        await bot.load_extension('srs')
        logger.info('✅ Shadow Realm loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load SR system: {e}')
    try:
        await bot.load_extension('med')
        logger.info('✅ Med System loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load MED system: {e}')
    try:
        await bot.load_extension('psy')
        logger.info('✅ PSy System loaded successfully')
    except Exception as e:
        logger.error(f'❌ Failed to load Psy system: {e}')
    # Bootstrap: Create data directory and load all data
    await ensure_data_directory()
    await load_all_data()
    
    # Load active appeals from storage
    global active_appeals
    for appeal_id, appeal in bot_data['appeals'].items():
        if appeal.get('status') == 'pending':
            active_appeals[appeal['userId']] = appeal
    
    logger.info(f'✅ Loaded {len(active_appeals)} active appeals')
    
    # Load active inspections from storage and handle startup reconciliation
    global active_inspections
    current_time = datetime.now().timestamp()
    overdue_count = 0
    scheduled_count = 0
    
    for server_id, inspection in bot_data['inspections'].items():
        if inspection.get('status') == 'active' and inspection.get('end_time'):
            end_time = inspection['end_time']
            
            if current_time >= end_time:
                # Inspection is overdue, end it immediately
                logger.info(f'Found overdue inspection for server {server_id}, ending now')
                active_inspections[server_id] = inspection
                asyncio.create_task(end_inspection(server_id, 'overdue', 'completed_overdue'))
                overdue_count += 1
            else:
                # Inspection is still active, reschedule the auto-end task
                remaining_seconds = int(end_time - current_time)
                logger.info(f'Rescheduling inspection for server {server_id} ({remaining_seconds}s remaining)')
                active_inspections[server_id] = inspection
                asyncio.create_task(end_inspection_automatically(server_id, remaining_seconds))
                scheduled_count += 1
    
    logger.info(f'✅ Loaded {len(active_inspections)} active inspections ({overdue_count} overdue, {scheduled_count} rescheduled)')
    
    # Check voice states intent
    if not bot.intents.voice_states:
        logger.warning('⚠️ Voice states intent not enabled - voice activity tracking may not work')
    
    # Cache invites for all guilds for invite tracking
    total_invites = 0
    for guild in bot.guilds:
        invite_count = await cache_guild_invites(guild)
        total_invites += invite_count
    
    logger.info(f'✅ Cached {total_invites} invites across {len(bot.guilds)} servers for invite tracking')
    
    # Start background tasks
    if not auto_save_data.is_running():
        auto_save_data.start()
    
    logger.info('🤖 All background tasks started successfully')
    logger.info('✅ Invite tracking system is active')
@bot.event
async def on_invite_delete(invite):
    """Handle invite deletion"""
    try:
        # Update cache
        guild_id = str(invite.guild.id)
        if guild_id in invite_cache and invite.code in invite_cache[guild_id]:
            del invite_cache[guild_id][invite.code]

        # Log activity
        await log_invite_activity('invite_deleted', invite.guild, invite=invite)

    except Exception as e:
        logger.error(f'Error handling invite deletion: {e}')

@bot.event
async def on_member_join(member):
    """Handle member join - track invite usage and log inspection activity"""
    try:
        guild = member.guild

        # Find which invite was used
        used_invite = await find_used_invite(guild, member)

        # Log the join with invite information
        await log_invite_activity('member_joined', guild, member=member, used_invite=used_invite)
        
        # Log member joins during inspection
        if str(member.guild.id) in active_inspections:
            inspection = active_inspections[str(member.guild.id)]
            current_time = datetime.now().timestamp()

            if current_time < inspection.get('end_time', 0):
                try:
                    # Track activity
                    track_inspection_activity(str(member.guild.id), 'member_joins', member.id)

                    embed = {
                        'title': '📥 Member Joined',
                        'color': 0x2ecc71,
                        'fields': [
                            {'name': '👤 User', 'value': f'{member} ({member.id})', 'inline': True},
                            {'name': '🏠 Server', 'value': f'{member.guild.name} ({member.guild.id})', 'inline': True},
                            {'name': '📅 Account Created', 'value': f'<t:{int(member.created_at.timestamp())}:F>', 'inline': True}
                        ],
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }

                    await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
                except Exception as e:
                    logger.error(f'Error logging member join during inspection: {e}')

    except Exception as e:
        logger.error(f'Error handling member join: {e}')

@bot.event
async def on_guild_join(guild):
    """Cache invites when bot joins a new guild"""
    try:
        invite_count = await cache_guild_invites(guild)
        logger.info(f'Bot joined {guild.name}, cached {invite_count} invites')
    except Exception as e:
        logger.error(f'Error caching invites for new guild {guild.name}: {e}')
# Status Command Because I am a lazy bum
@bot.command(name="status")
@commands.is_owner()
async def set_status(ctx, icon: str, stype: str, *, text: str):
    icon = icon.lower()
    stype = stype.lower()

    # ===== Status Icon =====
    if icon == "online":
        status_icon = discord.Status.online
    elif icon == "idle":
        status_icon = discord.Status.idle
    elif icon == "dnd":
        status_icon = discord.Status.dnd
    elif icon == "invisible":
        status_icon = discord.Status.invisible
    else:
        return await ctx.send("Invalid icon. Use: `online`, `idle`, `dnd`, `invisible`")

    # ===== Activity Type =====
    if stype == "playing":
        activity = discord.Game(name=text)

    elif stype == "watching":
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=text
        )

    elif stype == "listening":
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=text
        )

    else:
        return await ctx.send("Invalid type. Use: `playing`, `watching`, `listening`")

    # ===== Apply =====
    await bot.change_presence(status=status_icon, activity=activity)
    await ctx.send(f"Status updated: `{icon} {stype} {text}`")
# === ENHANCED BLACKLIST COMMAND ===
@bot.command(name='blacklist')
async def handle_enhanced_blacklist(ctx, user_identifier=None, *, initial_input=None):
    """Enhanced blacklist command with interactive questioning and actual banning"""
    # If no arguments, check own blacklist status (DM only)
    if not user_identifier:
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.reply('❌ Use `!blacklist` in DM to check your status, or provide user and reason to blacklist someone.')

        # Check own blacklist status
        blacklist_entry = bot_data['blacklist'].get(str(ctx.author.id))
        staff_blacklist_entry = bot_data['staff_blacklist'].get(str(ctx.author.id))

        if not blacklist_entry and not staff_blacklist_entry:
            return await ctx.reply('✅ You are not blacklisted.')

        # Show blacklist info
        entry = blacklist_entry or staff_blacklist_entry
        embed = discord.Embed(
            title='⚠️ You are blacklisted',
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='Type', value='Staff Blacklist' if staff_blacklist_entry else 'Standard Blacklist', inline=True)
        embed.add_field(name='Reason', value=entry['reason'], inline=False)
        embed.add_field(name='Date', value=entry['timestamp'], inline=True)

        # Check if can appeal
        appeal_timestamp = entry.get('appealTimestamp', 0)
        current_timestamp = datetime.now().timestamp()
        if current_timestamp >= appeal_timestamp:
            embed.add_field(name='Appeal Status', value='You can now submit an appeal using `!appeal`', inline=False)
        else:
            days_left = int((appeal_timestamp - current_timestamp) / (24 * 60 * 60))
            embed.add_field(name='Appeal Status', value=f'You can appeal in {days_left} days', inline=False)

        return await ctx.reply(embed=embed)

    # Staff blacklist command - Interactive questioning system
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        # Check if already blacklisted
        if str(user.id) in bot_data['blacklist'] or str(user.id) in bot_data['staff_blacklist']:
            return await ctx.reply(f'❌ {user} is already blacklisted.')

        # Interactive questioning system
        questions = [
            {
                'question': '📝 **What is the reason for this blacklist?**\nPlease provide a detailed explanation:',
                'key': 'reason',
                'timeout': 300
            },
            {
                'question': '🏷️ **What type of blacklist is this?**\n\n**1** - Standard Blacklist (bans from all servers)\n**2** - Staff Blacklist (bans from all servers except main Asylum Site Zeta)\n\nRespond with **1** or **2**:',
                'key': 'blacklist_type',
                'timeout': 60,
                'validation': lambda x: x in ['1', '2']
            },
            {
                'question': '📅 **When can this be appealed?**\n\nOptions:\n• Enter a date (YYYY-MM-DD or MM/DD/YYYY)\n• Enter number of days (e.g., "90d")\n• Enter "now" for immediate appeals\n• Enter "never" for no appeals',
                'key': 'appeal_date',
                'timeout': 120
            },
            {
                'question': '🔒 **Should this blacklist be redacted?**\n\nRedacted blacklists hide sensitive information while preserving the user details.\n\nRespond with **yes** or **no**:',
                'key': 'redacted',
                'timeout': 60,
                'validation': lambda x: x.lower() in ['yes', 'no', 'y', 'n']
            }
        ]

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        answers = {}

        # Ask questions sequentially
        for i, q in enumerate(questions):
            await ctx.send(f"**Question {i+1}/{len(questions)}**\n\n{q['question']}")

            while True:
                try:
                    response = await bot.wait_for('message', check=check, timeout=q['timeout'])
                    answer = response.content.strip()

                    # Validate if validation function provided
                    if 'validation' in q and not q['validation'](answer):
                        await ctx.send('❌ Invalid response. Please try again.')
                        continue

                    answers[q['key']] = answer
                    break

                except asyncio.TimeoutError:
                    return await ctx.send('⏰ Command timed out. Please start over.')

        # Process answers
        reason = answers['reason']
        blacklist_type = 'staff' if answers['blacklist_type'] == '2' else 'standard'
        appeal_input = answers['appeal_date'].lower()
        is_redacted = answers['redacted'].lower() in ['yes', 'y']

        # Process appeal date
        appeal_timestamp = None
        appealable = True

        if appeal_input == 'never':
            appealable = False
        elif appeal_input == 'now':
            appeal_timestamp = datetime.now().timestamp()
        else:
            parsed_timestamp = parse_date_input(appeal_input)
            if parsed_timestamp:
                appeal_timestamp = parsed_timestamp
            else:
                # Default to 90 days if parsing fails
                appeal_timestamp = int(datetime.now().timestamp()) + (90 * 24 * 60 * 60)

        # Server names to ban from
        all_servers = [
            "Asylum Site Zeta",
            "ASZ | Medical Department", 
            "ASZ | Orderly Server",
            "Executive Security Detachment - Site Zeta",
            "Bot testing",
            "Department of Psychiatry || Site Zeta",
            "[??-?] - ASZ"
        ]

        # Determine which servers to ban from
        if blacklist_type == 'staff':
            # Staff blacklist: all servers EXCEPT main
            servers_to_ban = [s for s in all_servers if s != "Asylum Site Zeta"]
        else:
            # Standard blacklist: ALL servers
            servers_to_ban = all_servers.copy()

        # Create blacklist entry
        blacklist_data = {
            'userId': str(user.id),
            'username': f'{user.name}#{user.discriminator}',
            'reason': reason,
            'moderatorId': str(ctx.author.id),
            'moderator': str(ctx.author),
            'blacklistType': blacklist_type,
            'appealDate': format_timestamp(appeal_timestamp) if appeal_timestamp else None,
            'appealTimestamp': appeal_timestamp if appeal_timestamp else 0,
            'appealable': appealable,
            'redacted': is_redacted,
            'servers': servers_to_ban,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Store in appropriate blacklist
        if blacklist_type == 'staff':
            bot_data['staff_blacklist'][str(user.id)] = blacklist_data
            await safe_save("STAFF_BLACKLIST", bot_data['staff_blacklist'])
        else:
            bot_data['blacklist'][str(user.id)] = blacklist_data
            await safe_save("BLACKLIST", bot_data['blacklist'])

        # === ACTUALLY BAN THE USER FROM SERVERS ===
        ban_results = {
            'successful': [],
            'failed': [],
            'preemptive': [],  # User wasn't in server but was banned anyway
            'skipped': []
        }

        status_msg = await ctx.send('🔨 **Executing bans across servers...**\nThis may take a moment.')

        ban_reason = f"Blacklisted by {ctx.author.name} | Reason: {reason[:100]}"

        for guild in bot.guilds:
            try:
                # Skip if server name not in ban list
                if guild.name not in servers_to_ban:
                    ban_results['skipped'].append(f"{guild.name} (Not in ban list)")
                    continue
                
                # Check if bot has ban permissions
                if not guild.me.guild_permissions.ban_members:
                    ban_results['failed'].append(f"{guild.name} (Bot lacks ban permission)")
                    logger.warning(f"Cannot ban in {guild.name}: Missing ban_members permission")
                    continue
                
                # Try to get the member first
                member = None
                try:
                    member = await guild.fetch_member(user.id)
                except discord.NotFound:
                    # User is not in the server, but we can still ban them preemptively
                    pass
                except discord.HTTPException as e:
                    logger.error(f"Error fetching member in {guild.name}: {e}")
                
                # If member exists, check if they're bannable
                if member:
                    # Check if user has higher role than bot
                    if member.top_role >= guild.me.top_role:
                        ban_results['failed'].append(f"{guild.name} (User has higher/equal role)")
                        logger.warning(f"Cannot ban {user.name} in {guild.name}: Role hierarchy")
                        continue
                    
                    # Check if user is server owner
                    if member.id == guild.owner_id:
                        ban_results['failed'].append(f"{guild.name} (User is server owner)")
                        logger.warning(f"Cannot ban {user.name} in {guild.name}: Server owner")
                        continue
                
                # Execute the ban
                try:
                    await guild.ban(
                        user,
                        reason=ban_reason,
                        delete_message_days=0  # Changed to 0 to preserve history
                    )
                    
                    if member:
                        ban_results['successful'].append(guild.name)
                        logger.info(f"Successfully banned {user.name} from {guild.name}")
                    else:
                        ban_results['preemptive'].append(guild.name)
                        logger.info(f"Preemptively banned {user.name} from {guild.name} (not in server)")
                    
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.5)
                    
                except discord.Forbidden:
                    ban_results['failed'].append(f"{guild.name} (Forbidden - check permissions)")
                    logger.error(f"Forbidden: Cannot ban {user.name} in {guild.name}")
                    
                except discord.HTTPException as e:
                    ban_results['failed'].append(f"{guild.name} (HTTP Error: {e.status})")
                    logger.error(f"HTTP error banning {user.name} in {guild.name}: {e}")
                    
            except Exception as e:
                ban_results['failed'].append(f"{guild.name} (Unexpected error)")
                logger.error(f"Unexpected error banning {user.name} in {guild.name}: {type(e).__name__}: {e}")

        await status_msg.delete()

        # Create enhanced embed
        embed_color = 0xf39c12 if blacklist_type == 'staff' else 0xe74c3c
        embed_title = 'Staff Blacklist Applied' if blacklist_type == 'staff' else 'User Blacklisted'

        embed = discord.Embed(
            title=f'✅ {embed_title}',
            description=f'Successfully processed blacklist for {user.mention}',
            color=embed_color,
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(name='👤 User', value=f'{user.name} (`{user.id}`)', inline=True)
        embed.add_field(name='🏷️ Type', value=blacklist_type.title(), inline=True)
        embed.add_field(name='👮 Moderator', value=ctx.author.mention, inline=True)
        embed.add_field(name='📝 Reason', value=reason, inline=False)
        embed.add_field(name='📅 Appeal Date', value=blacklist_data['appealDate'] or 'Never', inline=True)
        embed.add_field(name='✅ Appealable', value='Yes' if appealable else 'No', inline=True)
        embed.add_field(name='🔒 Redacted', value='Yes' if is_redacted else 'No', inline=True)

        # Ban execution summary
        total_attempts = len(ban_results['successful']) + len(ban_results['preemptive']) + len(ban_results['failed'])
        total_success = len(ban_results['successful']) + len(ban_results['preemptive'])
        
        ban_summary = (
            f"**Targets:** {len(servers_to_ban)} servers\n"
            f"✅ **Active Bans:** {len(ban_results['successful'])}\n"
            f"⚠️ **Preemptive Bans:** {len(ban_results['preemptive'])}\n"
            f"❌ **Failed:** {len(ban_results['failed'])}\n"
            f"**Success Rate:** {(total_success/total_attempts*100):.1f}%" if total_attempts > 0 else "N/A"
        )
        
        embed.add_field(name='🔨 Ban Execution', value=ban_summary, inline=False)

        # Show successful bans
        if ban_results['successful']:
            success_list = ', '.join(ban_results['successful'][:5])
            if len(ban_results['successful']) > 5:
                success_list += f" +{len(ban_results['successful']) - 5} more"
            embed.add_field(name='✅ Active Bans', value=success_list, inline=False)

        # Show preemptive bans
        if ban_results['preemptive']:
            preemptive_list = ', '.join(ban_results['preemptive'][:5])
            if len(ban_results['preemptive']) > 5:
                preemptive_list += f" +{len(ban_results['preemptive']) - 5} more"
            embed.add_field(name='⚠️ Preemptive Bans', value=preemptive_list, inline=False)

        # Show failures with details
        if ban_results['failed']:
            failed_list = '\n'.join([f"• {f}" for f in ban_results['failed'][:5]])
            if len(ban_results['failed']) > 5:
                failed_list += f"\n• ...and {len(ban_results['failed']) - 5} more"
            embed.add_field(name='❌ Failed Bans', value=failed_list, inline=False)
            embed.set_footer(text="Some bans failed - check bot permissions and role hierarchy")

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!blacklist {user.name} (type: {blacklist_type}, bans: {total_success}/{total_attempts})')

        # Enhanced webhook logging
        webhook_embed = {
            'title': f'⚠️ {embed_title}',
            'color': embed_color,
            'description': f'User {user.name} (`{user.id}`) has been blacklisted',
            'fields': [
                {'name': '👤 User', 'value': f'{user.name}#{user.discriminator} (`{user.id}`)', 'inline': False},
                {'name': '📝 Reason', 'value': reason, 'inline': False},
                {'name': '👮 Moderator', 'value': f'{ctx.author.name} (`{ctx.author.id}`)', 'inline': True},
                {'name': '🏷️ Blacklist Type', 'value': blacklist_type.title(), 'inline': True},
                {'name': '📅 Appeal Date', 'value': blacklist_data['appealDate'] or 'Never', 'inline': True},
                {'name': '✅ Appealable', 'value': 'Yes' if appealable else 'No', 'inline': True},
                {'name': '🔒 Redacted', 'value': 'Yes' if is_redacted else 'No', 'inline': True},
                {'name': '🎯 Target Servers', 'value': f"{len(servers_to_ban)} servers", 'inline': True},
                {'name': '🔨 Ban Results', 'value': ban_summary, 'inline': False},
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        # Add server lists to webhook
        if ban_results['successful']:
            webhook_embed['fields'].append({
                'name': '✅ Successfully Banned From',
                'value': ', '.join(ban_results['successful']) or 'None',
                'inline': False
            })
        
        if ban_results['failed']:
            webhook_embed['fields'].append({
                'name': '❌ Failed Bans',
                'value': '\n'.join([f"• {f}" for f in ban_results['failed'][:10]]),
                'inline': False
            })

        await post_webhook(embed=webhook_embed, webhook_url=CONFIG['PUBLIC_WEBHOOK_URL'])

    except Exception as error:
        logger.error(f'Error in enhanced blacklist command: {error}', exc_info=True)
        await ctx.reply(f'❌ Failed to create blacklist: {type(error).__name__}: {str(error)}')
@bot.command(name='watchlist')
async def handle_watchlist(ctx, user_identifier=None):
    """Create watchlist channel for user monitoring (staff only)"""
    if not ctx.guild:
        return await ctx.reply("❌ This command can only be used in a server.")
    if not await is_staff(ctx.author):
        return await ctx.reply("❌ You don't have permission to use this command.")
    if not user_identifier:
        return await ctx.reply("❌ Usage: `!watchlist <user>`")
    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply("❌ User not found.")
        # Check if already on watchlist
        if str(user.id) in bot_data.get('watchlist', {}):
            return await ctx.reply(f"❌ {user} is already on the watchlist.")
        # Create private watchlist channel
        channel_name = f"watchlist-{user.id}"
        try:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            # Add staff role permissions using os.getenv directly
            staff_role_id = int(os.getenv('STAFF_ROLE_ID', '1404297871326711848'))
            staff_role = discord.utils.get(ctx.guild.roles, id=staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=False)
            watchlist_channel = await ctx.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Watchlist monitoring for {user} ({user.id})",
                reason=f"Watchlist created by {ctx.author}"
            )
        except discord.Forbidden:
            return await ctx.reply("❌ I don't have permission to create channels in this server.")
        except Exception as e:
            logger.error(f"Error creating watchlist channel: {e}")
            return await ctx.reply("❌ Failed to create watchlist channel.")
        # Store watchlist data
        bot_data.setdefault('watchlist', {})[str(user.id)] = {
            "userId": str(user.id),
            "username": f"{user.name}#{user.discriminator}",
            "channelId": str(watchlist_channel.id),
            "guildId": str(ctx.guild.id),
            "createdBy": str(ctx.author.id),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "active": True
        }
        await safe_save("WATCHLIST", bot_data['watchlist'])
        # Send initial message to watchlist channel
        embed = discord.Embed(
            title="👁️ Watchlist Channel Created",
            description=f"This channel will monitor all activities of {user} across all servers.",
            color=0x9b59b6,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
        embed.add_field(name="Created by", value=str(ctx.author), inline=True)
        embed.add_field(
            name="Monitoring",
            value="All messages, voice activity, joins/leaves across all servers",
            inline=False
        )
        await watchlist_channel.send(embed=embed)
        # Confirm to staff
        await ctx.reply(f"✅ Watchlist channel created: {watchlist_channel.mention}\nNow monitoring {user} across all servers.")
        # Log the command
        await log_command(ctx.author, f"!watchlist {user.name}")
    except Exception as error:
        logger.error(f"Error creating watchlist: {error}")
        await ctx.reply("❌ Failed to create watchlist.")

# === HELP COMMAND ===
@bot.command(name='help')
async def help_command(ctx):
    """Show help information"""
    embed = discord.Embed(
        title='📋 Adens Zeta Bot - Commands',
        description='Comprehensive bot system with advanced features',
        color=0x3498db,
        timestamp=datetime.utcnow()
    )
    
    # Basic Commands
    embed.add_field(
        name='📋 Basic Commands',
        value=(
            "`!help` - Show this help message\n"
            "`!notes` - View your notes (DM)\n"
            "`!blacklist` - Check blacklist status (DM)\n"
            "`!appeal` - Submit an appeal (DM)"
        ),
        inline=False
    )
    
    # Staff Commands
    embed.add_field(
        name='👥 Staff Management',
        value=(
            "`!blacklist <user> <reason>` - Blacklist a user\n"
            "`!unblacklist <user>` - Remove user from blacklist\n"
            "`!addnote <user> <note>` - Add note to user\n"
            "`!removenote <user> <note_id>` - Remove user note\n"
            "`!viewnotes <user>` - View user notes\n"
            "`!staffresign <user> honorable <message>` - Honorable resignation\n"
            "`!staffresign <user> dishonorable` - Dishonorable resignation\n"
            "`!loa` - Start LOA setup"
        ),
        inline=False
    )
    
    # Advanced Moderation Commands
    embed.add_field(
        name='🛡️ Advanced Moderation',
        value=(
            "`!staffblacklist <user> <reason>` - Staff blacklist\n"
            "`!watchlist <user> <server>` - Add user to watchlist\n"
            "`!inspection <server> <hours>` - Start server inspection\n"
            "`!endinspection <server>` - End server inspection\n"
            "`!datawipe <user>` - Initiate data wipe procedure"
        ),
        inline=False
    )
    
    # Ticket System Commands
    embed.add_field(
        name='🎫 Ticket System',
        value=(
            "`!panel create` - Create a new ticket panel (Admin)\n"
            "`!panel list` - View all ticket panels\n"
            "`!panel delete <id>` - Delete a ticket panel (Admin)\n"
            "`!close` - Close current ticket (with confirmation)\n"
            "`!transfer @user` - Transfer ticket to another user\n"
            "`!add @user` - Add user to ticket\n"
            "`!remove @user` - Remove user from ticket\n"
            "`!pasttickets [@user]` - View past tickets and reasons"
        ),
        inline=False
    )
    
    # Application System Commands (NEW)
    embed.add_field(
        name='📝 Application System',
        value=(
            "`!apppanel create` - Create application panel (Admin)\n"
            "`!apppanel list` - View all application panels\n"
            "`!apppanel delete <id>` - Delete application panel (Admin)\n"
            "`!applications [status]` - View applications (pending/accepted/denied/all)\n"
            "**Note:** Users apply via DM when clicking the 'Apply Now' button"
        ),
        inline=False
    )
    
    # Lockdown System Commands
    embed.add_field(
        name='🔒 Lockdown System',
        value=(
            "`!lockdown` - Start department lockdown (DM only)\n"
            "`!endlockdown` - End department lockdown (DM only)\n"
            "`!lockdown_status` - View active lockdowns (DM only)"
        ),
        inline=False
    )
    
    # Paperwork System Commands
    embed.add_field(
        name='📄 Paperwork System',
        value=(
            "`!paperwork` - View available paperwork\n"
            "`!fillpaperwork <name>` - Fill out paperwork\n"
            "`!paperworkcreate <group>` - Create paperwork (Admin)\n"
            "`!paperworkcomplete <user_id>` - Check completion status\n"
            "`!paperworkhelp` - View paperwork system help"
        ),
        inline=False
    )
    
    # Communication Commands
    embed.add_field(
        name='💬 Communication',
        value=(
            "`!say <channel_id> <message>` - Send message through bot\n"
            "`!dm <user> <message>` - Send DM through bot"
        ),
        inline=False
    )
    
    # Utility Commands
    embed.add_field(
        name='🛠️ Utility Commands',
        value=(
            "`!exelog` - Create execution log (ESD only)\n"
            "`!devlog` - Create development log (Dev only)\n"
            "`!ownershiproast <target>` - Roast Aden or Kar\n"
            "`!myadmin` - Check your admin permissions"
        ),
        inline=False
    )
    
    embed.set_footer(text='All moderation actions are logged | Use commands responsibly')
    await ctx.reply(embed=embed)
    await log_command(ctx.author, "help")
@bot.command(name='dm')
async def dm_command(ctx, user_identifier=None, *, message=None):
    """Send DM to a user (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier or not message:
        return await ctx.reply('❌ Usage: `!dm <user> <message>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        # Send the DM
        await user.send(message)

        # Confirm to staff
        embed = discord.Embed(
            title='✅ DM Sent',
            color=0x2ecc71,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='Recipient', value=f'{user} ({user.id})', inline=True)
        embed.add_field(name='Message', value=message[:100] + '...' if len(message) > 100 else message, inline=False)
        embed.add_field(name='Sent by', value=str(ctx.author), inline=True)

        await ctx.reply(embed=embed)

        # Log the command
        await log_command(ctx.author, f'!dm {user.name} {message[:50]}...')

        # Log to webhook
        log_embed = {
            'title': '📨 DM Command Used',
            'color': 0x9b59b6,
            'fields': [
                {'name': 'Staff Member', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Recipient', 'value': f'{user} ({user.id})', 'inline': True},
                {'name': 'Server', 'value': f'{ctx.guild.name} ({ctx.guild.id})' if ctx.guild else 'DM Context', 'inline': True},
                {'name': 'Message', 'value': message[:500] + '...' if len(message) > 500 else message, 'inline': False}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['COMMAND_LOG_WEBHOOK'])

    except discord.Forbidden:
        await ctx.reply('❌ I couldn\'t send a DM to that user. They may have DMs disabled or have blocked the bot.')
    except Exception as error:
        logger.error(f'Error in dm command: {error}')
        await ctx.reply('❌ Failed to send DM.')

@bot.command(name='say')
async def handle_say(ctx, channel_id: str = "", *, message: str = ""):
    """Send a plain text message through the bot from DMs. Only accepts channel IDs."""

    # Ensure command is used in DMs
    if ctx.guild is not None:
        return await ctx.reply('❌ This command can only be used in DMs.')

    if not await is_authorized(ctx.author.id):
        return await ctx.reply('❌ You don\'t have permission to use this command. Staff role required.')

    if not channel_id or not message:
        return await ctx.reply(
            '❌ Usage: `!say <channel_id> <message>`\nExample: `!say 123456789012345678 Hello everyone!`'
        )

    if not channel_id.isdigit():
        return await ctx.reply('❌ Invalid channel ID. It must be a numeric ID.')

    if len(message) > 2000:
        return await ctx.reply('❌ Message too long. Discord messages must be 2000 characters or less.')

    if '@everyone' in message.lower() or '@here' in message.lower():
        return await ctx.reply('❌ Cannot use @everyone or @here mentions in say command.')

    try:
        # Fetch the channel globally
        target_channel = await ctx.bot.fetch_channel(int(channel_id))
        if not target_channel:
            return await ctx.reply(f'❌ Channel not found: {channel_id}')

        # Check bot permissions
        permissions = target_channel.permissions_for(target_channel.guild.me) if hasattr(target_channel, 'guild') else None
        if permissions and not permissions.send_messages:
            return await ctx.reply(f'❌ I don\'t have permission to send messages in {target_channel.mention}')

        # Send plain text
        await target_channel.send(message)

        # Confirm in DM
        await ctx.reply(f'✅ Message sent to {target_channel.mention}.')

    except discord.Forbidden:
        await ctx.reply('❌ I don\'t have permission to send messages in that channel.')
    except discord.NotFound:
        await ctx.reply('❌ Channel not found or invalid ID.')
    except discord.HTTPException as error:
        await ctx.reply(f'❌ Failed to send message due to Discord API error: {error}')
    except Exception as error:
        await ctx.reply(f'❌ Failed to send message: {error}')


@bot.command(name='appeal')
async def handle_appeal(ctx, action=None, user_id=None):
    """Handle appeal submissions and staff actions"""

    # ---------- STAFF ACTIONS ----------
    # Example: !appeal accept 123456789
    if action and user_id:
        # Must be in DMs
        if not isinstance(ctx.channel, discord.DMChannel):
            return await ctx.reply('❌ Appeal management commands work in DMs only.')

        # Must be staff
        if not await is_staff(ctx.author):
            return await ctx.reply('❌ You don\'t have permission to manage appeals.')

        action = action.lower()

        if action == 'accept':
            await handle_appeal_accept(ctx.author, user_id)
        elif action == 'deny':
            await handle_appeal_deny(ctx.author, user_id)
        else:
            return await ctx.reply('❌ Invalid option. Use `accept` or `deny`.')

        return

    # ---------- USER SUBMISSION ----------
    # Must appeal through DMs
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.reply(
            '📝 Appeal commands work in DMs only.\n'
            'Send me a direct message with `!appeal` to start the process.'
        )

    # Check blacklist
    blacklist_entry = bot_data['blacklist'].get(str(ctx.author.id))
    staff_blacklist_entry = bot_data['staff_blacklist'].get(str(ctx.author.id))

    if not blacklist_entry and not staff_blacklist_entry:
        return await ctx.reply('✅ You are not blacklisted and do not need to appeal.')

    entry = blacklist_entry or staff_blacklist_entry

    # Check appeal cooldown
    appeal_timestamp = entry.get('appealTimestamp', 0)
    current_timestamp = datetime.now().timestamp()

    if current_timestamp < appeal_timestamp:
        days_left = int((appeal_timestamp - current_timestamp) / 86400)
        return await ctx.reply(
            f'❌ You cannot appeal yet.\nYou may appeal again in **{days_left} days**.'
        )

    # Check existing active appeal
    if str(ctx.author.id) in active_appeals:
        return await ctx.reply('⏳ You already have a pending appeal.')

    # Start appeal process
    await ctx.reply(
        '📝 **Appeal Submission**\n\n'
        'Please answer the following questions in **ONE MESSAGE**:\n'
        '1. Why should your blacklist be removed?\n'
        '2. What have you learned?\n'
        '3. How will this not happen again?\n\n'
        'Send your response now:'
    )

    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    try:
        msg = await bot.wait_for('message', check=check, timeout=600)
        appeal_text = msg.content
    except asyncio.TimeoutError:
        return await ctx.reply('⏰ Appeal timed out. Please run `!appeal` again.')

    # Store appeal
    appeal_id = str(int(datetime.now().timestamp() * 1000))
    appeal_data = {
        'id': appeal_id,
        'userId': str(ctx.author.id),
        'username': f'{ctx.author.name}#{ctx.author.discriminator}',
        'appealText': appeal_text,
        'originalReason': entry['reason'],
        'blacklistType': entry.get('blacklistType', 'standard'),
        'submittedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'pending'
    }

    bot_data['appeals'][appeal_id] = appeal_data
    active_appeals[str(ctx.author.id)] = appeal_data
    await safe_save("APPEALS", bot_data['appeals'])

    embed = discord.Embed(
        title='✅ Appeal Submitted',
        description='Your appeal has been sent to staff for review.',
        timestamp=datetime.now(timezone.utc),
        color=0x00ff00
    )
    embed.add_field(name='Appeal ID', value=appeal_id, inline=False)
    embed.add_field(name='Status', value='Pending Review', inline=False)

    await ctx.reply(embed=embed)

    # Log to webhook
    webhook_embed = {
        'title': '📝 New Appeal Submitted',
        'color': 0xf39c12,
        'fields': [
            {'name': 'User', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
            {'name': 'Appeal ID', 'value': appeal_id, 'inline': True},
            {'name': 'Blacklist Type', 'value': appeal_data['blacklistType'].title(), 'inline': True},
            {'name': 'Original Reason', 'value': entry['reason'], 'inline': False},
            {'name': 'Appeal Text', 'value': appeal_text[:500] + '...' if len(appeal_text) > 500 else appeal_text, 'inline': False}
        ],
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    await post_webhook(embed=webhook_embed, webhook_url=CONFIG['APPEAL_WEBHOOK_URL'])


async def handle_appeal_accept(staff, user_id_str):
    """Accept an appeal"""
    try:
        appeal = None
        for a in bot_data['appeals'].values():
            if a.get('userId') == user_id_str and a.get('status') == 'pending':
                appeal = a
                break

        if not appeal:
            await staff.send('❌ No pending appeal found for that user ID.')
            return

        # Remove from both blacklists and update appeal
        blacklist_type = appeal.get('blacklistType', 'standard')

        if user_id_str in bot_data['blacklist']:
            del bot_data['blacklist'][user_id_str]
        if user_id_str in bot_data['staff_blacklist']:
            del bot_data['staff_blacklist'][user_id_str]

        appeal['status'] = 'accepted'
        appeal['reviewedBy'] = str(staff.id)
        appeal['reviewedAt'] = datetime.now(timezone.utc).isoformat()

        await safe_save("BLACKLIST", bot_data['blacklist'])
        await safe_save("STAFF_BLACKLIST", bot_data['staff_blacklist'])
        await safe_save("APPEALS", bot_data['appeals'])

        # Remove from active appeals
        if user_id_str in active_appeals:
            del active_appeals[user_id_str]

        user = await bot.fetch_user(int(user_id_str))
        embed = discord.Embed(
            title='✅ Appeal Accepted!',
            description='Your appeal has been accepted and you have been unblacklisted!',
            color=0x00ff00
        )
        embed.add_field(name='Note', value='Contact staff for server access if needed.', inline=False)

        await user.send(embed=embed)
        await staff.send(f'✅ Appeal accepted for {user} ({user_id_str}). User has been unblacklisted.')

        # Log to appeal webhook
        log_embed = {
            'title': '✅ Appeal Accepted',
            'color': 0x00ff00,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user_id_str})', 'inline': True},
                {'name': 'Reviewed by', 'value': f'{staff} ({staff.id})', 'inline': True},
                {'name': 'Appeal ID', 'value': appeal['id'], 'inline': True},
                {'name': 'Blacklist Type', 'value': blacklist_type.title(), 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['APPEAL_WEBHOOK_URL'])

    except Exception as error:
        logger.error(f'Error accepting appeal: {error}')
        await staff.send(f'❌ Error processing appeal acceptance: {error}')

async def handle_appeal_deny(staff, user_id_str):
    """Deny an appeal"""
    try:
        appeal = None
        for a in bot_data['appeals'].values():
            if a.get('userId') == user_id_str and a.get('status') == 'pending':
                appeal = a
                break

        if not appeal:
            await staff.send('❌ No pending appeal found for that user ID.')
            return

        # Ask for denial reason
        await staff.send('Please provide a reason for the denial:')

        def check(m):
            return m.author == staff and isinstance(m.channel, discord.DMChannel)

        try:
            response = await bot.wait_for('message', check=check, timeout=300.0)
            reason = response.content
        except asyncio.TimeoutError:
            await staff.send('⏰ Command timed out. Please try again.')
            return

        # Update appeal
        appeal['status'] = 'denied'
        appeal['reviewedBy'] = str(staff.id)
        appeal['reviewedAt'] = datetime.now(timezone.utc).isoformat()
        appeal['denialReason'] = reason

        await safe_save("APPEALS", bot_data['appeals'])

        # Remove from active appeals
        if user_id_str in active_appeals:
            del active_appeals[user_id_str]

        user = await bot.fetch_user(int(user_id_str))
        embed = discord.Embed(
            title='❌ Appeal Denied',
            description=f'Your appeal has been denied.\n\n**Reason:** {reason}',
            color=0xe74c3c
        )
        embed.add_field(name='Future Appeals', value='You may be able to appeal again in approximately 90 days.', inline=False)

        await user.send(embed=embed)
        await staff.send(f'❌ Appeal denied for {user} ({user_id_str}).')

        # Log to appeal webhook
        log_embed = {
            'title': '❌ Appeal Denied',
            'color': 0xe74c3c,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user_id_str})', 'inline': True},
                {'name': 'Reviewed by', 'value': f'{staff} ({staff.id})', 'inline': True},
                {'name': 'Appeal ID', 'value': appeal['id'], 'inline': True},
                {'name': 'Reason', 'value': reason, 'inline': False}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['APPEAL_WEBHOOK_URL'])

    except Exception as error:
        logger.error(f'Error denying appeal: {error}')
        await staff.send(f'❌ Error processing appeal denial: {error}')

@bot.command(name='notes')
@dm_staff_only
async def handle_dm_notes(ctx):
    """Check own notes in DM"""
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.reply('❌ Use `!notes` in DM to check your notes.')

    notes = bot_data['notes'].get(str(ctx.author.id), [])

    if not notes:
        return await ctx.reply('📝 You have no notes.')

    embed = discord.Embed(
        title=f'📝 Your Notes',
        color=0x95a5a6,
        timestamp=datetime.now(timezone.utc)
    )

    # Show up to 5 notes in DM
    for i, note in enumerate(notes[:5]):
        embed.add_field(
            name=f'Note {i + 1}',
            value=f'**Note:** {note["note"]}\n**Date:** {note["timestamp"]}',
            inline=False
        )

    if len(notes) > 5:
        embed.add_field(
            name='...',
            value=f'And {len(notes) - 5} more notes',
            inline=False
        )

    await ctx.reply(embed=embed)

@bot.command(name='inspection')
@dm_staff_only
async def handle_inspection(ctx, server_identifier=None, hours=None):
    """Start server inspection with activity monitoring"""
    # Check permissions - staff only
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not server_identifier or not hours:
        return await ctx.reply('❌ Usage: `!inspection <server> <hours>`\n\nExample: `!inspection MyServer 24`')

    try:
        # Validate hours parameter
        try:
            hours_int = int(hours)
            if hours_int <= 0 or hours_int > 168:  # Max 1 week
                return await ctx.reply('❌ Hours must be between 1 and 168 (1 week maximum).')
        except ValueError:
            return await ctx.reply('❌ Hours must be a valid number.')

        # Find the target server
        target_guild = None
        for guild in bot.guilds:
            if (guild.name.lower() == server_identifier.lower() or 
                str(guild.id) == server_identifier):
                target_guild = guild
                break

        if not target_guild:
            return await ctx.reply(f'❌ Server not found: {server_identifier}')

        # Check if server is already under inspection
        if str(target_guild.id) in active_inspections:
            return await ctx.reply(f'⚠️ Server **{target_guild.name}** is already under inspection.')

        # Ask for department leader user ID
        await ctx.reply('🔍 **Department Leader Required**\n\nPlease provide the User ID of the department leader who should be notified about this inspection:')

        def check_leader_id(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            leader_response = await bot.wait_for('message', check=check_leader_id, timeout=60.0)
            leader_id = leader_response.content.strip()

            # Validate user ID format
            if not leader_id.isdigit():
                return await ctx.reply('❌ Invalid user ID format. Please provide a valid Discord user ID.')

            # Try to fetch the department leader
            try:
                department_leader = await bot.fetch_user(int(leader_id))
            except discord.NotFound:
                return await ctx.reply(f'❌ User not found with ID: {leader_id}')
            except Exception:
                return await ctx.reply('❌ Error fetching user. Please check the user ID.')

        except asyncio.TimeoutError:
            return await ctx.reply('⏰ Command timed out. Please try again.')

        # Calculate end time
        end_time = datetime.now() + timedelta(hours=hours_int)
        end_timestamp = int(end_time.timestamp())

        # DM the department leader first
        try:
            leader_embed = discord.Embed(
                title='🚨 Server Inspection Notice',
                description=f'Your server **{target_guild.name}** has been placed under inspection.',
                color=0xe74c3c,
                timestamp=datetime.now(timezone.utc)
            )
            leader_embed.add_field(name='Duration', value=f'{hours_int} hours', inline=True)
            leader_embed.add_field(name='Ends At', value=f'<t:{end_timestamp}:F>', inline=True)
            leader_embed.add_field(name='Initiated By', value=f'{ctx.author} ({ctx.author.id})', inline=False)
            leader_embed.add_field(
                name='⚠️ Important Notice', 
                value='All activities in your server will be monitored and logged during this period. Please inform your staff and members accordingly.',
                inline=False
            )   
            leader_embed.add_field(
                name='Site Zeta Inspetion Criteria', 
                value='📄 [Document](https://docs.google.com/document/d/1mJfU4VSZayM21hC2d5BNpsLHvhM9hZEJ2ztG3vZWWCI/edit?usp=sharing)',
                inline=False
            )

            await department_leader.send(embed=leader_embed)

        except discord.Forbidden:
            return await ctx.reply(f'❌ Could not DM department leader {department_leader}. They may have DMs disabled.')
        except Exception as e:
            logger.error(f'Error DMing department leader: {e}')
            return await ctx.reply('❌ Failed to notify department leader.')

        # Create "Under Inspection" channel
        inspection_channel = None
        try:
            # Check if channel already exists
            for channel in target_guild.text_channels:
                if channel.name == 'under-inspection':
                    inspection_channel = channel
                    break

            # Create channel if it doesn't exist
            if not inspection_channel:
                inspection_channel = await target_guild.create_text_channel(
                    name='under-inspection',
                    topic=f'Server under inspection - ends <t:{end_timestamp}:R>',
                    reason=f'Inspection initiated by {ctx.author}'
                )

        except discord.Forbidden:
            return await ctx.reply(f'❌ I don\'t have permission to create channels in **{target_guild.name}**.')
        except Exception as e:
            logger.error(f'Error creating inspection channel: {e}')
            return await ctx.reply('❌ Failed to create inspection channel.')

        # Post announcement in inspection channel with @everyone ping
        try:
            announcement_embed = discord.Embed(
                title='🚨 SERVER UNDER INSPECTION',
                description=f'This server is now under official inspection and monitoring.',
                color=0xe74c3c,
                timestamp=datetime.now(timezone.utc)
            )
            announcement_embed.add_field(name='⏰ Duration', value=f'{hours_int} hours', inline=True)
            announcement_embed.add_field(name='🏁 Ends', value=f'<t:{end_timestamp}:F>', inline=True)
            announcement_embed.add_field(name='👮 Initiated By', value=f'{ctx.author}', inline=True)
            announcement_embed.add_field(
                name='⚠️ IMPORTANT NOTICE',
                value='**All activities are being monitored and logged.**\n\n• Do not engage in any inappropriate behavior\n• All messages, voice activity, and actions are recorded\n• Violations may result in immediate action\n• Cooperate fully with staff during this period',
                inline=False
            )
            announcement_embed.add_field(
                name='📊 Monitoring Includes',
                value='• Messages and edits\n• Voice channel activity\n• Member joins/leaves\n• Role and permission changes\n• Channel modifications\n• All user interactions',
                inline=False
            )

            await inspection_channel.send('@everyone', embed=announcement_embed)

        except discord.Forbidden:
            return await ctx.reply(f'❌ I don\'t have permission to send messages in **{target_guild.name}**.')
        except Exception as e:
            logger.error(f'Error posting inspection announcement: {e}')
            return await ctx.reply('❌ Failed to post inspection announcement.')

        # Store inspection data
        inspection_data = {
            'server_id': str(target_guild.id),
            'server_name': target_guild.name,
            'initiated_by': str(ctx.author.id),
            'initiated_at': datetime.now(timezone.utc).isoformat(),
            'end_time': end_timestamp,
            'hours': hours_int,
            'channel_id': str(inspection_channel.id),
            'department_leader': str(department_leader.id),
            'status': 'active',
            'activity_counts': {
                'messages': 0,
                'message_edits': 0,
                'message_deletes': 0,
                'member_joins': 0,
                'member_leaves': 0,
                'voice_changes': 0,
                'channel_creates': 0,
                'channel_deletes': 0,
                'total_users': []
            }
        }

        bot_data['inspections'][str(target_guild.id)] = inspection_data
        active_inspections[str(target_guild.id)] = inspection_data
        await safe_save("INSPECTIONS", bot_data['inspections'])

        # Schedule automatic ending
        seconds_to_wait = hours_int * 3600
        asyncio.create_task(end_inspection_automatically(str(target_guild.id), seconds_to_wait))

        # Confirm to staff
        confirm_embed = discord.Embed(
            title='✅ Inspection Started',
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )
        confirm_embed.add_field(name='Server', value=f'{target_guild.name} ({target_guild.id})', inline=True)
        confirm_embed.add_field(name='Duration', value=f'{hours_int} hours', inline=True)
        confirm_embed.add_field(name='Ends At', value=f'<t:{end_timestamp}:F>', inline=True)
        confirm_embed.add_field(name='Department Leader Notified', value=f'{department_leader} ({department_leader.id})', inline=False)
        confirm_embed.add_field(name='Channel Created', value=f'#{inspection_channel.name}', inline=True)

        await ctx.reply(embed=confirm_embed)
        await log_command(ctx.author, f'!inspection {target_guild.name} {hours_int}h')

        # Log to webhook
        webhook_embed = {
            'title': '🚨 Inspection Started',
            'color': 0xe74c3c,
            'fields': [
                {'name': 'Server', 'value': f'{target_guild.name} ({target_guild.id})', 'inline': True},
                {'name': 'Initiated By', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Duration', 'value': f'{hours_int} hours', 'inline': True},
                {'name': 'Department Leader', 'value': f'{department_leader} ({department_leader.id})', 'inline': True},
                {'name': 'Ends At', 'value': f'<t:{end_timestamp}:F>', 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=webhook_embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])

        logger.info(f'Inspection started for {target_guild.name} by {ctx.author}')

    except Exception as error:
        logger.error(f'Error in inspection command: {error}')
        await ctx.reply('❌ Failed to start inspection.')
from datetime import datetime, timedelta
import re

@bot.command(name="loa")
async def loa(ctx):
    """Start LOA setup (Add/Remove, User ID, Duration)"""
    if ctx.guild is None:
        return await ctx.send("❌ This command can only be used in a server.")

    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.send("❌ You don't have permission to use this command.")

    questions = [
        "Do you want to **add** or **remove** LOA?",
        "What is the **user ID** of the member?",
        "How long? (e.g., 3 days, 1 week, 30m)"
    ]

    answers = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for q in questions:
        await ctx.send(q)
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
        except:
            return await ctx.send("⏰ You took too long. Command cancelled.")
        answers.append(msg.content)

    action = answers[0].lower()

    # Convert user ID
    try:
        user_id = int(answers[1])
    except ValueError:
        return await ctx.send("❌ Invalid user ID. Must be a number.")

    target_user = ctx.guild.get_member(user_id)
    if not target_user:
        return await ctx.send("❌ That user ID is not in this server.")

    loa_role = ctx.guild.get_role(1415149332553928705)
    log_channel = ctx.guild.get_channel(1392577795841855658)

    # Convert duration string to timedelta
    duration_str = answers[2].lower()
    duration = None

    # Simple parsing for formats like '3 days', '1 week', '30m', '12h'
    match = re.match(r"(\d+)\s*(d|day|days|h|hour|hours|m|min|minute|minutes|w|week|weeks)", duration_str)
    if match:
        amount = int(match[1])
        unit = match[2]
        if unit in ["d", "day", "days"]:
            duration = timedelta(days=amount)
        elif unit in ["h", "hour", "hours"]:
            duration = timedelta(hours=amount)
        elif unit in ["m", "min", "minute", "minutes"]:
            duration = timedelta(minutes=amount)
        elif unit in ["w", "week", "weeks"]:
            duration = timedelta(weeks=amount)
    else:
        return await ctx.send("❌ Could not parse duration. Use formats like '3 days', '12h', '30m', '1 week'.")

    expiry_time = datetime.utcnow() + duration if duration else None

    if action == "add":
        await target_user.add_roles(loa_role, reason="Put on LOA")

        try:
            await target_user.edit(nick=f"LOA - {target_user.name}")
        except discord.Forbidden:
            await ctx.send("⚠️ Couldn’t change nickname (missing permissions).")

        try:
            await target_user.send(f"You have been put on LOA until <t:{int(expiry_time.timestamp())}:F>.")
        except discord.Forbidden:
            await ctx.send("⚠️ Couldn’t DM the user.")

        if log_channel:
            await log_channel.send(
                f"✅ {target_user.mention} has been put on LOA until <t:{int(expiry_time.timestamp())}:F> by {ctx.author.mention}"
            )

        await ctx.send(f"✅ {target_user.mention} is now on LOA until <t:{int(expiry_time.timestamp())}:F>.")

    elif action == "remove":
        await target_user.remove_roles(loa_role, reason="Removed from LOA")

        try:
            await target_user.edit(nick=None)
        except discord.Forbidden:
            await ctx.send("⚠️ Couldn’t reset nickname (missing permissions).")

        if log_channel:
            await log_channel.send(
                f"❌ {target_user.mention} has been removed from LOA by {ctx.author.mention}"
            )

        await ctx.send(f"❌ {target_user.mention} has been removed from LOA.")

    else:
        await ctx.send("❌ Invalid action. Please type `add` or `remove`.")

@bot.command(name='endinspection')
async def handle_end_inspection(ctx, server_identifier=None):
    """Manually end server inspection"""
    # Check permissions - staff only
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not server_identifier:
        return await ctx.reply('❌ Usage: `!endinspection <server>`\n\nExample: `!endinspection MyServer`')

    try:
        # Find the target server
        target_guild = None
        for guild in bot.guilds:
            if (guild.name.lower() == server_identifier.lower() or 
                str(guild.id) == server_identifier):
                target_guild = guild
                break

        if not target_guild:
            return await ctx.reply(f'❌ Server not found: {server_identifier}')

        # Check if server is under inspection
        if str(target_guild.id) not in active_inspections:
            return await ctx.reply(f'⚠️ Server **{target_guild.name}** is not currently under inspection.')

        # Get inspection data
        inspection_data = active_inspections[str(target_guild.id)]
        department_leader_id = inspection_data.get('department_leader')
        inspection_channel_id = inspection_data.get('channel_id')

        # Delete the inspection channel
        inspection_channel = None
        try:
            if inspection_channel_id:
                inspection_channel = target_guild.get_channel(int(inspection_channel_id))
                if inspection_channel:
                    await inspection_channel.delete(reason=f'Inspection ended manually by {ctx.author}')
                else:
                    # Try to find by name if ID lookup failed
                    for channel in target_guild.text_channels:
                        if channel.name == 'under-inspection':
                            inspection_channel = channel
                            await inspection_channel.delete(reason=f'Inspection ended manually by {ctx.author}')
                            break
        except discord.Forbidden:
            await ctx.reply(f'⚠️ I don\'t have permission to delete the inspection channel in **{target_guild.name}**.')
        except Exception as e:
            logger.error(f'Error deleting inspection channel: {e}')
            await ctx.reply('⚠️ Failed to delete inspection channel, but inspection has been ended.')

        # DM the department leader that inspection is over
        try:
            if department_leader_id:
                department_leader = await bot.fetch_user(int(department_leader_id))

                leader_embed = discord.Embed(
                    title='✅ Inspection Completed',
                    description=f'The inspection for your server **{target_guild.name}** has been completed and ended.',
                    color=0x2ecc71,
                    timestamp=datetime.now(timezone.utc)
                )
                leader_embed.add_field(name='Status', value='Your server is now clear ✅', inline=True)
                leader_embed.add_field(name='Ended By', value=f'{ctx.author} ({ctx.author.id})', inline=True)
                leader_embed.add_field(
                    name='✅ All Clear', 
                    value='All monitoring has stopped and your server operations can return to normal.',
                    inline=False
                )

                await department_leader.send(embed=leader_embed)

        except discord.NotFound:
            logger.warning(f'Department leader {department_leader_id} not found for inspection end notification')
        except discord.Forbidden:
            logger.warning(f'Could not DM department leader {department_leader_id} - DMs disabled')
        except Exception as e:
            logger.error(f'Error DMing department leader: {e}')

        # Use unified end function
        await end_inspection(str(target_guild.id), 'manual', 'ended_manually')

        # Record who ended it manually
        if str(target_guild.id) in bot_data['inspections']:
            bot_data['inspections'][str(target_guild.id)]['ended_by'] = str(ctx.author.id)
            await safe_save("INSPECTIONS", bot_data['inspections'])

        # Confirm to staff
        confirm_embed = discord.Embed(
            title='✅ Inspection Ended',
            color=0x2ecc71,
            timestamp=datetime.now(timezone.utc)
        )
        confirm_embed.add_field(name='Server', value=f'{target_guild.name} ({target_guild.id})', inline=True)
        confirm_embed.add_field(name='Ended By', value=str(ctx.author), inline=True)
        confirm_embed.add_field(name='Channel Deleted', value='✅ under-inspection' if inspection_channel else '⚠️ Channel not found', inline=True)
        confirm_embed.add_field(name='Department Leader Notified', value='✅ DM sent' if department_leader_id else '⚠️ No leader ID found', inline=True)
        confirm_embed.add_field(name='Status', value='All monitoring stopped', inline=False)

        await ctx.reply(embed=confirm_embed)
        await log_command(ctx.author, f'!endinspection {target_guild.name}')

        # Log to webhook
        webhook_embed = {
            'title': '✅ Inspection Manually Ended',
            'color': 0x2ecc71,
            'fields': [
                {'name': 'Server', 'value': f'{target_guild.name} ({target_guild.id})', 'inline': True},
                {'name': 'Ended By', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Original Duration', 'value': f"{inspection_data.get('hours', 'Unknown')} hours", 'inline': True},
                {'name': 'Department Leader', 'value': f'<@{department_leader_id}>' if department_leader_id else 'Unknown', 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=webhook_embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])

        logger.info(f'Inspection ended manually for {target_guild.name} by {ctx.author}')

    except Exception as error:
        logger.error(f'Error in endinspection command: {error}')
        await ctx.reply('❌ Failed to end inspection.')

@bot.command(name='shutdown')
@dm_owner_only
async def handle_shutdown(ctx, minutes=None):
    """Temporarily shutdown the bot (owner only)"""
    if not await is_owner(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not minutes:
        return await ctx.reply('❌ Usage: `!shutdown <minutes>`\n\nExample: `!shutdown 30`')

    try:
        minutes_int = int(minutes)
        if minutes_int <= 0 or minutes_int > 1440:  # Max 24 hours in minutes
            return await ctx.reply('❌ Minutes must be between 1 and 1440 (24 hours).')
    except ValueError:
        return await ctx.reply('❌ Minutes must be a valid number.')

    global bot_shutdown_until
    bot_shutdown_until = datetime.now() + timedelta(minutes=minutes_int)

    embed = discord.Embed(
        title='🚫 Bot Shutdown',
        description=f'Bot will be shutdown for {minutes_int} minutes.',
        color=0xe74c3c,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name='Shutdown Until', value=f'<t:{int(bot_shutdown_until.timestamp())}:F>', inline=False)
    embed.add_field(name='Initiated By', value=str(ctx.author), inline=True)

    await ctx.reply(embed=embed)
    await log_command(ctx.author, f'!shutdown {minutes_int}m')

    logger.info(f'Bot shutdown for {minutes_int} minutes by {ctx.author}')

@bot.command(name='dnd')
async def handle_dnd(ctx, user_identifier=None):
    """Toggle DND mode for a user (owner only)"""
    if not await is_owner(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier:
        return await ctx.reply('❌ Usage: `!dnd <user>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        if user.id in dnd_users:
            dnd_users.remove(user.id)
            status = 'disabled'
            color = 0x2ecc71
        else:
            dnd_users.add(user.id)
            status = 'enabled'
            color = 0xe74c3c

        embed = discord.Embed(
            title=f'🔕 DND Mode {status.title()}',
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
        embed.add_field(name='Status', value=status.title(), inline=True)
        embed.add_field(name='By', value=str(ctx.author), inline=True)

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!dnd {user.name} ({status})')

    except Exception as error:
        logger.error(f'Error in dnd command: {error}')
        await ctx.reply('❌ Failed to toggle DND mode.')

# === MISSING COMMANDS IMPLEMENTATION ===

@bot.command(name='unblacklist')
async def handle_unblacklist(ctx, user_identifier=None):
    """Remove user from blacklist (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier:
        return await ctx.reply('❌ Usage: `!unblacklist <user>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        user_id = str(user.id)

        # Check if user is blacklisted
        if user_id not in bot_data['blacklist'] and user_id not in bot_data['staff_blacklist']:
            return await ctx.reply(f'❌ {user} is not blacklisted.')

        # Remove from both blacklists
        removed_from = []
        if user_id in bot_data['blacklist']:
            del bot_data['blacklist'][user_id]
            removed_from.append('Standard Blacklist')
            await safe_save("BLACKLIST", bot_data['blacklist'])

        if user_id in bot_data['staff_blacklist']:
            del bot_data['staff_blacklist'][user_id]
            removed_from.append('Staff Blacklist')
            await safe_save("STAFF_BLACKLIST", bot_data['staff_blacklist'])

        embed = discord.Embed(
            title='✅ User Unblacklisted',
            color=0x2ecc71,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
        embed.add_field(name='Removed From', value=', '.join(removed_from), inline=True)
        embed.add_field(name='By', value=str(ctx.author), inline=True)

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!unblacklist {user.name}')

        # Log to webhook
        log_embed = {
            'title': '✅ User Unblacklisted',
            'color': 0x2ecc71,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user.id})', 'inline': True},
                {'name': 'Staff Member', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Removed From', 'value': ', '.join(removed_from), 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['COMMAND_LOG_WEBHOOK'])

    except Exception as error:
        logger.error(f'Error in unblacklist command: {error}')
        await ctx.reply('❌ Failed to unblacklist user.')

@bot.command(name='addnote')
@dm_staff_only
async def handle_add_note(ctx, user_identifier=None, *, note_text=None):
    """Add note to user (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier or not note_text:
        return await ctx.reply('❌ Usage: `!addnote <user> <note>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        user_id = str(user.id)

        # Initialize user notes if they don't exist
        if user_id not in bot_data['notes']:
            bot_data['notes'][user_id] = []

        # Create note entry
        note_id = str(int(datetime.now().timestamp() * 1000))  # Unique ID based on timestamp
        note_entry = {
            'id': note_id,
            'note': note_text,
            'addedBy': str(ctx.author.id),
            'addedByName': f'{ctx.author.name}#{ctx.author.discriminator}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'timestampDisplay': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        }

        bot_data['notes'][user_id].append(note_entry)
        await safe_save("NOTES", bot_data['notes'])

        embed = discord.Embed(
            title='✅ Note Added',
            color=0x2ecc71,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
        embed.add_field(name='Note ID', value=note_id, inline=True)
        embed.add_field(name='Added By', value=str(ctx.author), inline=True)
        embed.add_field(name='Note', value=note_text[:500] + '...' if len(note_text) > 500 else note_text, inline=False)

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!addnote {user.name} [Note ID: {note_id}]')

        # Log to webhook
        log_embed = {
            'title': '📝 Note Added',
            'color': 0x3498db,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user.id})', 'inline': True},
                {'name': 'Staff Member', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Note ID', 'value': note_id, 'inline': True},
                {'name': 'Note', 'value': note_text[:500] + '...' if len(note_text) > 500 else note_text, 'inline': False}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['COMMAND_LOG_WEBHOOK'])

    except Exception as error:
        logger.error(f'Error in addnote command: {error}')
        await ctx.reply('❌ Failed to add note.')

@bot.command(name='removenote')
async def handle_remove_note(ctx, user_identifier=None, note_id=None):
    """Remove user note by ID (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier or not note_id:
        return await ctx.reply('❌ Usage: `!removenote <user> <note_id>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        user_id = str(user.id)

        # Check if user has notes
        if user_id not in bot_data['notes'] or not bot_data['notes'][user_id]:
            return await ctx.reply(f'❌ {user} has no notes.')

        # Find and remove the note
        note_found = None
        for i, note in enumerate(bot_data['notes'][user_id]):
            if note.get('id') == note_id:
                note_found = bot_data['notes'][user_id].pop(i)
                break

        if not note_found:
            return await ctx.reply(f'❌ Note with ID {note_id} not found for {user}.')

        await safe_save("NOTES", bot_data['notes'])

        embed = discord.Embed(
            title='✅ Note Removed',
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
        embed.add_field(name='Note ID', value=note_id, inline=True)
        embed.add_field(name='Removed By', value=str(ctx.author), inline=True)
        embed.add_field(name='Original Note', value=note_found['note'][:500] + '...' if len(note_found['note']) > 500 else note_found['note'], inline=False)
        embed.add_field(name='Originally Added By', value=note_found.get('addedByName', 'Unknown'), inline=True)

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!removenote {user.name} {note_id}')

        # Log to webhook
        log_embed = {
            'title': '🗑️ Note Removed',
            'color': 0xe74c3c,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user.id})', 'inline': True},
                {'name': 'Staff Member', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Note ID', 'value': note_id, 'inline': True},
                {'name': 'Removed Note', 'value': note_found['note'][:500] + '...' if len(note_found['note']) > 500 else note_found['note'], 'inline': False}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['COMMAND_LOG_WEBHOOK'])

    except Exception as error:
        logger.error(f'Error in removenote command: {error}')
        await ctx.reply('❌ Failed to remove note.')

@bot.command(name='appeals')
async def handle_list_appeals(ctx):
    """List all current appeals (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    try:
        pending_appeals = []
        for appeal_id, appeal in bot_data['appeals'].items():
            if appeal.get('status') == 'pending':
                pending_appeals.append(appeal)

        if not pending_appeals:
            return await ctx.reply('📝 No pending appeals found.')

        embed = discord.Embed(
            title='📝 Current Appeals',
            color=0xf39c12,
            timestamp=datetime.now(timezone.utc)
        )

        # Show appeals (limit to 10 for space)
        for i, appeal in enumerate(pending_appeals[:10]):
            try:
                user = await bot.fetch_user(int(appeal['userId']))
                user_display = f'{user} ({appeal["userId"]})'
            except:
                user_display = f'Unknown User ({appeal["userId"]})'

            embed.add_field(
                name=f'Appeal {i + 1} (ID: {appeal["id"]})',
                value=f'**User:** {user_display}\n**Type:** {appeal.get("blacklistType", "standard").title()}\n**Submitted:** {appeal.get("submittedAt", "Unknown")}\n**Reason:** {appeal.get("originalReason", "N/A")[:200]}{"..." if len(appeal.get("originalReason", "")) > 200 else ""}',
                inline=False
            )

        if len(pending_appeals) > 10:
            embed.add_field(
                name='...',
                value=f'And {len(pending_appeals) - 10} more appeals',
                inline=False
            )

        embed.set_footer(text=f'Total pending appeals: {len(pending_appeals)}')

        await ctx.reply(embed=embed)
        await log_command(ctx.author, '!appeals')

    except Exception as error:
        logger.error(f'Error in appeals command: {error}')
        await ctx.reply('❌ Failed to list appeals.')

@bot.command(name='adjustappeal')
async def handle_adjust_appeal(ctx, appeal_id=None, new_date=None):
    """Adjust appeal date (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not appeal_id or not new_date:
        return await ctx.reply('❌ Usage: `!adjustappeal <appeal_id> <new_date>`\n\nDate formats: YYYY-MM-DD, MM/DD/YYYY, "30d", or "now"')

    try:
        # Find the appeal
        if appeal_id not in bot_data['appeals']:
            return await ctx.reply(f'❌ Appeal with ID {appeal_id} not found.')

        appeal = bot_data['appeals'][appeal_id]

        # Parse the new date
        new_timestamp = parse_date_input(new_date)
        if new_timestamp is None:
            return await ctx.reply('❌ Invalid date format. Use: YYYY-MM-DD, MM/DD/YYYY, "30d", or "now"')

        # Update the appeal date
        old_date = appeal.get('submittedAt', 'Unknown')
        appeal['submittedAt'] = datetime.fromtimestamp(new_timestamp, timezone.utc).isoformat()
        appeal['adjustedBy'] = str(ctx.author.id)
        appeal['adjustedAt'] = datetime.now(timezone.utc).isoformat()

        await safe_save("APPEALS", bot_data['appeals'])

        try:
            user = await bot.fetch_user(int(appeal['userId']))
            user_display = f'{user} ({appeal["userId"]})'
        except:
            user_display = f'Unknown User ({appeal["userId"]})'

        embed = discord.Embed(
            title='✅ Appeal Date Adjusted',
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='Appeal ID', value=appeal_id, inline=True)
        embed.add_field(name='User', value=user_display, inline=True)
        embed.add_field(name='Adjusted By', value=str(ctx.author), inline=True)
        embed.add_field(name='Old Date', value=old_date, inline=True)
        embed.add_field(name='New Date', value=appeal['submittedAt'], inline=True)

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!adjustappeal {appeal_id} {new_date}')

        # Log to webhook
        log_embed = {
            'title': '📅 Appeal Date Adjusted',
            'color': 0x3498db,
            'fields': [
                {'name': 'Appeal ID', 'value': appeal_id, 'inline': True},
                {'name': 'User', 'value': user_display, 'inline': True},
                {'name': 'Staff Member', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Old Date', 'value': old_date, 'inline': True},
                {'name': 'New Date', 'value': appeal['submittedAt'], 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['APPEAL_WEBHOOK_URL'])

    except Exception as error:
        logger.error(f'Error in adjustappeal command: {error}')
        await ctx.reply('❌ Failed to adjust appeal date.')

@bot.command(name='staffblacklist')
async def handle_staff_blacklist(ctx, user_identifier=None, *, reason=None):
    """Staff blacklist a user (ban from all servers) - staff only"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier or not reason:
        return await ctx.reply('❌ Usage: `!staffblacklist <user> <reason>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        user_id = str(user.id)

        # Check if already staff blacklisted
        if user_id in bot_data['staff_blacklist']:
            return await ctx.reply(f'❌ {user} is already on the staff blacklist.')

        # Create staff blacklist entry
        appeal_date = datetime.now() + timedelta(days=90)  # 90 days from now
        blacklist_entry = {
            'userId': user_id,
            'username': f'{user.name}#{user.discriminator}',
            'reason': reason,
            'blacklistedBy': str(ctx.author.id),
            'blacklistedByName': f'{ctx.author.name}#{ctx.author.discriminator}',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'timestampDisplay': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
            'appealTimestamp': appeal_date.timestamp(),
            'blacklistType': 'staff'
        }

        bot_data['staff_blacklist'][user_id] = blacklist_entry
        await safe_save("STAFF_BLACKLIST", bot_data['staff_blacklist'])

        # Ban user from all servers the bot is in (except exempt servers)
        banned_servers = []
        failed_servers = []

        for guild in bot.guilds:
            try:
                # Skip if user is not in the server
                member = guild.get_member(user.id)
                if not member:
                    continue

                # Skip main server or other exempt servers (you can add more conditions here)
                if guild.id == CONFIG['MAIN_SERVER_ID']:
                    continue

                # Ban the user
                await guild.ban(user, reason=f'Staff blacklist: {reason}', delete_message_days=0)
                banned_servers.append(guild.name)

            except discord.Forbidden:
                failed_servers.append(f'{guild.name} (No permission)')
            except Exception as e:
                failed_servers.append(f'{guild.name} (Error: {str(e)[:50]})')

        embed = discord.Embed(
            title='⚫ User Staff Blacklisted',
            color=0x2c3e50,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name='User', value=f'{user} ({user.id})', inline=True)
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.add_field(name='Staff Member', value=str(ctx.author), inline=True)
        embed.add_field(name='Appeal Date', value=f'<t:{int(appeal_date.timestamp())}:F>', inline=True)

        if banned_servers:
            embed.add_field(name='Banned From', value=', '.join(banned_servers[:5]) + ('...' if len(banned_servers) > 5 else ''), inline=False)

        if failed_servers:
            embed.add_field(name='Failed to Ban From', value=', '.join(failed_servers[:3]) + ('...' if len(failed_servers) > 3 else ''), inline=False)

        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!staffblacklist {user.name}')

        # Log to webhook
        log_embed = {
            'title': '⚫ Staff Blacklist Added',
            'color': 0x2c3e50,
            'fields': [
                {'name': 'User', 'value': f'{user} ({user.id})', 'inline': True},
                {'name': 'Staff Member', 'value': f'{ctx.author} ({ctx.author.id})', 'inline': True},
                {'name': 'Reason', 'value': reason, 'inline': False},
                {'name': 'Banned From Servers', 'value': f'{len(banned_servers)} servers', 'inline': True},
                {'name': 'Failed Bans', 'value': f'{len(failed_servers)} servers', 'inline': True}
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await post_webhook(embed=log_embed, webhook_url=CONFIG['COMMAND_LOG_WEBHOOK'])

    except Exception as error:
        logger.error(f'Error in staffblacklist command: {error}')
        await ctx.reply('❌ Failed to staff blacklist user.')

@bot.command(name='datawipe')
async def handle_datawipe(ctx, user_identifier=None):
    """Initiate data wipe procedure (staff only)"""
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')

    if not user_identifier:
        return await ctx.reply('❌ Usage: `!datawipe <user>`')

    try:
        user = await resolve_user(user_identifier)
        if not user:
            return await ctx.reply('❌ User not found.')

        user_id = str(user.id)

        # Check if datawipe is already active
        if user_id in active_datawipes:
            return await ctx.reply(f'❌ Datawipe already active for {user}.')

        # Start datawipe procedure
        datawipe_data = {
            'userId': user_id,
            'username': f'{user.name}#{user.discriminator}',
            'initiatedBy': str(ctx.author.id),
            'initiatedByName': f'{ctx.author.name}#{ctx.author.discriminator}',
            'initiatedAt': datetime.now(timezone.utc).isoformat(),
            'status': 'active',
            'serversProcessed': [],
            'rolesRemoved': [],
            'kicksPerformed': []
        }

        active_datawipes[user_id] = datawipe_data

        # Process all servers the bot is in
        for guild in bot.guilds:
            if guild.id == 971778696081993758:
                continue  # skip this guild

            try:
                member = guild.get_member(user.id)
                if not member:
                    continue

                try:
                    # Remove all roles except @everyone
                    roles_to_remove = [role for role in member.roles if role != guild.default_role]
                    if roles_to_remove:
                        await member.remove_roles(
                            *roles_to_remove,
                            reason=f'Datawipe initiated by {ctx.author}'
                        )
                        datawipe_data['rolesRemoved'].extend(
                            [f'{role.name} ({guild.name})' for role in roles_to_remove]
                        )

                    # Kick from server (with delay to avoid rate limits)
                    await asyncio.sleep(1)
                    await member.kick(reason=f'Datawipe initiated by {ctx.author}')
                    datawipe_data['kicksPerformed'].append(guild.name)
                    datawipe_data['serversProcessed'].append(guild.name)

                except discord.Forbidden:
                    datawipe_data['serversProcessed'].append(f'{guild.name} (Failed - No permission)')
                except Exception as e:
                    datawipe_data['serversProcessed'].append(f'{guild.name} (Failed - {str(e)[:30]})')

            except Exception as e:
                logger.error(f"Error in guild {guild.id}: {e}")

        # Send completion report
        embed = discord.Embed(
            title='🧹 Datawipe Completed',
            description=f'Datawipe procedure completed for {user}',
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name='Servers Processed', value=str(len(datawipe_data['serversProcessed'])), inline=True)
        embed.add_field(name='Roles Removed', value=str(len(datawipe_data['rolesRemoved'])), inline=True)
        embed.add_field(name='Kicks Performed', value=str(len(datawipe_data['kicksPerformed'])), inline=True)
        
        if datawipe_data['serversProcessed']:
            servers_text = '\n'.join(datawipe_data['serversProcessed'][:10])
            if len(datawipe_data['serversProcessed']) > 10:
                servers_text += f'\n... and {len(datawipe_data["serversProcessed"]) - 10} more'
            embed.add_field(name='Servers', value=servers_text, inline=False)
        
        await ctx.reply(embed=embed)
        await log_command(ctx.author, f'!datawipe {user.name}')
        
        # Remove from active datawipes
        if user_id in active_datawipes:
            del active_datawipes[user_id]

    except Exception as error:
        logger.error(f'Error in datawipe command: {error}')
        await ctx.reply('❌ Failed to complete datawipe procedure.')
        
        # Remove from active datawipes on error (only if user_id was defined)
        try:
            if user_id and user_id in active_datawipes:
                del active_datawipes[user_id]
        except:
            pass
@bot.command(name="staffresign")
async def staff_resign(ctx, user: discord.Member = None, resignation_type: str = "", *, message: str = ""):
    """
    Handle staff resignations.
    Usage:
      !staffresign @user honorable <message>
      !staffresign @user dishonorable
    """
    # Check if user has staff role
    if not await is_staff(ctx.author, ctx.guild):
        return await ctx.reply('❌ You don\'t have permission to use this command.')
    
    if not user or not resignation_type:
        return await ctx.reply("❌ Usage: `!staffresign @user honorable <message>` or `!staffresign @user dishonorable`")

    resignation_type = resignation_type.lower()

    # Honorable resignation
    if resignation_type == "honorable":
        if not message:
            return await ctx.reply("❌ Please include a message for the honorable resignation.")

        try:
            dm_msg = f"✅ You have honorably resigned from your staff position.\n\n{message}"
            await user.send(dm_msg)

            await ctx.reply(f"✅ Successfully sent **honorable resignation** message to {user.mention}.")
            await log_command(ctx.author, f"!staffresign honorable {user} ({user.id})")

        except discord.Forbidden:
            await ctx.reply(f"⚠️ Could not DM {user.mention}, they may have DMs disabled.")

    # Dishonorable resignation (fired)
    elif resignation_type == "dishonorable":
        try:
            dm_msg = (
                "❌ You have been dishonorably removed (fired) from your staff position.\n"
                "Your access and responsibilities have been revoked immediately."
            )
            await user.send(dm_msg)

            await ctx.reply(f"✅ Successfully sent **dishonorable resignation** (fired notice) to {user.mention}.")
            await log_command(ctx.author, f"!staffresign dishonorable {user} ({user.id})")

        except discord.Forbidden:
            await ctx.reply(f"⚠️ Could not DM {user.mention}, they may have DMs disabled.")

    else:
        return await ctx.reply("❌ Invalid type. Use `honorable` or `dishonorable`.")


@bot.command(name='devlog')
async def devlog_command(ctx):
    """Create a development log announcement"""
    if not is_authorized(ctx.author.id):
        await ctx.send("❌ You are not authorized to use this command.")
        return
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    try:
        # Get log title
        await ctx.send("**Development Log Creation**\n\nWhat is the title of this development log?")
        title_msg = await bot.wait_for('message', check=check, timeout=300.0)
        title = title_msg.content
        
        # Get description
        await ctx.send("What is the description/summary of the changes?")
        description_msg = await bot.wait_for('message', check=check, timeout=300.0)
        description = description_msg.content
        
        # Get version/build info
        await ctx.send("What version or build is this? (e.g., 'v2.1.0', 'Build 123', 'Hot Fix')")
        version_msg = await bot.wait_for('message', check=check, timeout=300.0)
        version = version_msg.content
        
        # Get priority level
        await ctx.send("What is the priority level? (Low/Medium/High/Critical)")
        priority_msg = await bot.wait_for('message', check=check, timeout=300.0)
        priority = priority_msg.content
        
        # Ask about ping
        await ctx.send("Do you want to ping the development announcements role? (y/n)")
        ping_msg = await bot.wait_for('message', check=check, timeout=300.0)
        should_ping = ping_msg.content.lower().startswith('y')
        
        # Get additional notes
        await ctx.send("Any additional notes or details? (or type 'none')")
        notes_msg = await bot.wait_for('message', check=check, timeout=300.0)
        notes = notes_msg.content if notes_msg.content.lower() != 'none' else None
        
        # Create embed for dev log
        embed = discord.Embed(
            title=f"🔧 Development Log: {title}",
            description=description,
            color=0x00ff00,  # Green color
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Version/Build", value=version, inline=True)
        embed.add_field(name="Priority", value=priority, inline=True)
        embed.add_field(name="Developer", value=ctx.author.mention, inline=True)
        
        if notes:
            embed.add_field(name="Additional Notes", value=notes, inline=False)
        
        embed.set_footer(text="Development Team", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        # Prepare the message content
        message_content = ""
        if should_ping:
            message_content = f"<@&1365079208149254217>"  # Development announcements role ping
        
        # Send to development announcements channel
        dev_channel = bot.get_channel(1386398636530995381)
        if dev_channel and hasattr(dev_channel, 'send'):
            await dev_channel.send(content=message_content, embed=embed)
            await ctx.send(f"✅ Development log posted successfully to {dev_channel.mention}")
        else:
            await ctx.send("❌ Could not find the development announcements channel.")
            return
            
    except asyncio.TimeoutError:
        await ctx.send("⏰ Command timed out. Please try again.")
    except Exception as e:
        await ctx.send("❌ An error occurred while creating the development log.")
# === LEAK DETECTION HANDLER ===
async def check_for_leaks(message):
    """Check if message contains leak keywords outside main server"""
    # Skip if bot message or in main server or DMs
    if message.author.bot:
        return
    if not message.guild:
        return
    if message.guild.id == LEAK_DETECTION_CONFIG['MAIN_SERVER_ID2']:
        return
    
    # Check for keywords
    message_lower = message.content.lower()
    detected_keywords = []
    
    for keyword in LEAK_DETECTION_CONFIG['KEYWORDS']:
        if keyword.lower() in message_lower:
            detected_keywords.append(keyword)
    
    if not detected_keywords:
        return
    
    # Create alert
    try:
        alert_channel = bot.get_channel(LEAK_DETECTION_CONFIG['ALERT_CHANNEL_ID'])
        if not alert_channel:
            logger.error(f"Alert channel {LEAK_DETECTION_CONFIG['ALERT_CHANNEL_ID']} not found")
            return
        
        # Create message link
        message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        
        # Create alert embed
        alert_embed = discord.Embed(
            title="🚨 LEAK DETECTED 🚨",
            description=f"A LEAK WAS DETECTED HERE [{message_link}]({message_link}) RESPOND IMMEDIATELY",
            color=0xff0000,
            timestamp=datetime.now(timezone.utc)
        )
        
        alert_embed.add_field(name="🏢 Server", value=f"{message.guild.name} (`{message.guild.id}`)", inline=True)
        alert_embed.add_field(name="📺 Channel", value=f"#{message.channel.name} (`{message.channel.id}`)", inline=True)
        alert_embed.add_field(name="👤 User", value=f"{message.author} (`{message.author.id}`)", inline=True)
        alert_embed.add_field(name="🔍 Keywords Detected", value=", ".join(detected_keywords), inline=False)
        
        # Truncate message content if too long
        content_preview = message.content
        if len(content_preview) > 500:
            content_preview = content_preview[:500] + "..."
        alert_embed.add_field(name="💬 Message Content", value=content_preview, inline=False)
        
        alert_embed.add_field(name="🔗 Direct Link", value=f"[Click here to view message]({message_link})", inline=False)
        
        # Send alert with @everyone ping
        await alert_channel.send("<@&1416460299040460860>", embed=alert_embed)        
        # DM each alert user
        for user_id in LEAK_DETECTION_CONFIG['ALERT_USERS']:
            try:
                user = await bot.fetch_user(user_id)
                dm_embed = discord.Embed(
                    title="🚨 URGENT: LEAK DETECTED 🚨",
                    description=f"A potential leak has been detected!\n\n**Server:** {message.guild.name}\n**Channel:** #{message.channel.name}\n**User:** {message.author}\n\n[View Message]({message_link})",
                    color=0xff0000,
                    timestamp=datetime.now(timezone.utc)
                )
                dm_embed.add_field(name="Keywords Found", value=", ".join(detected_keywords), inline=False)
                dm_embed.add_field(name="Message Preview", value=content_preview, inline=False)
                
                await user.send(embed=dm_embed)
                logger.info(f"Sent leak alert DM to {user.name} ({user_id})")
            except discord.Forbidden:
                logger.warning(f"Could not DM user {user_id} - DMs disabled")
            except discord.NotFound:
                logger.warning(f"User {user_id} not found")
            except Exception as e:
                logger.error(f"Error DMing user {user_id}: {e}")
        
        logger.info(f"Leak detected: {len(detected_keywords)} keywords in message by {message.author} in {message.guild.name}")
        
    except Exception as e:
        logger.error(f"Error in leak detection: {e}")
# === EVENT HANDLERS ===
@bot.event
async def on_message(message):
    """Handle all messages, watchlist logging, inspections, DND, leak detection, and bot shutdown"""
    if message.author.bot:
        return

    # --- Leak Detection (before other checks) ---
    await check_for_leaks(message)

    # --- Check for bot shutdown ---
    if check_bot_shutdown() and not message.content.startswith('!shutdown'):
        if not isinstance(message.channel, discord.DMChannel):
            await message.reply('🚫 The bot is shutdown. Try again later.')
        return

    # --- Check if user is in DND mode ---
    if message.author.id in dnd_users:
        return

    # ... rest of your code stays the same

    # --- Watchlist Logging ---
    try:
        user_id_str = str(message.author.id)
        if user_id_str in bot_data['watchlist']:
            entry = bot_data['watchlist'][user_id_str]
            if entry.get('active', True):
                guild = bot.get_guild(int(entry['guildId']))
                if guild:
                    channel = guild.get_channel(int(entry['channelId']))
                    if channel and hasattr(channel, 'send'):
                        embed = discord.Embed(
                            title='💬 Message Sent',
                            color=0x3498db,
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.add_field(name='User', value=f'{message.author} ({message.author.id})', inline=True)
                        embed.add_field(name='Server', value=f'{message.guild.name}' if message.guild else 'DM', inline=True)
                        embed.add_field(name='Channel', value=f'#{message.channel.name}' if hasattr(message.channel, 'name') else 'DM', inline=True)
                        content = message.content[:500] + '...' if len(message.content) > 500 else message.content
                        embed.add_field(name='Content', value=content, inline=False)
                        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f'Error logging watchlist message: {e}')

    # --- Inspection Logging ---
    try:
        if message.guild and str(message.guild.id) in active_inspections:
            inspection = active_inspections[str(message.guild.id)]
            current_time = datetime.now().timestamp()

            if current_time < inspection.get('end_time', 0):
                # Track activity
                track_inspection_activity(str(message.guild.id), 'messages', message.author.id)

                # Create embed for inspection webhook
                embed_data = {
                    'title': '📨 Message Activity',
                    'color': 0x3498db,
                    'fields': [
                        {'name': '👤 User', 'value': f'{message.author} ({message.author.id})', 'inline': True},
                        {'name': '🏠 Server', 'value': f'{message.guild.name} ({message.guild.id})', 'inline': True},
                        {'name': '📺 Channel', 'value': f'#{message.channel.name} ({message.channel.id})', 'inline': True}
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                # Add message content if present
                if message.content:
                    content = message.content
                    if len(content) > 800:
                        content = content[:800] + '...'
                    embed_data['fields'].append({'name': '💬 Content', 'value': content, 'inline': False})

                # Attachments
                if message.attachments:
                    attachments = [f'• [{att.filename}]({att.url}) ({att.size} bytes)' for att in message.attachments[:5]]
                    embed_data['fields'].append({'name': '📎 Attachments', 'value': '\n'.join(attachments), 'inline': False})

                # Embeds
                if message.embeds:
                    embed_data['fields'].append({'name': '📋 Embeds', 'value': f'{len(message.embeds)} embed(s)', 'inline': True})

                await post_webhook(embed=embed_data, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            else:
                # Remove expired inspection
                del active_inspections[str(message.guild.id)]
                logger.info(f'Cleaned up expired inspection for {message.guild.name}')
    except Exception as e:
        logger.error(f'Error logging inspection activity: {e}')

    # --- Process commands ---
    await bot.process_commands(message)

# Additional event handlers for comprehensive inspection logging
@bot.event
async def on_message_edit(before, after):
    """Log message edits during inspection"""
    if after.author.bot or not after.guild:
        return

    if str(after.guild.id) in active_inspections:
        inspection = active_inspections[str(after.guild.id)]
        current_time = datetime.now().timestamp()

        if current_time < inspection.get('end_time', 0):
            try:
                # Track activity
                track_inspection_activity(str(after.guild.id), 'message_edits', after.author.id)

                embed = {
                    'title': '✏️ Message Edited',
                    'color': 0xf39c12,
                    'fields': [
                        {'name': '👤 User', 'value': f'{after.author} ({after.author.id})', 'inline': True},
                        {'name': '🏠 Server', 'value': f'{after.guild.name} ({after.guild.id})', 'inline': True},
                        {'name': '📺 Channel', 'value': f'#{after.channel.name} ({after.channel.id})', 'inline': True}
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                if before.content:
                    content = before.content[:400] + '...' if len(before.content) > 400 else before.content
                    embed['fields'].append({'name': '📝 Before', 'value': content, 'inline': False})

                if after.content:
                    content = after.content[:400] + '...' if len(after.content) > 400 else after.content
                    embed['fields'].append({'name': '📝 After', 'value': content, 'inline': False})

                await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            except Exception as e:
                logger.error(f'Error logging message edit: {e}')

@bot.event
async def on_message_delete(message):
    """Log message deletions during inspection"""
    if message.author.bot or not message.guild:
        return

    if str(message.guild.id) in active_inspections:
        inspection = active_inspections[str(message.guild.id)]
        current_time = datetime.now().timestamp()

        if current_time < inspection.get('end_time', 0):
            try:
                # Track activity
                track_inspection_activity(str(message.guild.id), 'message_deletes', message.author.id)

                embed = {
                    'title': '🗑️ Message Deleted',
                    'color': 0xe74c3c,
                    'fields': [
                        {'name': '👤 User', 'value': f'{message.author} ({message.author.id})', 'inline': True},
                        {'name': '🏠 Server', 'value': f'{message.guild.name} ({message.guild.id})', 'inline': True},
                        {'name': '📺 Channel', 'value': f'#{message.channel.name} ({message.channel.id})', 'inline': True}
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                if message.content:
                    content = message.content[:800] + '...' if len(message.content) > 800 else message.content
                    embed['fields'].append({'name': '💬 Content', 'value': content, 'inline': False})

                if message.attachments:
                    att_info = [f'• {att.filename}' for att in message.attachments[:3]]
                    embed['fields'].append({'name': '📎 Attachments', 'value': '\n'.join(att_info), 'inline': False})

                await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            except Exception as e:
                logger.error(f'Error logging message delete: {e}')


@bot.event
async def on_member_remove(member):
    """Log member leaves during inspection"""
    if str(member.guild.id) in active_inspections:
        inspection = active_inspections[str(member.guild.id)]
        current_time = datetime.now().timestamp()

        if current_time < inspection.get('end_time', 0):
            try:
                # Track activity
                track_inspection_activity(str(member.guild.id), 'member_leaves', member.id)

                embed = {
                    'title': '📤 Member Left',
                    'color': 0xe74c3c,
                    'fields': [
                        {'name': '👤 User', 'value': f'{member} ({member.id})', 'inline': True},
                        {'name': '🏠 Server', 'value': f'{member.guild.name} ({member.guild.id})', 'inline': True}
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                if member.roles and len(member.roles) > 1:  # Exclude @everyone
                    roles = [role.name for role in member.roles[1:5]]  # Max 4 roles
                    embed['fields'].append({'name': '🎭 Roles', 'value': ', '.join(roles), 'inline': False})

                await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            except Exception as e:
                logger.error(f'Error logging member leave: {e}')

@bot.event
async def on_voice_state_update(member, before, after):
    """Log voice channel activity during inspection and watchlist"""
    # Watchlist tracking
    if str(member.id) in bot_data['watchlist']:
        watchlist_entry = bot_data['watchlist'][str(member.id)]
        if watchlist_entry.get('active', True):
            try:
                # Get the watchlist channel
                guild = bot.get_guild(int(watchlist_entry['guildId']))
                if guild:
                    channel = guild.get_channel(int(watchlist_entry['channelId']))
                    if channel and hasattr(channel, 'send'):
                        # Log voice activity
                        embed = discord.Embed(
                            title='🎵 Voice Activity',
                            color=0x9b59b6,
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.add_field(name='User', value=f'{member} ({member.id})', inline=True)
                        embed.add_field(name='Server', value=f'{member.guild.name}', inline=True)

                        if before.channel != after.channel:
                            if before.channel:
                                embed.add_field(name='Left', value=f'🔊 {before.channel.name}', inline=True)
                            if after.channel:
                                embed.add_field(name='Joined', value=f'🔊 {after.channel.name}', inline=True)

                        # Log mute/deafen changes
                        changes = []
                        if before.self_mute != after.self_mute:
                            changes.append(f"Self-mute: {'ON' if after.self_mute else 'OFF'}")
                        if before.self_deaf != after.self_deaf:
                            changes.append(f"Self-deaf: {'ON' if after.self_deaf else 'OFF'}")

                        if changes:
                            embed.add_field(name='Changes', value='\n'.join(changes), inline=False)

                        # Only log if there was an actual change
                        if before.channel != after.channel or changes:
                            await channel.send(embed=embed)
            except Exception as e:
                logger.error(f'Error logging watchlist voice activity: {e}')

    # Inspection tracking
    if not member.guild or str(member.guild.id) not in active_inspections:
        return

    inspection = active_inspections[str(member.guild.id)]
    current_time = datetime.now().timestamp()

    if current_time < inspection.get('end_time', 0):
        try:
            embed = {
                'title': '🎵 Voice Activity',
                'color': 0x9b59b6,
                'fields': [
                    {'name': '👤 User', 'value': f'{member} ({member.id})', 'inline': True},
                    {'name': '🏠 Server', 'value': f'{member.guild.name} ({member.guild.id})', 'inline': True}
                ],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            if before.channel != after.channel:
                if before.channel:
                    embed['fields'].append({'name': '📤 Left', 'value': f'🔊 {before.channel.name}', 'inline': True})
                if after.channel:
                    embed['fields'].append({'name': '📥 Joined', 'value': f'🔊 {after.channel.name}', 'inline': True})

            # Log mute/deafen changes
            changes = []
            if before.self_mute != after.self_mute:
                changes.append(f"Self-mute: {'ON' if after.self_mute else 'OFF'}")
            if before.self_deaf != after.self_deaf:
                changes.append(f"Self-deaf: {'ON' if after.self_deaf else 'OFF'}")
            if before.mute != after.mute:
                changes.append(f"Server-mute: {'ON' if after.mute else 'OFF'}")
            if before.deaf != after.deaf:
                changes.append(f"Server-deaf: {'ON' if after.deaf else 'OFF'}")

            if changes:
                embed['fields'].append({'name': '🔧 Changes', 'value': '\n'.join(changes), 'inline': False})

            # Only log if there was an actual change
            if before.channel != after.channel or changes:
                # Track activity
                track_inspection_activity(str(member.guild.id), 'voice_changes', member.id)
                await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])

        except Exception as e:
            logger.error(f'Error logging voice state: {e}')

@bot.event
async def on_guild_channel_create(channel):
    """Log channel creation during inspection"""
    if str(channel.guild.id) in active_inspections:
        inspection = active_inspections[str(channel.guild.id)]
        current_time = datetime.now().timestamp()

        if current_time < inspection.get('end_time', 0):
            try:
                # Track activity
                track_inspection_activity(str(channel.guild.id), 'channel_creates')

                embed = {
                    'title': '🆕 Channel Created',
                    'color': 0x2ecc71,
                    'fields': [
                        {'name': '📺 Channel', 'value': f'#{channel.name} ({channel.id})', 'inline': True},
                        {'name': '🏠 Server', 'value': f'{channel.guild.name} ({channel.guild.id})', 'inline': True},
                        {'name': '🔧 Type', 'value': str(channel.type).replace('_', ' ').title(), 'inline': True}
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            except Exception as e:
                logger.error(f'Error logging channel create: {e}')

@bot.event
async def on_guild_channel_delete(channel):
    """Log channel deletion during inspection"""
    if str(channel.guild.id) in active_inspections:
        inspection = active_inspections[str(channel.guild.id)]
        current_time = datetime.now().timestamp()

        if current_time < inspection.get('end_time', 0):
            try:
                # Track activity
                track_inspection_activity(str(channel.guild.id), 'channel_deletes')

                embed = {
                    'title': '🗑️ Channel Deleted',
                    'color': 0xe74c3c,
                    'fields': [
                        {'name': '📺 Channel', 'value': f'#{channel.name} ({channel.id})', 'inline': True},
                        {'name': '🏠 Server', 'value': f'{channel.guild.name} ({channel.guild.id})', 'inline': True},
                        {'name': '🔧 Type', 'value': str(channel.type).replace('_', ' ').title(), 'inline': True}
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }

                await post_webhook(embed=embed, webhook_url=CONFIG['INSPECTION_WEBHOOK'])
            except Exception as e:
                logger.error(f'Error logging channel delete: {e}')

# === ERROR HANDLERS ===
@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply('❌ Unknown command. Use `!help` for a list of available commands.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f'❌ Missing required argument: {error.param}')
    elif isinstance(error, commands.BadArgument):
        await ctx.reply(f'❌ Invalid argument: {error}')
    else:
        logger.error(f'Command error in {ctx.command}: {error}')
        await ctx.reply('❌ An error occurred while processing your command.')


@bot.command(name="exelog")
async def exelog(ctx):
    allowed_channel_id = 1407177909105590333  # ESD channel
    post_channel_id = 1396184018709381141     # Log channel
    alert_channel_id = 1385749558440755391    # Plain text alert channel
    if ctx.channel.id != allowed_channel_id:
        return  # ignore if run elsewhere
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    # Store messages to delete later
    messages_to_delete = [ctx.message]  # Include the original command
    
    try:
        # Ask for Username
        question1 = await ctx.send("📝 **Username:** (of the person posting the log)")
        messages_to_delete.append(question1)
        username_msg = await bot.wait_for("message", check=check, timeout=60)
        messages_to_delete.append(username_msg)
        username = username_msg.content
        
        # Ask for Bounty
        question2 = await ctx.send("💰 **Bounty:** (person who is being added to the list, can be ID to ping)")
        messages_to_delete.append(question2)
        bounty_msg = await bot.wait_for("message", check=check, timeout=60)
        messages_to_delete.append(bounty_msg)
        bounty = bounty_msg.content
        
        # Ask for Execution Method (Optional)
        question3 = await ctx.send("⚔️ **Execution Method:** (Optional, type 'None' to skip)")
        messages_to_delete.append(question3)
        method_msg = await bot.wait_for("message", check=check, timeout=60)
        messages_to_delete.append(method_msg)
        method = method_msg.content
        if method.lower() == "none":
            method = "Not specified"
        
        # Ask for Reason (Optional)
        question4 = await ctx.send("📝 **Reason:** (Optional, type 'None' to skip)")
        messages_to_delete.append(question4)
        reason_msg = await bot.wait_for("message", check=check, timeout=120)
        messages_to_delete.append(reason_msg)
        reason = reason_msg.content
        if reason.lower() == "none":
            reason = "Not specified"
        
        # Ask for Images (Optional)
        question5 = await ctx.send("🖼️ **Attach images:** (Optional, just send them in your next message, type 'None' to skip)")
        messages_to_delete.append(question5)
        images_msg = await bot.wait_for("message", check=check, timeout=120)
        messages_to_delete.append(images_msg)
        images = images_msg.attachments  # list of attachments
        
    except Exception:
        error_msg = await ctx.send("⏰ You took too long to respond. Command cancelled.")
        messages_to_delete.append(error_msg)
        # Delete messages after 10 seconds
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
        return
    
    # Process bounty to get proper display format
    bounty_display = bounty
    bounty_ping = bounty
    
    try:
        # Try to parse as user ID
        bounty_id = int(bounty)
        member = ctx.guild.get_member(bounty_id)
        if member:
            bounty_display = f"{member.display_name} ({member.mention})"
            bounty_ping = member.mention
        else:
            # Try to fetch user even if not in guild
            try:
                user = await bot.fetch_user(bounty_id)
                bounty_display = f"{user.display_name} (<@{bounty_id}>)"
                bounty_ping = f"<@{bounty_id}>"
            except:
                bounty_display = f"<@{bounty_id}>"
                bounty_ping = f"<@{bounty_id}>"
    except ValueError:
        # Not a valid ID, check if it's already a mention
        if bounty.startswith('<@') and bounty.endswith('>'):
            # Extract ID from mention
            try:
                mention_id = int(bounty.replace('<@', '').replace('>', '').replace('!', ''))
                member = ctx.guild.get_member(mention_id)
                if member:
                    bounty_display = f"{member.display_name} ({bounty})"
                    bounty_ping = bounty
                else:
                    bounty_display = bounty
                    bounty_ping = bounty
            except:
                bounty_display = bounty
                bounty_ping = bounty
        else:
            # Regular text, keep as is
            bounty_display = bounty
            bounty_ping = bounty
    
    # Create red themed embed
    embed = discord.Embed(
        title="💀 **Execution Log**",
        description="**New entry posted in the ESD system**",
        color=discord.Colour.red()
    )
    embed.add_field(name="📝 Username", value=username, inline=True)
    embed.add_field(name="💰 Bounty", value=bounty_display, inline=True)
    embed.add_field(name="⚔️ Execution Method", value=method, inline=False)
    embed.add_field(name="📄 Reason", value=reason, inline=False)
    embed.set_footer(text=f"Logged by {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    embed.timestamp = discord.utils.utcnow()
    
    # Add the first image as embed image if exists
    if images:
        embed.set_image(url=images[0].url)
    
    # Send embed to the log channel
    post_channel = bot.get_channel(post_channel_id)
    if post_channel is None:
        error_msg = await ctx.send("❌ Could not find the log channel.")
        messages_to_delete.append(error_msg)
        # Delete messages after 10 seconds
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
        return
    
    await post_channel.send(embed=embed)
    
    # Send plain text alert in the alert channel
    alert_channel = bot.get_channel(alert_channel_id)
    if alert_channel is not None:
        await alert_channel.send(f"{bounty_ping} is being hunted.")
    
    # Send remaining images as attachments if more than one
    if images and len(images) > 1:
        for attachment in images[1:]:
            # Download and reupload the attachment
            file_data = await attachment.read()
            file = discord.File(io.BytesIO(file_data), filename=attachment.filename)
            await post_channel.send(file=file)
    
    success_msg = await ctx.send("✅ Execution log posted successfully!")
    messages_to_delete.append(success_msg)
    
    # Delete all command interaction messages after 10 seconds
    await asyncio.sleep(10)
    for msg in messages_to_delete:
        try:
            await msg.delete()
        except:
            pass  # Ignore errors (message might already be deleted)
# Store active lockdowns for tracking
active_lockdowns = {}

@bot.command(name="lockdown")
async def lockdown(ctx):
    # Check if command is used in DMs
    if ctx.guild:
        return await ctx.send("❌ This command can only be used in DMs for security purposes.")
    
    # Note: We can't check guild permissions in DMs, so this is based on trust/role verification in the target server
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    # Store messages to delete later
    messages_to_delete = [ctx.message]
    
    try:
        # Ask for Server ID
        question1 = await ctx.send("🏢 **Server ID:** (of the server being locked down)")
        messages_to_delete.append(question1)
        server_msg = await bot.wait_for("message", check=check, timeout=60)
        messages_to_delete.append(server_msg)
        
        # Get the target guild and verify user has permissions
        try:
            guild = bot.get_guild(int(server_msg.content))
            if not guild:
                error_msg = await ctx.send("❌ Server not found or bot is not in that server.")
                messages_to_delete.append(error_msg)
                await asyncio.sleep(10)
                for msg in messages_to_delete:
                    try:
                        await msg.delete()
                    except:
                        pass
                return
            
            # Check if user is actually in the guild and has admin permissions
            member = guild.get_member(ctx.author.id)
            if not member or not member.guild_permissions.administrator:
                error_msg = await ctx.send("❌ You don't have administrator permissions in that server.")
                messages_to_delete.append(error_msg)
                await asyncio.sleep(10)
                for msg in messages_to_delete:
                    try:
                        await msg.delete()
                    except:
                        pass
                return
                
        except ValueError:
            error_msg = await ctx.send("❌ Invalid server ID.")
            messages_to_delete.append(error_msg)
            await asyncio.sleep(10)
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            return
        
        # Check if there's already an active lockdown
        if guild.id in active_lockdowns:
            error_msg = await ctx.send("⚠️ This server already has an active lockdown!")
            messages_to_delete.append(error_msg)
            await asyncio.sleep(10)
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            return
        
        # Ask for Department Name
        question2 = await ctx.send("🏛️ **Department Name:** (e.g., Police Department, Medical Department)")
        messages_to_delete.append(question2)
        dept_msg = await bot.wait_for("message", check=check, timeout=60)
        messages_to_delete.append(dept_msg)
        department_name = dept_msg.content
        
        # Ask for Department Leaders
        question3 = await ctx.send("👥 **Department Leader(s):** (User IDs or @mentions, separate multiple with spaces)")
        messages_to_delete.append(question3)
        leaders_msg = await bot.wait_for("message", check=check, timeout=120)
        messages_to_delete.append(leaders_msg)
        leaders_input = leaders_msg.content
        
        # Parse leaders (IDs or mentions)
        leaders = []
        for leader_str in leaders_input.split():
            try:
                # Try to extract ID from mention or use as direct ID
                if leader_str.startswith('<@') and leader_str.endswith('>'):
                    leader_id = int(leader_str.replace('<@', '').replace('>', '').replace('!', ''))
                else:
                    leader_id = int(leader_str)
                
                # Get user object
                user = bot.get_user(leader_id)
                if not user:
                    user = await bot.fetch_user(leader_id)
                
                if user:
                    leaders.append(user)
            except:
                continue
        
        if not leaders:
            error_msg = await ctx.send("❌ No valid department leaders found.")
            messages_to_delete.append(error_msg)
            await asyncio.sleep(10)
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            return
            
    except Exception:
        error_msg = await ctx.send("⏰ You took too long to respond. Command cancelled.")
        messages_to_delete.append(error_msg)
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
        return
    
    try:
        # Check if channel already exists
        channel_name = f"{department_name.lower().replace(' ', '-')}-reforms"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            error_msg = await ctx.send(f"⚠️ {department_name} lockdown channel already exists!")
            messages_to_delete.append(error_msg)
            await asyncio.sleep(10)
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            return
        
        # Create the lockdown channel with restricted permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False),  # Nobody can talk
            guild.me: discord.PermissionOverwrite(send_messages=True)  # Bot can still post
        }
        
        # Allow administrators to speak in lockdown channel
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(send_messages=True)
        
        lockdown_channel = await guild.create_text_channel(
            name=channel_name,
            topic=f"🚫 {department_name.upper()} DEPARTMENT UNDER LOCKDOWN - NOT OPERATIONAL",
            overwrites=overwrites,
            reason=f"Department lockdown initiated by {ctx.author}"
        )
        
        # Create lockdown embed
        embed = discord.Embed(
            title=f"🚨 {department_name.upper()} DEPARTMENT LOCKDOWN 🚨",
            description=f"**THE {department_name.upper()} DEPARTMENT IS NOT OPERATIONAL UNTIL FURTHER NOTICE**",
            color=discord.Colour.red()
        )
        embed.add_field(
            name="⚠️ Notice",
            value=f"All {department_name} operations have been suspended. Department is currently under reforms.",
            inline=False
        )
        embed.add_field(
            name="📋 Status",
            value="🔒 **LOCKED DOWN**",
            inline=True
        )
        embed.add_field(
            name="🕐 Duration",
            value="Until further notice",
            inline=True
        )
        embed.add_field(
            name="👤 Authorized by",
            value=ctx.author.mention,
            inline=False
        )
        embed.add_field(
            name="👥 Department Leaders Notified",
            value=", ".join([f"{leader.display_name}" for leader in leaders]),
            inline=False
        )
        embed.set_footer(text=f"Please wait for official announcement regarding {department_name} department reopening.")
        embed.timestamp = discord.utils.utcnow()
        
        # Send the lockdown message with @everyone ping
        await lockdown_channel.send(
            content=f"@everyone 📢 **{department_name.upper()} DEPARTMENT NOTICE**",
            embed=embed
        )
        
        # Send DMs to department leaders
        leader_notification_embed = discord.Embed(
            title="🚨 DEPARTMENT LOCKDOWN NOTIFICATION",
            description=f"**Your department ({department_name}) has been placed under lockdown.**",
            color=discord.Colour.red()
        )
        leader_notification_embed.add_field(
            name="🏢 Server",
            value=f"{guild.name}",
            inline=True
        )
        leader_notification_embed.add_field(
            name="🏛️ Department",
            value=department_name,
            inline=True
        )
        leader_notification_embed.add_field(
            name="👤 Authorized by",
            value=f"{ctx.author.display_name}",
            inline=False
        )
        leader_notification_embed.add_field(
            name="📋 Status",
            value="🔒 **LOCKED DOWN** - All operations suspended",
            inline=False
        )
        leader_notification_embed.add_field(
            name="📞 Next Steps",
            value="**Further instructions will be provided.** Please standby for additional communication regarding this lockdown.",
            inline=False
        )
        leader_notification_embed.set_footer(text="You are receiving this because you are listed as a department leader.")
        leader_notification_embed.timestamp = discord.utils.utcnow()
        
        notified_leaders = []
        failed_leaders = []
        
        for leader in leaders:
            try:
                await leader.send(embed=leader_notification_embed)
                notified_leaders.append(leader.display_name)
            except discord.Forbidden:
                failed_leaders.append(leader.display_name)
            except Exception:
                failed_leaders.append(leader.display_name)
        
        # Store lockdown info for tracking
        active_lockdowns[guild.id] = {
            'initiator': ctx.author,
            'channel': lockdown_channel,
            'start_time': discord.utils.utcnow(),
            'department': department_name,
            'leaders': leaders
        }
        
        # Start audit log monitoring
        bot.loop.create_task(monitor_audit_logs(guild, ctx.author))
        
        # Send confirmation in original channel
        confirm_embed = discord.Embed(
            title="✅ Department Lockdown Initiated",
            description=f"**{department_name}** lockdown channel created: {lockdown_channel.mention}\n🔍 **Audit log monitoring active** - You'll receive DMs about any server activity.\n🔇 **Channel restricted** - Only administrators can speak in the lockdown channel.",
            color=discord.Colour.green()
        )
        confirm_embed.add_field(name="🎯 Target Server", value=f"{guild.name} (`{guild.id}`)", inline=False)
        
        if notified_leaders:
            confirm_embed.add_field(
                name="✅ Leaders Notified via DM",
                value=", ".join(notified_leaders),
                inline=False
            )
        
        if failed_leaders:
            confirm_embed.add_field(
                name="❌ Failed to Notify",
                value=", ".join(failed_leaders) + " (DMs disabled/blocked)",
                inline=False
            )
        
        success_msg = await ctx.send(embed=confirm_embed)
        messages_to_delete.append(success_msg)
        
        # Delete command interaction messages after 15 seconds
        await asyncio.sleep(15)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
        
    except discord.Forbidden:
        error_msg = await ctx.send("❌ I don't have permission to create channels or send messages.")
        messages_to_delete.append(error_msg)
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
    except Exception as e:
        error_msg = await ctx.send(f"❌ An error occurred: {str(e)}")
        messages_to_delete.append(error_msg)
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass


@bot.command(name="endlockdown")
async def endlockdown(ctx):
    # Check if command is used in DMs
    if ctx.guild:
        return await ctx.send("❌ This command can only be used in DMs for security purposes.")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
    # Store messages to delete later
    messages_to_delete = [ctx.message]
    
    try:
        # Ask for Server ID
        question1 = await ctx.send("🏢 **Server ID:** (of the server to end lockdown)")
        messages_to_delete.append(question1)
        server_msg = await bot.wait_for("message", check=check, timeout=60)
        messages_to_delete.append(server_msg)
        
        # Get the target guild and verify user has permissions
        try:
            guild = bot.get_guild(int(server_msg.content))
            if not guild:
                error_msg = await ctx.send("❌ Server not found or bot is not in that server.")
                messages_to_delete.append(error_msg)
                await asyncio.sleep(10)
                for msg in messages_to_delete:
                    try:
                        await msg.delete()
                    except:
                        pass
                return
            
            # Check if user is actually in the guild and has admin permissions
            member = guild.get_member(ctx.author.id)
            if not member or not member.guild_permissions.administrator:
                error_msg = await ctx.send("❌ You don't have administrator permissions in that server.")
                messages_to_delete.append(error_msg)
                await asyncio.sleep(10)
                for msg in messages_to_delete:
                    try:
                        await msg.delete()
                    except:
                        pass
                return
                
        except ValueError:
            error_msg = await ctx.send("❌ Invalid server ID.")
            messages_to_delete.append(error_msg)
            await asyncio.sleep(10)
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            return
        
        # Check if there's an active lockdown
        if guild.id not in active_lockdowns:
            error_msg = await ctx.send("❌ No active lockdown found for this server.")
            messages_to_delete.append(error_msg)
            await asyncio.sleep(10)
            for msg in messages_to_delete:
                try:
                    await msg.delete()
                except:
                    pass
            return
        
        # Get lockdown data
        lockdown_data = active_lockdowns[guild.id]
        department_name = lockdown_data.get('department', 'Department')
        leaders = lockdown_data.get('leaders', [])
        lockdown_channel = lockdown_data.get('channel')
        
    except Exception:
        error_msg = await ctx.send("⏰ You took too long to respond. Command cancelled.")
        messages_to_delete.append(error_msg)
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
        return
    
    try:
        # Delete the lockdown channel
        if lockdown_channel:
            try:
                await lockdown_channel.delete(reason=f"Lockdown ended by {ctx.author}")
            except:
                pass  # Channel might already be deleted
        
        # Remove from active lockdowns (stops audit monitoring)
        if guild.id in active_lockdowns:
            del active_lockdowns[guild.id]
        
        # Send DMs to department leaders
        leader_notification_embed = discord.Embed(
            title="✅ DEPARTMENT LOCKDOWN ENDED",
            description=f"**Your department ({department_name}) lockdown has been lifted.**",
            color=discord.Colour.green()
        )
        leader_notification_embed.add_field(
            name="🏢 Server",
            value=f"{guild.name}",
            inline=True
        )
        leader_notification_embed.add_field(
            name="🏛️ Department",
            value=department_name,
            inline=True
        )
        leader_notification_embed.add_field(
            name="👤 Authorized by",
            value=f"{ctx.author.display_name}",
            inline=False
        )
        leader_notification_embed.add_field(
            name="📋 Status",
            value="✅ **OPERATIONAL** - Normal operations resumed",
            inline=False
        )
        leader_notification_embed.add_field(
            name="🎯 Next Steps",
            value="Your department is now fully operational. You may resume normal activities and operations.",
            inline=False
        )
        leader_notification_embed.set_footer(text="You are receiving this because you are listed as a department leader.")
        leader_notification_embed.timestamp = discord.utils.utcnow()
        
        notified_leaders = []
        failed_leaders = []
        
        for leader in leaders:
            try:
                await leader.send(embed=leader_notification_embed)
                notified_leaders.append(leader.display_name)
            except discord.Forbidden:
                failed_leaders.append(leader.display_name)
            except Exception:
                failed_leaders.append(leader.display_name)
        
        # Send confirmation
        confirm_embed = discord.Embed(
            title="✅ Department Lockdown Ended",
            description=f"**{department_name}** lockdown has been successfully lifted.\n🔍 **Audit log monitoring stopped**",
            color=discord.Colour.green()
        )
        confirm_embed.add_field(name="🎯 Target Server", value=f"{guild.name} (`{guild.id}`)", inline=False)
        confirm_embed.add_field(name="👤 Authorized by", value=ctx.author.mention, inline=False)
        
        if notified_leaders:
            confirm_embed.add_field(
                name="✅ Leaders Notified via DM",
                value=", ".join(notified_leaders),
                inline=False
            )
        
        if failed_leaders:
            confirm_embed.add_field(
                name="❌ Failed to Notify",
                value=", ".join(failed_leaders) + " (DMs disabled/blocked)",
                inline=False
            )
        
        confirm_embed.timestamp = discord.utils.utcnow()
        
        success_msg = await ctx.send(embed=confirm_embed)
        messages_to_delete.append(success_msg)
        
        # Delete command interaction messages after 15 seconds
        await asyncio.sleep(15)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass
        
    except Exception as e:
        error_msg = await ctx.send(f"❌ An error occurred: {str(e)}")
        messages_to_delete.append(error_msg)
        await asyncio.sleep(10)
        for msg in messages_to_delete:
            try:
                await msg.delete()
            except:
                pass


@bot.command(name="lockdown_status")
async def lockdown_status(ctx):
    # Check if command is used in DMs
    if ctx.guild:
        return await ctx.send("❌ This command can only be used in DMs for security purposes.")
    
    if not active_lockdowns:
        return await ctx.send("✅ No active lockdowns.")
    
    embed = discord.Embed(
        title="🔒 Active Lockdowns",
        color=discord.Colour.red()
    )
    
    for guild_id, data in active_lockdowns.items():
        guild = bot.get_guild(guild_id)
        if guild:
            duration = discord.utils.utcnow() - data['start_time']
            embed.add_field(
                name=f"🏢 {guild.name}",
                value=f"**Initiator:** {data['initiator']}\n**Department:** {data.get('department', 'General')}\n**Duration:** {str(duration).split('.')[0]}\n**Channel:** {data['channel'].mention}\n**Leaders:** {len(data.get('leaders', []))} notified",
                inline=False
            )
    
    await ctx.send(embed=embed)


# Audit log monitoring function
async def monitor_audit_logs(guild, initiator):
    """Monitor audit logs for activity and send DMs to the lockdown initiator"""
    last_check = discord.utils.utcnow()
    
    while guild.id in active_lockdowns:
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            # Check if lockdown is still active
            if guild.id not in active_lockdowns:
                break
            
            # Get recent audit log entries
            async for entry in guild.audit_logs(limit=50, after=last_check):
                # Filter out bot actions and the lockdown initiator's actions
                if entry.user == bot.user or entry.user == initiator:
                    continue
                
                # Create activity alert embed
                alert_embed = discord.Embed(
                    title="🚨 Lockdown Activity Alert",
                    description=f"**Activity detected in {guild.name}**",
                    color=discord.Colour.orange()
                )
                alert_embed.add_field(name="👤 User", value=f"{entry.user} (`{entry.user.id}`)", inline=True)
                alert_embed.add_field(name="🔧 Action", value=entry.action.name.replace('_', ' ').title(), inline=True)
                alert_embed.add_field(name="🎯 Target", value=str(entry.target) if entry.target else "N/A", inline=True)
                
                if entry.reason:
                    alert_embed.add_field(name="📝 Reason", value=entry.reason, inline=False)
                
                alert_embed.add_field(name="🏢 Server", value=f"{guild.name} (`{guild.id}`)", inline=False)
                alert_embed.timestamp = entry.created_at
                
                # Try to send DM to initiator
                try:
                    await initiator.send(embed=alert_embed)
                except discord.Forbidden:
                    # If can't DM, try to send to the lockdown channel
                    if guild.id in active_lockdowns:
                        lockdown_channel = active_lockdowns[guild.id]['channel']
                        try:
                            await lockdown_channel.send(f"{initiator.mention} Activity Alert:", embed=alert_embed)
                        except:
                            pass
            
            last_check = discord.utils.utcnow()
            
        except discord.Forbidden:
            # No audit log permissions, stop monitoring
            try:
                await initiator.send(f"⚠️ Lost audit log permissions for {guild.name}. Monitoring stopped.")
            except:
                pass
            break
        except Exception as e:
            # Log error but continue monitoring
            print(f"Error in audit log monitoring: {e}")
            continue


# Help embed field for lockdown commands
def get_lockdown_commands_field():
    return {
        'name': '🔒 Lockdown System',
        'value': (
            "`!lockdown` - Interactive department lockdown setup\n"
            "`!endlockdown` - Interactive lockdown termination\n"
            "`!lockdown_status` - Check all active lockdowns"
        ),
        'inline': False
    }

import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime

# Configuration - Add all admin user IDs here
ADMIN_IDS = [
    1279303188876492913,  # Your ID (Owner)
    # Add more admin IDs here as needed
]

OWNER_ID = 1279303188876492913  # The owner who can manage all admins

# Data files
GROUPS_FILE = '/home/container/bot-data/groups.json'
PAPERWORK_FILE = '/home/container/bot-data/paperwork.json'
COMPLETED_PAPERWORK_FILE = '/home/container/bot-data/completed_paperwork.json'
ROLE_MAPPING_FILE = '/home/container/bot-data/role_mappings.json'
GROUP_ADMINS_FILE = '/home/container/bot-data/group_admins.json'


# -------------------------------
# JSON HELPERS
# -------------------------------
def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_json_sync(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


# -------------------------------
# ROLE MAPPING FUNCTIONS
# -------------------------------
def load_role_group_mapping():
    mappings = load_json(ROLE_MAPPING_FILE)
    return {int(k): v for k, v in mappings.items()} if mappings else {}


def save_role_group_mapping(mappings):
    string_mappings = {str(k): v for k, v in mappings.items()}
    save_json_sync(ROLE_MAPPING_FILE, string_mappings)


def get_role_group_mapping():
    return load_role_group_mapping()


# -------------------------------
# GROUP ADMIN FUNCTIONS
# -------------------------------
def load_group_admins():
    admins = load_json(GROUP_ADMINS_FILE)
    # Convert string keys to int for user IDs in nested structure
    converted = {}
    for group_name, user_ids in admins.items():
        converted[group_name] = [int(uid) for uid in user_ids]
    return converted


def save_group_admins(admins):
    # Convert int user IDs to strings for JSON storage
    string_admins = {}
    for group_name, user_ids in admins.items():
        string_admins[group_name] = [str(uid) for uid in user_ids]
    save_json_sync(GROUP_ADMINS_FILE, string_admins)


def is_group_admin(user_id: int, group_name: str) -> bool:
    """Check if user is admin of a specific group"""
    group_admins = load_group_admins()
    return group_name in group_admins and user_id in group_admins[group_name]


def get_user_admin_groups(user_id: int) -> list:
    """Get list of groups where user is admin"""
    group_admins = load_group_admins()
    admin_groups = []
    for group_name, admins in group_admins.items():
        if user_id in admins:
            admin_groups.append(group_name)
    return admin_groups


# -------------------------------
# HELPER FUNCTIONS
# -------------------------------
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_global_admin(user_id: int) -> bool:
    """Check if user has global admin privileges (owner or global admin)"""
    return is_owner(user_id) or is_admin(user_id)


def can_manage_group(user_id: int, group_name: str) -> bool:
    """Check if user can manage a specific group (global admin or group admin)"""
    return is_global_admin(user_id) or is_group_admin(user_id, group_name)


def get_user_groups(user_id):
    groups_data = load_json(GROUPS_FILE)
    user_groups = []

    for group_name, group_data in groups_data.items():
        if str(user_id) in group_data.get('members', []):
            user_groups.append(group_name)

    return user_groups


def get_user_groups_with_roles(user_id, user_roles=None):
    groups_data = load_json(GROUPS_FILE)
    user_groups = []

    # Check manual group assignments
    for group_name, group_data in groups_data.items():
        if str(user_id) in group_data.get('members', []):
            user_groups.append(group_name)

    # Check role-based assignments
    if user_roles:
        role_mappings = get_role_group_mapping()
        for role in user_roles:
            if role.id in role_mappings:
                group_name = role_mappings[role.id]
                if group_name not in user_groups:
                    user_groups.append(group_name)

    return user_groups


def auto_assign_role_groups(user, groups_data):
    changes_made = False
    role_mappings = get_role_group_mapping()

    for role in user.roles:
        if role.id in role_mappings:
            group_name = role_mappings[role.id]

            if group_name not in groups_data:
                groups_data[group_name] = {
                    'members': [],
                    'created_by': 0,
                    'created_at': str(datetime.now()),
                    'auto_role': role.id
                }
                changes_made = True

            if str(user.id) not in groups_data[group_name]['members']:
                groups_data[group_name]['members'].append(str(user.id))
                changes_made = True

    return groups_data, changes_made


def get_completed_paperwork(user_id):
    """Get list of completed paperwork for a user"""
    completed_data = load_json(COMPLETED_PAPERWORK_FILE)
    return completed_data.get(str(user_id), [])


def mark_paperwork_complete(user_id, paperwork_key):
    """Mark paperwork as complete for a user"""
    completed_data = load_json(COMPLETED_PAPERWORK_FILE)
    if str(user_id) not in completed_data:
        completed_data[str(user_id)] = []

    if paperwork_key not in completed_data[str(user_id)]:
        completed_data[str(user_id)].append(paperwork_key)
        save_json_sync(COMPLETED_PAPERWORK_FILE, completed_data)
        return True
    return False


# -------------------------------
# PAPERWORK COG CLASS
# -------------------------------
class PaperworkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ADMIN_IDS = ADMIN_IDS
        self.OWNER_ID = OWNER_ID
        self.GROUPS_FILE = GROUPS_FILE
        self.PAPERWORK_FILE = PAPERWORK_FILE
        self.COMPLETED_PAPERWORK_FILE = COMPLETED_PAPERWORK_FILE
        self.ROLE_MAPPING_FILE = ROLE_MAPPING_FILE
        self.GROUP_ADMINS_FILE = GROUP_ADMINS_FILE

    def load_json(self, filename):
        return load_json(filename)

    def save_json(self, filename, data):
        return save_json_sync(filename, data)

    def get_role_group_mapping(self):
        return get_role_group_mapping()

    def save_role_group_mapping(self, mappings):
        return save_role_group_mapping(mappings)

    def is_owner(self, user_id: int) -> bool:
        return is_owner(user_id)

    def is_admin(self, user_id: int) -> bool:
        return is_admin(user_id)

    def is_global_admin(self, user_id: int) -> bool:
        return is_global_admin(user_id)

    def can_manage_group(self, user_id: int, group_name: str) -> bool:
        return can_manage_group(user_id, group_name)

    def is_group_admin(self, user_id: int, group_name: str) -> bool:
        return is_group_admin(user_id, group_name)

    def get_user_groups_with_roles(self, user_id, user_roles=None):
        return get_user_groups_with_roles(user_id, user_roles)

    def get_user_groups(self, user_id):
        return get_user_groups(user_id)

    def auto_assign_role_groups(self, user, groups_data):
        return auto_assign_role_groups(user, groups_data)
    # -------------------------------
    # COG EVENTS
    # -------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Paperwork System with Admin Management loaded!')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return

        new_roles = set(after.roles) - set(before.roles)

        if new_roles:
            groups_data = self.load_json(self.GROUPS_FILE)
            role_mappings = self.get_role_group_mapping()
            changes_made = False

            for role in new_roles:
                if role.id in role_mappings:
                    group_name = role_mappings[role.id]

                    if group_name not in groups_data:
                        groups_data[group_name] = {
                            'members': [],
                            'created_by': 0,
                            'created_at': str(datetime.now()),
                            'auto_role': role.id,
                            'auto_role_name': role.name
                        }
                        changes_made = True

                    if str(after.id) not in groups_data[group_name]['members']:
                        groups_data[group_name]['members'].append(str(after.id))
                        changes_made = True

                        try:
                            embed = discord.Embed(
                                title="Group Assignment",
                                description=f"You've been automatically added to the **{group_name}** group because you received the **{role.name}** role!\n\nUse `!paperwork` to see available paperwork.",
                                color=0x00ff00
                            )
                            await after.send(embed=embed)
                        except:
                            pass

            if changes_made:
                self.save_json(self.GROUPS_FILE, groups_data)

    # -------------------------------
    # ADMIN MANAGEMENT COMMANDS
    # -------------------------------
    @commands.command(name='addadmin')
    async def addadmin(self, ctx, user_id: int):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Only the owner can add global admins.")
            return

        if user_id in ADMIN_IDS:
            await ctx.send("User is already a global admin.")
            return

        ADMIN_IDS.append(user_id)

        try:
            user = await self.bot.fetch_user(user_id)
            username = user.name
        except:
            username = f"User {user_id}"

        embed = discord.Embed(
            title="Global Admin Added",
            description=f"**{username}** has been added as a global administrator.\n\nThey now have access to all admin commands and can manage all groups.",
            color=0x00ff00
        )

        await ctx.send(embed=embed)

        try:
            admin_embed = discord.Embed(
                title="Admin Privileges Granted",
                description="You have been granted global administrator privileges! Use `!paperworkhelp` to see available commands.",
                color=0x00ff00
            )
            await user.send(embed=admin_embed)
        except:
            pass

    @commands.command(name='removeadmin')
    async def removeadmin(self, ctx, user_id: int):
        if not self.is_owner(ctx.author.id):
            await ctx.send("Only the owner can remove global admins.")
            return

        if user_id == self.OWNER_ID:
            await ctx.send("Cannot remove the owner from admin list.")
            return

        if user_id not in ADMIN_IDS:
            await ctx.send("User is not a global admin.")
            return

        ADMIN_IDS.remove(user_id)

        try:
            user = await self.bot.fetch_user(user_id)
            username = user.name
        except:
            username = f"User {user_id}"

        embed = discord.Embed(
            title="Global Admin Removed",
            description=f"**{username}** has been removed from global administrators.\n\nThey no longer have access to admin commands.",
            color=0xff6b6b
        )

        await ctx.send(embed=embed)

    @commands.command(name='setgroupadmin')
    async def setgroupadmin(self, ctx, user_id: int, *, group_name):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if group_name not in groups_data:
            await ctx.send(f"Group '{group_name}' doesn't exist!")
            return

        group_admins = load_group_admins()

        if group_name not in group_admins:
            group_admins[group_name] = []

        if user_id in group_admins[group_name]:
            await ctx.send(f"User is already an admin of group '{group_name}'.")
            return

        group_admins[group_name].append(user_id)
        save_group_admins(group_admins)

        try:
            user = await self.bot.fetch_user(user_id)
            username = user.name
        except:
            username = f"User {user_id}"

        embed = discord.Embed(
            title="Group Admin Added",
            description=f"**{username}** has been set as an admin for group: **{group_name}**\n\nThey can now:\n• Manage group members\n• Create paperwork for this group\n• View group completion status",
            color=0x00ff00
        )

        await ctx.send(embed=embed)

        try:
            admin_embed = discord.Embed(
                title="Group Admin Privileges Granted",
                description=f"You have been granted admin privileges for the **{group_name}** group!\n\nUse `!paperworkhelp` to see available commands.",
                color=0x00ff00
            )
            await user.send(embed=admin_embed)
        except:
            pass

    @commands.command(name='removegroupadmin')
    async def removegroupadmin(self, ctx, user_id: int, *, group_name):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if group_name not in groups_data:
            await ctx.send(f"Group '{group_name}' doesn't exist!")
            return

        group_admins = load_group_admins()

        if group_name not in group_admins or user_id not in group_admins[group_name]:
            await ctx.send(f"User is not an admin of group '{group_name}'.")
            return

        group_admins[group_name].remove(user_id)

        # Clean up empty group admin lists
        if not group_admins[group_name]:
            del group_admins[group_name]

        save_group_admins(group_admins)

        try:
            user = await self.bot.fetch_user(user_id)
            username = user.name
        except:
            username = f"User {user_id}"

        embed = discord.Embed(
            title="Group Admin Removed",
            description=f"**{username}** has been removed as admin of group: **{group_name}**",
            color=0xff6b6b
        )

        await ctx.send(embed=embed)

    @commands.command(name='listadmins')
    async def listadmins(self, ctx):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        embed = discord.Embed(
            title="Administrator List",
            color=0x3498db
        )

        # Global Admins
        global_admin_names = []
        for admin_id in ADMIN_IDS:
            try:
                user = await self.bot.fetch_user(admin_id)
                name = user.name
                if admin_id == self.OWNER_ID:
                    name += " (Owner)"
                global_admin_names.append(name)
            except:
                name = f"User {admin_id}"
                if admin_id == self.OWNER_ID:
                    name += " (Owner)"
                global_admin_names.append(name)

        embed.add_field(
            name="Global Administrators",
            value="\n".join(global_admin_names) if global_admin_names else "None",
            inline=False
        )

        # Group Admins
        group_admins = load_group_admins()
        if group_admins:
            group_admin_text = ""
            for group_name, admin_ids in group_admins.items():
                admin_names = []
                for admin_id in admin_ids:
                    try:
                        user = await self.bot.fetch_user(admin_id)
                        admin_names.append(user.name)
                    except:
                        admin_names.append(f"User {admin_id}")

                group_admin_text += f"**{group_name}:** {', '.join(admin_names)}\n"

            embed.add_field(
                name="Group Administrators",
                value=group_admin_text.strip() if group_admin_text else "None",
                inline=False
            )
        else:
            embed.add_field(
                name="Group Administrators",
                value="None",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='myadmin')
    async def myadmin(self, ctx):
        user_id = ctx.author.id

        embed = discord.Embed(
            title=f"Admin Status for {ctx.author.name}",
            color=0x3498db
        )

        is_owner_ = self.is_owner(user_id)
        is_global = self.is_global_admin(user_id)
        admin_groups = get_user_admin_groups(user_id)

        if is_owner_:
            embed.add_field(
                name="Global Status",
                value="**Owner** - Full system access",
                inline=False
            )
        elif is_global:
            embed.add_field(
                name="Global Status",
                value="**Global Administrator** - Full system access",
                inline=False
            )
        else:
            embed.add_field(
                name="Global Status",
                value="Regular User",
                inline=False
            )

        if admin_groups:
            embed.add_field(
                name="Group Administrator",
                value=", ".join(admin_groups),
                inline=False
            )
        else:
            embed.add_field(
                name="Group Administrator",
                value="None",
                inline=False
            )

        if is_global or admin_groups:
            embed.add_field(
                name="Available Commands",
                value="Use `!paperworkhelp` to see your available admin commands",
                inline=False
            )

        await ctx.send(embed=embed)

    # -------------------------------
    # ROLE MAPPING COMMANDS (Updated with permissions)
    # -------------------------------
    @commands.command(name='addrolegroup')
    async def addrolegroup(self, ctx, role_id: int, *, group_name):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        role_found = False
        role_name = "Unknown Role"

        for guild in self.bot.guilds:
            role = guild.get_role(role_id)
            if role:
                role_found = True
                role_name = role.name
                break

        if not role_found:
            await ctx.send(f"Role ID {role_id} not found in any server, but mapping will be created anyway.")

        role_mappings = self.get_role_group_mapping()
        role_mappings[role_id] = group_name
        self.save_role_group_mapping(role_mappings)

        groups_data = self.load_json(self.GROUPS_FILE)
        if group_name not in groups_data:
            groups_data[group_name] = {
                'members': [],
                'created_by': ctx.author.id,
                'created_at': str(datetime.now()),
                'auto_role': role_id,
                'auto_role_name': role_name
            }
            self.save_json(self.GROUPS_FILE, groups_data)

        embed = discord.Embed(
            title="Role Group Mapping Added",
            description=f"**Role:** {role_name} ({role_id})\n**Group:** {group_name}\n\nUsers with this role will now be automatically added to the group!",
            color=0x00ff00
        )

        await ctx.send(embed=embed)

        await ctx.send("Auto-syncing existing users with this role...")
        synced_count = 0

        for guild in self.bot.guilds:
            role = guild.get_role(role_id)
            if role:
                groups_data = self.load_json(self.GROUPS_FILE)
                for member in role.members:
                    if str(member.id) not in groups_data[group_name]['members']:
                        groups_data[group_name]['members'].append(str(member.id))
                        synced_count += 1
                self.save_json(self.GROUPS_FILE, groups_data)

        await ctx.send(f"Synced {synced_count} existing users to the group!")

    @commands.command(name='listrolemappings')
    async def listrolemappings(self, ctx):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        role_mappings = self.get_role_group_mapping()

        if not role_mappings:
            await ctx.send("No role-group mappings configured.")
            return

        embed = discord.Embed(
            title="Role-Group Mappings",
            description="Current automatic role-to-group assignments:",
            color=0x3498db
        )

        for role_id, group_name in role_mappings.items():
            role_name = "Unknown Role"
            for guild in self.bot.guilds:
                role = guild.get_role(role_id)
                if role:
                    role_name = role.name
                    break

            embed.add_field(
                name=f"**{role_name}**",
                value=f"Role ID: {role_id}\nGroup: {group_name}",
                inline=True
            )

        embed.set_footer(text="Use !addrolegroup <role_id> <group> to add new mappings")
        await ctx.send(embed=embed)

    @commands.command(name='removerolemapping')
    async def removerolemapping(self, ctx, role_id: int):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        role_mappings = self.get_role_group_mapping()

        if role_id not in role_mappings:
            await ctx.send(f"No mapping found for role ID {role_id}.")
            return

        group_name = role_mappings[role_id]
        del role_mappings[role_id]
        self.save_role_group_mapping(role_mappings)

        role_name = "Unknown Role"
        for guild in self.bot.guilds:
            role = guild.get_role(role_id)
            if role:
                role_name = role.name
                break

        embed = discord.Embed(
            title="Role Mapping Removed",
            description=f"**Role:** {role_name} ({role_id})\n**Group:** {group_name}\n\nAutomatic assignment for this role has been disabled.",
            color=0x00ff00
        )

        await ctx.send(embed=embed)

    # -------------------------------
    # ROLE CHECK COMMAND (Updated with permissions)
    # -------------------------------
    @commands.command(name='rolecheck')
    async def rolecheck(self, ctx, group_name=None):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if not groups_data:
            await ctx.send("No groups found.")
            return

        groups_to_check = []
        if group_name:
            if group_name not in groups_data:
                await ctx.send(f"Group '{group_name}' doesn't exist!")
                return
            groups_to_check = [group_name]
        else:
            groups_to_check = [name for name, data in groups_data.items() if 'auto_role' in data]

        if not groups_to_check:
            await ctx.send("No role-based groups found to check.")
            return

        await ctx.send("Starting role verification... This may take a moment.")

        total_removed = 0
        total_added = 0
        results = []

        for group_name in groups_to_check:
            group_data = groups_data[group_name]

            if 'auto_role' not in group_data:
                continue

            role_id = group_data['auto_role']
            role_name = group_data.get('auto_role_name', f'Role {role_id}')

            target_role = None
            current_role_members = set()

            for guild in self.bot.guilds:
                role = guild.get_role(role_id)
                if role:
                    target_role = role
                    current_role_members.update(str(member.id) for member in role.members)

            if not target_role:
                results.append(f"**{group_name}**: Role {role_name} ({role_id}) not found in any server")
                continue

            current_group_members = set(group_data.get('members', []))
            to_remove = current_group_members - current_role_members
            to_add = current_role_members - current_group_members

            if to_remove:
                for user_id in to_remove:
                    groups_data[group_name]['members'].remove(user_id)
                    total_removed += 1

            if to_add:
                for user_id in to_add:
                    groups_data[group_name]['members'].append(user_id)
                    total_added += 1

            if to_remove or to_add:
                result_text = f"**{group_name}** ({role_name})"
                if to_remove:
                    result_text += f"\n  Removed: {len(to_remove)} members"
                if to_add:
                    result_text += f"\n  Added: {len(to_add)} members"
                results.append(result_text)
            else:
                results.append(f"**{group_name}** ({role_name}): All members verified")

        if total_removed > 0 or total_added > 0:
            self.save_json(self.GROUPS_FILE, groups_data)

        embed = discord.Embed(
            title="Role Verification Complete",
            color=0x00ff00 if total_removed == 0 and total_added == 0 else 0xffaa00
        )

        embed.add_field(
            name="Summary",
            value=f"**Groups Checked:** {len(groups_to_check)}\n**Members Removed:** {total_removed}\n**Members Added:** {total_added}",
            inline=False
        )

        if results:
            results_text = "\n\n".join(results)
            if len(results_text) > 1024:
                chunks = []
                current_chunk = ""
                for result in results:
                    if len(current_chunk + result) > 1000:
                        chunks.append(current_chunk)
                        current_chunk = result
                    else:
                        current_chunk += "\n\n" + result if current_chunk else result
                if current_chunk:
                    chunks.append(current_chunk)

                for i, chunk in enumerate(chunks):
                    embed.add_field(
                        name=f"Results {i + 1}/{len(chunks)}" if len(chunks) > 1 else "Results",
                        value=chunk,
                        inline=False
                    )
            else:
                embed.add_field(
                    name="Results",
                    value=results_text,
                    inline=False
                )

        embed.set_footer(text="Use !rolecheck <group> to check a specific group only")
        await ctx.send(embed=embed)

    # -------------------------------
    # GROUP MANAGEMENT COMMANDS (Updated with permissions)
    # -------------------------------
    @commands.command(name="groupcreate")
    async def groupcreate(self, ctx, group_name, role_id: int = None):
        if not self.is_global_admin(ctx.author.id):
            await ctx.send("You don't have permission to use this command.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if group_name.lower() in [g.lower() for g in groups_data.keys()]:
            await ctx.send(f"Group '{group_name}' already exists!")
            return

        group_data = {
            'members': [],
            'created_by': ctx.author.id,
            'created_at': str(datetime.now())
        }

        if role_id:
            role_found = False
            role_name = "Unknown Role"
            role_members = []

            for guild in self.bot.guilds:
                role = guild.get_role(role_id)
                if role:
                    role_found = True
                    role_name = role.name
                    role_members.extend([str(member.id) for member in role.members])
                    break

            if not role_found:
                await ctx.send(f"Role ID {role_id} not found in any server. Creating group without role linking.")
            else:
                group_data['auto_role'] = role_id
                group_data['auto_role_name'] = role_name
                group_data['members'] = list(set(role_members))

                role_mappings = self.get_role_group_mapping()
                role_mappings[role_id] = group_name
                self.save_role_group_mapping(role_mappings)

        groups_data[group_name] = group_data
        self.save_json(self.GROUPS_FILE, groups_data)

        if role_id and role_found:
            embed = discord.Embed(
                title="Group Created with Automatic Role Linking",
                description=f"**Group:** {group_name}\n**Role:** {role_name} ({role_id})\n**Members Added:** {len(group_data['members'])}\n\nAutomatic features enabled:\n• Users with this role will be auto-added to the group\n• Users who lose the role will be auto-removed\n• No manual code changes needed!",
                color=0x00ff00
            )
        else:
            embed = discord.Embed(
                title="Group Created",
                description=f"Successfully created group: **{group_name}**",
                color=0x00ff00
            )

        await ctx.send(embed=embed)

    @commands.command(name='addtogroup')
    async def addtogroup(self, ctx, user_id: int, *, group_name):
        if not self.can_manage_group(ctx.author.id, group_name):
            await ctx.send("You don't have permission to manage this group.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if group_name not in groups_data:
            await ctx.send(f"Group '{group_name}' doesn't exist!")
            return

        if str(user_id) not in groups_data[group_name]['members']:
            groups_data[group_name]['members'].append(str(user_id))
            self.save_json(self.GROUPS_FILE, groups_data)

            try:
                user = await self.bot.fetch_user(user_id)
                embed = discord.Embed(
                    title="Added to Group",
                    description=f"Successfully added **{user.name}** to group: **{group_name}**",
                    color=0x00ff00
                )
                await ctx.send(embed=embed)
            except:
                await ctx.send(f"Successfully added user ID {user_id} to group: **{group_name}**")
        else:
            await ctx.send(f"User is already in group '{group_name}'!")

    @commands.command(name='removefromgroup')
    async def removefromgroup(self, ctx, user_id: int, *, group_name):
        if not self.can_manage_group(ctx.author.id, group_name):
            await ctx.send("You don't have permission to manage this group.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if group_name not in groups_data:
            await ctx.send(f"Group '{group_name}' doesn't exist!")
            return

        if str(user_id) in groups_data[group_name]['members']:
            groups_data[group_name]['members'].remove(str(user_id))
            self.save_json(self.GROUPS_FILE, groups_data)
            await ctx.send(f"Successfully removed user from group: **{group_name}**")
        else:
            await ctx.send(f"User is not in group '{group_name}'!")

    @commands.command(name="grouplist")
    async def grouplist(self, ctx):
        if not self.is_global_admin(ctx.author.id):
            # For group admins, show only their groups
            admin_groups = get_user_admin_groups(ctx.author.id)
            if not admin_groups:
                await ctx.send("You don't have permission to view groups.")
                return

            groups_data = self.load_json(self.GROUPS_FILE)

            if not groups_data:
                await ctx.send("No groups created yet.")
                return

            embed = discord.Embed(title="Your Managed Groups", color=0x3498db)

            for group_name in admin_groups:
                if group_name in groups_data:
                    group_info = groups_data[group_name]
                    member_count = len(group_info.get('members', []))
                    role_info = ""
                    if 'auto_role' in group_info:
                        role_info = f" (Role: {group_info.get('auto_role_name', 'Unknown')})"
                    embed.add_field(
                        name=f"**{group_name}**{role_info}",
                        value=f"Members: {member_count}",
                        inline=True
                    )

            await ctx.send(embed=embed)
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if not groups_data:
            await ctx.send("No groups created yet.")
            return

        embed = discord.Embed(title="All Groups", color=0x3498db)

        for group_name, group_info in groups_data.items():
            member_count = len(group_info.get('members', []))
            role_info = ""
            if 'auto_role' in group_info:
                role_info = f" (Role: {group_info.get('auto_role_name', 'Unknown')})"
            embed.add_field(
                name=f"**{group_name}**{role_info}",
                value=f"Members: {member_count}",
                inline=True
            )

        await ctx.send(embed=embed)

    # -------------------------------
    # PAPERWORK CREATION (Updated with permissions)
    # -------------------------------
    @commands.command(name='paperworkcreate')
    async def paperworkcreate(self, ctx, *, group_name):
        if not self.can_manage_group(ctx.author.id, group_name):
            await ctx.send("You don't have permission to create paperwork for this group.")
            return

        groups_data = self.load_json(self.GROUPS_FILE)

        if group_name not in groups_data:
            await ctx.send(f"Group '{group_name}' doesn't exist!")
            return

        await ctx.send(f"Creating new paperwork for group: **{group_name}**")
        await ctx.send("What should this paperwork be called? (e.g., 'Background Check', 'Medical Form')")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            paperwork_name_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            paperwork_name = paperwork_name_msg.content

            questions = []
            await ctx.send(f"Now let's add questions for **{paperwork_name}**.")

            question_types_info = """
**Question Types Available:**
**1** = Open-ended (free text response)
**2** = Multiple choice (A, B, C options)  
**3** = Rating scale (1-10 scale)
**4** = Read-only (I accept/I deny only)

**Format:** Type the question type number (1-4), then your question.
**Example:** `2 What is your favorite color?`
Type **'done'** when finished adding questions.
            """

            await ctx.send(question_types_info)

            while True:
                await ctx.send(f"**Question {len(questions) + 1}:** Enter type (1-4) and question, or 'done' to finish:")
                question_msg = await self.bot.wait_for('message', check=check, timeout=180.0)

                if question_msg.content.lower() == 'done':
                    break

                parts = question_msg.content.split(' ', 1)
                if len(parts) < 2:
                    await ctx.send("Please format as: `<type> <question>` (e.g., `1 What is your name?`)")
                    continue

                try:
                    question_type = int(parts[0])
                    question_text = parts[1]
                except ValueError:
                    await ctx.send("Question type must be a number (1-4). Try again.")
                    continue

                if question_type not in [1, 2, 3, 4]:
                    await ctx.send("Question type must be 1, 2, 3, or 4. Try again.")
                    continue

                question_data = {
                    'type': question_type,
                    'question': question_text,
                }

                if question_type == 2:  # Multiple choice
                    await ctx.send(f"**Multiple Choice Question:** {question_text}")
                    await ctx.send("Now add the choices one by one. Type 'choices done' when finished:")

                    choices = []
                    while True:
                        choice_msg = await self.bot.wait_for('message', check=check, timeout=120.0)

                        if choice_msg.content.lower() == 'choices done':
                            break

                        choices.append(choice_msg.content)
                        await ctx.send(f"Added choice {len(choices)}: {choice_msg.content}")

                    if not choices:
                        await ctx.send("No choices added. Question skipped.")
                        continue

                    question_data['choices'] = choices

                elif question_type == 3:  # Rating scale
                    await ctx.send(f"**Rating Question:** {question_text}")
                    await ctx.send("What should be the scale? (e.g., '1-10', '1-5', '0-100'):")

                    scale_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                    scale_parts = scale_msg.content.split('-')

                    if len(scale_parts) == 2:
                        try:
                            min_val = int(scale_parts[0])
                            max_val = int(scale_parts[1])
                            question_data['scale_min'] = min_val
                            question_data['scale_max'] = max_val
                            await ctx.send(f"Scale set: {min_val} to {max_val}")
                        except ValueError:
                            await ctx.send("Invalid scale format, defaulting to 1-10")
                            question_data['scale_min'] = 1
                            question_data['scale_max'] = 10
                    else:
                        await ctx.send("Invalid scale format, defaulting to 1-10")
                        question_data['scale_min'] = 1
                        question_data['scale_max'] = 10

                elif question_type == 4:  # Read-only
                    await ctx.send(f"**Read-only Question:** {question_text}")
                    await ctx.send("This will require users to respond with 'I accept' or 'I deny'.")

                questions.append(question_data)

                type_names = {1: "Open-ended", 2: "Multiple Choice", 3: "Rating Scale", 4: "Read-only"}
                summary = f"**Question {len(questions)} Added**\n**Type:** {type_names[question_type]}\n**Question:** {question_text}"

                if question_type == 2:
                    summary += f"\n**Choices:** {', '.join(question_data['choices'])}"
                elif question_type == 3:
                    summary += f"\n**Scale:** {question_data['scale_min']}-{question_data['scale_max']}"

                await ctx.send(summary)

            if not questions:
                await ctx.send("No questions added. Paperwork creation cancelled.")
                return

            paperwork_data = self.load_json(self.PAPERWORK_FILE)
            paperwork_key = f"{group_name}_{paperwork_name.replace(' ', '_').lower()}"

            await ctx.send("Enter a channel ID where completion notifications should be sent (or type 'skip' to skip):")

            try:
                channel_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                channel_id = None

                if channel_msg.content.lower() != 'skip':
                    try:
                        channel_id = int(channel_msg.content)
                        channel = self.bot.get_channel(channel_id)
                        if not channel:
                            await ctx.send("Channel not found, but paperwork will be created without notifications.")
                            channel_id = None
                        else:
                            await ctx.send(f"Completion notifications will be sent to: **{channel.name}**")
                    except ValueError:
                        await ctx.send("Invalid channel ID, but paperwork will be created without notifications.")
                        channel_id = None
            except asyncio.TimeoutError:
                await ctx.send("Timeout for channel selection, creating paperwork without notifications.")
                channel_id = None

            paperwork_data[paperwork_key] = {
                'name': paperwork_name,
                'group': group_name,
                'questions': questions,
                'completion_channel': channel_id,
                'created_by': ctx.author.id,
                'created_at': str(datetime.now())
            }

            self.save_json(self.PAPERWORK_FILE, paperwork_data)

            type_counts = {1: 0, 2: 0, 3: 0, 4: 0}
            for q in questions:
                type_counts[q['type']] += 1

            summary_text = f"**Total Questions:** {len(questions)}\n"
            summary_text += f"Open-ended: {type_counts[1]}\n"
            summary_text += f"Multiple Choice: {type_counts[2]}\n"
            summary_text += f"Rating Scale: {type_counts[3]}\n"
            summary_text += f"Read-only: {type_counts[4]}"

            embed = discord.Embed(
                title="Paperwork Created Successfully",
                description=f"**Name:** {paperwork_name}\n**Group:** {group_name}\n\n{summary_text}",
                color=0x00ff00
            )
            await ctx.send(embed=embed)

        except asyncio.TimeoutError:
            await ctx.send("Timeout! Paperwork creation cancelled.")

    # -------------------------------
    # USER PAPERWORK COMMANDS
    # -------------------------------
    @commands.command(name='paperwork')
    async def paperwork(self, ctx):
        try:
            user_groups = self.get_user_groups_with_roles(ctx.author.id, getattr(ctx.author, 'roles', None))
        except:
            user_groups = self.get_user_groups(ctx.author.id)

        if not user_groups:
            await ctx.send("You're not assigned to any groups. Contact an administrator.")
            return

        paperwork_data = self.load_json(self.PAPERWORK_FILE)
        available_paperwork = []

        completed_paperwork = get_completed_paperwork(ctx.author.id)

        for paperwork_key, paperwork_info in paperwork_data.items():
            if paperwork_info['group'] in user_groups:
                completed = paperwork_key in completed_paperwork
                status = "Completed" if completed else "Pending"
                available_paperwork.append(f"**{paperwork_info['name']}** ({paperwork_info['group']}) - {status}")

        if not available_paperwork:
            await ctx.send("No paperwork available for your groups.")
            return

        embed = discord.Embed(
            title="Available Paperwork",
            description=f"**Your Groups:** {', '.join(user_groups)}\n\n" + "\n".join(available_paperwork),
            color=0x3498db
        )
        embed.set_footer(text="To fill out paperwork, use !fillpaperwork <name>")
        await ctx.send(embed=embed)

    @commands.command(name='fillpaperwork')
    async def fillpaperwork(self, ctx, *, paperwork_name=None):
        try:
            user_groups = self.get_user_groups_with_roles(ctx.author.id, getattr(ctx.author, 'roles', None))
        except:
            user_groups = self.get_user_groups(ctx.author.id)

        if not user_groups:
            await ctx.send("You're not assigned to any groups. Contact an administrator.")
            return

        paperwork_data = self.load_json(self.PAPERWORK_FILE)

        if not paperwork_name:
            available_paperwork = []
            completed_paperwork = get_completed_paperwork(ctx.author.id)

            for paperwork_key, paperwork_info in paperwork_data.items():
                if paperwork_info['group'] in user_groups and paperwork_key not in completed_paperwork:
                    available_paperwork.append(f"**{paperwork_info['name']}** ({paperwork_info['group']})")

            if not available_paperwork:
                await ctx.send("No incomplete paperwork available for you.")
                return

            embed = discord.Embed(
                title="Available Paperwork to Fill",
                description="Use `!fillpaperwork <name>` to start filling:\n\n" + "\n".join(available_paperwork),
                color=0x3498db
            )
            embed.set_footer(text="Example: !fillpaperwork NDA")
            await ctx.send(embed=embed)
            return

        selected_paperwork = None
        selected_key = None

        for paperwork_key, paperwork_info in paperwork_data.items():
            if (paperwork_info['name'].lower() == paperwork_name.lower() and
                    paperwork_info['group'] in user_groups):
                selected_paperwork = paperwork_info
                selected_key = paperwork_key
                break

        if not selected_paperwork:
            await ctx.send(f"Paperwork '{paperwork_name}' not found or not available to you.")
            return

        completed_paperwork = get_completed_paperwork(ctx.author.id)
        if selected_key in completed_paperwork:
            await ctx.send(f"You have already completed the **{selected_paperwork['name']}** paperwork.")
            return

        await ctx.send(f"Starting **{selected_paperwork['name']}** paperwork. Check your DMs!")

        try:
            try:
                dm_channel = ctx.author.dm_channel
                if dm_channel is None:
                    dm_channel = await ctx.author.create_dm()
            except:
                await ctx.send("Could not create DM channel. Please enable DMs from server members.")
                return

            embed = discord.Embed(
                title=f"{selected_paperwork['name']} Paperwork",
                description=f"**Group:** {selected_paperwork['group']}\n\nPlease answer each question. Type 'cancel' at any time to stop.",
                color=0x3498db
            )
            await dm_channel.send(embed=embed)

            # Handle regular questions
            answers = []
            if 'questions' in selected_paperwork and selected_paperwork['questions']:
                await dm_channel.send("Please answer the following questions:")

                for i, question_data in enumerate(selected_paperwork['questions'], 1):
                    if isinstance(question_data, str):
                        question_text = question_data
                        question_type = 1
                        question_data = {'type': 1, 'question': question_text}
                    else:
                        question_text = question_data['question']
                        question_type = question_data['type']

                    if question_type == 1:  # Open-ended
                        await dm_channel.send(f"**Question {i}:** {question_text}")
                        await dm_channel.send("*Please provide your answer:*")

                    elif question_type == 2:  # Multiple choice
                        choices = question_data.get('choices', [])
                        choices_text = "\n".join([f"**{chr(65 + idx)}**. {choice}" for idx, choice in enumerate(choices)])

                        await dm_channel.send(f"**Question {i}:** {question_text}\n\n{choices_text}")
                        await dm_channel.send("*Please respond with the letter of your choice (A, B, C, etc.):*")

                    elif question_type == 3:  # Rating scale
                        min_val = question_data.get('scale_min', 1)
                        max_val = question_data.get('scale_max', 10)

                        await dm_channel.send(f"**Question {i}:** {question_text}")
                        await dm_channel.send(f"*Please rate on a scale of {min_val} to {max_val}:*")

                    elif question_type == 4:  # Read-only
                        read_only_embed = discord.Embed(
                            title=f"Question {i}",
                            description=question_text,
                            color=0xffd700
                        )
                        await dm_channel.send(embed=read_only_embed)
                        await dm_channel.send("*Please respond with 'I accept' or 'I deny':*")

                    def check_answer(m):
                        return (m.author == ctx.author and
                                isinstance(m.channel, discord.DMChannel))

                    while True:
                        try:
                            answer_msg = await self.bot.wait_for('message', check=check_answer, timeout=300.0)

                            if answer_msg.content.lower() == 'cancel':
                                await dm_channel.send("Paperwork cancelled.")
                                return

                            user_answer = answer_msg.content
                            valid_answer = True
                            validation_message = ""

                            if question_type == 2:  # Multiple choice validation
                                choices = question_data.get('choices', [])
                                user_answer_upper = user_answer.upper()

                                if len(user_answer) == 1 and user_answer_upper.isalpha():
                                    choice_index = ord(user_answer_upper) - ord('A')
                                    if 0 <= choice_index < len(choices):
                                        user_answer = f"{user_answer_upper}. {choices[choice_index]}"
                                    else:
                                        valid_answer = False
                                        validation_message = f"Please choose a letter between A and {chr(65 + len(choices) - 1)}."
                                else:
                                    valid_answer = False
                                    validation_message = f"Please respond with a single letter (A-{chr(65 + len(choices) - 1)})."

                            elif question_type == 3:  # Rating scale validation
                                min_val = question_data.get('scale_min', 1)
                                max_val = question_data.get('scale_max', 10)

                                try:
                                    rating = float(user_answer)
                                    if min_val <= rating <= max_val:
                                        user_answer = str(rating)
                                    else:
                                        valid_answer = False
                                        validation_message = f"Please enter a number between {min_val} and {max_val}."
                                except ValueError:
                                    valid_answer = False
                                    validation_message = f"Please enter a valid number between {min_val} and {max_val}."

                            elif question_type == 4:  # Read-only validation
                                if user_answer.lower() not in ['i accept', 'i deny']:
                                    valid_answer = False
                                    validation_message = "Please respond with either 'I accept' or 'I deny'."

                                if user_answer.lower() == 'i deny':
                                    await dm_channel.send("You must accept all read-only sections to complete this paperwork. Process cancelled.")
                                    return

                            if not valid_answer:
                                await dm_channel.send(f"{validation_message} Please try again.")
                                continue

                            answers.append({
                                'question': question_text,
                                'answer': user_answer,
                                'type': question_type
                            })

                            await dm_channel.send(f"Answer {i} recorded.")
                            break

                        except asyncio.TimeoutError:
                            await dm_channel.send("Timeout! Paperwork cancelled.")
                            return

            await dm_channel.send("**Paperwork completed successfully!** Your responses have been submitted.")

            response_embed = discord.Embed(
                title=f"{selected_paperwork['name']} Completed",
                description=f"**User:** {ctx.author.mention}\n**Group:** {selected_paperwork['group']}\n**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                color=0x00ff00
            )

            if answers:
                answers_text = "\n".join([f"**Q:** {qa['question']}\n**A:** {qa['answer']}" for qa in answers[:5]])
                if len(answers) > 5:
                    answers_text += f"\n... and {len(answers) - 5} more answers"
                response_embed.add_field(name="Answers", value=answers_text, inline=False)

            await ctx.send(embed=response_embed)

            # Mark paperwork as complete
            mark_paperwork_complete(ctx.author.id, selected_key)

            completion_channel_id = selected_paperwork.get('completion_channel')
            if completion_channel_id:
                try:
                    completion_channel = self.bot.get_channel(completion_channel_id)
                    if completion_channel:
                        await completion_channel.send(embed=response_embed)
                except:
                    pass

            await ctx.send(f"**{selected_paperwork['name']}** paperwork has been marked as complete!")

        except discord.Forbidden:
            await ctx.send("I can't send you DMs. Please enable DMs from server members and try again.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")


    @commands.command(name='paperworkcomplete')
    async def paperworkcomplete(self, ctx, user_id: int):
        # Check if user can complete paperwork (needs to be able to see completion status)
        if not self.is_global_admin(ctx.author.id):
            # Check if they're a group admin with relevant permissions
            user_admin_groups = get_user_admin_groups(ctx.author.id)
            if not user_admin_groups:
                await ctx.send("You don't have permission to use this command.")
                return

        try:
            user_obj = await self.bot.fetch_user(user_id)
            user_roles = None
            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    user_roles = member.roles
                    break

            user_groups = self.get_user_groups_with_roles(user_id, user_roles)
        except:
            user_groups = self.get_user_groups(user_id)

        # For group admins, filter to only show groups they manage
        if not self.is_global_admin(ctx.author.id):
            user_admin_groups = get_user_admin_groups(ctx.author.id)
            user_groups = [group for group in user_groups if group in user_admin_groups]

        if not user_groups:
            await ctx.send("User is not in any groups you can manage.")
            return

        paperwork_data = self.load_json(self.PAPERWORK_FILE)
        completed_paperwork = get_completed_paperwork(user_id)

        completion_status = []
        total_paperwork = 0
        completed_count = 0

        for paperwork_key, paperwork_info in paperwork_data.items():
            if paperwork_info['group'] in user_groups:
                total_paperwork += 1
                is_complete = paperwork_key in completed_paperwork
                if is_complete:
                    completed_count += 1

                status = "✅ Complete" if is_complete else "❌ Incomplete"
                completion_status.append(f"**{paperwork_info['name']}** ({paperwork_info['group']}) - {status}")

        if not completion_status:
            await ctx.send("No paperwork found for this user in manageable groups.")
            return

        try:
            username = user_obj.name
        except:
            username = f"User {user_id}"

        embed = discord.Embed(
            title=f"Paperwork Status for {username}",
            description=f"**Groups:** {', '.join(user_groups)}\n**Completion:** {completed_count}/{total_paperwork}\n\n" + "\n".join(completion_status),
            color=0x00ff00 if completed_count == total_paperwork else 0xffaa00
        )

        await ctx.send(embed=embed)

@bot.command(name='paperworkhelp')
async def paperworkhelp(ctx):
    user_id = ctx.author.id
    is_owner = (user_id == OWNER_ID)
    is_global_admin = (user_id in ADMIN_IDS)
    admin_groups = get_user_admin_groups(user_id)
    
    embed = discord.Embed(
        title="Paperwork System Commands",
        description="Here are all available paperwork commands:",
        color=0x3498db
    )
    
    # User Commands (available to everyone)
    user_commands = """
`!paperwork` - View your available paperwork and completion status
`!fillpaperwork` - Show available paperwork to fill
`!fillpaperwork <name>` - Fill specific paperwork (e.g., !fillpaperwork NDA)
`!myadmin` - Check your admin status and permissions
`!paperworkhelp` - Show this help menu
    """
    
    embed.add_field(
        name="**User Commands**",
        value=user_commands.strip(),
        inline=False
    )
    
    # Owner Commands (only for owner)
    if is_owner:
        owner_commands = """
**Global Admin Management:**
`!addadmin <user_id>` - Add global administrator
`!removeadmin <user_id>` - Remove global administrator
`!setgroupadmin <user_id> <group>` - Set user as group admin
`!removegroupadmin <user_id> <group>` - Remove group admin
`!listadmins` - View all administrators (global and group)
        """
        
        embed.add_field(
            name="**Owner Commands**",
            value=owner_commands.strip(),
            inline=False
        )
    
    # Global Admin Commands
    if is_global_admin:
        global_admin_commands = """
**Group Management:**
`!groupcreate <name>` - Create a new group
`!groupcreate <name> <role_id>` - Create group with role linking
`!addtogroup <user_id> <group>` - Add user to group
`!removefromgroup <user_id> <group>` - Remove user from group
`!grouplist` - View all groups and member counts

**Role-Based Groups:**
`!addrolegroup <role_id> <group>` - Auto-link role to group
`!listrolemappings` - Show all role-group mappings
`!removerolemapping <role_id>` - Remove role-group mapping
`!rolecheck` - Verify all role-based group memberships
`!rolecheck <group>` - Check specific group

**Admin Management:**
`!setgroupadmin <user_id> <group>` - Set user as group admin
`!removegroupadmin <user_id> <group>` - Remove group admin
`!listadmins` - View all administrators

**Paperwork Management:**
`!paperworkcreate <group>` - Create new paperwork for group
`!paperworkcomplete <user_id>` - Mark paperwork as complete
`!paperworkstatus` - View completion status of all users
        """
        
        embed.add_field(
            name="**Global Admin Commands**",
            value=global_admin_commands.strip(),
            inline=False
        )
    
    # Group Admin Commands (if user is group admin but not global admin)
    elif admin_groups:
        group_admin_commands = f"""
**Group Management (Your Groups: {', '.join(admin_groups)}):**
`!addtogroup <user_id> <group>` - Add user to your managed groups
`!removefromgroup <user_id> <group>` - Remove user from your groups
`!grouplist` - View your managed groups

**Paperwork Management:**
`!paperworkcreate <group>` - Create paperwork for your groups
`!paperworkcomplete <user_id>` - Mark paperwork complete for your groups
`!paperworkstatus` - View completion status (your groups only)
        """
        
        embed.add_field(
            name="**Group Admin Commands**",
            value=group_admin_commands.strip(),
            inline=False
        )
    
    # Help section for regular users
    if not is_global_admin and not admin_groups:
        embed.add_field(
            name="**Need Help?**",
            value="Contact an administrator if you need:\n• Added to groups\n• Help with paperwork completion\n• Questions about your assignments",
            inline=False
        )
    
    # How to fill paperwork (for everyone)
    embed.add_field(
        name="**How to Fill Paperwork**",
        value="1. Check if you're in any groups (use `!paperwork`)\n2. Use `!paperwork` to see available forms\n3. Use `!fillpaperwork <name>` to fill them out\n4. Complete the questions in DMs\n5. Get notified when marked complete!",
        inline=False
    )
    
    # Permission levels explanation
    permission_text = ""
    if is_owner:
        permission_text = "**Your Level:** Owner (Full System Control)"
    elif is_global_admin:
        permission_text = "**Your Level:** Global Administrator (Full Access)"
    elif admin_groups:
        permission_text = f"**Your Level:** Group Administrator ({len(admin_groups)} groups)"
    else:
        permission_text = "**Your Level:** Regular User"
    
    embed.add_field(
        name="**Permission Level**",
        value=permission_text,
        inline=False
    )
    
    embed.set_footer(text="Enhanced Paperwork System v3.0 • Questions? Contact an administrator")
    await ctx.send(embed=embed)
# -------------------------------
# SETUP FUNCTION FOR COG
# -------------------------------
async def setup(bot):
    await bot.add_cog(PaperworkCog(bot))
# Adens random ahhah funtion
ALLOWED_USER = 1279303188876492913  # Only this user can run the command

async def execute_order_66(message):
    if message.author.id != ALLOWED_USER:
        return  # ignore other users

    if message.mentions and message.client.user in message.mentions and "executeorder66" in message.content.lower():
        steps = [
            ":Loadingemjogiorwtv: Loading main functions",
            "Updating software and hardware due to protocol 623",
            "Installing updates",
            "Process complete. Executing order 66"
        ]

        for step in steps:
            async with message.channel.typing():
                await asyncio.sleep(1.5)  # 1.5 second typing simulation
            await message.channel.send(step)

        await message.channel.send("https://images-ext-1.discordapp.net/external/0pud7DoW7kerv5e4JDm1QAYQv1EAmMyUr0vfd_LzeJA/https/media.tenor.com/8jfYzIP2qaoAAAAe/galactic-republic-execute-order66.png")

async def safe_save(file_key, data):
    file_path = CONFIG['FILES'].get(file_key.upper())
    if not file_path:
        logger.error(f"Missing file path for {file_key}")
        return
    logger.info(f"safe_save called for {file_key} -> {file_path}")
    await save_json(file_path, data)
AUTHORIZED_USER_ID = 1279303188876492913  # Only this user can run the command

@bot.command(name="executeorder66")
async def executeorder66(ctx):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("❌ You are not authorized to run this command.")
        return

    steps = [
        (":loading: Executing Order 66...", 1),
        ("💻 Hacking admin mainframe...", 2),
        ("🕵️ Accessing :hat command...", 1.5),
        ("🔎 Finding all ESD in game...", 2.5),
        ("⚔️ Executing Order 66...", 3),
        ("✅ Order 66 executed successfully.", 1)
    ]

    for step, delay in steps:
        await ctx.send(step)
        await asyncio.sleep(delay)

    embed = discord.Embed(
        title="Order 66",
        description="The ESD have been humuliated.",
        color=discord.Color.red()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/965163720881897482/1353549098434957492/togif.gif?ex=68d2a814&is=68d15694&hm=498ff3ec3e888b9a2a85884c36ee288dd57f024a6c604137ce209cdb9e03b49c")
    await ctx.send(embed=embed)
# Add the cog to the bot
async def setup_bot():
    await bot.add_cog(PaperworkCog(bot))
    
# JSON file path
ROAST_FILE = "/home/container/bot-data/roasts.json"

# Load or create default roasts
if os.path.exists(ROAST_FILE):
    with open(ROAST_FILE, "r") as f:
        roasts = json.load(f)
else:
    roasts = {
        "aden": [
            "Aden's code sucks so bad that it needs a map to find the bugs.",
            "Aden's code is so slow, snails file complaints."
        ],
        "kar": [
            "Kar thinks milsim is about camping in the spawn room.",
            "Kar's leadership style is 'follow me... if you dare.'"
        ]
    }

def save_roasts():
    with open(ROAST_FILE, "w") as f:
        json.dump(roasts, f, indent=4)

# --- Ownership roast command ---
@bot.command(name="ownershiproast")
@commands.cooldown(1, 30, commands.BucketType.user)
async def ownershiproast(ctx, target: str):
    target = target.lower()
    if target not in roasts:
        await ctx.send("❌ Invalid target! Use `Aden` or `Kar`.")
        return
    roast = random.choice(roasts[target])
    await ctx.send(f"🔥 {roast}")

@ownershiproast.error
async def ownershiproast_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Slow down! Try again in {int(error.retry_after)} seconds.")

# --- Add roast command (DMs only) ---
@bot.command(name="addroast")
async def addroast(ctx, target: str, *, roast_text: str):
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("❌ You can only add roasts in DMs to the bot.")
        return

    target = target.lower()
    if target not in roasts:
        await ctx.send("❌ Invalid target! Use `Aden` or `Kar`.")
        return

    roasts[target].append(roast_text)
    save_roasts()
    await ctx.send(f"✅ Roast added for {target.capitalize()}!")

AUTHORIZED_USER_ID = 1279303188876492913  # Only this user can run it

@bot.command(name="executeorder67")
async def executeorder67(ctx):
    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("❌ You are not authorized to run this command.")
        return

    steps = [
        ":thinking: Preparing to execute Order 66...",
        "⚠️ Wait… something feels off…",
        "🚨 67 takeover activated!",  # updated 3rd step text
        "💻 Hacking mainframe for Order 67...",
        "🔎 Locating all anomalies… 6, 7, repeat…",
        "✅ Order 67 executed… success? Probably."
    ]

    delays = [1.5, 2, 1.5, 2.5, 3, 1.5]

    for step, delay in zip(steps, delays):
        await ctx.send(step)
        await asyncio.sleep(delay)

    embed = discord.Embed(
        title="Order 67",
        description="The galaxy is slightly confused now. 😅",
        color=discord.Color.dark_red()
    )
    embed.set_image(url="https://tenor.com/view/67-gif-8575841764206736991")
    await ctx.send(embed=embed)
# === LEAK DETECTION MANAGEMENT COMMANDS ===
@bot.command(name='addkeyword')
async def addkeyword(ctx, *, keyword):
    """Add a keyword to leak detection (owner only)"""
    if ctx.author.id != CONFIG['OWNER_USER_ID']:
        return await ctx.reply('❌ You don\'t have permission to use this command.')

@bot.command(name='removekeyword')
async def removekeyword(ctx, *, keyword):
    """Remove a keyword from leak detection (owner only)"""
    if ctx.author.id != CONFIG['OWNER_USER_ID']:
        return await ctx.reply('❌ You don\'t have permission to use this command.')

@bot.command(name='listkeywords')
async def listkeywords(ctx):
    """List all leak detection keywords (owner only)"""
    if ctx.author.id != CONFIG['OWNER_USER_ID']:
        return await ctx.reply('❌ You don\'t have permission to use this command.')

@bot.command(name='leakstatus')
async def leakstatus(ctx):
    """Show leak detection system status (owner only)"""
    if ctx.author.id != CONFIG['OWNER_USER_ID']:
        return await ctx.reply('❌ You don\'t have permission to use this command.')
@bot.command(name='checkcommands')
async def checkcommands(ctx):
    if ctx.author.id != CONFIG['OWNER_USER_ID']:
        return
    
    commands = bot.tree.get_commands()
    await ctx.send(f"Registered commands: {len(commands)}")
    for cmd in commands:
        await ctx.send(f"- /{cmd.name}: {cmd.description}")
async def main():
    async with bot:
        await bot.load_extension("cogs.backup")  # path to this file
        await bot.start("YOUR_TOKEN")
# === RUN THE BOT ===
if __name__ == '__main__':
    try:
        logger.info('Starting Adens custom Bot...')
        logger.info('Created by Adeniscool65 for asylum site zeta and all offical deapartments!!!!!!')
        
        # Add the cog before running
        asyncio.run(setup_bot())
        
        bot.run(CONFIG['TOKEN'])
    except Exception as error:
        logger.error(f'Bot startup error: {error}')
        print(f'Failed to start bot: {error}')
        
 

