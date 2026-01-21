#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gradio-Flask桥接器

实现Gradio界面与Flask API的通信
"""

import requests
import logging
from typing import Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class GradioBridge:
    """Gradio与Flask的桥接器"""
    
    def __init__(self, flask_base_url: str = "http://localhost:5001"):
        """
        初始化桥接器
        
        Args:
            flask_base_url: Flask应用基础URL
        """
        self.flask_base_url = flask_base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.current_user = None
        logger.info(f"Gradio桥接器初始化完成，Flask URL: {self.flask_base_url}")
    
    def test_connection(self) -> bool:
        """
        测试与Flask应用的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.session.get(f"{self.flask_base_url}/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("Flask连接测试成功")
                return True
            else:
                logger.error(f"Flask连接测试失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Flask连接测试异常: {e}")
            return False
    
    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            
        Returns:
            Dict[str, Any]: 注册结果
        """
        try:
            response = self.session.post(
                f"{self.flask_base_url}/api/auth/register",
                json={
                    'username': username,
                    'email': email,
                    'password': password
                },
                timeout=10
            )
            
            result = response.json()
            logger.info(f"用户注册结果: {result.get('message', '')}")
            return result
            
        except Exception as e:
            logger.error(f"用户注册异常: {e}")
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }
    
    def login_user(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            username_or_email: 用户名或邮箱
            password: 密码
            
        Returns:
            Dict[str, Any]: 登录结果
        """
        try:
            response = self.session.post(
                f"{self.flask_base_url}/api/auth/login",
                json={
                    'username_or_email': username_or_email,
                    'password': password
                },
                timeout=10
            )
            
            result = response.json()
            
            # 如果登录成功，保存令牌
            if result.get('success') and 'token' in result:
                self.token = result['token']
                self.current_user = {
                    'user_id': result.get('user_id'),
                    'username': result.get('username')
                }
                # 设置会话头部
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                logger.info(f"用户登录成功: {result.get('username')}")
            
            logger.info(f"用户登录结果: {result.get('message', '')}")
            return result
            
        except Exception as e:
            logger.error(f"用户登录异常: {e}")
            return {
                'success': False,
                'message': f'登录失败: {str(e)}'
            }
    
    def logout_user(self) -> Dict[str, Any]:
        """
        用户登出
        
        Returns:
            Dict[str, Any]: 登出结果
        """
        try:
            if not self.token:
                return {
                    'success': False,
                    'message': '未登录'
                }
            
            response = self.session.post(
                f"{self.flask_base_url}/api/auth/logout",
                timeout=10
            )
            
            result = response.json()
            
            # 清除本地令牌
            self.token = None
            self.current_user = None
            self.session.headers.pop('Authorization', None)
            
            logger.info(f"用户登出结果: {result.get('message', '')}")
            return result
            
        except Exception as e:
            logger.error(f"用户登出异常: {e}")
            return {
                'success': False,
                'message': f'登出失败: {str(e)}'
            }
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        获取用户资料
        
        Returns:
            Dict[str, Any]: 用户资料
        """
        try:
            if not self.token:
                return {
                    'success': False,
                    'message': '未登录'
                }
            
            response = self.session.get(
                f"{self.flask_base_url}/api/auth/profile",
                timeout=10
            )
            
            result = response.json()
            logger.info(f"获取用户资料结果: {result.get('message', '')}")
            return result
            
        except Exception as e:
            logger.error(f"获取用户资料异常: {e}")
            return {
                'success': False,
                'message': f'获取用户资料失败: {str(e)}'
            }
    
    def update_user_profile(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户资料
        
        Args:
            updates: 更新数据
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            if not self.token:
                return {
                    'success': False,
                    'message': '未登录'
                }
            
            response = self.session.put(
                f"{self.flask_base_url}/api/auth/profile",
                json=updates,
                timeout=10
            )
            
            result = response.json()
            logger.info(f"更新用户资料结果: {result.get('message', '')}")
            return result
            
        except Exception as e:
            logger.error(f"更新用户资料异常: {e}")
            return {
                'success': False,
                'message': f'更新用户资料失败: {str(e)}'
            }
    
    def verify_token(self) -> Dict[str, Any]:
        """
        验证当前令牌
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            if not self.token:
                return {
                    'success': False,
                    'message': '无令牌'
                }
            
            response = self.session.post(
                f"{self.flask_base_url}/api/auth/verify",
                json={'token': self.token},
                timeout=10
            )
            
            result = response.json()
            logger.info(f"验证令牌结果: {result.get('message', '')}")
            return result
            
        except Exception as e:
            logger.error(f"验证令牌异常: {e}")
            return {
                'success': False,
                'message': f'验证令牌失败: {str(e)}'
            }
    
    def is_logged_in(self) -> bool:
        """
        检查是否已登录
        
        Returns:
            bool: 是否已登录
        """
        return self.token is not None
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        获取当前用户信息
        
        Returns:
            Optional[Dict[str, Any]]: 当前用户信息
        """
        return self.current_user
    
    def create_user_data_dir(self, user_id: str) -> str:
        """
        为用户创建数据目录
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 数据目录路径
        """
        import os
        from pathlib import Path
        
        user_data_dir = Path(f"data/users/{user_id}")
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (user_data_dir / "videos").mkdir(exist_ok=True)
        (user_data_dir / "transcripts").mkdir(exist_ok=True)
        (user_data_dir / "conversations").mkdir(exist_ok=True)
        (user_data_dir / "sessions").mkdir(exist_ok=True)
        
        logger.info(f"用户数据目录创建完成: {user_data_dir}")
        return str(user_data_dir)
    
    def get_user_data_dir(self, user_id: str) -> str:
        """
        获取用户数据目录路径
        
        Args:
            user_id: 用户ID
            
        Returns:
            str: 数据目录路径
        """
        from pathlib import Path
        
        user_data_dir = Path(f"data/users/{user_id}")
        return str(user_data_dir)
    
    def upload_video_to_user_space(self, user_id: str, video_file_path: str) -> Dict[str, Any]:
        """
        上传视频到用户空间
        
        Args:
            user_id: 用户ID
            video_file_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 上传结果
        """
        try:
            import os
            import shutil
            from pathlib import Path
            
            # 获取用户视频目录
            user_videos_dir = Path(self.get_user_data_dir(user_id)) / "videos"
            
            # 复制视频文件到用户目录
            video_path = Path(video_file_path)
            dest_path = user_videos_dir / video_path.name
            
            shutil.copy2(video_file_path, dest_path)
            
            logger.info(f"视频上传到用户空间成功: {dest_path}")
            return {
                'success': True,
                'message': '视频上传成功',
                'video_path': str(dest_path)
            }
            
        except Exception as e:
            logger.error(f"视频上传到用户空间失败: {e}")
            return {
                'success': False,
                'message': f'视频上传失败: {str(e)}'
            }
    
    def get_user_videos(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户视频列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 视频列表
        """
        try:
            from pathlib import Path
            
            user_videos_dir = Path(self.get_user_data_dir(user_id)) / "videos"
            
            if not user_videos_dir.exists():
                return {
                    'success': True,
                    'videos': [],
                    'message': '用户视频目录不存在'
                }
            
            videos = []
            for video_file in user_videos_dir.glob("*"):
                if video_file.is_file():
                    stat = video_file.stat()
                    videos.append({
                        'filename': video_file.name,
                        'path': str(video_file),
                        'size': stat.st_size,
                        'created_time': stat.st_ctime
                    })
            
            logger.info(f"获取用户视频列表成功: {len(videos)} 个视频")
            return {
                'success': True,
                'videos': videos,
                'count': len(videos)
            }
            
        except Exception as e:
            logger.error(f"获取用户视频列表失败: {e}")
            return {
                'success': False,
                'message': f'获取视频列表失败: {str(e)}'
            }