#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎时效性分析系统
自动化分析引擎test的时效性表现，并诊断问题原因
"""

import json
import os
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
import argparse
import logging


class DataPreprocessor:
    """数据预处理模块"""
    
    def __init__(self, config):
        self.config = config
    
    def load_data(self, file_path: str) -> List[Dict]:
        """加载数据"""
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
    
    def preprocess(self, raw_data: List[Dict]) -> List[Dict]:
        """预处理：计算doc年龄等基础字段"""
        processed_data = []
        
        for item in raw_data:
            try:
                processed_item = self._process_single_query(item)
                processed_data.append(processed_item)
            except Exception as e:
                logging.warning(f"处理query失败 '{item.get('query', 'unknown')}': {e}")
                continue
        
        return processed_data
    
    def _process_single_query(self, item: Dict) -> Dict:
        """处理单个query"""
        search_time = pd.to_datetime(item['search_time'])
        
        # 处理三个引擎的文档
        for engine_name in ['engine1', 'engine2', 'test']:
            if engine_name in item and 'docs' in item[engine_name]:
                item[engine_name]['docs'] = self._add_doc_age(
                    item[engine_name]['docs'], search_time
                )
        
        return item
    
    def _add_doc_age(self, docs: List[Dict], search_time) -> List[Dict]:
        """添加doc年龄字段"""
        for doc in docs:
            try:
                publish_time = pd.to_datetime(doc['publish_time'])
                doc['age_days'] = (search_time - publish_time).total_seconds() / 86400
                doc['age_hours'] = (search_time - publish_time).total_seconds() / 3600
            except Exception as e:
                logging.warning(f"计算doc年龄失败: {e}")
                doc['age_days'] = 999  # 默认值
                doc['age_hours'] = 999 * 24
        return docs


class FeatureExtractor:
    """特征提取模块"""
    
    def __init__(self, config):
        self.config = config
        self.top_k_values = config['features']['top_k_values']
        self.time_windows = config['features']['time_windows']
    
    def extract_features(self, query_data: Dict) -> Dict:
        """提取单个query的所有特征"""
        features = {
            'query': query_data['query'],
            'search_time': query_data['search_time']
        }
        
        # 提取三个引擎的特征
        for engine_name in ['engine1', 'engine2', 'test']:
            if engine_name not in query_data:
                continue
                
            engine_data = query_data[engine_name]
            docs = engine_data.get('docs', [])
            
            prefix = f"{engine_name}_"
            
            # 基础统计特征
            features[f"{prefix}total_docs"] = len(docs)
            
            # 不同TOP-K的特征
            for k in self.top_k_values:
                top_k_docs = docs[:k] if len(docs) >= k else docs
                if top_k_docs:
                    features.update(
                        self._calc_topk_features(top_k_docs, f"{prefix}top{k}")
                    )
            
            # 时效卡特征（仅engine1和engine2）
            if engine_name in ['engine1', 'engine2']:
                features[f"{prefix}has_card"] = engine_data.get('has_timeliness_card', False)
        
        # 计算baseline特征（engine1和engine2的平均）
        features.update(self._calc_baseline_features(features))
        
        # 计算test特有特征
        if 'test' in query_data:
            features['test_query_level'] = query_data['test'].get('query_timeliness_level', '其他时效')
            features.update(self._calc_test_specific_features(query_data['test'].get('docs', [])))
        
        return features
    
    def _calc_topk_features(self, docs: List[Dict], prefix: str) -> Dict:
        """计算TOP-K的统计特征"""
        if not docs:
            return self._empty_topk_features(prefix)
        
        ages = [doc['age_days'] for doc in docs]
        
        features = {
            f"{prefix}_avg_age": float(np.mean(ages)),
            f"{prefix}_median_age": float(np.median(ages)),
            f"{prefix}_min_age": float(np.min(ages)),
            f"{prefix}_max_age": float(np.max(ages)),
            f"{prefix}_std_age": float(np.std(ages)) if len(ages) > 1 else 0.0,
        }
        
        # 不同时间窗口的新鲜文档占比
        for window in self.time_windows:
            fresh_count = sum(1 for age in ages if age <= window)
            features[f"{prefix}_fresh_{window}d_ratio"] = fresh_count / len(ages)
        
        return features
    
    def _empty_topk_features(self, prefix: str) -> Dict:
        """返回空特征"""
        features = {
            f"{prefix}_avg_age": 999.0,
            f"{prefix}_median_age": 999.0,
            f"{prefix}_min_age": 999.0,
            f"{prefix}_max_age": 999.0,
            f"{prefix}_std_age": 0.0,
        }
        for window in self.time_windows:
            features[f"{prefix}_fresh_{window}d_ratio"] = 0.0
        return features
    
    def _calc_baseline_features(self, features: Dict) -> Dict:
        """计算baseline特征（engine1和engine2的平均）"""
        baseline = {}
        
        for k in self.top_k_values:
            # 平均doc年龄
            e1_avg = features.get(f"engine1_top{k}_avg_age", 999)
            e2_avg = features.get(f"engine2_top{k}_avg_age", 999)
            baseline[f"baseline_top{k}_avg_age"] = (e1_avg + e2_avg) / 2
            
            # 最小doc年龄
            e1_min = features.get(f"engine1_top{k}_min_age", 999)
            e2_min = features.get(f"engine2_top{k}_min_age", 999)
            baseline[f"baseline_top{k}_min_age"] = min(e1_min, e2_min)
            
            # 新鲜文档占比
            for window in self.time_windows:
                e1_ratio = features.get(f"engine1_top{k}_fresh_{window}d_ratio", 0)
                e2_ratio = features.get(f"engine2_top{k}_fresh_{window}d_ratio", 0)
                baseline[f"baseline_top{k}_fresh_{window}d_ratio"] = (e1_ratio + e2_ratio) / 2
        
        # 时效卡标签
        baseline['baseline_has_timeliness_need'] = (
            features.get('engine1_has_card', False) or 
            features.get('engine2_has_card', False)
        )
        
        return baseline
    
    def _calc_test_specific_features(self, test_docs: List[Dict]) -> Dict:
        """计算test引擎特有的特征（与时效性打分相关）"""
        if not test_docs:
            return {
                'test_score_age_correlation': 0.0,
                'test_score_std': 0.0,
                'test_fresh_avg_score': 0.0,
                'test_old_avg_score': 0.0,
                'test_fresh_old_gap': 0.0,
                'test_fresh_doc_count': 0,
                'test_old_doc_count': 0
            }
        
        ages = [doc['age_days'] for doc in test_docs]
        scores = [doc.get('timeliness_score', 0) for doc in test_docs]
        
        # 计算相关系数
        correlation = 0.0
        if len(ages) > 1 and np.std(ages) > 0 and np.std(scores) > 0:
            correlation = float(np.corrcoef(ages, scores)[0, 1])
        
        # 新旧文档打分对比
        fresh_threshold = self.config['features']['fresh_threshold']
        old_threshold = self.config['features']['old_threshold']
        
        fresh_docs = [doc for doc in test_docs if doc['age_days'] <= fresh_threshold]
        old_docs = [doc for doc in test_docs if doc['age_days'] > old_threshold]
        
        fresh_avg_score = float(np.mean([d.get('timeliness_score', 0) for d in fresh_docs])) if fresh_docs else 0.0
        old_avg_score = float(np.mean([d.get('timeliness_score', 0) for d in old_docs])) if old_docs else 0.0
        
        return {
            'test_score_age_correlation': correlation,
            'test_score_std': float(np.std(scores)),
            'test_fresh_avg_score': fresh_avg_score,
            'test_old_avg_score': old_avg_score,
            'test_fresh_old_gap': fresh_avg_score - old_avg_score,
            'test_fresh_doc_count': len(fresh_docs),
            'test_old_doc_count': len(old_docs)
        }


class TimelinessEvaluator:
    """时效性评估模块"""
    
    def __init__(self, config):
        self.config = config
        self.weights = config['thresholds']['weights']
        self.poor_threshold = config['thresholds']['poor_score']
        self.fair_threshold = config['thresholds']['fair_score']
    
    def evaluate(self, features: Dict) -> Dict:
        """评估时效性得分"""
        scores = {}
        
        # 维度1：平均doc年龄得分
        scores['dimension1_avg_age'] = self._calc_avg_age_score(features)
        
        # 维度2：新鲜文档覆盖率得分
        scores['dimension2_fresh_ratio'] = self._calc_fresh_ratio_score(features)
        
        # 维度3：最新文档发现能力得分
        scores['dimension3_min_age'] = self._calc_min_age_score(features)
        
        # 维度4：时效卡得分
        scores['dimension4_card'] = self._calc_card_score(features)
        
        # 综合得分
        total_score = (
            scores['dimension1_avg_age'] * self.weights['avg_age'] +
            scores['dimension2_fresh_ratio'] * self.weights['fresh_ratio'] +
            scores['dimension3_min_age'] * self.weights['min_age'] +
            scores['dimension4_card'] * self.weights['card']
        )
        
        # 判定标签
        if total_score >= self.fair_threshold:
            label = "时效性良好"
        elif total_score >= self.poor_threshold:
            label = "时效性一般"
        else:
            label = "时效性差"
        
        return {
            'total_score': round(total_score, 2),
            'label': label,
            'dimension_scores': {k: round(v, 2) for k, v in scores.items()}
        }
    
    def _calc_avg_age_score(self, features: Dict) -> float:
        """计算平均doc年龄得分（使用TOP5）"""
        test_avg = features.get('test_top5_avg_age', 999)
        baseline_avg = features.get('baseline_top5_avg_age', 999)
        
        if baseline_avg == 0 or baseline_avg == 999:
            return 100.0
        
        age_ratio = test_avg / baseline_avg
        
        if age_ratio <= 1.0:
            return 100.0
        elif age_ratio <= 1.5:
            return 100.0 - (age_ratio - 1.0) * 100
        elif age_ratio <= 2.0:
            return 50.0 - (age_ratio - 1.5) * 60
        else:
            return max(0.0, 20.0 - (age_ratio - 2.0) * 20)
    
    def _calc_fresh_ratio_score(self, features: Dict) -> float:
        """计算新鲜文档覆盖率得分（使用7天窗口）"""
        test_ratio = features.get('test_top5_fresh_7d_ratio', 0)
        baseline_ratio = features.get('baseline_top5_fresh_7d_ratio', 0)
        
        fresh_diff = test_ratio - baseline_ratio
        
        if fresh_diff >= 0:
            return 100.0
        elif fresh_diff >= -0.2:
            return 100.0 + fresh_diff * 250
        elif fresh_diff >= -0.4:
            return 50.0 + (fresh_diff + 0.2) * 150
        else:
            return max(0.0, 50.0 + (fresh_diff + 0.4) * 100)
    
    def _calc_min_age_score(self, features: Dict) -> float:
        """计算最新文档发现能力得分"""
        test_min = features.get('test_top5_min_age', 999)
        baseline_min = features.get('baseline_top5_min_age', 999)
        
        if baseline_min == 0 or baseline_min == 999:
            return 100.0
        
        min_age_ratio = test_min / baseline_min
        
        if min_age_ratio <= 1.2:
            return 100.0
        elif min_age_ratio <= 2.0:
            return 100.0 - (min_age_ratio - 1.2) * 62.5
        elif min_age_ratio <= 5.0:
            return 50.0 - (min_age_ratio - 2.0) * 13.3
        else:
            return 0.0
    
    def _calc_card_score(self, features: Dict) -> float:
        """计算时效卡得分"""
        # 简化处理：如果baseline不需要时效卡，满分
        if not features.get('baseline_has_timeliness_need', False):
            return 100.0
        
        # 否则根据其他维度表现给分
        return 100.0


class ReasonDiagnoser:
    """原因诊断模块"""
    
    def __init__(self, config):
        self.config = config
        self.thresholds = config['thresholds']
    
    def diagnose(self, query_data: Dict, features: Dict, evaluation: Dict) -> Dict:
        """诊断时效性差的原因"""
        # 只诊断时效性差的query
        if evaluation['label'] != "时效性差":
            return None
        
        # 按优先级诊断
        # 原因1：识别错误（最高优先级）
        reason1 = self._diagnose_recognition_error(query_data, features)
        if reason1['flag']:
            return reason1
        
        # 原因2：打分公式（第二优先级）
        reason2 = self._diagnose_scoring_formula(query_data, features)
        if reason2['flag']:
            return reason2
        
        # 原因3：融合策略（第三优先级）
        reason3 = self._diagnose_fusion_strategy(query_data, features)
        if reason3['flag']:
            return reason3
        
        # 如果都不是，标记为未知原因
        return {
            'flag': True,
            'reason': '原因未知',
            'sub_reason': '无法定位具体原因',
            'details': {}
        }
    
    def _diagnose_recognition_error(self, query_data: Dict, features: Dict) -> Dict:
        """诊断原因1：query时效性等级识别错误"""
        cfg = self.thresholds['recognition']
        
        # 判断是否应该是高时效
        should_be_high = False
        confidence = "低"
        evidence = []
        
        # 证据1：时效卡
        has_both_cards = features.get('engine1_has_card', False) and features.get('engine2_has_card', False)
        has_one_card = features.get('engine1_has_card', False) or features.get('engine2_has_card', False)
        
        if has_both_cards:
            should_be_high = True
            confidence = "高"
            evidence.append("两个权威引擎都有时效卡")
        elif has_one_card:
            confidence = "中"
            evidence.append("一个权威引擎有时效卡")
        
        # 证据2：平均doc年龄
        baseline_avg = features.get('baseline_top5_avg_age', 999)
        
        if baseline_avg <= cfg['fresh_age_strong']:
            freshness_pref = "强"
            evidence.append(f"权威引擎平均doc年龄≤{cfg['fresh_age_strong']}天")
            if confidence == "中":
                should_be_high = True
        elif baseline_avg <= cfg['fresh_age_medium']:
            freshness_pref = "中"
            evidence.append(f"权威引擎平均doc年龄≤{cfg['fresh_age_medium']}天")
        else:
            freshness_pref = "弱"
        
        # 证据3：新鲜文档占比
        baseline_fresh_ratio = features.get('baseline_top5_fresh_7d_ratio', 0)
        
        if baseline_fresh_ratio >= cfg['fresh_ratio_high']:
            fresh_concentration = "高"
            evidence.append(f"权威引擎新鲜文档占比≥{cfg['fresh_ratio_high']:.0%}")
            if freshness_pref == "强":
                should_be_high = True
        elif baseline_fresh_ratio >= cfg['fresh_ratio_medium']:
            fresh_concentration = "中"
        else:
            fresh_concentration = "低"
        
        # 判定
        test_level = features.get('test_query_level', '其他时效')
        
        if should_be_high and test_level == "其他时效":
            return {
                'flag': True,
                'reason': '原因1_识别错误',
                'sub_reason': '高时效query被误判为其他时效',
                'details': {
                    '时效性需求置信度': confidence,
                    '证据': evidence,
                    'baseline平均doc年龄': round(baseline_avg, 2),
                    'baseline新鲜文档占比': round(baseline_fresh_ratio, 2),
                    'engine1有时效卡': features.get('engine1_has_card', False),
                    'engine2有时效卡': features.get('engine2_has_card', False),
                    'test判别结果': test_level,
                    '正确判别': '高时效'
                }
            }
        
        return {'flag': False}
    
    def _diagnose_scoring_formula(self, query_data: Dict, features: Dict) -> Dict:
        """诊断原因2：doc时效性打分公式不合理"""
        test_level = features.get('test_query_level', '其他时效')
        
        # 根据query类型选择阈值
        if test_level == "高时效":
            cfg = self.thresholds['scoring']['high_timeliness']
        else:
            cfg = self.thresholds['scoring']['other_timeliness']
        
        problems = []
        
        # 检查1：相关系数
        corr = features.get('test_score_age_correlation', 0)
        if corr < cfg['corr_min'] or corr > cfg['corr_max']:
            problems.append({
                '问题': 'doc年龄与时效性打分相关性异常',
                '实际相关系数': round(corr, 3),
                '期望范围': f"[{cfg['corr_min']}, {cfg['corr_max']}]",
                '严重程度': 'high'
            })
        
        # 检查2：打分区分度
        score_std = features.get('test_score_std', 0)
        if score_std < cfg['std_min']:
            problems.append({
                '问题': '时效性打分区分度不足',
                '实际标准差': round(score_std, 3),
                '最小期望': cfg['std_min'],
                '严重程度': 'medium'
            })
        
        # 检查3：新旧文档打分差距
        gap = features.get('test_fresh_old_gap', 0)
        fresh_count = features.get('test_fresh_doc_count', 0)
        old_count = features.get('test_old_doc_count', 0)
        
        if fresh_count > 0 and old_count > 0:
            if gap < cfg['gap_min']:
                problems.append({
                    '问题': '新旧文档打分差距不足',
                    '实际差距': round(gap, 3),
                    '最小期望': cfg['gap_min'],
                    '新文档平均分': round(features.get('test_fresh_avg_score', 0), 3),
                    '旧文档平均分': round(features.get('test_old_avg_score', 0), 3),
                    '严重程度': 'high'
                })
        
        # 检查4：新文档排序位置
        test_fresh_ratio = features.get('test_top5_fresh_7d_ratio', 0)
        baseline_fresh_ratio = features.get('baseline_top5_fresh_7d_ratio', 0)
        
        if baseline_fresh_ratio > 0 and test_fresh_ratio < baseline_fresh_ratio * (1 / self.thresholds['scoring']['rank_ratio_max']):
            problems.append({
                '问题': '新文档打分导致排序靠后',
                'test新文档占比': round(test_fresh_ratio, 3),
                'baseline新文档占比': round(baseline_fresh_ratio, 3),
                '差距比例': round(baseline_fresh_ratio / test_fresh_ratio if test_fresh_ratio > 0 else 999, 2),
                '严重程度': 'high'
            })
        
        if problems:
            return {
                'flag': True,
                'reason': '原因2_打分公式',
                'sub_reason': '时效性打分计算公式不合理',
                'details': {
                    'query时效性等级': test_level,
                    '问题列表': problems,
                    '问题数量': len(problems)
                }
            }
        
        return {'flag': False}
    
    def _diagnose_fusion_strategy(self, query_data: Dict, features: Dict) -> Dict:
        """诊断原因3：融合策略不合理"""
        cfg = self.thresholds['fusion']
        problems = []
        
        # 检查1：计算理想排序的提升潜力
        test_docs = query_data.get('test', {}).get('docs', [])
        
        if len(test_docs) >= 5:
            # 按时效性打分排序（理想排序）
            sorted_docs = sorted(test_docs, key=lambda x: x.get('timeliness_score', 0), reverse=True)
            ideal_top5_avg_age = np.mean([doc['age_days'] for doc in sorted_docs[:5]])
            
            # 当前排序（假设按返回顺序）
            actual_top5_avg_age = features.get('test_top5_avg_age', 999)
            
            if actual_top5_avg_age > 0 and ideal_top5_avg_age < actual_top5_avg_age:
                improvement_potential = (actual_top5_avg_age - ideal_top5_avg_age) / actual_top5_avg_age
                
                if improvement_potential > cfg['improvement_potential']:
                    problems.append({
                        '问题': '时效性打分在融合中权重过低',
                        '当前平均doc年龄': round(actual_top5_avg_age, 2),
                        '理想平均doc年龄': round(ideal_top5_avg_age, 2),
                        '提升潜力': f"{improvement_potential:.1%}",
                        '严重程度': 'high'
                    })
        
        # 检查2：新文档是否被压制
        fresh_threshold = self.config['features']['fresh_threshold']
        fresh_docs = [doc for doc in test_docs if doc['age_days'] <= fresh_threshold]
        
        if fresh_docs and len(test_docs) >= 10:
            # 新文档的平均打分
            fresh_avg_score = np.mean([doc.get('timeliness_score', 0) for doc in fresh_docs])
            all_avg_score = np.mean([doc.get('timeliness_score', 0) for doc in test_docs])
            
            # 新文档在top10中的占比
            fresh_in_top10 = sum(1 for doc in test_docs[:10] if doc['age_days'] <= fresh_threshold)
            fresh_ratio_in_top10 = fresh_in_top10 / min(10, len(test_docs))
            
            expected_ratio = len(fresh_docs) / len(test_docs)
            
            if fresh_avg_score > all_avg_score + 0.1 and fresh_ratio_in_top10 < expected_ratio * cfg['fresh_suppression_ratio']:
                problems.append({
                    '问题': '新文档召回但被融合策略压制',
                    '新文档平均时效分': round(fresh_avg_score, 3),
                    '全部文档平均分': round(all_avg_score, 3),
                    '新文档在top10占比': round(fresh_ratio_in_top10, 3),
                    '期望占比': round(expected_ratio, 3),
                    '严重程度': 'medium'
                })
        
        if problems:
            return {
                'flag': True,
                'reason': '原因3_融合策略',
                'sub_reason': '时效性打分融合权重不合理',
                'details': {
                    '问题列表': problems,
                    '问题数量': len(problems)
                }
            }
        
        return {'flag': False}


class ReportGenerator:
    """报告生成模块"""
    
    def __init__(self, config):
        self.config = config
    
    def generate(self, all_results: List[Dict]) -> Dict:
        """生成分析报告"""
        # 汇总统计
        summary = self._generate_summary(all_results)
        
        # 筛选时效性差的query
        poor_queries = [
            r for r in all_results 
            if r['evaluation']['label'] == '时效性差'
        ]
        
        # 生成建议
        recommendations = self._generate_recommendations(poor_queries)
        
        report = {
            'summary': summary,
            'poor_queries': poor_queries,
            'recommendations': recommendations
        }
        
        # 根据配置决定是否包含所有结果
        if self.config['output']['detail_level'] == 'verbose':
            report['all_results'] = all_results
        
        return report
    
    def _generate_summary(self, all_results: List[Dict]) -> Dict:
        """生成汇总统计"""
        total = len(all_results)
        poor_count = sum(1 for r in all_results if r['evaluation']['label'] == '时效性差')
        
        # 统计原因分布
        reason_counts = {
            '原因1_识别错误': 0,
            '原因2_打分公式': 0,
            '原因3_融合策略': 0,
            '原因未知': 0
        }
        
        for r in all_results:
            if r['evaluation']['label'] == '时效性差' and r.get('diagnosis'):
                reason = r['diagnosis']['reason']
                if reason in reason_counts:
                    reason_counts[reason] += 1
        
        return {
            'total_queries': total,
            'poor_timeliness_queries': poor_count,
            'poor_ratio': round(poor_count / total, 4) if total > 0 else 0,
            'reason_distribution': {
                k: {
                    'count': v, 
                    'ratio': round(v / poor_count, 4) if poor_count > 0 else 0
                }
                for k, v in reason_counts.items()
            }
        }
    
    def _generate_recommendations(self, poor_queries: List[Dict]) -> List[Dict]:
        """生成改进建议"""
        # 统计各类问题
        reason_queries = {
            '原因1_识别错误': [],
            '原因2_打分公式': [],
            '原因3_融合策略': []
        }
        
        for q in poor_queries:
            if q.get('diagnosis'):
                reason = q['diagnosis']['reason']
                if reason in reason_queries:
                    reason_queries[reason].append(q['query'])
        
        recommendations = []
        
        # 原因1建议
        if reason_queries['原因1_识别错误']:
            recommendations.append({
                '优先级': 'P0',
                '问题': 'Query时效性等级识别错误',
                '影响范围': f"{len(reason_queries['原因1_识别错误'])}个query",
                '建议': [
                    '优化query时效性等级识别模型',
                    '增加时效性关键词特征（如"最新"、"今天"、日期等）',
                    '参考权威引擎的时效卡信号作为训练标签',
                    '考虑query的时间敏感度和搜索意图'
                ],
                '示例query': reason_queries['原因1_识别错误'][:5]
            })
        
        # 原因2建议
        if reason_queries['原因2_打分公式']:
            recommendations.append({
                '优先级': 'P1',
                '问题': 'Doc时效性打分公式不合理',
                '影响范围': f"{len(reason_queries['原因2_打分公式'])}个query",
                '建议': [
                    '调整高时效query的doc时效性打分公式',
                    '增大新旧文档的打分差距（建议≥0.3）',
                    '优化时效性打分的衰减函数（前期快速衰减，后期放缓）',
                    '提升打分区分度，避免打分过于集中'
                ],
                '示例query': reason_queries['原因2_打分公式'][:5]
            })
        
        # 原因3建议
        if reason_queries['原因3_融合策略']:
            recommendations.append({
                '优先级': 'P2',
                '问题': '时效性打分融合权重不合理',
                '影响范围': f"{len(reason_queries['原因3_融合策略'])}个query",
                '建议': [
                    '提升时效性打分在最终排序中的权重',
                    '针对高时效query，使用更高的时效性权重',
                    '避免相关性或质量打分过度压制新文档',
                    '考虑使用query类型自适应的融合策略'
                ],
                '示例query': reason_queries['原因3_融合策略'][:5]
            })
        
        return recommendations
    
    def export_json(self, report: Dict, output_path: str):
        """导出JSON格式报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logging.info(f"JSON报告已导出: {output_path}")
    
    def export_csv(self, report: Dict, output_path: str):
        """导出CSV格式（仅时效性差的query）"""
        poor_queries = report['poor_queries']
        
        rows = []
        for q in poor_queries:
            rows.append({
                'query': q['query'],
                'timeliness_score': q['evaluation']['total_score'],
                'label': q['evaluation']['label'],
                'primary_reason': q.get('diagnosis', {}).get('reason', ''),
                'sub_reason': q.get('diagnosis', {}).get('sub_reason', ''),
                'test_avg_age_top5': q['features'].get('test_top5_avg_age', 0),
                'baseline_avg_age_top5': q['features'].get('baseline_top5_avg_age', 0),
                'test_query_level': q['features'].get('test_query_level', ''),
                'test_fresh_ratio_7d': q['features'].get('test_top5_fresh_7d_ratio', 0),
                'baseline_fresh_ratio_7d': q['features'].get('baseline_top5_fresh_7d_ratio', 0)
            })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logging.info(f"CSV报告已导出: {output_path}")
    
    def export_html(self, report: Dict, output_path: str):
        """导出HTML格式报告"""
        html = self._generate_html(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        logging.info(f"HTML报告已导出: {output_path}")
    
    def _generate_html(self, report: Dict) -> str:
        """生成HTML报告"""
        summary = report['summary']
        recommendations = report['recommendations']
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>时效性分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background-color: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 24px; color: #4CAF50; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .recommendation {{ background-color: #fff3e0; padding: 15px; margin: 15px 0; border-left: 4px solid #ff9800; border-radius: 4px; }}
        .priority {{ display: inline-block; padding: 4px 8px; border-radius: 3px; font-weight: bold; }}
        .p0 {{ background-color: #f44336; color: white; }}
        .p1 {{ background-color: #ff9800; color: white; }}
        .p2 {{ background-color: #2196F3; color: white; }}
        ul {{ line-height: 1.8; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 搜索引擎时效性分析报告</h1>
        
        <div class="summary">
            <h2>📊 总体概况</h2>
            <div class="metric">
                <div class="metric-label">总query数</div>
                <div class="metric-value">{summary['total_queries']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">时效性差</div>
                <div class="metric-value">{summary['poor_timeliness_queries']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">占比</div>
                <div class="metric-value">{summary['poor_ratio']:.1%}</div>
            </div>
        </div>
        
        <h2>🎯 原因分布</h2>
        <table>
            <tr>
                <th>原因类型</th>
                <th>数量</th>
                <th>占比</th>
            </tr>
"""
        
        for reason, stats in summary['reason_distribution'].items():
            html += f"""
            <tr>
                <td>{reason}</td>
                <td>{stats['count']}</td>
                <td>{stats['ratio']:.1%}</td>
            </tr>
"""
        
        html += """
        </table>
        
        <h2>💡 改进建议</h2>
"""
        
        for rec in recommendations:
            priority_class = rec['优先级'].lower()
            html += f"""
        <div class="recommendation">
            <span class="priority {priority_class}">{rec['优先级']}</span>
            <strong> {rec['问题']}</strong>
            <p>影响范围: {rec['影响范围']}</p>
            <p>建议措施:</p>
            <ul>
"""
            for suggestion in rec['建议']:
                html += f"                <li>{suggestion}</li>\n"
            
            html += f"""
            </ul>
            <p><em>示例query: {', '.join(rec['示例query'])}</em></p>
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html


class TimelinessAnalysisSystem:
    """时效性分析系统主类"""
    
    def __init__(self, config_path='config.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 配置日志
        self._setup_logging()
        
        # 初始化各模块
        self.preprocessor = DataPreprocessor(self.config)
        self.feature_extractor = FeatureExtractor(self.config)
        self.evaluator = TimelinessEvaluator(self.config)
        self.diagnoser = ReasonDiagnoser(self.config)
        self.reporter = ReportGenerator(self.config)
    
    def _setup_logging(self):
        """配置日志"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'analysis.log')
        
        # 创建日志目录
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def run(self, input_file: str, output_dir: str = './output') -> Dict:
        """运行完整分析流程"""
        logging.info("=" * 50)
        logging.info("搜索引擎时效性分析系统")
        logging.info("=" * 50)
        
        # Step 1: 数据加载与预处理
        logging.info("\n[1/5] 数据加载与预处理...")
        raw_data = self.preprocessor.load_data(input_file)
        processed_data = self.preprocessor.preprocess(raw_data)
        logging.info(f"✓ 成功加载 {len(processed_data)} 个query")
        
        # Step 2: 特征提取与评估
        logging.info("\n[2/5] 特征提取与时效性评估...")
        all_results = []
        
        for idx, query_data in enumerate(processed_data, 1):
            if idx % 100 == 0:
                logging.info(f"  处理进度: {idx}/{len(processed_data)}")
            
            try:
                # 提取特征
                features = self.feature_extractor.extract_features(query_data)
                
                # 评估时效性
                evaluation = self.evaluator.evaluate(features)
                
                # 诊断原因（仅对时效性差的query）
                diagnosis = None
                if evaluation['label'] == '时效性差':
                    diagnosis = self.diagnoser.diagnose(query_data, features, evaluation)
                
                # 汇总结果
                result = {
                    'query': query_data['query'],
                    'features': features,
                    'evaluation': evaluation,
                    'diagnosis': diagnosis
                }
                
                all_results.append(result)
            except Exception as e:
                logging.error(f"处理query失败 '{query_data.get('query', 'unknown')}': {e}")
                continue
        
        logging.info(f"✓ 特征提取与评估完成")
        
        # Step 3: 生成报告
        logging.info("\n[3/5] 生成分析报告...")
        report = self.reporter.generate(all_results)
        logging.info(f"✓ 发现 {report['summary']['poor_timeliness_queries']} 个时效性差的query")
        
        # Step 4: 导出结果
        logging.info("\n[4/5] 导出结果...")
        os.makedirs(output_dir, exist_ok=True)
        
        if self.config['output']['export_json']:
            json_path = os.path.join(output_dir, 'analysis_report.json')
            self.reporter.export_json(report, json_path)
        
        if self.config['output']['export_html']:
            html_path = os.path.join(output_dir, 'analysis_report.html')
            self.reporter.export_html(report, html_path)
        
        if self.config['output']['export_csv']:
            csv_path = os.path.join(output_dir, 'poor_queries.csv')
            self.reporter.export_csv(report, csv_path)
        
        # Step 5: 打印摘要
        logging.info("\n[5/5] 分析完成")
        logging.info("=" * 50)
        self._print_summary(report['summary'])
        logging.info("=" * 50)
        
        return report
    
    def _print_summary(self, summary: Dict):
        """打印摘要信息"""
        logging.info(f"总query数: {summary['total_queries']}")
        logging.info(f"时效性差: {summary['poor_timeliness_queries']} ({summary['poor_ratio']:.1%})")
        logging.info("\n原因分布:")
        for reason, stats in summary['reason_distribution'].items():
            logging.info(f"  {reason}: {stats['count']} ({stats['ratio']:.1%})")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='搜索引擎时效性分析系统')
    parser.add_argument('--input', '-i', required=True, help='输入数据文件路径 (JSON/CSV)')
    parser.add_argument('--output', '-o', default='./output', help='输出目录 (默认: ./output)')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径 (默认: config.yaml)')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        return
    
    # 检查配置文件是否存在
    if not os.path.exists(args.config):
        print(f"错误: 配置文件不存在: {args.config}")
        return
    
    try:
        # 运行分析
        system = TimelinessAnalysisSystem(config_path=args.config)
        report = system.run(input_file=args.input, output_dir=args.output)
        
        print("\n✅ 分析完成！")
        print(f"📁 结果已保存到: {args.output}")
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        logging.exception("系统运行异常")


if __name__ == '__main__':
    main()
