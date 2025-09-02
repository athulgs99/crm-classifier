#!/usr/bin/env python3
"""Test script to verify GitHub integration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from servicenow.client import GitHubClient

def test_github_client():
    """Test GitHub client functionality"""
    print("Testing GitHub client...")
    
    client = GitHubClient()
    
    # Test fetching recent issues
    print("\n1. Fetching recent issues...")
    try:
        issues = client.get_issues(limit=3)
        print(f"✅ Successfully fetched {len(issues)} issues")
        
        if issues:
            print("\nSample issue:")
            issue = issues[0]
            print(f"  Number: {issue['number']}")
            print(f"  Title: {issue['title']}")
            print(f"  Priority: {issue['priority']}")
            print(f"  Owner: {issue['owner']}")
        
    except Exception as e:
        print(f"❌ Error fetching issues: {e}")
        return False
    
    # Test fetching specific issue
    if issues:
        print(f"\n2. Fetching specific issue #{issues[0]['number']}...")
        try:
            specific_issue = client.get_issue_by_number(issues[0]['number'])
            if specific_issue:
                print(f"✅ Successfully fetched issue #{specific_issue['number']}")
            else:
                print("❌ Failed to fetch specific issue")
                return False
        except Exception as e:
            print(f"❌ Error fetching specific issue: {e}")
            return False
    
    print("\n✅ All GitHub tests passed!")
    return True

if __name__ == "__main__":
    test_github_client()
