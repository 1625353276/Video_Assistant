#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大模型API独立测试脚本
Independent LLM API Test Script

专门用于测试通义千问大模型API的连接和响应质量
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from openai import OpenAI
from config.settings import settings


class LLMAPITester:
    """大模型API测试类"""
    
    def __init__(self):
        """初始化测试器"""
        self.llm_config = settings.get_model_config('llm')
        self.openai_config = self.llm_config.get('openai', {})
        
        # API配置
        self.api_key = self.openai_config.get('api_key')
        self.model_name = self.openai_config.get('model_name')
        self.base_url = self.openai_config.get('base_url')
        self.max_tokens = self.openai_config.get('max_tokens', 2000)
        self.temperature = self.openai_config.get('temperature', 0.7)
        
        # 创建客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # 测试统计
        self.test_results = []
        self.total_tests = 0
        self.successful_tests = 0
        
    def validate_configuration(self):
        """验证API配置"""
        print("=" * 60)
        print("1. API配置验证")
        print("=" * 60)
        
        config_items = [
            ("API Key", self.api_key),
            ("模型名称", self.model_name),
            ("API地址", self.base_url),
            ("最大Token数", self.max_tokens),
            ("温度参数", self.temperature)
        ]
        
        all_valid = True
        for name, value in config_items:
            if value:
                if name == "API Key":
                    print(f"   {name}: {str(value)[:20]}...")
                else:
                    print(f"   {name}: {value}")
            else:
                print(f"   {name}: ❌ 未配置")
                all_valid = False
        
        return all_valid
    
    def test_basic_connection(self):
        """测试基本连接"""
        print("\n" + "=" * 60)
        print("2. 基本连接测试")
        print("=" * 60)
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=50,
                temperature=0.7
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response and response.choices:
                answer = response.choices[0].message.content
                print(f"   ✅ 连接成功")
                print(f"   响应时间: {response_time:.2f}秒")
                print(f"   模型回答: {answer}")
                
                self.test_results.append({
                    "test": "基本连接",
                    "status": "成功",
                    "response_time": response_time,
                    "answer": answer
                })
                
                return True
            else:
                print("   ❌ 响应为空")
                return False
                
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            return False
    
    def test_knowledge_questions(self):
        """测试知识问答"""
        print("\n" + "=" * 60)
        print("3. 知识问答测试")
        print("=" * 60)
        
        questions = [
            "什么是人工智能？",
            "请解释机器学习的基本概念",
            "深度学习和传统机器学习有什么区别？"
        ]
        
        success_count = 0
        
        for i, question in enumerate(questions, 1):
            print(f"\n   问题 {i}: {question}")
            
            try:
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": question}],
                    max_tokens=300,
                    temperature=0.7
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response and response.choices:
                    answer = response.choices[0].message.content
                    print(f"   回答: {answer[:100]}...")
                    print(f"   响应时间: {response_time:.2f}秒")
                    print(f"   ✅ 问题 {i} 成功")
                    
                    self.test_results.append({
                        "test": f"知识问答{i}",
                        "status": "成功",
                        "question": question,
                        "response_time": response_time,
                        "answer": answer
                    })
                    
                    success_count += 1
                else:
                    print(f"   ❌ 问题 {i} 响应为空")
                    
            except Exception as e:
                print(f"   ❌ 问题 {i} 失败: {e}")
        
        print(f"\n   知识问答测试结果: {success_count}/{len(questions)} 成功")
        return success_count == len(questions)
    
    def test_creative_tasks(self):
        """测试创作任务"""
        print("\n" + "=" * 60)
        print("4. 创作任务测试")
        print("=" * 60)
        
        creative_prompts = [
            "写一首关于春天的诗",
            "创作一个关于科技的小故事",
            "用简单的语言解释什么是量子计算"
        ]
        
        success_count = 0
        
        for i, prompt in enumerate(creative_prompts, 1):
            print(f"\n   创作任务 {i}: {prompt}")
            
            try:
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.8
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response and response.choices:
                    answer = response.choices[0].message.content
                    print(f"   创作结果: {answer[:100]}...")
                    print(f"   响应时间: {response_time:.2f}秒")
                    print(f"   ✅ 创作任务 {i} 成功")
                    
                    self.test_results.append({
                        "test": f"创作任务{i}",
                        "status": "成功",
                        "prompt": prompt,
                        "response_time": response_time,
                        "answer": answer
                    })
                    
                    success_count += 1
                else:
                    print(f"   ❌ 创作任务 {i} 响应为空")
                    
            except Exception as e:
                print(f"   ❌ 创作任务 {i} 失败: {e}")
        
        print(f"\n   创作任务测试结果: {success_count}/{len(creative_prompts)} 成功")
        return success_count == len(creative_prompts)
    
    def test_conversation_ability(self):
        """测试对话能力"""
        print("\n" + "=" * 60)
        print("5. 对话能力测试")
        print("=" * 60)
        
        # 模拟多轮对话
        conversation = [
            {"role": "user", "content": "我叫小明，今年25岁"},
            {"role": "assistant", "content": "你好小明，很高兴认识你！"},
            {"role": "user", "content": "你还记得我的名字吗？"},
            {"role": "assistant", "content": "当然记得，你的名字是小明。"},
            {"role": "user", "content": "我今年多大了？"}
        ]
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=conversation,
                max_tokens=100,
                temperature=0.7
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response and response.choices:
                answer = response.choices[0].message.content
                print(f"   对话历史: 5轮对话")
                print(f"   当前问题: 我今年多大了？")
                print(f"   模型回答: {answer}")
                print(f"   响应时间: {response_time:.2f}秒")
                print(f"   ✅ 对话能力测试成功")
                
                # 检查是否正确回答了25岁
                if "25" in answer or "二十五" in answer:
                    print("   ✅ 上下文理解正确")
                else:
                    print("   ⚠️  上下文理解可能有误")
                
                self.test_results.append({
                    "test": "对话能力",
                    "status": "成功",
                    "response_time": response_time,
                    "answer": answer
                })
                
                return True
            else:
                print("   ❌ 对话测试响应为空")
                return False
                
        except Exception as e:
            print(f"   ❌ 对话能力测试失败: {e}")
            return False
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n" + "=" * 60)
        print("6. 错误处理测试")
        print("=" * 60)
        
        # 测试超长输入
        try:
            long_text = "请解释" + "很长的" * 1000 + "概念"
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": long_text}],
                max_tokens=50,
                temperature=0.7
            )
            
            print("   ✅ 超长输入处理正常")
            
        except Exception as e:
            print(f"   ⚠️  超长输入处理: {e}")
        
        # 测试空输入
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": ""}],
                max_tokens=50,
                temperature=0.7
            )
            
            print("   ✅ 空输入处理正常")
            
        except Exception as e:
            print(f"   ⚠️  空输入处理: {e}")
        
        return True
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("7. 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r["status"] == "成功"])
        
        print(f"   总测试数: {total_tests}")
        print(f"   成功测试: {successful_tests}")
        print(f"   失败测试: {total_tests - successful_tests}")
        print(f"   成功率: {successful_tests/total_tests*100:.1f}%")
        
        if successful_tests > 0:
            avg_response_time = sum(r.get("response_time", 0) for r in self.test_results if r["status"] == "成功") / successful_tests
            print(f"   平均响应时间: {avg_response_time:.2f}秒")
        
        print("\n   详细结果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "成功" else "❌"
            response_time = result.get("response_time", 0)
            print(f"   {status_icon} {result['test']}: {response_time:.2f}秒")
        
        # 总结
        print("\n" + "=" * 60)
        if successful_tests == total_tests:
            print("🎉 所有测试通过！大模型API工作正常！")
        elif successful_tests > total_tests * 0.8:
            print("⚠️  大部分测试通过，API基本可用，但有一些问题需要注意。")
        else:
            print("❌ 多个测试失败，API配置或模型可能有问题。")
        
        return successful_tests == total_tests
    
    def run_all_tests(self):
        """运行所有测试"""
        print("大模型API独立测试开始")
        print(f"测试模型: {self.model_name}")
        print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 验证配置
        if not self.validate_configuration():
            print("\n❌ 配置验证失败，测试终止")
            return False
        
        # 运行各项测试
        tests = [
            self.test_basic_connection,
            self.test_knowledge_questions,
            self.test_creative_tasks,
            self.test_conversation_ability,
            self.test_error_handling
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"\n❌ 测试异常: {e}")
        
        # 生成报告
        return self.generate_report()


def main():
    """主函数"""
    try:
        tester = LLMAPITester()
        success = tester.run_all_tests()
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
