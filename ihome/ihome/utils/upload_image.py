# 设置用户属性, 包括secret_id, secret_key, region
# appid已在配置中移除,请在参数Bucket中带上appid。Bucket由bucketname-appid组成
from qcloud_cos import CosConfig, CosS3Client

secret_id = 'AKIDASaYQ4YIuL6f3ENyfNrtm02qVFm5o7SY'  # 替换为用户的secret_id
secret_key = '3ufLPq2iBRSEZrmX4MPGj17SelglfQME'  # 替换为用户的secret_key
region = 'ap-shanghai'  # 替换为用户的region
token = None  # 使用临时密钥需要传入Token，默认为空,可不填
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token)  # 获取配置对象
client = CosS3Client(config)