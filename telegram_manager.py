"""
Ultra-Advanced Telegram Manager
With device fingerprinting, proxy rotation, and app spoofing
"""

import asyncio
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    FloodWaitError,
    PhoneNumberInvalidError,
    ApiIdInvalidError,
    AuthKeyUnregisteredError,
    ProxyConnectionError,
)

from config import SESSIONS_DIR
import database as db
from fingerprint import fingerprint_generator, DeviceFingerprint
from proxy_manager import proxy_manager, Proxy


class TelegramManager:
    """
    Advanced Telegram client manager with:
    - Device fingerprinting (real devices)
    - App spoofing (Nicegram, Telegram X, etc.)
    - One-time proxy rotation
    - Automatic dead proxy skip
    """
    
    def __init__(self):
        self._clients: Dict[str, TelegramClient] = {}
        self._pending_clients: Dict[str, TelegramClient] = {}
        self._fingerprints: Dict[str, DeviceFingerprint] = {}
        self._proxies_used: Dict[str, Proxy] = {}
    
    def _get_session_path(self, phone: str) -> str:
        """Get the session file path for a phone number."""
        safe_phone = phone.replace("+", "").replace(" ", "")
        return str(SESSIONS_DIR / f"session_{safe_phone}")
    
    def _create_client_with_fingerprint(
        self,
        session_path: str,
        api_id: int,
        api_hash: str,
        fingerprint: DeviceFingerprint,
        proxy: Optional[Proxy] = None,
    ) -> TelegramClient:
        """Create Telegram client with device fingerprint and optional proxy."""
        
        # Prepare proxy configuration
        proxy_config = None
        if proxy:
            if proxy.proxy_type.value == "mtproto":
                proxy_config = proxy.to_mtproto_dict()
            else:
                proxy_config = proxy.to_telethon_proxy()
        
        # Create client with fingerprint
        client = TelegramClient(
            session_path,
            api_id,
            api_hash,
            # Device fingerprint
            device_model=fingerprint.device_model,
            system_version=fingerprint.system_version,
            app_version=fingerprint.app_version,
            lang_code=fingerprint.lang_code,
            system_lang_code=fingerprint.system_lang_code,
            # Proxy
            proxy=proxy_config,
            # Connection settings
            connection_retries=1,  # No retries - move to next proxy
            retry_delay=0,
            timeout=30,
            auto_reconnect=False,  # Manual control
        )
        
        return client
    
    async def send_code(
        self,
        phone: str,
        api_id: str,
        api_hash: str,
        use_proxy: bool = True,
    ) -> Dict[str, Any]:
        """
        Send verification code with fingerprinting and proxy.
        Returns: {'success': bool, 'phone_code_hash': str, 'fingerprint': dict, 'proxy': dict}
        """
        try:
            api_id_int = int(api_id)
        except ValueError:
            return {'success': False, 'error': 'API ID must be a number'}
        
        session_path = self._get_session_path(phone)
        
        # Disconnect existing pending client if any
        if phone in self._pending_clients:
            try:
                await self._pending_clients[phone].disconnect()
            except:
                pass
        
        # Generate device fingerprint
        fingerprint = fingerprint_generator.generate_random_fingerprint()
        self._fingerprints[phone] = fingerprint
        
        # Get proxy if enabled
        proxy = None
        if use_proxy:
            proxy = await proxy_manager.get_proxy_for_login(phone)
            if proxy:
                self._proxies_used[phone] = proxy
                print(f"🔄 Using proxy {proxy.host}:{proxy.port} ({proxy.proxy_type.value})")
            else:
                print("⚠️ No proxy available, connecting directly")
        
        print(f"📱 Device: {fingerprint.device_model}")
        print(f"📲 App: {fingerprint.app_name} {fingerprint.app_version}")
        print(f"🔧 System: {fingerprint.system_version}")
        
        try:
            client = self._create_client_with_fingerprint(
                session_path,
                api_id_int,
                api_hash,
                fingerprint,
                proxy,
            )
            
            try:
                await client.connect()
            except (ProxyConnectionError, ConnectionError, OSError) as e:
                # Proxy failed - mark as dead and skip
                if proxy:
                    print(f"❌ Proxy failed: {proxy.host}:{proxy.port}")
                    await proxy_manager.mark_proxy_dead(proxy.id)
                    
                    # Try to get next proxy
                    next_proxy = await proxy_manager.get_proxy_for_login(phone)
                    if next_proxy:
                        self._proxies_used[phone] = next_proxy
                        print(f"🔄 Trying next proxy: {next_proxy.host}:{next_proxy.port}")
                        
                        client = self._create_client_with_fingerprint(
                            session_path,
                            api_id_int,
                            api_hash,
                            fingerprint,
                            next_proxy,
                        )
                        await client.connect()
                        proxy = next_proxy
                    else:
                        # No more proxies, try direct connection
                        print("⚠️ No more proxies, trying direct connection")
                        client = self._create_client_with_fingerprint(
                            session_path,
                            api_id_int,
                            api_hash,
                            fingerprint,
                            None,
                        )
                        await client.connect()
            
            # Check if already authorized
            if await client.is_user_authorized():
                me = await client.get_me()
                self._clients[phone] = client
                
                # Save account info
                account_id = str(uuid.uuid4())[:8]
                account = {
                    'id': account_id,
                    'phone': phone,
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'first_name': me.first_name or '',
                    'last_name': me.last_name or '',
                    'username': me.username or '',
                    'user_id': me.id,
                    'session_file': session_path,
                    'status': 'online',
                    'device_model': fingerprint.device_model,
                    'app_name': fingerprint.app_name,
                }
                await db.save_account(account)
                
                return {
                    'success': True,
                    'already_authorized': True,
                    'account': account,
                    'fingerprint': fingerprint_generator.get_fingerprint_info(fingerprint),
                    'proxy': proxy.to_dict() if proxy else None,
                }
            
            # Send code
            sent_code = await client.send_code_request(phone)
            
            # Store pending client and login info
            self._pending_clients[phone] = client
            await db.save_pending_login(
                phone,
                api_id,
                api_hash,
                sent_code.phone_code_hash,
                fingerprint_info={
                    'device_model': fingerprint.device_model,
                    'system_version': fingerprint.system_version,
                    'app_version': fingerprint.app_version,
                    'app_name': fingerprint.app_name,
                    'lang_code': fingerprint.lang_code,
                },
                proxy_info=proxy.to_dict() if proxy else None,
            )
            
            return {
                'success': True,
                'phone_code_hash': sent_code.phone_code_hash,
                'code_type': type(sent_code.type).__name__,
                'fingerprint': fingerprint_generator.get_fingerprint_info(fingerprint),
                'proxy': proxy.to_dict() if proxy else None,
            }
            
        except PhoneNumberInvalidError:
            if proxy:
                await proxy_manager.release_proxy(phone, mark_dead=False)
            return {'success': False, 'error': 'Invalid phone number format'}
        except ApiIdInvalidError:
            if proxy:
                await proxy_manager.release_proxy(phone, mark_dead=False)
            return {'success': False, 'error': 'Invalid API ID or API Hash'}
        except FloodWaitError as e:
            if proxy:
                await proxy_manager.release_proxy(phone, mark_dead=False)
            return {'success': False, 'error': f'Too many attempts. Please wait {e.seconds} seconds'}
        except Exception as e:
            if proxy:
                await proxy_manager.mark_proxy_dead(proxy.id)
            return {'success': False, 'error': str(e)}
    
    async def verify_code(self, phone: str, code: str) -> Dict[str, Any]:
        """
        Verify the OTP code.
        Returns: {'success': bool, 'needs_2fa': bool, 'account': dict}
        """
        pending = await db.get_pending_login(phone)
        if not pending:
            return {'success': False, 'error': 'No pending login found. Please start over.'}
        
        client = self._pending_clients.get(phone)
        fingerprint = self._fingerprints.get(phone)
        proxy = self._proxies_used.get(phone)
        
        if not client:
            # Recreate client from pending info
            try:
                api_id_int = int(pending['api_id'])
                session_path = self._get_session_path(phone)
                
                # Recreate fingerprint if not available
                if not fingerprint:
                    fingerprint = fingerprint_generator.generate_random_fingerprint()
                    self._fingerprints[phone] = fingerprint
                
                client = self._create_client_with_fingerprint(
                    session_path,
                    api_id_int,
                    pending['api_hash'],
                    fingerprint,
                    proxy,
                )
                await client.connect()
                self._pending_clients[phone] = client
            except Exception as e:
                return {'success': False, 'error': f'Failed to reconnect: {str(e)}'}
        
        try:
            await client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=pending['phone_code_hash']
            )
            
            # Success - get user info
            me = await client.get_me()
            
            # Move to active clients
            self._clients[phone] = client
            if phone in self._pending_clients:
                del self._pending_clients[phone]
            await db.delete_pending_login(phone)
            
            # Clear proxy tracking (successful use)
            if phone in self._proxies_used:
                del self._proxies_used[phone]
            
            # Save account with fingerprint info
            account_id = str(uuid.uuid4())[:8]
            account = {
                'id': account_id,
                'phone': phone,
                'api_id': pending['api_id'],
                'api_hash': pending['api_hash'],
                'first_name': me.first_name or '',
                'last_name': me.last_name or '',
                'username': me.username or '',
                'user_id': me.id,
                'session_file': self._get_session_path(phone),
                'status': 'online',
                'device_model': fingerprint.device_model if fingerprint else None,
                'app_name': fingerprint.app_name if fingerprint else None,
            }
            await db.save_account(account)
            
            return {
                'success': True,
                'account': account,
                'fingerprint': fingerprint_generator.get_fingerprint_info(fingerprint) if fingerprint else None,
            }
            
        except SessionPasswordNeededError:
            return {'success': True, 'needs_2fa': True}
        except PhoneCodeInvalidError:
            return {'success': False, 'error': 'Invalid code. Please try again.'}
        except PhoneCodeExpiredError:
            return {'success': False, 'error': 'Code expired. Please request a new one.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def verify_2fa(self, phone: str, password: str) -> Dict[str, Any]:
        """
        Verify 2FA password.
        Returns: {'success': bool, 'account': dict}
        """
        pending = await db.get_pending_login(phone)
        if not pending:
            return {'success': False, 'error': 'No pending login found. Please start over.'}
        
        client = self._pending_clients.get(phone)
        fingerprint = self._fingerprints.get(phone)
        
        if not client:
            return {'success': False, 'error': 'Session expired. Please start over.'}
        
        try:
            await client.sign_in(password=password)
            
            # Success - get user info
            me = await client.get_me()
            
            # Move to active clients
            self._clients[phone] = client
            if phone in self._pending_clients:
                del self._pending_clients[phone]
            await db.delete_pending_login(phone)
            
            # Clear proxy tracking
            if phone in self._proxies_used:
                del self._proxies_used[phone]
            
            # Save account
            account_id = str(uuid.uuid4())[:8]
            account = {
                'id': account_id,
                'phone': phone,
                'api_id': pending['api_id'],
                'api_hash': pending['api_hash'],
                'first_name': me.first_name or '',
                'last_name': me.last_name or '',
                'username': me.username or '',
                'user_id': me.id,
                'session_file': self._get_session_path(phone),
                'status': 'online',
                'device_model': fingerprint.device_model if fingerprint else None,
                'app_name': fingerprint.app_name if fingerprint else None,
            }
            await db.save_account(account)
            
            return {
                'success': True,
                'account': account,
                'fingerprint': fingerprint_generator.get_fingerprint_info(fingerprint) if fingerprint else None,
            }
            
        except PasswordHashInvalidError:
            return {'success': False, 'error': 'Invalid password. Please try again.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_client(self, phone: str) -> Optional[TelegramClient]:
        """Get an active client for a phone number."""
        if phone in self._clients:
            client = self._clients[phone]
            if client.is_connected():
                return client
        
        # Try to restore from saved session
        account = await db.get_account_by_phone(phone)
        if account and account['session_file']:
            try:
                api_id_int = int(account['api_id'])
                
                # Generate new fingerprint for reconnection
                fingerprint = fingerprint_generator.generate_random_fingerprint()
                
                client = self._create_client_with_fingerprint(
                    account['session_file'],
                    api_id_int,
                    account['api_hash'],
                    fingerprint,
                    None,  # No proxy for reconnection
                )
                await client.connect()
                
                if await client.is_user_authorized():
                    self._clients[phone] = client
                    return client
            except Exception:
                pass
        
        return None
    
    async def check_account_status(self, account_id: str) -> Dict[str, Any]:
        """Check if an account is still valid and get its status."""
        account = await db.get_account(account_id)
        if not account:
            return {'success': False, 'error': 'Account not found'}
        
        client = await self.get_client(account['phone'])
        if not client:
            await db.update_account_status(account_id, 'offline')
            return {'success': True, 'status': 'offline', 'valid': False}
        
        try:
            me = await client.get_me()
            await db.update_account_status(account_id, 'online')
            return {
                'success': True,
                'status': 'online',
                'valid': True,
                'user': {
                    'id': me.id,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'username': me.username,
                    'phone': me.phone,
                }
            }
        except AuthKeyUnregisteredError:
            await db.update_account_status(account_id, 'offline')
            return {'success': True, 'status': 'offline', 'valid': False, 'error': 'Session expired'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def logout_account(self, account_id: str) -> Dict[str, Any]:
        """Logout and remove an account."""
        account = await db.get_account(account_id)
        if not account:
            return {'success': False, 'error': 'Account not found'}
        
        phone = account['phone']
        
        # Try to logout from Telegram
        client = await self.get_client(phone)
        if client:
            try:
                await client.log_out()
            except:
                pass
            
            try:
                await client.disconnect()
            except:
                pass
        
        # Remove from active clients
        if phone in self._clients:
            del self._clients[phone]
        
        # Clean up fingerprint and proxy tracking
        if phone in self._fingerprints:
            del self._fingerprints[phone]
        if phone in self._proxies_used:
            del self._proxies_used[phone]
        
        # Delete session file
        session_path = Path(account.get('session_file', ''))
        if session_path.exists():
            try:
                session_path.unlink()
                # Also try to delete .session file
                session_file = Path(str(session_path) + '.session')
                if session_file.exists():
                    session_file.unlink()
            except:
                pass
        
        # Remove from database
        await db.delete_account(account_id)
        
        return {'success': True}
    
    async def disconnect_all(self):
        """Disconnect all clients."""
        for client in self._clients.values():
            try:
                await client.disconnect()
            except:
                pass
        
        for client in self._pending_clients.values():
            try:
                await client.disconnect()
            except:
                pass
        
        self._clients.clear()
        self._pending_clients.clear()
        self._fingerprints.clear()
        self._proxies_used.clear()


# Global instance
telegram_manager = TelegramManager()
