#!/usr/bin/env python3
"""
Demo script to populate the Streamlit Time Tracker with sample data
Run this before starting the Streamlit app to see it in action with sample data.
"""

import csv
import os
from datetime import datetime, timedelta, date

def create_sample_data():
    """Create sample time tracking data for demonstration"""

    data_file = 'time_tracking_data.csv'
    fieldnames = ['date', 'project', 'category', 'duration_hours', 'description']

    # Sample data spanning the last 2 weeks
    today = date.today()
    sample_entries = []

    # Week 1 data
    base_date = today - timedelta(days=14)
    sample_entries.extend([
        (base_date, 'Project_A', 'coding', 6.0, 'Authentication system development'),
        (base_date, 'Project_A', 'meeting', 1.5, 'Team standup and planning'),
        (base_date + timedelta(days=1), 'Project_B', 'coding', 5.5, 'Frontend component creation'),
        (base_date + timedelta(days=1), 'Project_B', 'research', 2.0, 'UI/UX best practices research'),
        (base_date + timedelta(days=2), 'Project_C', 'coding', 4.0, 'Database schema design'),
        (base_date + timedelta(days=2), 'Project_A', 'documentation', 2.5, 'API documentation updates'),
        (base_date + timedelta(days=3), 'Project_B', 'coding', 7.0, 'Core feature implementation'),
        (base_date + timedelta(days=3), 'Project_B', 'meeting', 0.5, 'Quick client sync'),
        (base_date + timedelta(days=4), 'Project_C', 'research', 3.0, 'Technology stack evaluation'),
        (base_date + timedelta(days=4), 'Project_A', 'coding', 4.5, 'Bug fixes and optimization'),
    ])

    # Week 2 data (current week)
    base_date = today - timedelta(days=7)
    sample_entries.extend([
        (base_date, 'Project_A', 'meeting', 2.0, 'Sprint planning and retrospective'),
        (base_date, 'Project_A', 'coding', 5.0, 'User interface improvements'),
        (base_date + timedelta(days=1), 'Project_B', 'coding', 6.5, 'Backend API development'),
        (base_date + timedelta(days=1), 'Project_C', 'documentation', 1.5, 'User manual creation'),
        (base_date + timedelta(days=2), 'Project_C', 'coding', 4.0, 'Data processing pipeline'),
        (base_date + timedelta(days=2), 'Project_A', 'meeting', 1.0, 'Code review session'),
        (base_date + timedelta(days=3), 'Project_B', 'coding', 3.5, 'Testing and quality assurance'),
        (base_date + timedelta(days=3), 'Project_B', 'research', 2.5, 'Performance optimization research'),
        (base_date + timedelta(days=4), 'Project_C', 'coding', 5.5, 'Integration and deployment'),
        (base_date + timedelta(days=4), 'Project_A', 'documentation', 1.0, 'README updates'),
    ])

    # Recent data (this week)
    recent_base = today - timedelta(days=4)
    sample_entries.extend([
        (recent_base, 'Project_A', 'coding', 7.5, 'Feature completion and testing'),
        (recent_base + timedelta(days=1), 'Project_B', 'meeting', 1.5, 'Stakeholder presentation'),
        (recent_base + timedelta(days=1), 'Project_B', 'coding', 4.0, 'Bug fixes and improvements'),
        (recent_base + timedelta(days=2), 'Project_C', 'coding', 6.0, 'Final implementation phase'),
        (recent_base + timedelta(days=2), 'Project_A', 'meeting', 0.75, 'Daily standup'),
        (today - timedelta(days=1), 'Project_A', 'coding', 5.0, 'Code cleanup and documentation'),
        (today - timedelta(days=1), 'Project_B', 'research', 2.0, 'Next sprint planning research'),
        (today, 'Project_C', 'coding', 3.0, 'Current development work'),
    ])

    # Create or overwrite the CSV file
    with open(data_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for entry_date, project, category, duration, description in sample_entries:
            writer.writerow({
                'date': entry_date.strftime('%Y-%m-%d'),
                'project': project,
                'category': category,
                'duration_hours': duration,
                'description': description
            })

    print(f"✅ Created sample data with {len(sample_entries)} entries")
    print(f"📁 Data saved to: {data_file}")
    print("\n📊 Sample data summary:")

    # Show summary of created data
    from collections import defaultdict

    project_totals = defaultdict(float)
    category_totals = defaultdict(float)

    for entry_date, project, category, duration, description in sample_entries:
        project_totals[project] += duration
        category_totals[category] += duration

    print("\n🎯 Projects:")
    for project, hours in sorted(project_totals.items()):
        print(f"  {project}: {hours:.1f}h")

    print("\n📋 Categories:")  
    for category, hours in sorted(category_totals.items()):
        print(f"  {category}: {hours:.1f}h")

    total_hours = sum(project_totals.values())
    print(f"\n⏱️  Total Hours: {total_hours:.1f}h")

    print("\n🚀 Now run: streamlit run streamlit_time_tracker.py")

if __name__ == "__main__":
    create_sample_data()
