# -*- coding: utf-8 -*-

import os
import sys
import json

from config import appconf
from config.exceptions import *
from typing import List

from alibabacloud_ecs20140526.client import Client as Ecs20140526Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class APIRequest:
    def __init__(self, logger):
        self.logger = logger

    @staticmethod
    def create_client() -> Ecs20140526Client:
        """
        使用AK&SK初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考。
        # 建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html。
        config = open_api_models.Config(
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID。,
            access_key_id=appconf['api']['ak_id'],
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET。,
            access_key_secret=appconf['api']['ak_secret']
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Ecs
        config.endpoint = appconf['api']['endpoint']
        return Ecs20140526Client(config)

    def submit_add(self, priority, src_ip, sg_region_id, sg_id) -> None:
        client = APIRequest.create_client()
        permissions_0 = ecs_20140526_models.AuthorizeSecurityGroupRequestPermissions(
            policy='accept',
            priority=f"{priority}",
            ip_protocol='ALL',
            source_cidr_ip=src_ip,
            port_range='-1/-1',
            description='AliyunDoorKeeper-AutoCreated'
        )
        authorize_security_group_request = ecs_20140526_models.AuthorizeSecurityGroupRequest(
            region_id=sg_region_id,
            security_group_id=sg_id,
            permissions=[
                permissions_0
            ]
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.authorize_security_group_with_options(authorize_security_group_request, runtime)
            if resp.status_code != 200:
                #some error happened
                self.logger.warn(f"Operation failed;"
                                 f"Action: add;"
                                 f"Params: priority: {priority}, src_ip: {src_ip}, sg_region_id: {sg_region_id}, sg_id: {sg_id};"
                                 f"{json.dumps(resp.body.to_map())}")
                raise E_API_Request_Error
            else:
                self.logger.info(f"Success;"
                                 f"Action: add;"
                                 f"Params: priority: {priority}, src_ip: {src_ip}, sg_region_id: {sg_region_id}, sg_id: {sg_id};")
                
        except Exception as error:
            self.logger.error(error.message)
            raise Exception(error.message)
    
    def submit_del(self, priority, src_ip, sg_region_id, sg_id) -> None:
        client = APIRequest.create_client()
        permissions_0 = ecs_20140526_models.RevokeSecurityGroupRequestPermissions(
            policy='accept',
            priority=f"{priority}",
            ip_protocol='ALL',
            source_cidr_ip=src_ip,
            port_range='-1/-1'
        )
        revoke_security_group_request = ecs_20140526_models.RevokeSecurityGroupRequest(
            region_id=sg_region_id,
            security_group_id=sg_id,
            permissions=[
                permissions_0
            ]
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = client.revoke_security_group_with_options(revoke_security_group_request, runtime)
            if resp.status_code != 200:
                #some error happened
                self.logger.warn(f"Operation failed;"
                                 f"Action: delete;"
                                 f"Params: priority: {priority}, src_ip: {src_ip}, sg_region_id: {sg_region_id}, sg_id: {sg_id};"
                                 f"{json.dumps(resp.body.to_map())}")
                raise E_API_Request_Error
            else:
                self.logger.info(f"Success;"
                                 f"Action: delete;"
                                 f"Params: priority: {priority}, src_ip: {src_ip}, sg_region_id: {sg_region_id}, sg_id: {sg_id};")
        except Exception as error:
            self.logger.error(error.message)
            raise Exception(error.message)