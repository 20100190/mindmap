#!/usr/bin/env python3
"""
Health check script for the mindmap API.
Can be used for monitoring, deployment verification, etc.
"""
import asyncio
import aiohttp
import sys
import os
import json
import argparse
from typing import Dict, Any, Optional

async def check_health(base_url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Perform health check on the API.
    
    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds
        
    Returns:
        Dict containing health check results
    """
    results = {
        'overall_health': 'unknown',
        'checks': {}
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        
        # Basic health check
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    results['checks']['basic_health'] = {
                        'status': 'healthy',
                        'response_time': response.headers.get('x-response-time', 'unknown'),
                        'data': data
                    }
                else:
                    results['checks']['basic_health'] = {
                        'status': 'unhealthy',
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            results['checks']['basic_health'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # API documentation check
        try:
            async with session.get(f"{base_url}/docs") as response:
                results['checks']['docs_available'] = {
                    'status': 'available' if response.status == 200 else 'unavailable',
                    'status_code': response.status
                }
        except Exception as e:
            results['checks']['docs_available'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Simple API endpoint test (if test query provided)
        test_query = os.getenv('HEALTH_CHECK_TEST_QUERY', 'test mindmap')
        if test_query and test_query != 'skip':
            try:
                payload = {'query': test_query}
                async with session.post(f"{base_url}/api/v1/query", json=payload) as response:
                    if response.status in [200, 400]:  # 400 might be expected for test query
                        results['checks']['query_endpoint'] = {
                            'status': 'responsive',
                            'status_code': response.status
                        }
                    else:
                        results['checks']['query_endpoint'] = {
                            'status': 'error',
                            'status_code': response.status
                        }
            except Exception as e:
                results['checks']['query_endpoint'] = {
                    'status': 'error',
                    'error': str(e)
                }
    
    # Determine overall health
    healthy_checks = sum(1 for check in results['checks'].values() 
                        if check.get('status') in ['healthy', 'available', 'responsive'])
    total_checks = len(results['checks'])
    
    if healthy_checks == total_checks:
        results['overall_health'] = 'healthy'
    elif healthy_checks > total_checks / 2:
        results['overall_health'] = 'degraded'
    else:
        results['overall_health'] = 'unhealthy'
    
    return results

async def main():
    parser = argparse.ArgumentParser(description='Health check for Mindmap API')
    parser.add_argument('--url', default='http://localhost:8001', 
                       help='Base URL of the API (default: http://localhost:8001)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Request timeout in seconds (default: 30)')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--fail-on-unhealthy', action='store_true',
                       help='Exit with code 1 if health check fails')
    
    args = parser.parse_args()
    
    try:
        results = await check_health(args.url, args.timeout)
        
        if args.format == 'json':
            print(json.dumps(results, indent=2))
        else:
            print(f"Overall Health: {results['overall_health'].upper()}")
            print("-" * 50)
            
            for check_name, check_result in results['checks'].items():
                status = check_result.get('status', 'unknown')
                print(f"{check_name}: {status.upper()}")
                
                if 'error' in check_result:
                    print(f"  Error: {check_result['error']}")
                if 'status_code' in check_result:
                    print(f"  Status Code: {check_result['status_code']}")
                if 'response_time' in check_result:
                    print(f"  Response Time: {check_result['response_time']}")
        
        if args.fail_on_unhealthy and results['overall_health'] == 'unhealthy':
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nHealth check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())