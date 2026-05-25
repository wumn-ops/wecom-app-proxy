import base64
import hashlib
import struct
import time
from urllib.parse import unquote
from xml.etree import ElementTree

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class WXBizMsgCrypt:
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        self.token = token
        self.corp_id = corp_id
        self.key = base64.b64decode(encoding_aes_key + "=")

    def verify_url(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """验证回调 URL，解密 echostr 返回明文。
        echostr 应已由框架做过 URL 解码（FastAPI 自动处理）。
        """
        signature = self._signature(timestamp, nonce, echostr)
        if signature != msg_signature:
            raise ValueError(f"签名不匹配: 期望={msg_signature}, 计算={signature}")
        return self._decrypt(echostr)

    def decrypt_msg(self, msg_signature: str, timestamp: str, nonce: str, encrypted: str) -> str:
        """解密回调消息，返回明文字符串。"""
        signature = self._signature(timestamp, nonce, encrypted)
        if signature != msg_signature:
            raise ValueError("签名验证失败")
        return self._decrypt(encrypted)

    def _signature(self, timestamp: str, nonce: str, encrypt: str) -> str:
        """生成 SHA1 签名。"""
        raw = "".join(sorted([self.token, timestamp, nonce, encrypt]))
        return hashlib.sha1(raw.encode()).hexdigest()

    def _decrypt(self, encrypted: str) -> str:
        """AES-256-CBC 解密消息。"""
        ciphertext = base64.b64decode(encrypted)
        iv = self.key[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
        # 企业微信使用 PKCS#7 填充至 32 字节的倍数
        plaintext = unpad(cipher.decrypt(ciphertext), 32)

        # 格式: random(16) + msg_len(4) + msg + corpid
        msg_len = struct.unpack("!I", plaintext[16:20])[0]
        msg = plaintext[20:20 + msg_len].decode("utf-8")
        # corp_id_suffix = plaintext[20 + msg_len:].decode("utf-8")

        return msg

    def encrypt_msg(self, reply: str) -> str:
        """加密回复消息，返回加密后的 XML 字符串。"""
        random_bytes = hashlib.sha1(str(time.time()).encode()).digest()[:16]
        msg_bytes = reply.encode("utf-8")
        raw = random_bytes + struct.pack("!I", len(msg_bytes)) + msg_bytes + self.corp_id.encode("utf-8")

        # PKCS#7 填充至 32 字节的倍数（与企业微信服务端一致）
        pad_len = 32 - len(raw) % 32
        padded = raw + bytes([pad_len] * pad_len)

        iv = self.key[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()

        timestamp = str(int(time.time()))
        nonce = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
        signature = self._signature(timestamp, nonce, encrypted)

        return (
            f'<xml>'
            f'<Encrypt><![CDATA[{encrypted}]]></Encrypt>'
            f'<MsgSignature><![CDATA[{signature}]]></MsgSignature>'
            f'<TimeStamp>{timestamp}</TimeStamp>'
            f'<Nonce><![CDATA[{nonce}]]></Nonce>'
            f'</xml>'
        )


def parse_callback_xml(xml_str: str) -> dict:
    """解析回调 XML 消息，提取关键字段。"""
    root = ElementTree.fromstring(xml_str)
    result = {}
    for child in root:
        result[child.tag] = child.text
    return result
